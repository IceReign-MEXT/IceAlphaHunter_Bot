#!/usr/bin/env python3
import os
import requests
import asyncio
from dotenv import load_dotenv

# FIX: Force override to ignore cached shell variables
load_dotenv(override=True)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEFAULT_CHANNEL = os.getenv("PRIVATE_CHANNEL_ID")

def _post_message_sync(chat_id, text):
    """Low-level synchronous POST to Telegram API."""
    if not BOT_TOKEN:
        print("alert_sender: BOT_TOKEN not configured")
        return False, "no-token"
    
    # Use default channel if no specific chat_id provided
    target = chat_id if chat_id is not None else DEFAULT_CHANNEL
    
    # Clean up the token just in case whitespace got in
    token_clean = BOT_TOKEN.strip()
    url = f"https://api.telegram.org/bot{token_clean}/sendMessage"
    
    payload = {
        "chat_id": target,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            return True, r.text
        else:
            return False, f"Error {r.status_code}: {r.text}"
    except Exception as e:
        return False, str(e)

async def send_alert(text, chat_id=None):
    """Async wrapper for sending alerts."""
    loop = asyncio.get_event_loop()
    ok, resp = await loop.run_in_executor(None, _post_message_sync, chat_id, text)
    if not ok:
        print(f"⚠️ Telegram Fail: {resp}")
    return ok, resp

# Self-test when run directly
if __name__ == "__main__":
    from sys import argv
    msg = argv[1] if len(argv) > 1 else "Test from alert_sender.py"
    ok, r = _post_message_sync(None, msg)
    print("Result:", r)
