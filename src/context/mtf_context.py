import pandas as pd


def build_htf_frames(df):
    """
    Construye M15 y H1 desde M5.
    No modifica tu pipeline actual.
    """

    if df is None or len(df) == 0:
        return None, None

    if "datetime" not in df.columns:
        return None, None

    df = df.copy()
    df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    df = df.set_index("datetime")

    m15 = df.resample("15T").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last"
    }).dropna()

    h1 = df.resample("1H").agg({
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last"
    }).dropna()

    m15 = m15.reset_index()
    h1 = h1.reset_index()

    return m15, h1


def detect_trend_h1(h1):
    """
    Tendencia simple H1 usando últimas velas
    """

    if h1 is None or len(h1) < 10:
        return "neutral"

    close = h1["close"]

    sma_fast = close.rolling(5).mean().iloc[-1]
    sma_slow = close.rolling(9).mean().iloc[-1]

    if sma_fast > sma_slow:
        return "bullish"

    if sma_fast < sma_slow:
        return "bearish"

    return "neutral"


def detect_structure_m15(m15):
    """
    Estructura simple en M15
    """

    if m15 is None or len(m15) < 10:
        return "neutral"

    last_high = m15["high"].iloc[-1]
    prev_high = m15["high"].iloc[-5:-1].max()

    last_low = m15["low"].iloc[-1]
    prev_low = m15["low"].iloc[-5:-1].min()

    if last_high > prev_high:
        return "bullish"

    if last_low < prev_low:
        return "bearish"

    return "neutral"


def filter_signals_mtf(signals, trend_1h, structure_m15):
    """
    Filtra señales usando scoring MTF.

    No elimina todas las señales agresivamente.
    """

    if not isinstance(signals, list) or len(signals) == 0:
        return []

    filtered = []

    for signal in signals:

        if not isinstance(signal, dict):
            continue

        signal_type = str(signal.get("type", "")).upper()

        if signal_type not in ["BUY", "SELL"]:
            continue

        score = 0

        # ----------------------
        # Trend H1 (peso mayor)
        # ----------------------

        if trend_1h == "bullish" and signal_type == "BUY":
            score += 2

        elif trend_1h == "bearish" and signal_type == "SELL":
            score += 2

        elif trend_1h == "neutral":
            score += 1

        # ----------------------
        # Structure M15
        # ----------------------

        if structure_m15 == "bullish" and signal_type == "BUY":
            score += 1

        elif structure_m15 == "bearish" and signal_type == "SELL":
            score += 1

        # ----------------------
        # Evitar contradicción fuerte
        # ----------------------

        if trend_1h == "bullish" and signal_type == "SELL":
            score -= 1

        if trend_1h == "bearish" and signal_type == "BUY":
            score -= 1

        signal["mtf_score"] = score

        # ----------------------
        # Umbral mínimo
        # ----------------------

        if score >= 2:
            filtered.append(signal)

    return filtered