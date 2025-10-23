# IceAlphaHunter Bot - Clean skeleton
This repo contains a clean, production-ready skeleton:
- webhook_server.py : FastAPI webhook receiver
- main_hunter.py : orchestrator (instructions to run uvicorn)
- blockchain_scanner.py : detection scaffold (replace detect_new_items with real logic)
- scorer.py : scoring engine
- alert_manager.py : decides public vs subscriber alerts
- alert_sender.py : sends Telegram messages (reads BOT_TOKEN from .env)

Steps to run (local):
1. Create .env with BOT token and WEBHOOK_PATH (example below).
2. Install deps: pip install -r requirements.txt
3. Start webhook: export PORT=8080; uvicorn webhook_server:app --host 0.0.0.0 --port $PORT
4. Set Telegram webhook to your public URL + WEBHOOK_PATH.
5. Integrate your real scanner logic into blockchain_scanner.detect_new_items().

.env example:
BOT_TOKEN=put_bot_token_here
PRIVATE_CHANNEL_ID=your_channel_or_owner_chat_id
WEBHOOK_PATH=secure-webhook-12345
PORT=8080
