# blockchain_scanner.py (ensure these lines are near the top)
import os
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv # <-- Make sure this is present

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv() # <-- Make sure this is called once

# ... rest of your blockchain_scanner.py code ...
