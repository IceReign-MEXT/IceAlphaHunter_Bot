import os
import tweepy
import asyncio
from dotenv import load_dotenv
from aiohttp import ClientSession

load_dotenv()

# --- 1. Twitter Authentication ---
auth = tweepy.OAuth1UserHandler(
    os.getenv("TWITTER_API_KEY"),
    os.getenv("TWITTER_API_SECRET_KEY"),
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
            print(f"Alert sent, status: {resp.status}")

# --- 3. Monitor new follows from a list of influencers ---
async def monitor_influencers():
    influencers = ["", ""]  # usernames
    previous_follows = {}

    while True:
        for influencer in influencers:
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

        await asyncio.sleep(60)  # check every minute

# --- 4. Run the scanner ---
async def main():
    await monitor_influencers()

if __name__ == "__main__":
    asyncio.run(main())
