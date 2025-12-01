import os
from dotenv import load_dotenv

# Force reload of .env
load_dotenv(override=True)

token = os.getenv("TELEGRAM_BOT_TOKEN")
print(f"Token loaded: {token}")

if token == "8324510631:AAFW6iKXcbvfgNdeCK43LhGqqdOoo11czHs":
    print("✅ Token MATCHES the working one!")
else:
    print("❌ Token does NOT match. Check .env file.")
