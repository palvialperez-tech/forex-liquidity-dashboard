from .swing_detector import detect_swings
from .equal_levels import detect_equal_levels
from .liquidity_sweeps import detect_sweeps
from .liquidity_pools import detect_liquidity_pools

def run_liquidity_engine(df):

    df = detect_swings(df)

    eq_highs, eq_lows = detect_equal_levels(df)

    sweeps = detect_sweeps(df)

    return {
        "data": df,
        "equal_highs": eq_highs,
        "equal_lows": eq_lows,
        "sweeps": sweeps
    }
    
    pools = detect_liquidity_pools(df)

    return {
        "equal_highs": equal_highs,
        "equal_lows": equal_lows,
        "sweeps": sweeps,
        "pools": pools
}