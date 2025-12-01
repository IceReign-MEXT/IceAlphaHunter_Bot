#!/bin/bash

# 1. Start the Fake Web Server (Background)
python3 keep_alive.py &

# 2. Start the Business/Payment Bot (Background)
python3 business_bot.py &

# 3. Start the Scanner (Foreground - keeps container running)
python3 blockchain_scanner.py
