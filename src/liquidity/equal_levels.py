def detect_equal_levels(df, tolerance=0.0001):

    eq_highs = []
    eq_lows = []

    highs = df[df["swing_high"]]
    lows = df[df["swing_low"]]

    for i in range(len(highs)-1):

        h1 = highs.iloc[i]["high"]
        h2 = highs.iloc[i+1]["high"]

        if abs(h1 - h2) <= tolerance:

            eq_highs.append((h1 + h2)/2)

    for i in range(len(lows)-1):

        l1 = lows.iloc[i]["low"]
        l2 = lows.iloc[i+1]["low"]

        if abs(l1 - l2) <= tolerance:

            eq_lows.append((l1 + l2)/2)

    return eq_highs, eq_lows