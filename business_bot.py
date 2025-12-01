import asyncio
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest # Needed for timeout settings
import database
import payment

# Enable logging to see connection issues clearly
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv(override=True)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MY_WALLET = os.getenv("ETHEREUM_WALLET")
PRICE = os.getenv("SUBSCRIPTION_PRICE_ETH", "0.05")

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        is_paid, expiry = database.check_access(user.id)
        
        if is_paid:
            import time
            days_left = int((expiry - time.time()) / 86400)
            await update.message.reply_text(f"🦅 **IceAlphaHunter Pro**\n\nWelcome back, Master {user.first_name}.\n✅ Status: ACTIVE ({days_left} days left).\n\nWaiting for new tokens...")
        else:
            await update.message.reply_text(
                f"🔒 **IceAlphaHunter Pro**\n\n"
                f"❌ **Status:** UNAUTHORIZED\n\n"
                f"**To Activate Access:**\n"
                f"1. Send **{PRICE} ETH** to:\n`{MY_WALLET}`\n"
                f"2. Copy the Transaction Hash (TX ID)\n"
                f"3. Type: `/verify <TX_ID>`\n\n"
                f"Need help? Type /help"
            )
    except Exception as e:
        print(f"Error in start command: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"❓ **IceAlphaHunter Guide**\n\n"
        f"**How do I subscribe?**\n"
        f"Send exactly {PRICE} ETH to our wallet address.\n"
        f"Wallet: `{MY_WALLET}`\n\n"
        f"**How do I verify?**\n"
        f"After sending ETH, copy the TX Hash and type:\n"
        f"`/verify 0x12345...abcdef`"
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ **Format Error**\n\nPlease paste your Transaction Hash.\nExample: `/verify 0x8a9d...`")
        return

    tx_hash = context.args[0]
    await update.message.reply_text("🔍 **Checking Blockchain...**\nPlease wait a moment.")
    
    # Run payment check in a way that doesn't block the bot
    success, msg = payment.verify_payment(tx_hash, user_id)
    
    if success:
        database.add_subscription(user_id, days=30)
        await update.message.reply_text(f"{msg}\n\n🦅 **Access Granted.**\nYou are now hunting.")
    else:
        await update.message.reply_text(msg)

# --- MAIN EXECUTION ---

def main():
    print("🦅 IceAlphaHunter Business is Live (High Latency Mode)...")
    
    # FIX: Increase Connection Timeouts for slow/mobile internet
    # We allow 60 seconds to connect and read data before crashing
    trequest = HTTPXRequest(connection_pool_size=8, connect_timeout=60, read_timeout=60)

    application = Application.builder().token(TOKEN).request(trequest).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verify", verify))
    application.add_handler(CommandHandler("help", help_command))

    # Run with allowed updates to save bandwidth
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
