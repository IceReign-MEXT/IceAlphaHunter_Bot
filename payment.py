import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(override=True)
ALCHEMY_URL = os.getenv("ALCHEMY_URL")
MY_WALLET = os.getenv("ETHEREUM_WALLET")
SUBSCRIPTION_PRICE = 0.05 # ETH

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

def verify_payment(tx_hash, user_id):
    try:
        # Get Transaction Receipt
        tx = w3.eth.get_transaction(tx_hash)
        receipt = w3.eth.get_transaction_receipt(tx_hash)

        # 1. Check if successful (status 1)
        if receipt['status'] != 1:
            return False, "❌ Transaction Failed on Blockchain."

        # 2. Check if it went to YOUR wallet
        if tx['to'].lower() != MY_WALLET.lower():
            return False, "❌ Funds were not sent to the Bot Wallet."

        # 3. Check Amount (in ETH)
        value_eth = float(w3.from_wei(tx['value'], 'ether'))
        if value_eth < SUBSCRIPTION_PRICE:
            return False, f"❌ Insufficient funds. Sent: {value_eth}, Required: {SUBSCRIPTION_PRICE}"

        # 4. Check Age (Prevent reusing old transactions)
        # In a real pro bot, you would save used TX_HASHES to database to prevent reuse.
        # For now, we assume honest verification flow.
        
        return True, "✅ Payment Verified! Welcome to the Alpha."

    except Exception as e:
        return False, f"Error verifying: {str(e)}"
