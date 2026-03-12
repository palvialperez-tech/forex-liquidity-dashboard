def detect_sweeps(df):

    sweeps = []

    for i in range(1, len(df)):

        prev_high = df.iloc[i-1]["high"]
        prev_low = df.iloc[i-1]["low"]

        high = df.iloc[i]["high"]
        low = df.iloc[i]["low"]
        close = df.iloc[i]["close"]

        # sweep arriba
        if high > prev_high and close < prev_high:

            sweeps.append({
                "type": "sell_sweep",
                "price": high,
                "index": i
            })

        # sweep abajo
        if low < prev_low and close > prev_low:

            sweeps.append({
                "type": "buy_sweep",
                "price": low,
                "index": i
            })

    return sweeps