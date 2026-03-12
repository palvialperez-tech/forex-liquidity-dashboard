import pandas as pd


# src/liquidity/zone_builder.py
def build_zones(liquidity, fvg_list=None):
    """
    Construye zonas de compra/venta combinando:
    - equal highs/lows
    - order blocks
    - FVG (opcional)
    """
    sell_zones = []
    buy_zones = []

    # Equal Highs -> SELL ZONES
    for price in liquidity.get("equal_highs", []):
        sell_zones.append({"type": "sell", "top": price + 0.0005, "bottom": price - 0.0005, "liquidity": "equal_high"})

    # Equal Lows -> BUY ZONES
    for price in liquidity.get("equal_lows", []):
        buy_zones.append({"type": "buy", "top": price + 0.0005, "bottom": price - 0.0005, "liquidity": "equal_low"})

    # FVG -> añadir a zonas si se pasó fvg_list
    if fvg_list:
        for fvg in fvg_list:
            if fvg['type'] == 'bullish_fvg':
                buy_zones.append({"type":"buy","top":fvg['top'],"bottom":fvg['bottom'],"liquidity":"fvg"})
            elif fvg['type'] == 'bearish_fvg':
                sell_zones.append({"type":"sell","top":fvg['top'],"bottom":fvg['bottom'],"liquidity":"fvg"})

    return {"sell_zones": sell_zones, "buy_zones": buy_zones}