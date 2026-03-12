def _safe_float(value, default=None):
    try:
        return float(value)
    except Exception:
        return default


def _get_signal_direction(signal):
    if not isinstance(signal, dict):
        return None

    signal_type = str(signal.get("type", "")).upper()

    if signal_type == "BUY":
        return "BUY"

    if signal_type == "SELL":
        return "SELL"

    return None


def _get_sweep_direction(latest_sweep):
    if not isinstance(latest_sweep, dict):
        return None

    direction = str(latest_sweep.get("direction", "")).upper()
    if direction in ["BUY", "SELL"]:
        return direction

    sweep_type = str(latest_sweep.get("type", "")).lower()

    if sweep_type == "high_sweep":
        return "SELL"

    if sweep_type == "low_sweep":
        return "BUY"

    return None


def _calculate_sweep_bonus(signal, latest_sweep, sweep_lookback_bars=12):
    """
    Bonus por sweep reciente alineado con la dirección de la señal.
    """

    if not isinstance(signal, dict):
        return 0, False

    if not isinstance(latest_sweep, dict):
        return 0, False

    signal_dir = _get_signal_direction(signal)
    sweep_dir = _get_sweep_direction(latest_sweep)

    if signal_dir is None or sweep_dir is None:
        return 0, False

    if signal_dir != sweep_dir:
        return 0, False

    signal_idx = signal.get("index")
    sweep_idx = latest_sweep.get("index")

    try:
        signal_idx = int(signal_idx)
        sweep_idx = int(sweep_idx)
    except Exception:
        return 1, True if signal_dir == sweep_dir else (0, False)

    bars_since_sweep = signal_idx - sweep_idx

    if bars_since_sweep < 0:
        # El sweep ocurrió después de la señal, igual damos bonus mínimo si coincide dirección
        return 1, True

    if bars_since_sweep <= 3:
        return 2, True

    if bars_since_sweep <= sweep_lookback_bars:
        return 1, True

    return 0, True


def rank_signals(df, signals, max_distance=0.0020, latest_sweep=None):
    """
    Clasifica señales en:
    - best_signal
    - active_signals
    - discarded_signals

    age se usa como contexto y ranking,
    no como descarte automático.

    Mejora:
    - integra latest_sweep como bonus de score
    """

    if signals is None or len(signals) == 0:
        return None, [], []

    last_index = len(df) - 1
    current_price = _safe_float(df["close"].iloc[-1], default=None)

    if current_price is None:
        return None, [], []

    active = []
    discarded = []

    for raw_signal in signals:
        if not isinstance(raw_signal, dict):
            continue

        s = dict(raw_signal)

        idx = s.get("index")
        entry = _safe_float(s.get("entry"), default=None)

        if idx is None or entry is None:
            s["discard_reason"] = "invalid_signal"
            discarded.append(s)
            continue

        try:
            idx = int(idx)
        except Exception:
            s["discard_reason"] = "invalid_index"
            discarded.append(s)
            continue

        age = last_index - idx
        distance = abs(entry - current_price)

        base_score = s.get("score", 0)
        try:
            base_score = float(base_score)
        except Exception:
            base_score = 0

        sweep_bonus, sweep_match = _calculate_sweep_bonus(
            signal=s,
            latest_sweep=latest_sweep,
            sweep_lookback_bars=12
        )

        ranking_score = base_score + sweep_bonus

        s["index"] = idx
        s["entry"] = entry
        s["age"] = age
        s["distance"] = distance
        s["base_score"] = base_score
        s["sweep_bonus"] = sweep_bonus
        s["sweep_match"] = sweep_match
        s["ranking_score"] = ranking_score

        if distance > max_distance:
            s["discard_reason"] = "too_far_from_price"
            discarded.append(s)
            continue

        active.append(s)

    if len(active) == 0:
        return None, [], discarded

    active_sorted = sorted(
        active,
        key=lambda x: (
            -x.get("ranking_score", 0),
            -x.get("score", 0),
            x.get("distance", 999),
            x.get("age", 9999)
        )
    )

    best = dict(active_sorted[0])

    conflict = False
    for s in active_sorted[1:]:
        if s.get("type") != best.get("type") and s.get("ranking_score", 0) >= best.get("ranking_score", 0):
            if abs(s.get("distance", 999) - best.get("distance", 999)) <= 0.0005:
                conflict = True
                break

    if conflict:
        best["discard_reason"] = "direction_conflict"
        discarded.extend(active_sorted)
        return None, [], discarded

    return best, active_sorted, discarded