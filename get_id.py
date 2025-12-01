import asyncio
import os
import requests
from dotenv import load_dotenv

load_dotenv(override=True)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def get_updates():
    url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
    resp = requests.get(url).json()
    if not resp.get("ok"):
        print("❌ Error:", resp)
        return

    results = resp.get("result", [])
    if not results:
        print("📭 No messages found. Please send 'hello' to your channel first!")
        return

    # Get the last message
    last = results[-1]
    if "channel_post" in last:
        chat = last["channel_post"]["chat"]
        print(f"\n✅ FOUND CHANNEL ID: {chat['id']}")
        print(f"Name: {chat.get('title')}")
    elif "message" in last:
        chat = last["message"]["chat"]
        print(f"\n✅ FOUND CHAT ID: {chat['id']}")
        print(f"Type: {chat['type']}")
    else:
        print(last)

if __name__ == "__main__":
    get_updates()
