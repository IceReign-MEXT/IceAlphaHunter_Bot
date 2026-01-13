#!/bin/bash

echo "--- Running Pre-Push Checks for IceAlphaHunter_Bot ---"

# --- 1. Check for .env file existence ---
if [ ! -f .env ]; then
    echo "❌ ERROR: .env file not found! Please create one based on .env.example."
    exit 1
else
    echo "✅ .env file found."
fi

# --- 2. Load .env variables for script's use (not for global shell) ---
# This ensures the script uses the same variables your Python app will use.
source .env

# --- 3. Check for essential environment variables ---
ESSENTIAL_VARS=(
    "TELEGRAM_BOT_TOKEN"
    "ADMIN_ID"
    "VIP_CHANNEL_ID"
    "ETH_MAIN"
    "SOL_MAIN"
    "DATABASE_URL"
    "ETHEREUM_RPC"
    "HELIUS_RPC"
)

MISSING_VARS=0
echo -e "\n--- Checking essential .env variables ---"
for var in "${ESSENTIAL_VARS[@]}"; do
    if [ -z "$(eval "echo \$$var")" ]; then
        echo "❌ ERROR: Environment variable '$var' is not set in .env or is empty."
        MISSING_VARS=$((MISSING_VARS+1))
    else
        echo "✅ $var is set."
    fi
done

if [ "$MISSING_VARS" -gt 0 ]; then
    echo "❌ CRITICAL: $MISSING_VARS essential environment variable(s) are missing or empty. Please fix your .env file."
    exit 1
fi

echo "✅ All essential .env variables are set."


# --- 4. Python Environment Checks ---
echo -e "\n--- Checking Python environment ---"
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️ WARNING: Virtual environment is not active. Please activate it: 'source venv/bin/activate'."
    # Don't exit here, as other checks might still be useful.
fi

# Check if requirements are installed
if [ -f requirements.txt ]; then
    echo "Checking if Python dependencies are installed (might take a moment)..."
    python -c "import pkg_resources; pkg_resources.require(open('requirements.txt').read())" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ All dependencies from requirements.txt are installed."
    else
        echo "❌ ERROR: Some dependencies from requirements.txt are not installed. Run 'pip install -r requirements.txt'."
        exit 1
    fi
else
    echo "⚠️ WARNING: requirements.txt not found. Cannot check Python dependencies."
fi


# --- 5. RPC Connection Test (Python script for robust check) ---
echo -e "\n--- Testing Blockchain RPC Connections ---"
# We'll create a temporary Python script to test RPC connections
TEMP_RPC_TEST_SCRIPT="temp_rpc_test.py"
cat <<EOF > "$TEMP_RPC_TEST_SCRIPT"
import os
from web3 import Web3
import psycopg2
from dotenv import load_dotenv
import sys

load_dotenv() # Load from .env for this test script

ETHEREUM_RPC = os.getenv("ETHEREUM_RPC")
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Ethereum RPC Check ---
print("Attempting to connect to Ethereum RPC...")
try:
    w3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC))
    if w3.is_connected():
        print(f"✅ Ethereum RPC connected. Current block: {w3.eth.block_number}")
    else:
        print(f"❌ Ethereum RPC FAILED to connect: {ETHEREUM_RPC}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error connecting to Ethereum RPC: {e}")
    sys.exit(1)

# --- PostgreSQL Database Check ---
print("Attempting to connect to PostgreSQL Database...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1;") # Simple query to test connection
    conn.close()
    print("✅ PostgreSQL Database connected successfully.")
except Exception as e:
    print(f"❌ PostgreSQL Database FAILED to connect: {e}")
    sys.exit(1)

sys.exit(0) # All checks passed
EOF

python "$TEMP_RPC_TEST_SCRIPT"
RPC_TEST_RESULT=$?
rm "$TEMP_RPC_TEST_SCRIPT" # Clean up temp script

if [ "$RPC_TEST_RESULT" -ne 0 ]; then
    echo "❌ CRITICAL: One or more RPC/Database connections failed. Please check your ETHEREUM_RPC and DATABASE_URL in .env."
    exit 1
else
    echo "✅ All RPC/Database connections passed."
fi

echo -e "\n--- All essential checks passed! You can proceed to push and deploy. ---"
exit 0
