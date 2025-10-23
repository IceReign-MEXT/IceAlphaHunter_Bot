#!/usr/bin/env python3
"""
alert_sender.py

Provides:
- async send_alert(message, chat_id=None)  -> awaitable for async code
- send_alert_sync(chat_id, message)        -> sync helper for scripts
Reads BOT token and default channel from .env
"""
import os
import requests
import asyncio
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
DEFAULT_CHANNEL = os.getenv("PRIVATE_CHANNEL_ID")  # use channel id or owner chat id

def _post_message_sync(chat_id, text):
    """Low-level synchronous POST to Telegram API."""
    if not BOT_TOKEN:
        print("alert_sender: BOT_TOKEN not configured")
        return False, "no-token"
    target = chat_id if chat_id is not None else DEFAULT_CHANNEL
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": target,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    try:
        r = requests.post(url, json=payload, timeout=8)
        if r.status_code == 200:
            return True, r.text
        else:
            return False, r.text
    except Exception as e:
        return False, str(e)

async def send_alert(text, chat_id=None):
    """
    Async-friendly send function. Use inside async loops:
      await send_alert('message here')
    """
    loop = asyncio.get_event_loop()
    ok, resp = await loop.run_in_executor(None, _post_message_sync, chat_id, text)
    if not ok:
        # print error locally; in production you may log and retry
        print("send_alert failed:", resp)
    return ok, resp

def send_alert_sync(chat_id, text):
    """Synchronous wrapper (blocking)."""
    ok, resp = _post_message_sync(chat_id, text)
    return ok, resp

# quick test when run directly
if __name__ == "__main__":
    ok, r = send_alert_sync(None, "Alert sender test ✅")
    print("OK:", ok)
    print(r)
