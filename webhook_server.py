#!/usr/bin/env python3
# webhook_server.py — FastAPI webhook receiver for Telegram and internal calls
import os, asyncio, logging
from fastapi import FastAPI, Request, BackgroundTasks
from dotenv import load_dotenv
from alert_sender import send_alert_sync
from blockchain_scanner import start_scanner_background
load_dotenv()
LOG = logging.getLogger("webhook_server")
app = FastAPI()
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "secure-webhook-12345")

@app.post("/" + WEBHOOK_PATH)
async def telegram_webhook(request: Request, background: BackgroundTasks):
    payload = await request.json()
    # Minimal command handling; expand in main_hunter or a command router
    try:
        message = payload.get("message") or payload.get("edited_message") or {}
        text = message.get("text","")
        chat = message.get("chat",{})
        chat_id = chat.get("id")
        # basic commands
        if text:
            parts = text.strip().split()
            cmd = parts[0].lower()
            if cmd == "/start":
                send_alert_sync(chat_id, "✅ Bot online. Use /subscribe or /deposit.")
            elif cmd == "/subscribe":
                send_alert_sync(chat_id, "Subscription process: send deposit tx hash with /verifytx <hash>")
            elif cmd == "/verifytx" and len(parts) > 1:
                tx = parts[1]
                # Do async verification via blockchain_verifier if present
                from blockchain_verifier import verify_and_credit_tx
                ok = await asyncio.get_event_loop().run_in_executor(None, verify_and_credit_tx, chat_id, tx)
                send_alert_sync(chat_id, f"Verification result: {ok}")
            # add more handlers as needed
    except Exception as e:
        LOG.exception("Webhook handler error: %s", e)
    return {"ok": True}
