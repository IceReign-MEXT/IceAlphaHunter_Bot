import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(override=True)
ALCHEMY_URL = os.getenv("ALCHEMY_URL")
ETH_API_KEY = os.getenv("ETHEREUM_API_KEY") # Etherscan Key needed for verification check

w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

def scan_token_safety(token_address):
    """
    Returns a safety score (0-100) and a warning list.
    """
    score = 100
    warnings = []
    
    # 1. Check if address is valid
    if not w3.is_address(token_address):
        return 0, ["Invalid Address"]
    
    checksum_addr = w3.to_checksum_address(token_address)
    
    # 2. Check Code Size (If 0, it's not a contract / fake)
    code = w3.eth.get_code(checksum_addr)
    if len(code) <= 2:
        return 0, ["❌ No Contract Code (Fake/Empty)"]

    # 3. Simple Bytecode Analysis (Looking for 'selfdestruct' or weird patterns)
    code_str = code.hex()
    
    # Check for Mint functions (risk of unlimited printing)
    if "mint" in code_str or "40c10f19" in code_str: # mint signature
        score -= 20
        warnings.append("⚠️ Mint Function Detected (Owner might print tokens)")

    # Check for Blacklist function
    if "blacklist" in code_str:
        score -= 30
        warnings.append("⚠️ Blacklist Logic Detected")

    # 4. (Optional) Check Liquidity/Holders would go here
    # Since we are scanning INSTANTLY upon creation, liquidity might be low.
    
    return score, warnings
