import pandas as pd


def _pip_size_for_symbol(symbol="EURUSD"):
    if symbol.upper().endswith("JPY"):
        return 0.01
    return 0.0001


def _to_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def _safe_price(signal):
    if not isinstance(signal, dict):
        return None

    for key in ["entry", "price", "level", "target_price"]:
        if key in signal:
            value = _to_float(signal.get(key))
            if value is not None:
                return value

    return None


def _build_target(price, current_price, source, label, pip_size):
    if price is None:
        return None

    direction = "above" if price > current_price else "below"
    distance_pips = abs(price - current_price) / pip_size

    return {
        "type": label,
        "source": source,
        "price": float(price),
        "direction": direction,
        "distance_pips": round(distance_pips, 2)
    }


def _extract_liquidity_targets(liquidity, current_price, pip_size):
    targets = []

    if isinstance(liquidity, pd.DataFrame):
        records = liquidity.to_dict("records")
    elif isinstance(liquidity, list):
        records = liquidity
    else:
        records = []

    for item in records:
        if not isinstance(item, dict):
            continue

        price = None
        label = item.get("type", "liquidity")

        for key in ["price", "level", "entry", "target_price", "high", "low"]:
            if key in item:
                price = _to_float(item.get(key))
                if price is not None:
                    break

        if price is None:
            continue

        target = _build_target(
            price=price,
            current_price=current_price,
            source="liquidity",
            label=label,
            pip_size=pip_size
        )

        if target is not None:
            targets.append(target)

    return targets


def _extract_zone_targets(zones, current_price, pip_size):
    targets = []

    if isinstance(zones, pd.DataFrame):
        records = zones.to_dict("records")
    elif isinstance(zones, list):
        records = zones
    else:
        records = []

    for item in records:
        if not isinstance(item, dict):
            continue

        zone_type = item.get("type", "zone")

        candidates = []
        for key in ["price", "level", "entry", "target_price", "top", "bottom", "high", "low"]:
            if key in item:
                value = _to_float(item.get(key))
                if value is not None:
                    candidates.append(value)

        for price in candidates:
            target = _build_target(
                price=price,
                current_price=current_price,
                source="zone",
                label=zone_type,
                pip_size=pip_size
            )
            if target is not None:
                targets.append(target)

    return targets


def _extract_signal_targets(signals, current_price, pip_size):
    targets = []

    if isinstance(signals, pd.DataFrame):
        records = signals.to_dict("records")
    elif isinstance(signals, list):
        records = signals
    else:
        records = []

    for item in records:
        if not isinstance(item, dict):
            continue

        price = _safe_price(item)
        if price is None:
            continue

        signal_type = str(item.get("type", "signal")).upper()

        target = _build_target(
            price=price,
            current_price=current_price,
            source="signal",
            label=signal_type,
            pip_size=pip_size
        )
        if target is not None:
            targets.append(target)

    return targets


def _deduplicate_targets(targets, pip_size, merge_threshold_pips=1.5):
    if not targets:
        return []

    targets_sorted = sorted(targets, key=lambda x: x["price"])
    deduped = []

    merge_threshold = merge_threshold_pips * pip_size

    for target in targets_sorted:
        if not deduped:
            deduped.append(target)
            continue

        last = deduped[-1]
        if abs(target["price"] - last["price"]) <= merge_threshold and target["direction"] == last["direction"]:
            if target["distance_pips"] < last["distance_pips"]:
                deduped[-1] = target
        else:
            deduped.append(target)

    return deduped


def build_liquidity_targets(
    df,
    liquidity=None,
    zones=None,
    signals=None,
    symbol="EURUSD",
    min_distance_pips=2,
    max_distance_pips=25
):
    if df is None or len(df) == 0:
        return []

    current_price = float(df["close"].iloc[-1])
    pip_size = _pip_size_for_symbol(symbol)

    targets = []
    targets.extend(_extract_liquidity_targets(liquidity, current_price, pip_size))
    targets.extend(_extract_zone_targets(zones, current_price, pip_size))
    targets.extend(_extract_signal_targets(signals, current_price, pip_size))

    filtered = []
    for t in targets:
        dist = t.get("distance_pips", 999999)
        if dist >= min_distance_pips and dist <= max_distance_pips:
            filtered.append(t)

    filtered = _deduplicate_targets(filtered, pip_size=pip_size, merge_threshold_pips=1.5)
    filtered = sorted(filtered, key=lambda x: x["distance_pips"])

    return filtered


def get_nearest_targets(liquidity_targets, top_n=5):
    if not isinstance(liquidity_targets, list):
        return []

    return liquidity_targets[:top_n]


def get_side_targets(liquidity_targets, side="above", top_n=5):
    if not isinstance(liquidity_targets, list):
        return []

    out = [t for t in liquidity_targets if t.get("direction") == side]
    out = sorted(out, key=lambda x: x.get("distance_pips", 999999))
    return out[:top_n]