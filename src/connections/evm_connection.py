import logging
import os
import time
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv, set_key
from web3 import Web3
from web3.middleware import geth_poa_middleware
from src.constants.networks import EVM_NETWORKS
from src.connections.base_connection import BaseConnection, Action, ActionParameter

logger = logging.getLogger("connections.evm_connection")

class EVMConnectionError(Exception):
    """Base exception for EVM connection errors"""
    pass

class EVMConnection(BaseConnection):
    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing EVM connection...")
        self._web3 = None
        
        # Get network configuration
        network = config.get("network", "ethereum")
        if network not in EVM_NETWORKS:
            raise ValueError(f"Invalid network '{network}'. Must be one of: {', '.join(EVM_NETWORKS.keys())}")
            
        network_config = EVM_NETWORKS[network]
        self.rpc_url = network_config["rpc_url"]
        self.scanner_url = network_config["scanner_url"]
        self.chain_id = network_config["chain_id"]
        
        super().__init__(config)
        self._initialize_web3()

        self.ERC20_ABI = [
            {
                "constant": True,
                "inputs": [{"name": "_owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "balance", "type": "uint256"}],
                "type": "function"
            },
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            },
            {
                "constant": False,
                "inputs": [
                    {"name": "_to", "type": "address"},
                    {"name": "_value", "type": "uint256"}
                ],
                "name": "transfer",
                "outputs": [{"name": "", "type": "bool"}],
                "type": "function"
            }
        ]

        # Configure aggregator API endpoint
        self.aggregator_api = "https://aggregator-api.kyberswap.com/{network}/api/v1"  # Replace with actual aggregator API

    def _get_explorer_link(self, tx_hash: str) -> str:
        """Generate block explorer link for transaction"""
        return f"https://{self.scanner_url}/tx/{tx_hash}"

    def _initialize_web3(self):
        """Initialize Web3 connection"""
        if not self._web3:
            self._web3 = Web3(Web3.HTTPProvider(self.rpc_url))
            self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if not self._web3.is_connected():
                raise EVMConnectionError("Failed to connect to EVM network")
            
            try:
                chain_id = self._web3.eth.chain_id
                logger.info(f"Connected to EVM network with chain ID: {chain_id}")
            except Exception as e:
                logger.warning(f"Could not get chain ID: {e}")

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate EVM configuration from JSON"""
        if "network" not in config:
            raise ValueError("Missing 'network' in config")
        if config["network"] not in EVM_NETWORKS:
            raise ValueError(f"Invalid network '{config['network']}'. Must be one of: {', '.join(EVM_NETWORKS.keys())}")
        return config

    def register_actions(self) -> None:
        """Register available EVM actions"""
        self.actions = {
            "get-token-by-ticker": Action(
                name="get-token-by-ticker",
                parameters=[
                    ActionParameter("ticker", True, str, "Token ticker symbol to look up")
                ],
                description="Get token address by ticker symbol"
            ),
            "get-balance": Action(
                name="get-balance",
                parameters=[
                    ActionParameter("address", False, str, "Address to check balance for"),
                    ActionParameter("token_address", False, str, "Optional token address")
                ],
                description="Get native or token balance"
            ),
            "transfer": Action(
                name="transfer",
                parameters=[
                    ActionParameter("to_address", True, str, "Recipient address"),
                    ActionParameter("amount", True, float, "Amount to transfer"),
                    ActionParameter("token_address", False, str, "Optional token address")
                ],
                description="Send native tokens or ERC20 tokens"
            ),
            "swap": Action(
                name="swap",
                parameters=[
                    ActionParameter("token_in", True, str, "Input token address"),
                    ActionParameter("token_out", True, str, "Output token address"),
                    ActionParameter("amount", True, float, "Amount to swap"),
                    ActionParameter("slippage", False, float, "Max slippage percentage")
                ],
                description="Swap tokens using aggregator"
            )
        }

    def configure(self) -> bool:
        logger.info("\n⛓️ EVM CHAIN SETUP")
        if self.is_configured():
            logger.info("EVM connection is already configured")
            response = input("Do you want to reconfigure? (y/n): ")
            if response.lower() != 'y':
                return True

        try:
            if not os.path.exists('.env'):
                with open('.env', 'w') as f:
                    f.write('')

            private_key = input("\nEnter your wallet private key: ")
            if not private_key.startswith('0x'):
                private_key = '0x' + private_key
            
            scanner_api_key = input("\nEnter your Explorer API key (optional): ")
            
            set_key('.env', 'EVM_PRIVATE_KEY', private_key)
            if scanner_api_key:
                set_key('.env', f"{self.config['network'].upper()}_SCAN_API_KEY", scanner_api_key)

            if not self._web3.is_connected():
                raise EVMConnectionError("Failed to connect to EVM network")

            account = self._web3.eth.account.from_key(private_key)
            logger.info(f"\n✅ Successfully connected with address: {account.address}")
            return True

        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

    def is_configured(self, verbose: bool = False) -> bool:
        try:
            load_dotenv()
            if not os.getenv('EVM_PRIVATE_KEY'):
                if verbose:
                    logger.error("Missing EVM_PRIVATE_KEY in .env")
                return False

            if not self._web3.is_connected():
                if verbose:
                    logger.error("Not connected to EVM network")
                return False
            return True

        except Exception as e:
            if verbose:
                logger.error(f"Configuration check failed: {e}")
            return False

    def get_token_by_ticker(self, ticker: str) -> Optional[str]:
        """Get token address by ticker symbol using the configured block explorer"""
        try:
            response = requests.get(
                f"https://api.dexscreener.com/latest/dex/search?q={ticker}"
            )
            response.raise_for_status()

            data = response.json()
            if not data.get('pairs'):
                return None

            # Filter pairs for the current network
            network_pairs = [
                pair for pair in data["pairs"] 
                if pair.get("networkId", "").lower() == self.config.get('network', 'ethereum').lower()
            ]
            
            # Sort by liquidity (or FDV as a fallback)
            network_pairs.sort(key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or x.get('fdv', 0)), reverse=True)

            # Filter for exact ticker match
            network_pairs = [
                pair for pair in network_pairs
                if pair.get("baseToken", {}).get("symbol", "").lower() == ticker.lower()
            ]

            if network_pairs:
                return network_pairs[0].get("baseToken", {}).get("address")
            return None

        except Exception as error:
            logger.error(f"Error fetching token address: {str(error)}")
            return None

    def get_balance(self, address: Optional[str] = None, token_address: Optional[str] = None) -> float:
        """Get balance for an address or the configured wallet"""
        try:
            if not address:
                private_key = os.getenv('EVM_PRIVATE_KEY')
                if not private_key:
                    raise EVMConnectionError("No wallet configured")
                account = self._web3.eth.account.from_key(private_key)
                address = account.address

            if token_address:
                contract = self._web3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.ERC20_ABI
                )
                balance = contract.functions.balanceOf(address).call()
                decimals = contract.functions.decimals().call()
                return balance / (10 ** decimals)
            else:
                balance = self._web3.eth.get_balance(address)
                return self._web3.from_wei(balance, 'ether')

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise

    def transfer(self, to_address: str, amount: float, token_address: Optional[str] = None) -> str:
        """Transfer native tokens or ERC20 tokens to an address"""
        try:
            private_key = os.getenv('EVM_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)
            
            if token_address:
                contract = self._web3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.ERC20_ABI
                )
                decimals = contract.functions.decimals().call()
                amount_raw = int(amount * (10 ** decimals))
                
                tx = contract.functions.transfer(
                    Web3.to_checksum_address(to_address),
                    amount_raw
                ).build_transaction({
                    'from': account.address,
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'gasPrice': self._web3.eth.gas_price,
                    'chainId': self.chain_id
                })
            else:
                tx = {
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'to': Web3.to_checksum_address(to_address),
                    'value': self._web3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': self._web3.eth.gas_price,
                    'chainId': self.chain_id
                }

            signed = account.sign_transaction(tx)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            return self._get_explorer_link(tx_hash.hex())

        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            raise

    def _get_swap_route(self, token_in: str, token_out: str, amount_in: float) -> Dict:
        """Get the best swap route from aggregator API"""
        try:
            # Handle native token address
            NATIVE_TOKEN = "0x0000000000000000000000000000000000000000"
            
            # Convert amount to raw value
            if token_in.lower() == NATIVE_TOKEN.lower():
                amount_raw = self._web3.to_wei(amount_in, 'ether')
            else:
                token_contract = self._web3.eth.contract(
                    address=Web3.to_checksum_address(token_in),
                    abi=self.ERC20_ABI
                )
                decimals = token_contract.functions.decimals().call()
                amount_raw = int(amount_in * (10 ** decimals))
            
            # Get route from aggregator API
            url = f"{self.aggregator_api}/route"
            headers = {"x-client-id": "zerepy"}
            params = {
                "tokenIn": token_in,
                "tokenOut": token_out,
                "amount": str(amount_raw),
                "chainId": self.chain_id
            }
            
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            return response.json()
                
        except Exception as e:
            logger.error(f"Failed to get swap route: {e}")
            raise

    def _get_encoded_swap_data(self, route_data: Dict, slippage: float = 0.5) -> str:
        """Get encoded swap data from aggregator API"""
        try:
            private_key = os.getenv('EVM_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)
            
            url = f"{self.aggregator_api}/build"
            headers = {"x-client-id": "zerepy"}
            
            payload = {
                "route": route_data,
                "sender": account.address,
                "recipient": account.address,
                "slippage": slippage,
                "deadline": int(time.time() + 1200),  # 20 minutes
                "chainId": self.chain_id
            }
            
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            return response.json()["data"]
                
        except Exception as e:
            logger.error(f"Failed to encode swap data: {e}")
            raise

    def _handle_token_approval(self, token_address: str, spender_address: str, amount: int) -> None:
        """Handle token approval for spender"""
        try:
            private_key = os.getenv('EVM_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)
            
            token_contract = self._web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=self.ERC20_ABI
            )
            
            # Check current allowance
            current_allowance = token_contract.functions.allowance(
                account.address,
                spender_address
            ).call()
            
            if current_allowance < amount:
                approve_tx = token_contract.functions.approve(
                    spender_address,
                    amount
                ).build_transaction({
                    'from': account.address,
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'gasPrice': self._web3.eth.gas_price,
                    'chainId': self.chain_id
                })
                
                signed_approve = account.sign_transaction(approve_tx)
                tx_hash = self._web3.eth.send_raw_transaction(signed_approve.rawTransaction)
                logger.info(f"Approval transaction sent: {self._get_explorer_link(tx_hash.hex())}")
                
                # Wait for approval to be mined
                self._web3.eth.wait_for_transaction_receipt(tx_hash)
                
        except Exception as e:
            logger.error(f"Approval failed: {e}")
            raise

    def swap(self, token_in: str, token_out: str, amount: float, slippage: float = 0.5) -> str:
        """Execute a token swap using the KyberSwap router"""
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)

            # Check token balance before proceeding
            current_balance = self.get_balance(
                address=account.address,
                token_address=None if token_in.lower() == NATIVE_TOKEN.lower() else token_in
            )
            
            if current_balance < amount:
                raise ValueError(f"Insufficient balance. Required: {amount}, Available: {current_balance}")
                
            # Get optimal swap route
            route_data = self._get_swap_route(token_in, token_out, amount)
            
            # Get encoded swap data
            encoded_data = self._get_encoded_swap_data(route_data["routeSummary"], slippage)
            
            # Get router address from route data
            router_address = route_data["routerAddress"]
            
            # Handle token approval if not using native token
            if token_in.lower() != NATIVE_TOKEN.lower():
                if token_in.lower() == "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc223".lower():  # $wETH token
                    amount_raw = self._web3.to_wei(amount, 'ether')
                else:
                    token_contract = self._web3.eth.contract(
                        address=Web3.to_checksum_address(token_in),
                        abi=self.ERC20_ABI
                    )
                    decimals = token_contract.functions.decimals().call()
                    amount_raw = int(amount * (10 ** decimals))
                self._handle_token_approval(token_in, router_address, amount_raw)
            
            # Prepare transaction
            tx = {
                'from': account.address,
                'to': Web3.to_checksum_address(router_address),
                'data': encoded_data,
                'nonce': self._web3.eth.get_transaction_count(account.address),
                'gasPrice': self._web3.eth.gas_price,
                'chainId': self._web3.eth.chain_id,
                'value': self._web3.to_wei(amount, 'ether') if token_in.lower() == self.NATIVE_TOKEN.lower() else 0
            }
            
            # Estimate gas
            try:
                tx['gas'] = self._web3.eth.estimate_gas(tx)
            except Exception as e:
                logger.warning(f"Gas estimation failed: {e}, using default gas limit")
                tx['gas'] = 500000  # Default gas limit
            
            # Sign and send transaction
            signed_tx = account.sign_transaction(tx)
            tx_hash = self._web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Log and return explorer link immediately
            tx_link = self._get_explorer_link(tx_hash.hex())
            return f"\n🔄 Swap transaction sent: {tx_link}"
                
        except Exception as e:
            logger.error(f"Swap failed: {e}")
            raise
    def perform_action(self, action_name: str, kwargs) -> Any:
        """Execute a Sonic action with validation"""
        if action_name not in self.actions:
            raise KeyError(f"Unknown action: {action_name}")

        load_dotenv()
        
        if not self.is_configured(verbose=True):
            raise SonicConnectionError("Sonic is not properly configured")

        action = self.actions[action_name]
        errors = action.validate_params(kwargs)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")

        method_name = action_name.replace('-', '_')
        method = getattr(self, method_name)
        return method(**kwargs)