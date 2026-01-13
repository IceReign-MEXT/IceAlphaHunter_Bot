# whale_main.py (Polling Bot with Subscription Management)

import os
import logging
import asyncio
import time # For time.sleep in background loop
from dotenv import load_dotenv
import telebot # PyTelegramBotAPI
from telebot.async_telebot import AsyncTeleBot
from telebot import types # For keyboards, etc.
from datetime import datetime, timedelta

# Import your scanner and DB manager
from blockchain_scanner import scan_for_new_pools # Assuming this is your pool detector
from db_manager import initialize_db, get_subscriber, create_or_update_subscriber, \
                       update_subscription_status, get_active_premium_subscribers, \
                       check_and_update_expired_subscriptions

# --- Logging Configuration ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration from .env ---
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
VIP_CHANNEL_ID = os.getenv('VIP_CHANNEL_ID') # Main channel for premium alerts
ADMIN_ID = os.getenv('ADMIN_ID') # For admin-specific notifications
ETH_MAIN_WALLET = os.getenv('ETH_MAIN') # ETH wallet for payments
SOL_MAIN_WALLET = os.getenv('SOL_MAIN') # SOL wallet for payments
ETHEREUM_RPC = os.getenv('ETHEREUM_RPC')

# --- Bot Initialization ---
if not TELEGRAM_BOT_TOKEN:
    logging.error("CRITICAL: TELEGRAM_BOT_TOKEN environment variable is NOT set! Exiting.")
    exit(1)
if not ETHEREUM_RPC:
    logging.error("CRITICAL: ETHEREUM_RPC environment variable is NOT set! Exiting.")
    exit(1)
if not ETH_MAIN_WALLET or not SOL_MAIN_WALLET:
    logging.warning("Payment wallet addresses not fully set. Payment detection may not work.")

bot = AsyncTeleBot(TELEGRAM_BOT_TOKEN)

# --- Payment Plan Configuration ---
PLAN_NAME = "⚡ Sniper Pass"
PLAN_PRICE_USD = 25
PLAN_DURATION_DAYS = 30 # A month for simplicity
# You might want to get live ETH/USD price here for exact ETH amount

# --- Command Handlers ---

@bot.message_handler(commands=['start', 'help'])
async def send_welcome(message):
    chat_id = message.chat.id
    username = message.from_user.username if message.from_user.username else message.from_user.first_name

    # Ensure user is in DB
    create_or_update_subscriber(chat_id, username)
    subscriber = get_subscriber(chat_id)

    welcome_text = (
        f"👋 *Hello, {username}!* I'm IceAlphaHunter Bot.\n\n"
        "I provide premium alerts for new liquidity pools and other alpha.\n\n"
    )

    if subscriber and subscriber['status'] == 'premium' and subscriber['subscribed_until'] > datetime.now():
        remaining_time = subscriber['subscribed_until'] - datetime.now()
        welcome_text += (
            "💎 You currently have an *active premium subscription*! 🎉\n"
            f"Expires in: {remaining_time.days} days, {remaining_time.seconds // 3600} hours.\n"
            "Enjoy the alpha!"
        )
    else:
        welcome_text += (
            "Currently, you are on the *free tier*.\n"
            "Upgrade to premium to receive all exclusive alpha alerts!\n"
            "Use /subscribe to learn more."
        )

    await bot.send_message(chat_id, welcome_text, parse_mode='Markdown')

@bot.message_handler(commands=['subscribe'])
async def subscribe_command(message):
    chat_id = message.chat.id
    username = message.from_user.username if message.from_user.username else message.from_user.first_name

    create_or_update_subscriber(chat_id, username) # Ensure user is in DB

    invoice_text = (
        f"🧾 *INVOICE GENERATED for {PLAN_NAME} (30 days)* 📦\n"
        f"💵 Price: *${PLAN_PRICE_USD} USD*\n\n"
        "To subscribe, please send funds to one of the following addresses:\n\n"
        f"💠 *ETH (ERC-20)*\n`{ETH_MAIN_WALLET}`\n\n"
        f"🟣 *SOL (Solana)*\n`{SOL_MAIN_WALLET}`\n\n"
        "⚠️ *IMPORTANT: After sending payment, reply with `/paid YOUR_TRANSACTION_HASH`*\n"
        "Example: `/paid 0xabc123def456...` or `/paid 8dtuyskTtsB78DFDPWZ...`\n"
        "Your subscription will be activated after verification."
    )
    await bot.send_message(chat_id, invoice_text, parse_mode='Markdown')
    update_subscription_status(chat_id, 'pending_payment') # Mark as pending

