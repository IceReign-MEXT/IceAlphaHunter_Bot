import asyncio
import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.request import HTTPXRequest
import database
import payment

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

load_dotenv(override=True)
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MY_WALLET = os.getenv("ETHEREUM_WALLET")
PRICE = os.getenv("SUBSCRIPTION_PRICE_ETH", "0.10")

# IMAGE URL (A cool cyberpunk banner to make it look expensive)
# You can change this link to your own image later
BANNER_URL = "https://img.freepik.com/premium-photo/futuristic-cyberpunk-city-background-blue-neon-lights_146508-608.jpg"

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        is_paid, expiry = database.check_access(user.id)
        
        if is_paid:
            import time
            days_left = int((expiry - time.time()) / 86400)
            await update.message.reply_photo(
                photo=BANNER_URL,
                caption=f"🦅 **IceAlphaHunter Pro**\n\n"
                        f"Welcome back, Hunter {user.first_name}.\n"
                        f"✅ **Status:** ACTIVE LICENSE\n"
                        f"⏳ **Remaining:** {days_left} Days\n\n"
                        f"Scanning the mempool for targets...",
                parse_mode="Markdown"
            )
        else:
            # PROFESSIONAL SALES PITCH
            await update.message.reply_photo(
                photo=BANNER_URL,
                caption=f"🦅 **IceAlphaHunter Pro**\n\n"
                        f"You are currently on the **Guest List**.\n\n"
                        f"⚡️ **Premium Features:**\n"
                        f"• **Block-0 Sniping** (Beat the market)\n"
                        f"• **Anti-Rug Shield** (Security Scanning)\n"
                        f"• **Direct Etherscan Links**\n\n"
                        f"💎 **Subscription Cost:** `{PRICE} ETH` / Month\n\n"
                        f"👇 **How to Upgrade:**\n"
                        f"1. Tap the address below to copy.\n"
                        f"2. Send exactly **{PRICE} ETH**.\n"
                        f"3. Type `/verify <TX_HASH>`",
                parse_mode="Markdown"
            )
            # Send wallet separately for easy copying
            await update.message.reply_text(f"`{MY_WALLET}`", parse_mode="Markdown")
            
    except Exception as e:
        print(f"Error in start: {e}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"❓ **Support & Guide**\n\n"
        f"**1. Payment**\n"
        f"Send `{PRICE} ETH` to the wallet below. We accept ETH on Mainnet (ERC20).\n"
        f"`{MY_WALLET}`\n\n"
        f"**2. Activation**\n"
        f"After payment, copy the Transaction Hash and send:\n"
        f"`/verify 0xYourTransactionHash...`\n\n"
        f"**3. Support**\n"
        f"Issues? Contact the Developer: @IceReignMEXT",
        parse_mode="Markdown"
    )

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if len(context.args) < 1:
        await update.message.reply_text("⚠️ **Format Error**\n\nPlease paste your Transaction Hash.\nExample: `/verify 0x8a9d...`")
        return

    tx_hash = context.args[0]
    await update.message.reply_text("🔍 **Verifying on Blockchain...**\nConnecting to Ethereum Mainnet...")
    
    success, msg = payment.verify_payment(tx_hash, user_id)
    
    if success:
        database.add_subscription(user_id, days=30)
        await update.message.reply_text(f"{msg}\n\n🦅 **Welcome to the Alpha.**\nYou will now receive alerts automatically.")
    else:
        await update.message.reply_text(msg)

# --- MAIN EXECUTION ---

def main():
    print("🦅 IceAlphaHunter Business is Live...")
    trequest = HTTPXRequest(connection_pool_size=8, connect_timeout=60, read_timeout=60)
    application = Application.builder().token(TOKEN).request(trequest).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("verify", verify))
    application.add_handler(CommandHandler("help", help_command))

    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
