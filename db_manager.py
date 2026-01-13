# db_manager.py

import os
import psycopg2
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """Establishes and returns a database connection."""
    if not DATABASE_URL:
        logging.error("DATABASE_URL environment variable is not set.")
        raise ValueError("DATABASE_URL is required for database operations.")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    except Exception as e:
        logging.error(f"Error connecting to the database: {e}")
        raise

def initialize_db():
    """
    Ensures the 'subscribers' table exists.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS subscribers (
                chat_id BIGINT PRIMARY KEY,
                username TEXT,
                status TEXT DEFAULT 'free', -- 'free', 'pending_payment', 'premium'
                subscribed_until TIMESTAMP WITH TIME ZONE,
                last_payment_tx TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        conn.commit()
        logging.info("Database initialized successfully: 'subscribers' table checked/created.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")
        raise
    finally:
        if conn:
            conn.close()

def get_subscriber(chat_id):
    """Retrieves a subscriber's information."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM subscribers WHERE chat_id = %s", (chat_id,))
        subscriber = cur.fetchone()
        if subscriber:
            # Convert tuple to dictionary for easier access
            columns = [desc[0] for desc in cur.description]
            return dict(zip(columns, subscriber))
        return None
    except Exception as e:
        logging.error(f"Error getting subscriber {chat_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

def create_or_update_subscriber(chat_id, username):
    """Creates a new subscriber or updates an existing one's username."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO subscribers (chat_id, username, updated_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (chat_id) DO UPDATE SET username = EXCLUDED.username, updated_at = NOW();
        """, (chat_id, username))
        conn.commit()
        logging.info(f"Subscriber {chat_id} ({username}) created or updated.")
    except Exception as e:
        logging.error(f"Error creating/updating subscriber {chat_id}: {e}")
    finally:
        if conn:
            conn.close()

def update_subscription_status(chat_id, status, duration_days=None, tx_hash=None):
    """
    Updates a subscriber's status and expiry.
    Status can be 'free', 'pending_payment', 'premium'.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        # Default to existing subscribed_until if not extending premium
        subscribed_until_clause = ""
        if status == 'premium' and duration_days:
            # Extend current subscription or set a new one
            existing_sub = get_subscriber(chat_id)
            if existing_sub and existing_sub['subscribed_until'] and existing_sub['subscribed_until'] > datetime.now(existing_sub['subscribed_until'].tzinfo):
                 new_expiry = existing_sub['subscribed_until'] + timedelta(days=duration_days)
            else:
                 new_expiry = datetime.now() + timedelta(days=duration_days)
            subscribed_until_clause = f", subscribed_until = '{new_expiry.isoformat()}'"
        elif status == 'free':
            subscribed_until_clause = ", subscribed_until = NULL" # Remove expiry for free users

        tx_hash_clause = f", last_payment_tx = '{tx_hash}'" if tx_hash else ""

        cur.execute(f"""
            UPDATE subscribers SET status = %s {subscribed_until_clause} {tx_hash_clause}, updated_at = NOW()
            WHERE chat_id = %s;
        """, (status, chat_id))
        conn.commit()
        logging.info(f"Subscription status for {chat_id} updated to '{status}'.")
    except Exception as e:
        logging.error(f"Error updating subscription status for {chat_id}: {e}")
    finally:
        if conn:
            conn.close()

def get_active_premium_subscribers():
    """Retrieves all chat_ids of active premium subscribers."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT chat_id FROM subscribers WHERE status = 'premium' AND subscribed_until > NOW();")
        return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logging.error(f"Error getting active premium subscribers: {e}")
        return []
    finally:
        if conn:
            conn.close()

def check_and_update_expired_subscriptions():
    """Sets expired premium subscribers back to 'free' status."""
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE subscribers
            SET status = 'free', subscribed_until = NULL, updated_at = NOW()
            WHERE status = 'premium' AND subscribed_until <= NOW();
        """)
        updated_count = cur.rowcount
        if updated_count > 0:
            logging.info(f"Updated {updated_count} expired premium subscriptions to 'free'.")
            conn.commit()
        return updated_count
    except Exception as e:
        logging.error(f"Error checking and updating expired subscriptions: {e}")
        return 0
    finally:
        if conn:
            conn.close()
