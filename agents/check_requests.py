import os
import time
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

NETWORKS = {
    "sonic": {
        "rpc": os.getenv("SONIC_RPC", "https://rpc.blaze.soniclabs.com"),
        "contract_address": "0x5170DC48cb64F0DEe4Bd658Bf942F23E4f72f2Bf",
        "abi_path": "./abi.json"
    },
    "monad": {
        "rpc": os.getenv("MONAD_RPC", "https://testnet-rpc.monad.xyz/"),
        "contract_address": "0x0Ae3b3c65D1242EE40DcDD3f8440C2424abA3789",
        "abi_path": "./abi.json"
    }
}

contracts = {}
for network, config in NETWORKS.items():
    w3 = Web3(Web3.HTTPProvider(config["rpc"]))
    with open(config["abi_path"], "r") as f:
        abi = json.load(f)
    contracts[network] = w3.eth.contract(address=config["contract_address"], abi=abi)

EMAILJS_SERVICE_ID = os.getenv("EMAILJS_SERVICE_ID", "dewill")
EMAILJS_TEMPLATE_ID = os.getenv("EMAILJS_TEMPLATE_ID", "dewill_template")
EMAILJS_PUBLIC_KEY = os.getenv("EMAILJS_PUBLIC_KEY")
EMAILJS_PRIVATE_KEY = os.getenv("EMAILJS_PRIVATE_KEY")
EMAILJS_API_URL = "https://api.emailjs.com/api/v1.0/email/send"

def send_email(to_email, to_name, percentage, code, network):
    message = (
        f"Dear {to_name},\n\n"
        f"Your {percentage}% of funds from the {network.capitalize()} network are now available! "
        f"Use this code: {code} at http://localhost:5173/redeem to claim your funds.\n\n"
        f"Best regards,\nNed Stark"
    )
    payload = {
        "service_id": EMAILJS_SERVICE_ID,
        "template_id": EMAILJS_TEMPLATE_ID,
        "user_id": EMAILJS_PUBLIC_KEY,
        "accessToken": EMAILJS_PRIVATE_KEY,
        "template_params": {
            "to_email": to_email,
            "to_name": to_name,
            "message": message,
            "from_name": "Ned Stark"
        }
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(EMAILJS_API_URL, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Email sent to {to_email} for {network}")
    else:
        print(f"Email failed for {network}: {response.status_code} - {response.text}")

def check_requests():
    try:
        current_time = int(time.time())

        for network, contract in contracts.items():
            wallets = contract.functions.getKeys().call()
            print(wallets)

            for wallet in wallets:
                requests = contract.functions.getRequests(wallet).call()
                print(requests)
                for req in requests:
                    print(req)
                    email, code, percentage, reason, timestamp = req
                    print(email)
                    print(code)
                    if timestamp <= current_time:
                        print(timestamp)
                        print(current_time)
                        to_name = code.split("_")[1] if "_" in code else "Recipient"
                        print("success")

    except Exception as e:
        print(f"Error checking requests: {e}")

if __name__ == "__main__":
    while True:
        check_requests()
        time.sleep(60)