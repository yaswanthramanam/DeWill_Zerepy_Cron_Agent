import logging
import os
from dotenv import load_dotenv
from src.action_handler import register_action

logger = logging.getLogger("actions.sonic_actions")

@register_action("get-sonic-balance")
def get_sonic_balance(agent, **kwargs):
    """Get SONIC or token balance"""
    try:
        address = kwargs.get("address")
        token_address = kwargs.get("token_address")
        
        if not address:
            load_dotenv()
            private_key = os.getenv('SONIC_PRIVATE_KEY')
            web3 = agent.connection_manager.connections["sonic"]._web3
            account = web3.eth.account.from_key(private_key)
            address = account.address

        balance = agent.connection_manager.connections["sonic"].get_balance(
            address=address,
            token_address=token_address
        )
        
        if token_address:
            logger.info(f"Token Balance: {balance}")
        else:
            logger.info(f"SONIC Balance: {balance}")
            
        return balance

    except Exception as e:
        logger.error(f"Failed to get balance: {str(e)}")
        return None

@register_action("send-sonic")
def send_sonic(agent, **kwargs):
    """Send SONIC tokens to an address"""
    try:
        to_address = kwargs.get("to_address")
        amount = float(kwargs.get("amount"))

        tx_url = agent.connection_manager.connections["sonic"].transfer(
            to_address=to_address,
            amount=amount
        )

        logger.info(f"Transferred {amount} SONIC to {to_address}")
        logger.info(f"\nView transaction: {tx_url}")
        return tx_url

    except Exception as e:
        logger.error(f"Failed to send SONIC: {str(e)}")
        return None

@register_action("send-sonic-token")
def send_sonic_token(agent, **kwargs):
    """Send tokens on Sonic chain"""
    try:
        to_address = kwargs.get("to_address")
        token_address = kwargs.get("token_address")
        amount = float(kwargs.get("amount"))

        tx_url = agent.connection_manager.connections["sonic"].transfer(
            to_address=to_address,
            amount=amount,
            token_address=token_address
        )

        logger.info(f"Transferred {amount} tokens to {to_address}")
        logger.info(f"\nView transaction: {tx_url}")
        return tx_url

    except Exception as e:
        logger.error(f"Failed to send tokens: {str(e)}")
        return None

@register_action("swap-sonic")
def swap_sonic(agent, **kwargs):
    """Swap tokens"""
    try:
        token_in = kwargs.get("token_in")
        token_out = kwargs.get("token_out")
        amount = float(kwargs.get("amount"))
        slippage = float(kwargs.get("slippage", 0.5))

        tx_url = agent.connection_manager.connections["sonic"].swap(
            token_in=token_in,
            token_out=token_out,
            amount=amount,
            slippage=slippage
        )

        logger.info(f"Swapped {amount} tokens")
        logger.info(f"\nView transaction: {tx_url}")
        return tx_url

    except Exception as e:
        logger.error(f"Failed to swap tokens: {str(e)}")
        return None