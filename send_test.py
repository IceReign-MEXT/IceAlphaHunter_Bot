import os
import requests

# Telegram bot token
BOT_TOKEN = "8324510631:AAFW6iKXcbvfgNdeCK43LhGqqdOoo11czHs"

# Your Telegram chat ID (replace this number if needed)
CHAT_ID = "6453658778"

# Message text
TEXT = "Test message from IceAlphaHunter Bot ✅"

# Send message
url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
payload = {
    "chat_id": CHAT_ID,
    "text": TEXT,
    "parse_mode": "Markdown",
    "disable_web_page_preview": True
}

response = requests.post(url, json=payload)

print("Status:", response.status_code)
print("Response:", response.text)
