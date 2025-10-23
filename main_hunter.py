import asyncio
import os
from dotenv import load_dotenv

from blockchain_scanner import monitor_new_tokens
from alert_manager import alert_user

load_dotenv()

async def main():
    print("🚀 Starting IceAlphaHunter Bot Network...")

    try:
        await asyncio.gather(
            monitor_new_tokens(),
        )
    except Exception as e:
        print(f"[⚠️ ERROR] {e}")
        await alert_user(f"⚠️ Hunter bot crashed with error:\n{e}")

if __name__ == "__main__":
    asyncio.run(main())
