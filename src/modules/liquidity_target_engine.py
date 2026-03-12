import pandas as pd
import numpy as np


class LiquidityTargetEngine:

    def __init__(self, df):
        self.df = df.copy()

    def detect_equal_highs(self, tolerance=0.0005):

        highs = self.df["high"].values
        targets = []

        for i in range(2, len(highs)-2):

            if abs(highs[i] - highs[i-1]) < tolerance:
                targets.append({
                    "type": "equal_highs",
                    "price": highs[i],
                    "index": i
                })

        return targets


    def detect_equal_lows(self, tolerance=0.0005):

        lows = self.df["low"].values
        targets = []

        for i in range(2, len(lows)-2):

            if abs(lows[i] - lows[i-1]) < tolerance:
                targets.append({
                    "type": "equal_lows",
                    "price": lows[i],
                    "index": i
                })

        return targets


    def detect_swing_highs(self):

        highs = self.df["high"]
        swing_highs = []

        for i in range(2, len(highs)-2):

            if highs[i] > highs[i-1] and highs[i] > highs[i+1]:

                swing_highs.append({
                    "type": "swing_high",
                    "price": highs[i],
                    "index": i
                })

        return swing_highs


    def detect_swing_lows(self):

        lows = self.df["low"]
        swing_lows = []

        for i in range(2, len(lows)-2):

            if lows[i] < lows[i-1] and lows[i] < lows[i+1]:

                swing_lows.append({
                    "type": "swing_low",
                    "price": lows[i],
                    "index": i
                })

        return swing_lows


    def build_targets(self):

        targets = []

        targets += self.detect_equal_highs()
        targets += self.detect_equal_lows()
        targets += self.detect_swing_highs()
        targets += self.detect_swing_lows()

        targets_df = pd.DataFrame(targets)

        return targets_df