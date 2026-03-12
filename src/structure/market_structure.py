import pandas as pd


def detect_market_structure(df):

    swings_high = []
    swings_low = []

    # detectar swings
    for i in range(2, len(df)-2):

        high = df["high"].iloc[i]
        low = df["low"].iloc[i]

        if high > df["high"].iloc[i-1] and high > df["high"].iloc[i+1]:
            swings_high.append((i, high))

        if low < df["low"].iloc[i-1] and low < df["low"].iloc[i+1]:
            swings_low.append((i, low))


    bos = []
    choch = []

    last_high = None
    last_low = None

    for i in range(len(df)):

        price = df["close"].iloc[i]

        if last_high and price > last_high[1]:

            bos.append({
                "index": i,
                "type": "bullish_BOS",
                "level": last_high[1]
            })

            last_high = None

        if last_low and price < last_low[1]:

            bos.append({
                "index": i,
                "type": "bearish_BOS",
                "level": last_low[1]
            })

            last_low = None


        for sh in swings_high:
            if sh[0] == i:
                last_high = sh

        for sl in swings_low:
            if sl[0] == i:
                last_low = sl


    return {
        "swings_high": swings_high,
        "swings_low": swings_low,
        "bos": bos,
        "choch": choch
    }