#!/bin/bash

echo "--- Checking Bot Status on Termux (Revised) ---"

BOT_PORT=8080 # Assuming your bot runs on port 8080

echo -e "\n1. Checking for 'python' processes that might be your bot:"
# Search for python processes with 'whale_main.py' or 'flask run' (if it's using 'flask run')
# We'll use 'awk' to get PIDs and 'xargs ps -f' to get full command details
# This is more robust than simple pgrep for finding the specific command
ps aux | grep -E "python.*whale_main.py|flask run" | grep -v grep

if [ $? -eq 0 ]; then
    echo "  -> Potential bot process(es) found. Details above."
    # If found, you might want to show more info or confirm it's running via its name.
else
    echo "  -> No obvious 'whale_main.py' or 'flask run' python process found using 'ps aux'."
    echo "     If your bot is running, it might be under a different process name or was launched differently."
fi

echo -e "\n2. Attempting to connect to the bot's web interface (local) via curl:"
# 'curl' is the most reliable check given your netstat issue.
# We'll check for a successful HTTP status code (200 OK, 301, 302, etc.)
HTTP_STATUS=$(curl -o /dev/null -s -w "%{http_code}\n" http://127.0.0.1:$BOT_PORT/)

if [[ "$HTTP_STATUS" -ge 200 && "$HTTP_STATUS" -lt 400 ]]; then
    echo "  -> Successfully received an HTTP response (Status: $HTTP_STATUS) from http://127.0.0.1:$BOT_PORT/."
    echo "     This strongly indicates the bot is running and listening on $BOT_PORT."
else
    echo "  -> Could not connect to http://127.0.0.1:$BOT_PORT/ or received an error response (Status: $HTTP_STATUS)."
    echo "     The bot might not be running, or there's a network issue."
fi

echo -e "\n--- End of Check ---"