@bot.message_handler(commands=['paid'])
async def paid_command(message):
    chat_id = message.chat.id
    command_parts = message.text.split(maxsplit=1)
    if len(command_parts) < 2:
        await bot.send_message(chat_id, "Please provide your transaction hash after /paid. Example: `/paid YOUR_TRANSACTION_HASH`", parse_mode='Markdown')
        return

    tx_hash = command_parts[1].strip()
    await bot.send_message(chat_id, f"Received your payment claim with transaction hash: `{tx_hash}`. Verifying payment...", parse_mode='Markdown')
    logging.info(f"User {chat_id} claimed payment with TX: {tx_hash}")

    # TODO: Implement actual payment verification logic here
    # This would involve using web3.py to check ETH chain or Solana client to check SOL chain
    # for transactions to ETH_MAIN_WALLET or SOL_MAIN_WALLET with the correct amount.
    # For now, we'll simulate success.

    # Example of (placeholder) verification:
    is_payment_verified = True # Replace with actual verification
    # if check_eth_payment(tx_hash, ETH_MAIN_WALLET, PLAN_PRICE_USD) or \
    #    check_sol_payment(tx_hash, SOL_MAIN_WALLET, PLAN_PRICE_USD):
    #     is_payment_verified = True
    # else:
    #     is_payment_verified = False

    if is_payment_verified:
        update_subscription_status(chat_id, 'premium', duration_days=PLAN_DURATION_DAYS, tx_hash=tx_hash)
        await bot.send_message(chat_id, "✅ Payment verified! Your *premium subscription is now active*! 🎉 You will start receiving exclusive alpha alerts.", parse_mode='Markdown')
        # Notify admin
        if ADMIN_ID and int(ADMIN_ID) != chat_id: # Avoid double notification if admin is subscriber
             await bot.send_message(ADMIN_ID, f"🎉 New premium subscriber: @{message.from_user.username} (ID: {chat_id})! TX: {tx_hash}", parse_mode='Markdown')
    else:
        await bot.send_message(chat_id, "❌ Payment *could not be verified*. Please double-check your transaction hash or contact support.", parse_mode='Markdown')
        # Optionally, reset status if they claim a bad TX
        update_subscription_status(chat_id, 'free')

@bot.message_handler(commands=['status'])
async def status_command(message):
    chat_id = message.chat.id
    subscriber = get_subscriber(chat_id)

    if not subscriber:
        await bot.send_message(chat_id, "You are not registered. Please use /start.", parse_mode='Markdown')
        return

    status_text = f"Your current subscription status:\n" \
                  f"Status: *{subscriber['status'].capitalize()}*\n"

    if subscriber['status'] == 'premium' and subscriber['subscribed_until']:
        remaining_time = subscriber['subscribed_until'] - datetime.now(subscriber['subscribed_until'].tzinfo)
        if remaining_time.total_seconds() > 0:
            status_text += f"Expires: *{subscriber['subscribed_until'].strftime('%Y-%m-%d %H:%M:%S %Z')}* (in {remaining_time.days} days)\n"
        else:
            status_text += "Expires: *Expired!* (Your subscription has ended.)\n"
            # In case it's expired but not yet updated by background task
            update_subscription_status(chat_id, 'free')
    elif subscriber['status'] == 'pending_payment':
        status_text += "Awaiting payment verification.\n"
    else:
        status_text += "You are on the free tier. Use /subscribe to upgrade!"

    await bot.send_message(chat_id, status_text, parse_mode='Markdown')


# --- Background Scanner Loop ---
SCAN_INTERVAL_SECONDS = 10 # Scan for pools every 10 seconds
SUBSCRIPTION_CHECK_INTERVAL_SECONDS = 3600 # Check for expired subscriptions every hour

