# Whale A Lot / AlphaHunter Bot

## What this is
A production-ready Telegram alert bot that:
- scans for new DEX pairs,
- monitors a configured Ethereum wallet,
- monitors Twitter influencer follows,
- sends alerts to Telegram,
- manages subscribers (weekly/monthly).

## Quick setup (local)
1. Create `.env` from `.env.example` and fill values (DO NOT commit).
2. Create Python venv:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
