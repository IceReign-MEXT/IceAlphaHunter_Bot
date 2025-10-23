# scorer.py - simple scoring engine for token payloads
def evaluate_token_payload(payload: dict) -> dict:
    score = 0
    breakdown = {}
    # on-chain signals
    if payload.get("tiny_liquidity"):
        breakdown["tiny_liquidity"] = 20; score += 20
    if payload.get("minted_to_single_wallet"):
        breakdown["single_holder"] = 20; score += 20
    if payload.get("owner_not_renounced"):
        breakdown["owner_keys"] = 15; score += 15
    if payload.get("name_typosquat"):
        breakdown["typo_name"] = 15; score += 15
    # behavioral signals (placeholders)
    if payload.get("rapid_price_pump"):
        breakdown["rapid_pump"] = 15; score += 15
    # clamp
    if score > 100:
        score = 100
    return {"score": score, "breakdown": breakdown}
