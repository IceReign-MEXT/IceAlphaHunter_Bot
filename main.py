import os
import asyncio
import aiohttp
import logging
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, check_premium, add_subscription, add_referral, get_stats
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = os.getenv("PRIVATE_CHANNEL_ID")
WALLET = os.getenv("ETHEREUM_WALLET")
ETHERSCAN_KEY = os.getenv("ETHEREUM_API_KEY")
PUBLIC_CHANNEL = os.getenv("PUBLIC_CHANNEL_ID") # e.g., @ICEGODSICEDEVILS

init_db()
bot = Bot(token=TOKEN)
dp = Dispatcher()

# --- RENDER SERVER ---
app = Flask('')
@app.route('/health')
def health(): return "OK", 200
def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

# --- ALPHA LOGIC ---
async def fetch_alpha():
    url = "https://api.dexscreener.com/token-boosts/latest/v1"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                return await resp.json() if resp.status == 200 else []
        except: return []

# --- AUTO-SIGNAL BACKGROUND TASK ---
async def auto_signal_broadcaster():
    """Posts a teaser signal to the public channel every 4 hours"""
    logging.info("Auto-Signal Broadcaster Started...")
    while True:
        try:
            # Wait 4 hours (14400 seconds)
            await asyncio.sleep(14400)

            gems = await fetch_alpha()
            if gems:
                gem = gems[0] # Pick the top trending coin
                name = gem.get('header', 'Unknown Token')

                # Create a FOMO Teaser Message
                teaser = (
                    "🚨 <b>NEW ALPHA DETECTED</b> 🚨\n\n"
                    f"Token: <b>{name}</b>\n"
                    "Status: 🔥 Trending on DexScreener\n"
                    f"Link: <tg-spoiler>Click Bot to Unlock</tg-spoiler>\n\n"
                    "<i>VIP members are already trading this. Don't be late.</i>"
                )

                kb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔓 UNLOCK LINK", url=f"https://t.me/{(await bot.get_me()).username}")]
                ])

                await bot.send_message(chat_id=PUBLIC_CHANNEL, text=teaser, parse_mode="HTML", reply_markup=kb)
                logging.info(f"Auto-signal posted for {name}")
        except Exception as e:
            logging.error(f"Broadcaster Error: {e}")
            await asyncio.sleep(60)

# --- BOT HANDLERS ---
@dp.message(CommandStart())
async def start(message: types.Message):
    # (Existing referral & welcome logic...)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Hunter Alpha Gems", callback_data="alpha")],
        [InlineKeyboardButton(text="🎁 Refer Friends (Free VIP)", callback_data="ref")],
        [InlineKeyboardButton(text="💎 Purchase VIP", callback_data="buy")]
    ])
    await message.answer(f"🦅 <b>Ice Alpha Hunter PRO</b>\n\nWelcome {message.from_user.first_name}!", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "alpha")
async def alpha(callback: types.CallbackQuery):
    if not check_premium(callback.from_user.id):
        gems = await fetch_alpha()
        teaser = "❌ <b>VIP Access Only</b>\n\n🔥 <b>LATEST GEMS:</b>\n"
        for g in gems[:3]:
            teaser += f"🔹 {g.get('header')} | <tg-spoiler>🔒 Hidden</tg-spoiler>\n"
        teaser += "\n👉 Invite 3 friends or pay for VIP to unlock!"
        await callback.message.answer(teaser, parse_mode="HTML")
        return

    # (Rest of VIP Alpha display logic...)
    await callback.message.answer("🔥 Access Granted! Displaying Gems...")

# --- STARTUP ---
async def main():
    # Start the Auto-Signal Broadcaster in the background
    asyncio.create_task(auto_signal_broadcaster())

    await bot.delete_webhook(drop_pending_updates=True)
    Thread(target=run_web).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
