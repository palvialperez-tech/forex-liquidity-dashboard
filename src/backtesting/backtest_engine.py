import pandas as pd


def run_backtest(df, signals, rr_target=2, stop_pips=0.0010):

    trades = []

    equity = 10000
    risk_per_trade = 0.01

    for signal in signals:

        idx = signal["index"]
        entry = signal["entry"]

        if idx >= len(df) - 20:
            continue

        if signal["type"] == "BUY":

            stop = entry - stop_pips
            target = entry + (stop_pips * rr_target)

        else:

            stop = entry + stop_pips
            target = entry - (stop_pips * rr_target)

        outcome = "open"

        for i in range(idx + 1, min(idx + 20, len(df))):

            high = df["high"].iloc[i]
            low = df["low"].iloc[i]

            if signal["type"] == "BUY":

                if low <= stop:
                    outcome = "loss"
                    break

                if high >= target:
                    outcome = "win"
                    break

            else:

                if high >= stop:
                    outcome = "loss"
                    break

                if low <= target:
                    outcome = "win"
                    break

        risk_amount = equity * risk_per_trade

        if outcome == "win":
            profit = risk_amount * rr_target
            equity += profit

        elif outcome == "loss":
            profit = -risk_amount
            equity += profit

        else:
            profit = 0

        trades.append({
            "type": signal["type"],
            "entry": entry,
            "stop": stop,
            "target": target,
            "result": outcome,
            "profit": profit,
            "equity": equity
        })

    return pd.DataFrame(trades)