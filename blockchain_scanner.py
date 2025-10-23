# blockchain_scanner.py
import asyncio
from alert_sender import send_telegram_alert

async def monitor_new_pairs():
    print("Blockchain Scanner: Listening for new token pairs...")
    while True:
        await asyncio.sleep(180)  # check every 3 mins
        message = "💎 NEW PAIR ALERT 💎\nToken: $DEMO\nLiquidity: $5,200"
        await send_telegram_alert(message)
