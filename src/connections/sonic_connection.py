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
        super().__init__(config)
        self._initialize_web3()

    def _initialize_web3(self):
        """Initialize Web3 connection"""
        if not self._web3:
            rpc_url = self.config["rpc_url"]
            self._web3 = Web3(Web3.HTTPProvider(rpc_url))
            self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if not self._web3.is_connected():
                raise SonicConnectionError("Failed to connect to Sonic network")

    @property
    def is_llm_provider(self) -> bool:
        return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate Sonic configuration"""
        required = ["rpc_url", "network"]
        missing = [field for field in required if field not in config]
        if missing:
            raise ValueError(f"Missing config fields: {', '.join(missing)}")
        return config

    def register_actions(self) -> None:
        """Register available Sonic actions"""
        self.actions = {
            "get-balance": Action(
                name="get-balance",
                parameters=[
                    ActionParameter("address", True, str, "Address to check balance for"),
                    ActionParameter("token_address", False, str, "Optional token address")
                ],
                description="Get SONIC or token balance"
            ),
            "transfer": Action(
                name="transfer",
                parameters=[
                    ActionParameter("to_address", True, str, "Recipient address"),
                    ActionParameter("amount", True, float, "Amount to transfer"),
                    ActionParameter("token_address", False, str, "Optional token address")
                ],
                description="Send SONIC or tokens"
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
        """Configure Sonic connection"""
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

            # Save to .env
            set_key('.env', 'SONIC_PRIVATE_KEY', private_key)

            # Validate connection
            if not self._web3.is_connected():
                raise SonicConnectionError("Failed to connect to Sonic network")

            # Validate private key by deriving address
            account = self._web3.eth.account.from_key(private_key)
            logger.info(f"\n✅ Successfully connected with address: {account.address}")
            return True

        except Exception as e:
            logger.error(f"Configuration failed: {e}")
            return False

    def is_configured(self, verbose: bool = False) -> bool:
        """Check if connection is configured"""
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

    async def get_balance(self, address: str, token_address: Optional[str] = None) -> float:
        """Get SONIC or token balance"""
        try:
            if token_address:
                # Get ERC20 token balance
                contract = self._web3.eth.contract(
                    address=Web3.to_checksum_address(token_address),
                    abi=self.ERC20_ABI
                )
                balance = contract.functions.balanceOf(address).call()
                decimals = contract.functions.decimals().call()
                return balance / (10 ** decimals)
            else:
                # Get native SONIC balance
                balance = self._web3.eth.get_balance(address)
                return self._web3.from_wei(balance, 'ether')

        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            raise

    async def transfer(self, to_address: str, amount: float, token_address: Optional[str] = None) -> str:
        """Transfer SONIC or tokens"""
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)
            
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
                })
            else:
                # Transfer native SONIC
                tx = {
                    'nonce': self._web3.eth.get_transaction_count(account.address),
                    'to': Web3.to_checksum_address(to_address),
                    'value': self._web3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': self._web3.eth.gas_price
                }

            signed = account.sign_transaction(tx)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Transfer failed: {e}")
            raise

    async def swap(self, token_in: str, token_out: str, amount: float, slippage: float = 0.5) -> str:
        """Swap tokens using SonicSwap"""
        try:
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            account = self._web3.eth.account.from_key(private_key)

            # Get SonicSwap router contract
            router_address = "0x..." # Add actual router address
            router = self._web3.eth.contract(
                address=router_address,
                abi=self.ROUTER_ABI
            )

            # Calculate amounts
            token_contract = self._web3.eth.contract(
                address=Web3.to_checksum_address(token_in),
                abi=self.ERC20_ABI
            )
            decimals = token_contract.functions.decimals().call()
            amount_in = int(amount * (10 ** decimals))
            
            # Calculate minimum output amount
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
                })
                signed = account.sign_transaction(approve_tx)
                self._web3.eth.send_raw_transaction(signed.rawTransaction)

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
            })

            signed = account.sign_transaction(swap_tx)
            tx_hash = self._web3.eth.send_raw_transaction(signed.rawTransaction)
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Swap failed: {e}")
            raise

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

    # SonicSwap Router ABI (partial)
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