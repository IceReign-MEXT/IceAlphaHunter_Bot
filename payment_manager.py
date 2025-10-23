#!/usr/bin/env python3
"""
payment_manager.py

- SQLite-backed payment & subscription manager
- Creates payment requests (USD -> ETH) via CoinGecko
- Verifies ETH transactions via Etherscan (basic)
- Activates subscriptions on successful verification

Usage:
  from payment_manager import create_payment_request, verify_and_credit_tx, get_subscription
  req = create_payment_request(chat_id, plan_key)
  # show req['amount_eth'] and req['payment_address'] to user
  # user sends tx_hash -> call:
  ok, reason = verify_and_credit_tx(chat_id, tx_hash)
"""

import os
import time
import sqlite3
import requests
from decimal import Decimal
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_DIR = Path("data")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "payments.db"

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY", "")
PAYMENT_ADDRESS = (os.getenv("PAYMENT_ADDRESS") or "").strip().lower()
COINGECKO_API = "https://api.coingecko.com/api/v3/simple/price"

# Plans definition (usd prices) — edit as needed
PLANS = {
    "basic": {"label": "Basic", "days": 7, "price_usd": Decimal("15")},
    "pro": {"label": "Pro", "days": 30, "price_usd": Decimal("49")},
    "elite": {"label": "Elite", "days": 90, "price_usd": Decimal("120")}
}

MIN_CONFIRMATIONS = int(os.getenv("MIN_CONFIRMATIONS", "2"))  # confirmations to accept