async def background_scanner_and_manager_loop():
    """
    Combines the pool scanner and subscription management.
    """
    last_subscription_check = time.time()
    while True:
        logging.info("Starting scheduled new pool scan cycle.")
        new_pools = scan_for_new_pools() # Get detected pools from blockchain_scanner

        if new_pools:
            logging.info(f"Processing {len(new_pools)} new pool(s) for alerts.")
            active_premium_subscribers = get_active_premium_subscribers()
            if not active_premium_subscribers:
                logging.info("No active premium subscribers to send alerts to.")
                if ADMIN_ID: # Notify admin if alerts are happening but no one is getting them
                    await bot.send_message(ADMIN_ID, "⚠️ Detected new pools, but no active premium subscribers! Promote your bot!", parse_mode='Markdown')

            for pool in new_pools:
                # Basic filtering example: don't alert for WETH pairs (often existing tokens)
                # You'll want more sophisticated filtering here!
                if pool.get('is_weth_pair', False):
                    logging.info(f"Skipping WETH pair {pool['pair_address']} for alert.")
                    continue

                token0_symbol = pool['token0_info']['symbol']
                token1_symbol = pool['token1_info']['symbol']

                # Enhanced Alert Message with Emojis
                alert_message = (
                    "🔥 *NEW LIQUIDITY POOL DETECTED!* 🔥\n\n"
                    f"🔗 Pair Address: [`{pool['pair_address'][:6]}...`](https://etherscan.io/address/{pool['pair_address']})\n"
                    f"💰 Tokens: `{token0_symbol}/{token1_symbol}`\n"
                    f"➡️ Token0: [`{pool['token0_address'][:6]}...`](https://etherscan.io/address/{pool['token0_address']})\n"
                    f"➡️ Token1: [`{pool['token1_address'][:6]}...`](https://etherscan.io/address/{pool['token1_address']})\n"
                    f"📈 Total Pairs: `{pool['num_pairs_on_factory']}`\n"
                    f"📦 Block: `{pool['block_number']}`\n"
                    f"📝 TX: [View Transaction](https://etherscan.io/tx/{pool['transaction_hash']})\n\n"
                    "🚨 *DYOR - Do Your Own Research! This is not financial advice.* 🚨"
                )

                for chat_id in active_premium_subscribers:
                    await bot.send_message(chat_id, alert_message, parse_mode='Markdown', disable_web_page_preview=True)
                    logging.info(f"Alert sent to premium subscriber {chat_id} for new pool {pool['pair_address']}.")
        else:
            logging.info("No new pools detected in this scan cycle.")

        # Check for expired subscriptions periodically
        if time.time() - last_subscription_check >= SUBSCRIPTION_CHECK_INTERVAL_SECONDS:
            logging.info("Checking for expired subscriptions...")
            check_and_update_expired_subscriptions()
            last_subscription_check = time.time()

        await asyncio.sleep(SCAN_INTERVAL_SECONDS)


# --- Main entry point for running the bot ---
async def main():
    logging.info("Starting IceAlphaHunter_Bot application...")

    # 1. Initialize Database
    try:
        initialize_db()
    except Exception as e:
        logging.critical(f"Database initialization failed: {e}. Exiting.")
        exit(1)

    # 2. Initialize Blockchain Scanner connection
    try:
        from blockchain_scanner import w3 # Access the w3 object from scanner
        if w3.is_connected():
            logging.info("Initial blockchain RPC connection successful.")
        else:
            logging.critical("Initial blockchain RPC connection FAILED. Exiting.")
            exit(1)
    except Exception as e:
        logging.critical(f"Error initializing blockchain scanner: {e}. Exiting.")
        exit(1)

    # 3. Start background tasks
    asyncio.create_task(background_scanner_and_manager_loop())

    # 4. Start Telegram bot polling
    logging.info("Starting Telegram bot polling...")
    await bot.infinity_polling()

if __name__ == '__main__':
    # Using asyncio.run to run the async main function
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("Bot stopped by user (KeyboardInterrupt).")
    except Exception as e:
        logging.critical(f"An unhandled error occurred in main loop: {e}", exc_info=True)
