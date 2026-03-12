import pandas as pd


def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def _extract_levels(items, keys):
    levels = []

    if isinstance(items, pd.DataFrame):
        records = items.to_dict("records")
    elif isinstance(items, list):
        records = items
    else:
        records = []

    for item in records:
        if isinstance(item, (int, float)):
            levels.append(float(item))
            continue

        if not isinstance(item, dict):
            continue

        for key in keys:
            if key in item:
                value = _safe_float(item.get(key))
                if value is not None:
                    levels.append(value)
                    break

    return levels


def _deduplicate_levels(levels, pip_size=0.0001, merge_threshold_pips=1.5):
    if not levels:
        return []

    levels = sorted(levels)
    out = [levels[0]]
    threshold = pip_size * merge_threshold_pips

    for lvl in levels[1:]:
        if abs(lvl - out[-1]) > threshold:
            out.append(lvl)

    return out


def _build_sweep_event(
    sweep_type,
    level,
    candle_index,
    candle_time,
    high,
    low,
    close,
    pip_size
):
    if sweep_type == "high_sweep":
        direction = "SELL"
        sweep_distance_pips = (high - level) / pip_size
    else:
        direction = "BUY"
        sweep_distance_pips = (level - low) / pip_size

    return {
        "type": sweep_type,
        "level": round(level, 5),
        "index": int(candle_index),
        "datetime": candle_time,
        "high": round(high, 5),
        "low": round(low, 5),
        "close": round(close, 5),
        "direction": direction,
        "sweep_distance_pips": round(max(sweep_distance_pips, 0), 2)
    }


def detect_liquidity_sweeps(
    df,
    liquidity=None,
    sweep_threshold_pips=1.0,
    close_back_inside=True,
    lookback_bars=150,
    pip_size=0.0001
):
    """
    Detecta barridos de liquidez sobre equal highs / equal lows.

    Reglas:
    - high_sweep:
        la vela rompe por arriba del nivel
        y opcionalmente cierra de vuelta bajo el nivel
    - low_sweep:
        la vela rompe por abajo del nivel
        y opcionalmente cierra de vuelta sobre el nivel
    """

    if df is None or len(df) == 0:
        return []

    if liquidity is None:
        liquidity = {}

    work_df = df.copy().reset_index(drop=True)

    if lookback_bars is not None and len(work_df) > lookback_bars:
        offset = len(work_df) - lookback_bars
        work_df = work_df.tail(lookback_bars).reset_index(drop=True)
    else:
        offset = 0

    equal_highs = _extract_levels(
        liquidity.get("equal_highs", []),
        ("price", "level", "high", "top")
    )
    equal_lows = _extract_levels(
        liquidity.get("equal_lows", []),
        ("price", "level", "low", "bottom")
    )

    equal_highs = _deduplicate_levels(equal_highs, pip_size=pip_size, merge_threshold_pips=1.5)
    equal_lows = _deduplicate_levels(equal_lows, pip_size=pip_size, merge_threshold_pips=1.5)

    threshold = sweep_threshold_pips * pip_size
    sweeps = []

    for i in range(len(work_df)):
        row = work_df.iloc[i]

        high = _safe_float(row.get("high"))
        low = _safe_float(row.get("low"))
        close = _safe_float(row.get("close"))
        candle_time = row.get("datetime") if "datetime" in work_df.columns else i

        if high is None or low is None or close is None:
            continue

        # Sweep de highs
        for level in equal_highs:
            broke_above = high >= (level + threshold)

            if not broke_above:
                continue

            if close_back_inside:
                if close < level:
                    sweeps.append(
                        _build_sweep_event(
                            sweep_type="high_sweep",
                            level=level,
                            candle_index=i + offset,
                            candle_time=candle_time,
                            high=high,
                            low=low,
                            close=close,
                            pip_size=pip_size
                        )
                    )
            else:
                sweeps.append(
                    _build_sweep_event(
                        sweep_type="high_sweep",
                        level=level,
                        candle_index=i + offset,
                        candle_time=candle_time,
                        high=high,
                        low=low,
                        close=close,
                        pip_size=pip_size
                    )
                )

        # Sweep de lows
        for level in equal_lows:
            broke_below = low <= (level - threshold)

            if not broke_below:
                continue

            if close_back_inside:
                if close > level:
                    sweeps.append(
                        _build_sweep_event(
                            sweep_type="low_sweep",
                            level=level,
                            candle_index=i + offset,
                            candle_time=candle_time,
                            high=high,
                            low=low,
                            close=close,
                            pip_size=pip_size
                        )
                    )
            else:
                sweeps.append(
                    _build_sweep_event(
                        sweep_type="low_sweep",
                        level=level,
                        candle_index=i + offset,
                        candle_time=candle_time,
                        high=high,
                        low=low,
                        close=close,
                        pip_size=pip_size
                    )
                )

    # eliminar duplicados cercanos
    unique = []
    seen = set()

    for s in sweeps:
        key = (s["type"], round(s["level"], 5), s["index"])
        if key not in seen:
            seen.add(key)
            unique.append(s)

    return unique


def get_recent_sweeps(sweeps, last_n=10):
    if not isinstance(sweeps, list):
        return []
    return sweeps[-last_n:]


def get_latest_sweep(sweeps):
    if not isinstance(sweeps, list) or len(sweeps) == 0:
        return None
    return sweeps[-1]