# -------------------------
# Database
# -------------------------
def get_conn():
    return sqlite3.connect(str(DB_PATH), check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS subscriptions (
        chat_id INTEGER PRIMARY KEY,
        plan TEXT,
        start_ts INTEGER,
        end_ts INTEGER,
        status TEXT
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        plan TEXT,
        tx_hash TEXT,
        amount_eth TEXT,
        amount_usd TEXT,
        ts INTEGER,
        verified INTEGER DEFAULT 0
    )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------
# Utilities
# -------------------------
def now_ts():
    return int(time.time())

def ts_to_iso(ts):
    return datetime.utcfromtimestamp(ts).isoformat() if ts else None

def usd_to_eth(amount_usd: Decimal) -> Decimal:
    """Convert USD amount to ETH using CoinGecko (fallback to fixed if fails)"""
    try:
        r = requests.get(COINGECKO_API, params={"ids":"ethereum","vs_currencies":"usd"}, timeout=8)
        r.raise_for_status()
        j = r.json()
        price = Decimal(str(j["ethereum"]["usd"]))
        eth_amt = (Decimal(amount_usd) / price).quantize(Decimal("0.000000000000000001"))
        return eth_amt
    except Exception:
        # fallback: assume 1 ETH = 2000 USD (change if needed)
        fallback_price = Decimal(os.getenv("FALLBACK_ETH_PRICE_USD", "2000"))
        return (Decimal(amount_usd) / fallback_price).quantize(Decimal("0.000000000000000001"))

def normalize_addr(a: str) -> str:
    return (a or "").strip().lower()

# -------------------------
# Payment request creation
# -------------------------
def create_payment_request(chat_id: int, plan_key: str, prefer_currency: str="ETH") -> dict:
    """
    Create a payment request for a plan. Returns:
      {chat_id, plan_key, price_usd, amount_eth, payment_address, created_ts}
    """
    if plan_key not in PLANS:
        raise ValueError("Unknown plan")

    plan = PLANS[plan_key]
    price_usd = Decimal(plan["price_usd"])
    amount_eth = usd_to_eth(price_usd)

    # Optional: you might want unique destination per user (not here)
    if not PAYMENT_ADDRESS:
        raise RuntimeError("PAYMENT_ADDRESS not configured in .env")

    created_ts = now_ts()

    # Save pending payment to DB (unverified until user provides tx)
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
      INSERT INTO payments (chat_id, plan, amount_eth, amount_usd, ts, verified, tx_hash)
      VALUES (?, ?, ?, ?, ?, 0, '')
    """, (chat_id, plan_key, str(amount_eth), str(price_usd), created_ts))
    conn.commit()
    pid = cur.lastrowid
    conn.close()

    return {
        "payment_id": pid,
        "chat_id": chat_id,
        "plan_key": plan_key,
        "price_usd": str(price_usd),
        "amount_eth": str(amount_eth),
        "payment_address": PAYMENT_ADDRESS,
        "created_ts": created_ts,
        "note": f"Send exactly >= {amount_eth} ETH to {PAYMENT_ADDRESS} and then reply with /verifytx <txhash>"
    }

# -------------------------
# On-chain verification (ETH)
# -------------------------
def etherscan_get_receipt(tx_hash: str) -> dict:
    """Use Etherscan API to get transaction receipt (status) and blockNumber info."""
    if not ETHERSCAN_API_KEY:
        raise RuntimeError("ETHERSCAN_API_KEY not set in .env")
    url = "https://api.etherscan.io/api"
    params = {"module":"proxy","action":"eth_getTransactionByHash","txhash":tx_hash,"apikey":ETHERSCAN_API_KEY}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    j = r.json()
    return j.get("result")

def etherscan_get_tx_receipt_status(tx_hash: str) -> dict:
    """Get receipt status and confirmations via eth_getTransactionReceipt & blockNumber queries."""
    if not ETHERSCAN_API_KEY:
        raise RuntimeError("ETHERSCAN_API_KEY not set in .env")
    proxy = "https://api.etherscan.io/api"
    # get receipt
    r1 = requests.get(proxy, params={"module":"proxy","action":"eth_getTransactionReceipt","txhash":tx_hash,"apikey":ETHERSCAN_API_KEY}, timeout=10)
    r1.raise_for_status()
    rec = r1.json().get("result")
    # get current block
    r2 = requests.get(proxy, params={"module":"proxy","action":"eth_blockNumber","apikey":ETHERSCAN_API_KEY}, timeout=10)
    r2.raise_for_status()
    current_block_hex = r2.json().get("result")
    try:
        current_block = int(current_block_hex, 16)
    except:
        current_block = None
    return {"receipt": rec, "current_block": current_block}

def verify_and_credit_tx(chat_id: int, tx_hash: str) -> (bool, str):
    """
    Verify an ETH transaction matches a required payment for the user and credit subscription.
    Steps:
      - Find unverified pending payment for this chat_id (latest)
      - Check tx exists and to == PAYMENT_ADDRESS (or contract address for token)
      - Check value >= required wei
      - Check confirmations >= MIN_CONFIRMATIONS
      - If OK: mark payment verified and activate subscription
    Returns (ok:bool, reason:str)
    """
    tx_hash = tx_hash.strip()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, plan, amount_eth FROM payments WHERE chat_id=? AND verified=0 ORDER BY ts DESC LIMIT 1", (chat_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "No pending payment found for your account. Use /subscribe to create a payment request first."

    pid, plan_key, amount_eth_str = row
    amount_eth = Decimal(amount_eth_str)

    try:
        # Use etherscan to get tx details
        info = etherscan_get_tx_receipt_status(tx_hash)
        receipt = info.get("receipt")
        current_block = info.get("current_block")
        if not receipt:
            return False, "Transaction receipt not found yet. Try again after a few seconds."

        # extract to and value from transaction (receipt doesn't include 'to' or 'value')
        # fetch transaction raw
        tx = requests.get("https://api.etherscan.io/api", params={"module":"proxy","action":"eth_getTransactionByHash","txhash":tx_hash,"apikey":ETHERSCAN_API_KEY}, timeout=10).json().get("result")
        if not tx:
            return False, "Transaction data not retrievable."

        to_addr = normalize_addr(tx.get("to"))
        value_hex = tx.get("value") or "0x0"
        value_wei = int(value_hex, 16)
        # convert required eth to wei
        required_wei = int((amount_eth * Decimal(10**18)).to_integral_value())

        # confirmations
        block_number_hex = receipt.get("blockNumber")
        if not block_number_hex:
            return False, "Transaction not yet included in a block."
        tx_block = int(block_number_hex, 16)
        confirmations = (current_block - tx_block) if current_block and tx_block else 0

        # check destination
        if normalize_addr(to_addr) != normalize_addr(PAYMENT_ADDRESS):
            return False, f"Tx recipient ({to_addr}) does not match payment address."

        if value_wei < required_wei:
            return False, f"Tx value too small. Sent {Decimal(value_wei) / Decimal(10**18)} ETH, required >= {amount_eth} ETH."

        if confirmations < MIN_CONFIRMATIONS:
            return False, f"Only {confirmations} confirmations. Need {MIN_CONFIRMATIONS}."

        # All checks passed -> mark payment verified & activate subscription
        cur.execute("UPDATE payments SET tx_hash=?, verified=1 WHERE id=?", (tx_hash, pid))
        ts = now_ts()
        cur.execute("INSERT OR REPLACE INTO subscriptions (chat_id, plan, start_ts, end_ts, status) VALUES (?, ?, ?, ?, ?)",
                    (chat_id, plan_key, ts, ts + PLANS[plan_key]["days"] * 24 * 3600, "active"))
        # record amount & ts in payments table row (already updated)
        conn.commit()
        conn.close()
        return True, f"Payment verified. Subscription {plan_key} active until {ts_to_iso(ts + PLANS[plan_key]['days']*24*3600)}"
    except Exception as e:
        conn.close()
        return False, f"Verification error: {e}"

# -------------------------
# Subscription queries
# -------------------------
def get_subscription(chat_id: int) -> dict:
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT plan, start_ts, end_ts, status FROM subscriptions WHERE chat_id=?", (chat_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return {}
    plan, start_ts, end_ts, status = row
    return {"plan": plan, "start_ts": start_ts, "end_ts": end_ts, "status": status}

def list_active_subscribers():
    conn = get_conn()
    cur = conn.cursor()
    now = now_ts()
    cur.execute("SELECT chat_id FROM subscriptions WHERE status='active' AND end_ts>?", (now,))
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    return rows

# -------------------------
# CLI quick test
# -------------------------
if __name__ == "__main__":
    print("Payment manager quick test")
    print("PAYMENT_ADDRESS:", PAYMENT_ADDRESS)
    print("ETHERSCAN_API_KEY set:", bool(ETHERSCAN_API_KEY))
    print("Available plans:")
    for k,v in PLANS.items():
        print(k, v)
    print("Create a test payment request example:")
    print(create_payment_request(123456, "basic"))
