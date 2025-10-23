cd ~/myprojects/IceAlphaHunter_Bot

# Delete the broken file
rm health_check.py

# Recreate it cleanly
cat > health_check.py <<'PY'
#!/usr/bin/env python3
# health_check.py — quick system health check for IceAlphaHunter_Bot
import os
import requests
import importlib.util
from dotenv import load_dotenv

print("🔍 Running IceAlphaHunter System Check...\n")

# 1️⃣ Load environment
if not os.path.exists(".env"):
    print("❌ .env file not found in current directory.")
    print("👉 Create .env from your .env.example and fill BOT token & WEBHOOK_PATH.")
    raise SystemExit(1)

load_dotenv()
bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
webhook_path = os.getenv("WEBHOOK_PATH")
port = os.getenv("PORT", "8080")

if not bot_token:
    print("❌ TELEGRAM_BOT_TOKEN missing in .env")
else:
    print("✅ Telegram Bot Token found")

# 2️⃣ Test Telegram API
try:
    url = f"https://api.telegram.org/bot{bot_token}/getMe"
    r = requests.get(url, timeout=7)
    if r.status_code == 200 and r.json().get("ok"):
        data = r.json()["result"]
        print(f"🤖 Telegram Bot Connected: @{data.get('username','<unknown>')} (id={data.get('id')})")
    else:
        print("⚠️ Telegram API did not respond with bot info. Status:", r.status_code, r.text[:200])
except Exception as e:
    print(f"❌ Telegram test failed: {e}")

# 3️⃣ Check webhook server locally
try:
    webhook_path_val = webhook_path or "secure-webhook-12345"
    webhook_url = f"http://localhost:{port}/{webhook_path_val}"
    r = requests.get(webhook_url, timeout=3)
    if r.status_code in (200, 404):
        print(f"✅ Webhook server responding at {webhook_url} (HTTP {r.status_code})")
    else:
        print(f"⚠️ Webhook returned status {r.status_code} for {webhook_url}")
except Exception as e:
    print(f"❌ Webhook test failed: {e}")

# 4️⃣ Check required scripts exist
scripts = [
    "main_hunter.py",
    "blockchain_scanner.py",
    "alert_sender.py",
    "subscription_manager.py",
    "webhook_server.py",
    "alert_manager.py"
]

missing = []
for s in scripts:
    if not os.path.exists(s):
        missing.append(s)

if missing:
    print(f"❌ Missing core scripts: {', '.join(missing)}")
else:
    print("✅ All main scripts present")

# 5️⃣ Try import test for blockchain_scanner and alert_manager
for mod in ("blockchain_scanner", "alert_manager"):
    try:
        spec = importlib.util.find_spec(mod)
        if spec is None:
            print(f"⚠️ Could not import module '{mod}' (not found in PYTHONPATH).")
        else:
            print(f"✅ Module '{mod}' importable.")
    except Exception as e:
        print(f"❌ Import check failed for {mod}: {e}")

# 6️⃣ Optional: check that requirements are installed (quick)
print("\n🔧 Checking pip-installed packages (quick):")
try:
    import pkgutil
    needed = ["fastapi", "uvicorn", "requests", "apscheduler", "python_dotenv", "httpx"]
    installed = {p.name for p in pkgutil.iter_modules()}
    for p in ("fastapi", "uvicorn", "requests", "apscheduler", "dotenv", "httpx"):
        print(f" - {p}: {'OK' if p in installed else 'MISSING (may still be importable)'}")
except Exception as e:
    print("Could not enumerate installed packages:", e)

print("\n🏁 Health check complete.")
PY

# Make executable and run
chmod +x health_check.py
python3 health_check.py

