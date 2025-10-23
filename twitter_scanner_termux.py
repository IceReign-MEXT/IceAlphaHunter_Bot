import os
import tweepy
import asyncio
from aiohttp import ClientSession
from dotenv import load_dotenv

# --- Termux-safe .env loader ---
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if not os.path.exists(env_path):
    raise FileNotFoundError(f"❌ .env file not found at {env_path}")
else:
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded environment from {env_path}")

# --- Verify required environment variables ---
required_keys = [
    "TWITTER_CONSUMER_KEY", "TWITTER_CONSUMER_SECRET",
    "TWITTER_ACCESS_TOKEN", "TWITTER_ACCESS_TOKEN_SECRET",
    "TELEGRAM_BOT_TOKEN", "PRIVATE_CHANNEL_ID"
]
for key in required_keys:
    if not os.getenv(key):
        raise EnvironmentError(f"❌ Missing environment variable: {key}")
    else:
        print(f"✅ {key} loaded")

# --- 1. Twitter Authentication ---
auth = tweepy.OAuth1UserHandler(
    os.getenv("TWITTER_CONSUMER_KEY"),
    os.getenv("TWITTER_CONSUMER_SECRET"),
    os.getenv("TWITTER_ACCESS_TOKEN"),
    os.getenv("TWITTER_ACCESS_TOKEN_SECRET")
)
api = tweepy.API(auth)

# --- 2. Telegram alert async function ---
async def send_telegram_alert(message):
    url = f"https://api.telegram.org/bot{os.getenv('TELEGRAM_BOT_TOKEN')}/sendMessage"
    payload = {
        "chat_id": os.getenv("PRIVATE_CHANNEL_ID"),
        "text": message,
        "parse_mode": "Markdown"
    }
    async with ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            print(f"📩 Alert sent, status: {resp.status}")

# --- 3. Monitor new follows from a list of influencers ---
async def monitor_influencers():
    influencers = ["", ""]  # Add any handles you like
    previous_follows = {}

    while True:
        for influencer in influencers:
            try:
                user = api.get_user(screen_name=influencer)
                current_following = set(f.id for f in api.get_friend_ids(user_id=user.id))

                if influencer in previous_follows:
                    new_follows = current_following - previous_follows[influencer]
                    if new_follows:
                        for nf in new_follows:
                            nf_user = api.get_user(user_id=nf)
                            msg = f"🔥 {influencer} followed {nf_user.screen_name} ({nf_user.followers_count} followers)"
                            await send_telegram_alert(msg)

                previous_follows[influencer] = current_following

            except Exception as e:
                print(f"⚠️ Error with {influencer}: {e}")

        await asyncio.sleep(60)  # check every minute

# --- 4. Run the scanner ---
async def main():
    await monitor_influencers()

if __name__ == "__main__":
    asyncio.run(main())
