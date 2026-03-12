def detect_confluence(df, liquidity, structure, order_blocks, fvg_list=None, killzones=None):
    """
    Detecta señales basadas en:
    - Liquidity sweeps
    - BOS (break of structure)
    - Order Blocks
    - Opcionalmente FVG
    - Score: cantidad de confluencias
    - Killzones: evitar trades en zonas peligrosas
    """

    if killzones is None:
        killzones = []

    signals = []
    sweeps = liquidity.get("sweeps", [])
    pools = liquidity.get("liquidity_pools", [])
    bos_events = structure.get("bos", [])
    bullish_ob = order_blocks.get("bullish_ob", [])
    bearish_ob = order_blocks.get("bearish_ob", [])

    price_tol = 0.0012
    pool_tol = 0.0015
    bos_window = 40
    zone_tol = 0.0015

    for sweep in sweeps:
        index = sweep["index"]
        price = df.iloc[index]["close"]

        # Saltar si estamos en killzone
        if index in killzones:
            continue

        # =========================
        # Confluencias
        # =========================
        score = 0
        confluence_list = []

        # Liquidity Pool
        near_pool = any(abs(price - pool["price"]) < pool_tol for pool in pools)
        if near_pool:
            score += 1
            confluence_list.append("liquidity_pool")

        # BOS
        if sweep["type"] == "buy_sweep":
            bos_confirm = any(
                bos["type"] == "bullish_BOS" and abs(bos["index"] - index) < bos_window
                for bos in bos_events
            )
        else:
            bos_confirm = any(
                bos["type"] == "bearish_BOS" and abs(bos["index"] - index) < bos_window
                for bos in bos_events
            )

        if bos_confirm:
            score += 1
            confluence_list.append("BOS")

        # Order Blocks
        if sweep["type"] == "buy_sweep":
            near_ob = any(abs(price - ob["top"]) < price_tol for ob in bullish_ob)
            if near_ob:
                score += 1
                confluence_list.append("bullish_OB")
        else:
            near_ob = any(abs(price - ob["bottom"]) < price_tol for ob in bearish_ob)
            if near_ob:
                score += 1
                confluence_list.append("bearish_OB")

        # FVG
        if fvg_list:
            if sweep["type"] == "buy_sweep":
                near_fvg = any(fvg["type"]=="bullish" and fvg["bottom"]-price_tol <= price <= fvg["top"]+price_tol
                               for fvg in fvg_list)
            else:
                near_fvg = any(fvg["type"]=="bearish" and fvg["bottom"]-price_tol <= price <= fvg["top"]+price_tol
                               for fvg in fvg_list)
            if near_fvg:
                score += 1
                confluence_list.append("FVG")

        # =========================
        # Generar señal solo si score >= 2
        # =========================
        if score >= 2:
            signals.append({
                "type": "BUY" if sweep["type"]=="buy_sweep" else "SELL",
                "entry": price,
                "index": index,
                "score": score,
                "confluence": confluence_list
            })

    return signals