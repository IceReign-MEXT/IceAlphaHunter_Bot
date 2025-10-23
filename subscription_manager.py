# subscription_manager.py
import os
import sqlite3
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("SUB_DB_PATH", "subscribers.db")
PAYMENT_MODE = os.getenv("PAYMENT_MODE", "stripe")  # "stripe" or "onchain_manual"
PAYMENT_WALLET = os.getenv("PAYMENT_WALLET", "").lower()  # optional on-chain address

# subscription durations in days
DURATIONS = {
    "weekly": 7,
    "monthly": 30
}

class SubscriptionManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._ensure_tables()

    def _ensure_tables(self):
        c = self.conn.cursor()
        c.execute("""
        CREATE TABLE IF NOT EXISTS subscribers (
            chat_id TEXT PRIMARY KEY,
            tier TEXT,
            expires_at INTEGER
        )
        """)
        c.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            txid TEXT PRIMARY KEY,
            chat_id TEXT,
            amount REAL,
            created_at INTEGER
        )
        """)
        self.conn.commit()

    def add_subscription(self, chat_id: str, tier: str, period: str = "monthly"):
        days = DURATIONS.get(period, 30)
        now = int(time.time())
        c = self.conn.cursor()
        c.execute("SELECT expires_at FROM subscribers WHERE chat_id=?", (chat_id,))
        row = c.fetchone()
        if row and row[0] and row[0] > now:
            expires = row[0] + days*86400
        else:
            expires = now + days*86400
        c.execute("INSERT OR REPLACE INTO subscribers(chat_id, tier, expires_at) VALUES (?, ?, ?)", (chat_id, tier, expires))
        self.conn.commit()
        return expires

    def get_tier(self, chat_id: str):
        now = int(time.time())
        c = self.conn.cursor()
        c.execute("SELECT tier, expires_at FROM subscribers WHERE chat_id=?", (str(chat_id),))
        row = c.fetchone()
        if not row:
            return "free"
        tier, expires_at = row
        if expires_at < now:
            return "expired"
        return tier

    def check_and_cleanup(self):
        # optional: remove expired subscribers or mark them
        now = int(time.time())
        c = self.conn.cursor()
        c.execute("DELETE FROM subscribers WHERE expires_at < ?", (now - 86400*365*5,))  # keep long enough
        self.conn.commit()

    # On-chain/manual payment record (admin/manual verification)
    def record_payment(self, txid: str, chat_id: str, amount: float):
        now = int(time.time())
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO payments(txid, chat_id, amount, created_at) VALUES (?, ?, ?, ?)", (txid, chat_id, amount, now))
        self.conn.commit()
