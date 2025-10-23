#!/usr/bin/env python3
"""
alert_manager.py

Handles:
- Evaluating new token data from blockchain_scanner
- Detecting fake/suspicious patterns
- Sending formatted alerts through alert_sender
"""

import asyncio
from alert_sender import send_alert

# Thresholds / Rules
MIN_LIQUIDITY_USD = 10000
MIN_HOLDERS = 20
RUG_CHECK_WORDS = ["honeypot", "blacklist", "mintable", "trading_disabled"]

async def process_token_alert(token_data: dict):
    """
    Analyze a new token and decide whether to send an alert.
    token_data should include:
        - name
        - symbol
        - address
        - liquidity_usd
        - holders
        - source (dex, chain)
        - is_verified
        - warnings
    """
    name = token_data.get("name", "Unknown")
    symbol = token_data.get("symbol", "?")
    addr = token_data.get("address", "")
    liquidity = token_data.get("liquidity_usd", 0)
    holders = token_data.get("holders", 0)
    warnings = token_data.get("warnings", [])
    verified = token_data.get("is_verified", False)
    chain = token_data.get("source", "Unknown")

    # Basic detection
    fake_detected = False
    fake_reasons = []

    if liquidity < MIN_LIQUIDITY_USD:
        fake_detected = True
        fake_reasons.append(f"Low liquidity (${liquidity:,.0f})")

    if holders < MIN_HOLDERS:
        fake_detected = True
        fake_reasons.append(f"Few holders ({holders})")

    for w in warnings:
        for bad in RUG_CHECK_WORDS:
            if bad in w.lower():
                fake_detected = True
                fake_reasons.append(f"⚠️ {bad.capitalize()} risk")

    # Formatting message
    if fake_detected:
        title = "🚨 *Fake / Risky Token Detected!*"
        desc = f"❌ `{name} ({symbol})`\n🧩 {addr}\n⚙️ Chain: {chain}\n\nReasons:\n- " + "\n- ".join(fake_reasons)
    else:
        title = "🟢 *New Token Launch Detected!*"
        desc = (
            f"💎 `{name} ({symbol})`\n"
            f"📡 Source: {chain}\n"
            f"💧 Liquidity: ${liquidity:,.0f}\n"
            f"👥 Holders: {holders}\n"
            f"✅ Verified: {'Yes' if verified else 'No'}\n"
            f"🔗 Address: `{addr}`"
        )

    message = f"{title}\n\n{desc}"

    await send_alert(message)
    print(f"[ALERT] Sent for token {symbol} ({addr[:6]}...) | Fake: {fake_detected}")

# Optional quick test
if __name__ == "__main__":
    asyncio.run(process_token_alert({
        "name": "TestToken",
        "symbol": "TST",
        "address": "0x1234567890abcdef",
        "liquidity_usd": 8000,
        "holders": 12,
        "source": "Uniswap",
        "warnings": ["Honeypot risk"],
        "is_verified": False
    }))
