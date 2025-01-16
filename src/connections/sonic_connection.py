import logging
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv, set_key
from web3 import Web3
from web3.middleware import geth_poa_middleware
from src.connections.base_connection import BaseConnection, Action, ActionParameter

logger = logging.getLogger("connections.sonic_connection")

class SonicConnectionError(Exception):
    """Base exception for Sonic connection errors"""
    pass

class SonicConnection(BaseConnection):
    def __init__(self, config: Dict[str, Any]):
        logger.info("Initializing Sonic connection...")
        self._web3 = None
        self.network = config.get("network", "mainnet")
        self.explorer = config.get("scanner", "https://sonicscan.org")
        super().__init__(config)
        self._initialize_web3()

    def _get_explorer_link(self, tx_hash: str) -> str:
        """Generate block explorer link for transaction"""
        return f"{self.explorer}/tx/{tx_hash}"

    def _initialize_web3(self):
        """Initialize Web3 connection"""
        if not self._web3:
            rpc_url = self.config["rpc_url"]
            self._web3 = Web3(Web3.HTTPProvider(rpc_url))
            self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if not self._web3.is_connected():
                raise SonicConnectionError("Failed to connect to Sonic network")
            
            # Log the chain ID we're connected to
            try:
                chain_id = self._web3.eth.chain_id
                logger.info(f"Connected to network with chain ID: {chain_id}")
            except Exception as e:
                logger.warning(f"Could not get chain ID: {e}")

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        required = ["rpc_url", "network"]
        missing = [field for field in required if field not in config]
        if missing:
            raise ValueError(f"Missing config fields: {', '.join(missing)}")
        return config

    def register_actions(self) -> None:
        self.actions = {
            "get-balance": Action(
                name="get-balance",
                parameters=[
                    ActionParameter("address", False, str, "Address to check balance for (optional - uses configured wallet if not provided)"),
                    ActionParameter("token_address", False, str, "Optional token address")
                ],
                description="Get $S or token balance"
            ),
            "transfer": Action(
                name="transfer",
                parameters=[
                    ActionParameter("to_address", True, str, "Recipient address"),
                    ActionParameter("amount", True, float, "Amount to transfer"),
                    ActionParameter("token_address", False, str, "Optional token address")
                ],
                description="Send $S or tokens"
            ),
            "swap": Action(
                name="swap",
                parameters=[
                    ActionParameter("token_in", True, str, "Input token address"),
                    ActionParameter("token_out", True, str, "Output token address"),
                    ActionParameter("amount", True, float, "Amount to swap"),
                    ActionParameter("slippage", False, float, "Max slippage percentage")
                ],
                description="Swap tokens"
            )
        }

    def configure(self) -> bool:
        logger.info("\n🔷 SONIC CHAIN SETUP")
        if self.is_configured():
            logger.info("Sonic connection is already configured")
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
            set_key('.env', 'SONIC_PRIVATE_KEY', private_key)

            if not self._web3.is_connected():
                raise SonicConnectionError("Failed to connect to Sonic network")

            account = self._web3.eth.account.from_key(private_key)
            logger.info(f"\n✅ Successfully connected with address: {account.address}")
            return True

        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

    def is_configured(self, verbose: bool = False) -> bool:
        try:
            load_dotenv()
            if not os.getenv('SONIC_PRIVATE_KEY'):
                if verbose:
                    logger.error("Missing SONIC_PRIVATE_KEY in .env")
                return False

            if not self._web3.is_connected():
                if verbose:
                    logger.error("Not connected to Sonic network")
                return False
            return True

        except Exception as e:
            if verbose:
                logger.error(f"Configuration check failed: {e}")
            return False

    def get_balance(self, address: Optional[str] = None, token_address: Optional[str] = None) -> float:
        """
        Get balance for an address or the configured wallet
        
        Args:
            address: Optional address to check. Uses configured wallet if not provided
            token_address: Optional token address to check balance for
        """
        try:
            if not address:
                # Use configured wallet
                private_key = os.getenv('SONIC_PRIVATE_KEY')
                if not private_key:
                    raise SonicConnectionError("No wallet configured")
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
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)
            
            # Get the chain ID
            chain_id = self._web3.eth.chain_id
            
            if token_address:
                # Transfer ERC20 token
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
                    'chainId': chain_id  # Add chain ID for EIP-155 protection
                })
            else:
                # Transfer native SONIC
                tx = {
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'to': Web3.to_checksum_address(to_address),
                    'value': self._web3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': self._web3.eth.gas_price,
                    'chainId': chain_id  # Add chain ID for EIP-155 protection
                }

            signed = account.sign_transaction(tx)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            
            return self._get_explorer_link(tx_hash.hex())

        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            raise

    def swap(self, token_in: str, token_out: str, amount: float, slippage: float = 0.5) -> str:
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)

            router_address = "0x..." # Add actual router address 
            router = self._web3.eth.contract(
                address=router_address,
                abi=self.ROUTER_ABI
            )

            token_contract = self._web3.eth.contract(
                address=Web3.to_checksum_address(token_in),
                abi=self.ERC20_ABI
            )
            decimals = token_contract.functions.decimals().call()
            amount_in = int(amount * (10 ** decimals))
            
            amounts_out = router.functions.getAmountsOut(
                amount_in,
                [Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)]
            ).call()
            min_amount_out = int(amounts_out[1] * (1 - slippage/100))

            # Approve router if needed
            allowance = token_contract.functions.allowance(account.address, router_address).call()
            if allowance < amount_in:
                approve_tx = token_contract.functions.approve(
                    router_address,
                    amount_in
                ).build_transaction({
                    'from': account.address,
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'gasPrice': self._web3.eth.gas_price
                })
                signed = account.sign_transaction(approve_tx)
                tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
                self._web3.eth.wait_for_transaction_receipt(tx_hash)

            # Build swap transaction
            deadline = self._web3.eth.get_block('latest')['timestamp'] + 1200
            swap_tx = router.functions.swapExactTokensForTokens(
                amount_in,
                min_amount_out,
                [Web3.to_checksum_address(token_in), Web3.to_checksum_address(token_out)],
                account.address,
                deadline
            ).build_transaction({
                'from': account.address,
                'nonce': self._web3.eth.get_transaction_count(account.address),
                'gasPrice': self._web3.eth.gas_price
            })

            signed = account.sign_transaction(swap_tx)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            
            logger.info(f"\nView transaction: {tx_url}")
            return None

        except Exception as e:
            logger.error(f"Swap failed: {e}")
            raise

    def perform_action(self, action_name: str, kwargs) -> Any:
        """Execute a Sonic action with validation"""
        if action_name not in self.actions:
            raise KeyError(f"Unknown action: {action_name}")

        # Explicitly reload environment variables
        load_dotenv()
        
        if not self.is_configured(verbose=True):
            raise SonicConnectionError("Sonic is not properly configured")

        action = self.actions[action_name]
        errors = action.validate_params(kwargs)
        if errors:
            raise ValueError(f"Invalid parameters: {', '.join(errors)}")

        # Call the appropriate method based on action name
        method_name = action_name.replace('-', '_')
        method = getattr(self, method_name)
        return method(**kwargs)

    # Standard token interface ABI
    ERC20_ABI = [
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
        },
        {
            "constant": True,
            "inputs": [
                {"name": "_owner", "type": "address"},
                {"name": "_spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": False,
            "inputs": [
                {"name": "_spender", "type": "address"},
                {"name": "_value", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [{"name": "", "type": "bool"}],
            "type": "function"
        }
    ]

    ROUTER_ABI = [
        {
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMin", "type": "uint256"},
                {"name": "path", "type": "address[]"},
                {"name": "to", "type": "address"},
                {"name": "deadline", "type": "uint256"}
            ],
            "name": "swapExactTokensForTokens",
            "outputs": [{"name": "amounts", "type": "uint256[]"}],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "amountIn", "type": "uint256"},
                {"name": "path", "type": "address[]"}
            ],
            "name": "getAmountsOut",
            "outputs": [{"name": "amounts", "type": "uint256[]"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]