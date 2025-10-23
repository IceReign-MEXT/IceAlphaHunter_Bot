# snipe_testnet.py  -- SAFE testnet/sim simulation only
import os, asyncio, json, time
from dotenv import load_dotenv
from web3 import Web3
from web3.middleware import geth_poa_middleware

load_dotenv()

RPC = os.getenv("WEB3_PROVIDER")  # use testnet or local fork RPC
FACTORY = os.getenv("FACTORY_ADDRESS")        # factory address (testnet)
ROUTER = os.getenv("ROUTER_ADDRESS")          # router address (testnet)
WETH = os.getenv("WRAPPED_NATIVE")            # wrapped native token on chain (WETH/WBNB)
MIN_LIQ_THRESHOLD = float(os.getenv("MIN_LIQ_THRESHOLD", "0.1"))  # native token units
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("PRIVATE_CHANNEL_ID")

if not RPC or not FACTORY or not ROUTER:
    raise SystemExit("Set WEB3_PROVIDER, FACTORY_ADDRESS, ROUTER_ADDRESS in .env (use testnet!)")

w3 = Web3(Web3.HTTPProvider(RPC))
if os.getenv("POA") == "1":
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)

# Minimal ABIs
FACTORY_ABI = [{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"token0","type":"address"},{"indexed":True,"internalType":"address","name":"token1","type":"address"},{"indexed":False,"internalType":"address","name":"pair","type":"address"},{"indexed":False,"internalType":"uint256","name":"","type":"uint256"}],"name":"PairCreated","type":"event"}]
PAIR_ABI = [{"constant":True,"inputs":[],"name":"getReserves","outputs":[{"internalType":"uint112","name":"_reserve0","type":"uint112"},{"internalType":"uint112","name":"_reserve1","type":"uint112"},{"internalType":"uint32","name":"_blockTimestampLast","type":"uint32"}],"type":"function"},{"constant":True,"inputs":[],"name":"token0","outputs":[{"name":"","type":"address"}],"type":"function"},{"constant":True,"inputs":[],"name":"token1","outputs":[{"name":"","type":"address"}],"type":"function"}]
ERC20_ABI = [{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},{"constant":True,"inputs":[],"name":"name","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":True,"inputs":[],"name":"symbol","outputs":[{"name":"","type":"string"}],"type":"function"},{"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"}]

factory = w3.eth.contract(address=Web3.toChecksumAddress(FACTORY), abi=FACTORY_ABI)

def quick_token_meta(token_addr):
    try:
        token = w3.eth.contract(address=Web3.toChecksumAddress(token_addr), abi=ERC20_ABI)
        name = token.functions.name().call()
        symbol = token.functions.symbol().call()
        decimals = token.functions.decimals().call()
        supply = token.functions.totalSupply().call()
        return {"name": name, "symbol": symbol, "decimals": decimals, "supply": supply}
    except Exception as e:
        return {"error": str(e)}

def liquidity_ok(res0, res1, threshold_native = MIN_LIQ_THRESHOLD):
    # naive: check either reserve >= threshold * 10**18
    thr_raw = int(threshold_native * (10**18))
    return res0 >= thr_raw or res1 >= thr_raw

async def send_telegram(message):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print("No telegram configured:", message)
        return
    import aiohttp
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as s:
        await s.post(url, json={"chat_id": TELEGRAM_CHAT, "text": message, "parse_mode":"Markdown"})

# NOTE: Honeypot test requires a forked node (hardhat/ganache) where you can impersonate an account
# or a testnet account with tiny funds. Do NOT run this on mainnet with real funds.
def honeypot_simulation_example(fork_rpc, pair_addr, router_addr, test_account, private_key_hex):
    """
    Example: on a local fork, send a small buy tx then a sell tx to test whether sells are blocked.
    This function is illustrative — running it requires hardhat/ganache fork and funded test_account.
    """
    w3f = Web3(Web3.HTTPProvider(fork_rpc))
    # configure account etc...
    # perform a tiny buy via router.swapExactETHForTokens (simulate gas and slippage)
    # then attempt immediate swapExactTokensForETH to sell.
    # If sell reverts, token is likely a honeypot. Capture receipt and revert reason.
    raise NotImplementedError("Run this on a local fork environment with a funded test account.")

async def monitor_pairs_poll():
    print("Starting pair poller (testnet)...")
    seen = set()
    while True:
        latest = w3.eth.get_block('latest').number
        from_block = max(0, latest - 100)
        try:
            logs = w3.eth.get_logs({"fromBlock": from_block, "toBlock": latest, "address": Web3.toChecksumAddress(FACTORY)})
        except Exception as e:
            logs = []
        for l in logs:
            try:
                ev = factory.events.PairCreated().processLog(l)
            except Exception:
                continue
            t0 = ev["args"]["token0"]
            t1 = ev["args"]["token1"]
            pair = ev["args"]["pair"]
            key = pair + str(l["logIndex"])
            if key in seen:
                continue
            seen.add(key)
            # quick checks:
            try:
                pc = w3.eth.contract(address=Web3.toChecksumAddress(pair), abi=PAIR_ABI)
                r0, r1, _ = pc.functions.getReserves().call()
            except:
                r0 = r1 = 0
            m0 = quick_token_meta(t0)
            m1 = quick_token_meta(t1)
            safe = liquidity_ok(r0, r1)
            score = "SAFE" if safe else "RISKY/LOW_LIQ"
            msg = (
                f"*New Pair Detected (testnet)*\nPair: `{pair}`\n"
                f"Token0: `{m0.get('symbol') or t0}`\nToken1: `{m1.get('symbol') or t1}`\n"
                f"Reserves (raw): {r0} / {r1}\nScore: *{score}*\n_Manual review recommended._"
            )
            await send_telegram(msg)
        await asyncio.sleep(6)

if __name__ == "__main__":
    asyncio.run(monitor_pairs_poll())
