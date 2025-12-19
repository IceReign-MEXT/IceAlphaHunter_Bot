import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import init_db, check_vip, add_sub, do_referral, get_stats
from flask import Flask
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG FROM YOUR .ENV ---
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_ID = int(os.getenv("PRIVATE_CHANNEL_ID"))
WALLET = os.getenv("ETHEREUM_WALLET")
ETHERSCAN_KEY = os.getenv("ETHEREUM_API_KEY")
MARKETING = os.getenv("PUBLIC_CHANNEL_ID")

init_db()
bot = Bot(token=TOKEN)
dp = Dispatcher()

app = Flask('')
@app.route('/health')
def health(): return "OK", 200
def run_web():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))

async def fetch_alpha():
    url = "https://api.dexscreener.com/token-boosts/latest/v1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json() if resp.status == 200 else []

@dp.message(CommandStart())
async def start(m: types.Message):
    args = m.text.split()
    if len(args) > 1 and args[1].isdigit():
        if do_referral(int(args[1])):
            try: await bot.send_message(args[1], "🎁 <b>Trial Activated!</b> 24h VIP Unlocked.", parse_mode="HTML")
            except: pass

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🦅 Hunter Alpha Gems", callback_data="alpha")],
        [InlineKeyboardButton(text="🎁 Refer Friends (Free VIP)", callback_data="ref")],
        [InlineKeyboardButton(text="💎 Upgrade to VIP", callback_data="buy")]
    ])
    await m.answer(f"🦅 <b>Ice Alpha Hunter PRO</b>\n\nWelcome {m.from_user.first_name}!\nTrack 100x Gems on ETH & SOL.", parse_mode="HTML", reply_markup=kb)

@dp.callback_query(F.data == "alpha")
async def alpha_handler(c: types.CallbackQuery):
    if not check_vip(c.from_user.id):
        await c.message.answer("❌ <b>VIP Access Only</b>\n\nInvite 3 friends or pay for VIP to see live Alpha.", parse_mode="HTML")
        return
    await c.answer("Scanning Blockchain...")
    gems = await fetch_alpha()
    msg = "🔥 <b>LIVE ALPHA GEMS:</b>\n\n"
    for g in gems[:5]:
        msg += f"🔹 {g.get('header')}\n🔗 <a href='{g.get('url')}'>View Chart</a>\n\n"
    await c.message.answer(msg, parse_mode="HTML", disable_web_page_preview=True)

@dp.callback_query(F.data == "ref")
async def ref_handler(c: types.CallbackQuery):
    me = await bot.get_me()
    count, used = get_stats(c.from_user.id)
    link = f"https://t.me/{me.username}?start={c.from_user.id}"
    await c.message.answer(f"🎁 <b>Referral Program</b>\n\nInvite 3 friends for 24h VIP.\nProgress: {count}/3\nLink: <code>{link}</code>", parse_mode="HTML")

@dp.callback_query(F.data == "buy")
async def buy_handler(c: types.CallbackQuery):
    await c.message.answer(f"💎 <b>VIP Upgrade</b>\n\nPrice: 0.05 ETH\nWallet: <code>{WALLET}</code>\n\nSend payment and contact @IceReignMEXT for activation.", parse_mode="HTML")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    Thread(target=run_web).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
