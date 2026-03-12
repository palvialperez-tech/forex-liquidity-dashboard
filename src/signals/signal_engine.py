from src.confluence.confluence_engine import detect_confluence
from src.context.session_engine import detect_session  # tu módulo de sesiones

def generate_signals(df, liquidity, structure, order_blocks, fvg_list=None, killzones=None):
    """
    Genera señales basadas en sweeps, BOS, OB y FVG, filtradas por killzones y ponderadas por sesión.
    """
    signals = []

    sweeps = liquidity["sweeps"]
    bos_list = structure["bos"]

    bullish_obs = order_blocks["bullish_ob"]
    bearish_obs = order_blocks["bearish_ob"]

    if killzones is None:
        killzones = []

    # Precalcular sesión por índice
    session_map = detect_session(df)  # debe devolver dict {index: "London"/"NY"/"Tokyo"}

    for sweep in sweeps:
        idx = sweep["index"]
        price = df["close"].iloc[idx]

        # ================================
        # Excluir killzones
        # ================================
        if idx in killzones:
            continue

        # ================================
        # Confirmar BOS cercano
        # ================================
        bos_confirmed = any(abs(bos["index"] - idx) < 5 for bos in bos_list)
        if not bos_confirmed:
            continue

        # ================================
        # Determinar sesión y factor de score
        # ================================
        session = session_map.get(idx, None)
        session_factor = 1.0

        # Ajuste ejemplo: BUY más fuerte en London si mercado alcista
        if session == "London":
            session_factor = 1.2
        elif session == "NY":
            session_factor = 1.0
        elif session == "Tokyo":
            session_factor = 0.9

        # ================================
        # BUY SETUP
        # ================================
        if sweep["type"] == "buy_sweep":
            ob_near = any(abs(ob["index"] - idx) < 10 for ob in bullish_obs)
            fvg_near = False
            if fvg_list:
                fvg_near = any(abs(fvg["index"] - idx) < 5 for fvg in fvg_list)

            if ob_near:
                base_score = 1 + int(fvg_near)
                score = base_score * session_factor

                signals.append({
                    "type": "BUY",
                    "entry": price,
                    "index": idx,
                    "setup": "sweep + bos + bullish_ob",
                    "score": score,
                    "session": session
                })

        # ================================
        # SELL SETUP
        # ================================
        if sweep["type"] == "sell_sweep":
            ob_near = any(abs(ob["index"] - idx) < 10 for ob in bearish_obs)
            fvg_near = False
            if fvg_list:
                fvg_near = any(abs(fvg["index"] - idx) < 5 for fvg in fvg_list)

            if ob_near:
                base_score = 1 + int(fvg_near)
                score = base_score * session_factor

                signals.append({
                    "type": "SELL",
                    "entry": price,
                    "index": idx,
                    "setup": "sweep + bos + bearish_ob",
                    "score": score,
                    "session": session
                })

    # Ordenar por score descendente
    signals.sort(key=lambda x: x.get("score", 0), reverse=True)

    return signals