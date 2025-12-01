import asyncio
import os
import json
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
import database
import requests
import security 

load_dotenv(override=True)
ALCHEMY_URL = os.getenv("ALCHEMY_URL")
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL_ID")
UNISWAP_V2_FACTORY = "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
PAIR_CREATED_ABI = json.loads('[{"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"token0","type":"address"},{"indexed":true,"internalType":"address","name":"token1","type":"address"},{"indexed":false,"internalType":"address","name":"pair","type":"address"},{"indexed":false,"internalType":"uint256","name":"","type":"uint256"}],"name":"PairCreated","type":"event"}]')

def send_telegram(chat_id, text):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown", "disable_web_page_preview": True})
    except Exception as e:
        print(f"Msg Error: {e}")

async def monitor_new_tokens():
    print("🦅 IceAlphaHunter Scanner: CONNECTED.")
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    
    factory_contract = w3.eth.contract(address=UNISWAP_V2_FACTORY, abi=PAIR_CREATED_ABI)
    last_block = w3.eth.block_number

    while True:
        try:
            current_block = w3.eth.block_number
            if current_block > last_block:
                events = factory_contract.events.PairCreated.get_logs(fromBlock=last_block + 1, toBlock=current_block)
                for event in events:
                    args = event['args']
                    token0 = args['token0']
                    pair_addr = args['pair']
                    
                    # 1. Run Security Check
                    score, warnings = security.scan_token_safety(token0)
                    
                    warning_text = ""
                    if warnings:
                        warning_text = "\n⚠️ **RISK WARNINGS:**\n" + "\n".join(warnings)

                    # --- MSG 1: FOR PAID USERS (FULL DATA) ---
                    pro_msg = (
                        f"🆕 *NEW TOKEN DETECTED* 🦅\n"
                        f"-----------------------------\n"
                        f"🛡 **Safety Score:** {score}/100\n"
                        f"🪙 Token: `{token0}`\n"
                        f"🔗 Pair: `{pair_addr}`\n"
                        f"{warning_text}\n"
                        f"-----------------------------\n"
                        f"[View on Etherscan](https://etherscan.io/address/{token0})"
                    )
                    
                    # Broadcast to Paid DB
                    users = database.get_all_paid_users()
                    for user_id in users:
                        send_telegram(user_id, pro_msg)

                    # --- MSG 2: FOR PUBLIC CHANNEL (MARKETING) ---
                    # We hide the score or add a call to action
                    if PUBLIC_CHANNEL:
                        public_msg = (
                            f"🦅 **IceAlphaHunter Alert**\n\n"
                            f"We just detected a new token on Uniswap!\n"
                            f"🪙 Token: `{token0}`\n\n"
                            f"🛡 **Safety Score:** [LOCKED 🔒]\n"
                            f"⚠️ **Risk Analysis:** [LOCKED 🔒]\n\n"
                            f"💡 *Want to see if this token is a Scam or a Gem?*\n"
                            f"👉 [Click Here to Subscribe](https://t.me/IceAlphaHunter_Bot)"
                        )
                        send_telegram(PUBLIC_CHANNEL, public_msg)

                last_block = current_block
            await asyncio.sleep(2)

        except Exception as e:
            print(f"Scanner Error: {e}")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(monitor_new_tokens())
