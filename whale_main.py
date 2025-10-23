# whale_main.py
import os
import asyncio
from dotenv import load_dotenv
from flask import Flask, request, jsonify
import tweepy
from alert_sender import send_telegram_alert
from twitter_scanner import monitor_twitter_follows
from blockchain_scanner import monitor_new_pairs

# ========================
# Load environment variables
# ========================
load_dotenv()

# Telegram / Ethereum / Webhook
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
PRIVATE_CHANNEL_ID = os.getenv("PRIVATE_CHANNEL_ID")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
PORT = int(os.getenv("PORT", 8080))

# Twitter API
TWITTER_CONSUMER_KEY = os.getenv("TWITTER_CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.getenv("TWITTER_CONSUMER_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

# Blockchain
ETHEREUM_WALLET = os.getenv("ETHEREUM_WALLET")
ETHEREUM_API_KEY = os.getenv("ETHEREUM_API_KEY")
ALCHEMY_URL = os.getenv("ALCHEMY_URL")

# ========================
# Flask App (Webhook Server)
# ========================
app = Flask(__name__)

@app.route(f"/{WEBHOOK_PATH}", methods=["POST"])
def telegram_webhook():
    update = request.get_json()
    print("Received Telegram update:", update)

    if "message" in update:
        chat_id = update["message"]["chat"]["id"]
        text = update["message"]["text"]

        if text == "/start":
            print(f"User {chat_id} started the bot")
            # Here you can send a welcome message
        elif text == "/balance":
            print(f"User {chat_id} requested wallet balance")
            # Call blockchain API to get balance if needed

    return jsonify(success=True)

@app.route("/")
def index():
    return "Alpha Hunter Network Bot is running.", 200

# ========================
# Twitter Client
# ========================
twitter_client = tweepy.Client(
    consumer_key=TWITTER_CONSUMER_KEY,
    consumer_secret=TWITTER_CONSUMER_SECRET,
    access_token=TWITTER_ACCESS_TOKEN,
    access_token_secret=TWITTER_ACCESS_TOKEN_SECRET
)

# ========================
# Async Runner
# ========================
async def main():
    print("Initializing Alpha Hunter Network...")
    await asyncio.gather(
        monitor_twitter_follows(twitter_client),
        monitor_new_pairs()
    )

# ========================
# Run Flask + Async Scanners
# ========================
if __name__ == "__main__":
    # Run async scanners in background
    loop = asyncio.get_event_loop()
    loop.create_task(main())

    # Run Flask webhook server
    app.run(host="0.0.0.0", port=PORT)
