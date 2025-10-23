import json
import os

SUBSCRIBERS_FILE = "subscribers.json"

# Load existing subscribers
def load_subscribers():
    if os.path.exists(SUBSCRIBERS_FILE):
        with open(SUBSCRIBERS_FILE, "r") as f:
            return json.load(f)
    return []

# Save updated subscriber list
def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subscribers, f, indent=4)

# Add a new subscriber
def add_subscriber(chat_id):
    subscribers = load_subscribers()
    if chat_id not in subscribers:
        subscribers.append(chat_id)
        save_subscribers(subscribers)
        return True
    return False

# Remove a subscriber
def remove_subscriber(chat_id):
    subscribers = load_subscribers()
    if chat_id in subscribers:
        subscribers.remove(chat_id)
        save_subscribers(subscribers)
        return True
    return False
