#!/bin/bash

echo "🦅 STARTING ICE ALPHA HUNTER AUTO-INSTALLER..."

# 1. Update Server
echo "🔄 Updating System..."
sudo apt update && sudo apt upgrade -y

# 2. Install Tools (Python, Node, PM2)
echo "🛠 Installing Software..."
sudo apt install -y python3-pip python3-venv nodejs npm
sudo npm install -g pm2

# 3. Install Bot Libraries
echo "📚 Installing Python Libraries..."
pip3 install web3 python-telegram-bot python-dotenv requests

# 4. Clean up old processes if any
pm2 delete all 2>/dev/null

# 5. Start the Bots
echo "🚀 Launching Engines..."
pm2 start blockchain_scanner.py --name "scanner" --interpreter python3
pm2 start business_bot.py --name "business" --interpreter python3

# 6. Save Startup
echo "💾 Saving Configuration..."
pm2 save
pm2 startup | tail -n 1 | bash

echo "✅ INSTALLATION COMPLETE. YOUR BOT IS LIVE 24/7."
echo "🦅 Happy Hunting."
