import asyncio
from alert_sender import send_alert

async def test():
    print("Sending test message...")
    success, response = await send_alert("✅ TEST: Your Sniper Bot is connected and ready to hunt!")
    if success:
        print("✅ Success! Check your Telegram.")
    else:
        print(f"❌ Failed. Response: {response}")

if __name__ == "__main__":
    asyncio.run(test())
