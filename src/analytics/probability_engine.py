import numpy as np


def calculate_probabilities(df, signals, rr_target=2, stop_pips=0.0010):

    results = []

    wins = 0
    losses = 0
    rrs = []

    for signal in signals:

        idx = signal["index"]
        entry = signal["entry"]

        if idx >= len(df) - 10:
            continue

        if signal["type"] == "BUY":

            stop = entry - stop_pips
            target = entry + (stop_pips * rr_target)

        else:

            stop = entry + stop_pips
            target = entry - (stop_pips * rr_target)

        outcome = None

        for i in range(idx + 1, min(idx + 20, len(df))):

            high = df["high"].iloc[i]
            low = df["low"].iloc[i]

            if signal["type"] == "BUY":

                if low <= stop:
                    outcome = "loss"
                    losses += 1
                    break

                if high >= target:
                    outcome = "win"
                    wins += 1
                    rrs.append(rr_target)
                    break

            else:

                if high >= stop:
                    outcome = "loss"
                    losses += 1
                    break

                if low <= target:
                    outcome = "win"
                    wins += 1
                    rrs.append(rr_target)
                    break

        if outcome is None:
            losses += 1

    total = wins + losses

    if total == 0:
        return {
            "win_rate": 0,
            "avg_rr": 0,
            "expectancy": 0,
            "trades": 0
        }

    win_rate = wins / total
    avg_rr = np.mean(rrs) if rrs else 0

    expectancy = (win_rate * avg_rr) - ((1 - win_rate) * 1)

    return {
        "win_rate": round(win_rate, 3),
        "avg_rr": round(avg_rr, 2),
        "expectancy": round(expectancy, 3),
        "trades": total
    }