import numpy as np


def detect_liquidity_pools(df, tolerance=0.0002, min_cluster=3):

    highs = df["High"].values
    lows = df["Low"].values

    high_pools = []
    low_pools = []

    # --- HIGH LIQUIDITY POOLS ---

    for i in range(len(highs)):

        cluster = []

        for j in range(len(highs)):

            if abs(highs[i] - highs[j]) <= tolerance:
                cluster.append(highs[j])

        if len(cluster) >= min_cluster:

            level = np.mean(cluster)

            high_pools.append({
                "type": "sell_liquidity",
                "price": level,
                "cluster_size": len(cluster),
                "strength": round(len(cluster) / 10, 2)
            })

    # --- LOW LIQUIDITY POOLS ---

    for i in range(len(lows)):

        cluster = []

        for j in range(len(lows)):

            if abs(lows[i] - lows[j]) <= tolerance:
                cluster.append(lows[j])

        if len(cluster) >= min_cluster:

            level = np.mean(cluster)

            low_pools.append({
                "type": "buy_liquidity",
                "price": level,
                "cluster_size": len(cluster),
                "strength": round(len(cluster) / 10, 2)
            })

    return {
        "sell_side_liquidity": high_pools,
        "buy_side_liquidity": low_pools
    }