def detect_fvg(df, threshold=0.0005):
    """
    Detecta Fair Value Gaps (FVG) en un DataFrame OHLC.
    Retorna una lista de dicts: {'index': int, 'type': 'bullish'/'bearish', 'top': float, 'bottom': float}
    """
    fvg_list = []

    for i in range(2, len(df)):
        high0 = df['high'].iloc[i-2]
        low0 = df['low'].iloc[i-2]
        high1 = df['high'].iloc[i-1]
        low1 = df['low'].iloc[i-1]
        close = df['close'].iloc[i]

        # Bullish FVG: Gap entre velas previas
        if low0 > high1 + threshold:
            fvg_list.append({
                "index": i,
                "type": "bullish",
                "top": low0,
                "bottom": high1
            })

        # Bearish FVG: Gap entre velas previas
        if high0 < low1 - threshold:
            fvg_list.append({
                "index": i,
                "type": "bearish",
                "top": low1,
                "bottom": high0
            })

    return fvg_list