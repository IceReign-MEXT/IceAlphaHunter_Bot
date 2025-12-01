import sqlite3
import time

DB_NAME = "subscribers.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create table for users: ID, Expiry Date (timestamp)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, expiry_timestamp REAL)''')
    conn.commit()
    conn.close()

def add_subscription(user_id, days=30):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Calculate new expiry
    current_time = time.time()
    # If user already exists, add time to their current expiry
    c.execute("SELECT expiry_timestamp FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    
    if data and data[0] > current_time:
        new_expiry = data[0] + (days * 24 * 3600)
    else:
        new_expiry = current_time + (days * 24 * 3600)

    c.execute("INSERT OR REPLACE INTO users (user_id, expiry_timestamp) VALUES (?, ?)", (user_id, new_expiry))
    conn.commit()
    conn.close()
    return new_expiry

def check_access(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT expiry_timestamp FROM users WHERE user_id=?", (user_id,))
    data = c.fetchone()
    conn.close()
    
    if data:
        if data[0] > time.time():
            return True, data[0] # Active
        else:
            return False, 0 # Expired
    return False, 0 # Not found

def get_all_paid_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    current_time = time.time()
    c.execute("SELECT user_id FROM users WHERE expiry_timestamp > ?", (current_time,))
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# Initialize on load
init_db()
