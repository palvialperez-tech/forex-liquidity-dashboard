def detect_order_blocks(df, impulse_threshold=0.002):

    bullish_obs = []
    bearish_obs = []

    for i in range(2, len(df) - 2):

        open_price = df["open"].iloc[i]
        close_price = df["close"].iloc[i]

        next_close = df["close"].iloc[i + 1]
        next_next_close = df["close"].iloc[i + 2]

        move = abs(next_next_close - close_price)

        # detectar impulso fuerte
        if move < impulse_threshold:
            continue

        # BULLISH ORDER BLOCK
        if close_price < open_price and next_close > close_price:

            bullish_obs.append({
                "index": i,
                "top": open_price,
                "bottom": close_price,
                "type": "bullish_ob"
            })

        # BEARISH ORDER BLOCK
        if close_price > open_price and next_close < close_price:

            bearish_obs.append({
                "index": i,
                "top": close_price,
                "bottom": open_price,
                "type": "bearish_ob"
            })

    return {
        "bullish_ob": bullish_obs,
        "bearish_ob": bearish_obs
    }