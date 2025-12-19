import sqlite3
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('ice_business.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  expiry_date TEXT,
                  referrals INTEGER DEFAULT 0,
                  trial_used INTEGER DEFAULT 0)''')
    conn.commit()
    conn.close()

def check_vip(user_id):
    conn = sqlite3.connect('ice_business.db')
    c = conn.cursor()
    c.execute("SELECT expiry_date FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    if res and res[0]:
        expiry = datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
        return expiry > datetime.now()
    return False

def add_sub(user_id, hours):
    conn = sqlite3.connect('ice_business.db')
    c = conn.cursor()
    expiry = datetime.now() + timedelta(hours=hours)
    c.execute("INSERT OR REPLACE INTO users (user_id, expiry_date) VALUES (?, ?)",
              (user_id, expiry.strftime('%Y-%m-%d %H:%M:%S')))
    conn.commit()
    conn.close()

def do_referral(ref_id):
    conn = sqlite3.connect('ice_business.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (ref_id,))
    c.execute("UPDATE users SET referrals = referrals + 1 WHERE user_id = ?", (ref_id,))
    c.execute("SELECT referrals, trial_used FROM users WHERE user_id = ?", (ref_id,))
    res = c.fetchone()
    if res and res[0] >= 3 and res[1] == 0:
        c.execute("UPDATE users SET trial_used = 1 WHERE user_id = ?", (ref_id,))
        conn.commit()
        conn.close()
        add_sub(ref_id, 24)
        return True
    conn.commit()
    conn.close()
    return False

def get_stats(user_id):
    conn = sqlite3.connect('ice_business.db')
    c = conn.cursor()
    c.execute("SELECT referrals, trial_used FROM users WHERE user_id = ?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res if res else (0, 0)
