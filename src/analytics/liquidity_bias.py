def calculate_liquidity_bias(liquidity_targets):
    if not isinstance(liquidity_targets, list) or len(liquidity_targets) == 0:
        return {
            "liquidity_above": 0,
            "liquidity_below": 0,
            "pct_above": 0.0,
            "pct_below": 0.0,
            "bias": "neutral",
            "probable_sweep": "none",
            "best_target": None
        }

    above = [t for t in liquidity_targets if t.get("direction") == "above"]
    below = [t for t in liquidity_targets if t.get("direction") == "below"]

    total = len(liquidity_targets)
    count_above = len(above)
    count_below = len(below)

    pct_above = round((count_above / total) * 100, 2) if total > 0 else 0.0
    pct_below = round((count_below / total) * 100, 2) if total > 0 else 0.0

    nearest_above = sorted(above, key=lambda x: x.get("distance_pips", 999999))
    nearest_below = sorted(below, key=lambda x: x.get("distance_pips", 999999))

    best_above = nearest_above[0] if nearest_above else None
    best_below = nearest_below[0] if nearest_below else None

    bias = "neutral"
    probable_sweep = "none"
    best_target = None

    if best_above and not best_below:
        bias = "bullish"
        probable_sweep = "high"
        best_target = best_above

    elif best_below and not best_above:
        bias = "bearish"
        probable_sweep = "low"
        best_target = best_below

    elif best_above and best_below:
        dist_above = best_above.get("distance_pips", 999999)
        dist_below = best_below.get("distance_pips", 999999)

        if dist_above + 1 < dist_below:
            bias = "bullish"
            probable_sweep = "high"
            best_target = best_above
        elif dist_below + 1 < dist_above:
            bias = "bearish"
            probable_sweep = "low"
            best_target = best_below
        else:
            if count_above > count_below:
                bias = "bullish"
                probable_sweep = "high"
                best_target = best_above
            elif count_below > count_above:
                bias = "bearish"
                probable_sweep = "low"
                best_target = best_below
            else:
                bias = "neutral"
                probable_sweep = "both"
                best_target = best_above if dist_above <= dist_below else best_below

    return {
        "liquidity_above": count_above,
        "liquidity_below": count_below,
        "pct_above": pct_above,
        "pct_below": pct_below,
        "bias": bias,
        "probable_sweep": probable_sweep,
        "best_target": best_target
    }