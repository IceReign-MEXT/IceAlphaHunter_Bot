#!/bin/bash

echo "--- Checking Bot Status on Termux ---"

BOT_PORT=8080 # Assuming your bot runs on port 8080 as per the logs

echo -e "\n1. Checking for 'python' processes that might be your bot:"
# Search for python processes that contain 'whale_main.py' or 'whale'
pgrep -f "python.*whale_main.py" || pgrep -f "python.*whale"

if [ $? -eq 0 ]; then
    echo "  -> Potential bot process found."
else
    echo "  -> No obvious 'whale_main.py' or 'whale' python process found."
fi

echo -e "\n2. Checking if anything is listening on port $BOT_PORT:"
# 'netstat -tuln' shows TCP/UDP listening sockets, 'grep' filters for the port
netstat -tuln | grep ":$BOT_PORT "

if [ $? -eq 0 ]; then
    echo "  -> Something is actively listening on port $BOT_PORT."
else
    echo "  -> Nothing is listening on port $BOT_PORT. The bot might not be running or is on a different port."
fi

echo -e "\n3. Attempting to connect to the bot's web interface (local):"
# 'curl' is a web client. We use -I for HEAD request (less data), -s for silent.
curl -Is http://127.0.0.1:$BOT_PORT/ | head -n 1

if [ $? -eq 0 ]; then
    echo "  -> Successfully received a response from http://127.0.0.1:$BOT_PORT/."
else
    echo "  -> Could not connect to http://127.0.0.1:$BOT_PORT/. Check if the bot is running and accessible."
fi

echo -e "\n--- End of Check ---"
