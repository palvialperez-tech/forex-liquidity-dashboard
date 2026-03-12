from src.data.load_data import load_eurusd
from src.liquidity.liquidity_engine import run_liquidity_engine
from src.liquidity.zone_builder import build_zones
from src.liquidity.target_engine import (
    build_liquidity_targets,
    get_nearest_targets,
    get_side_targets
)
from src.liquidity.sweep_detector import (
    detect_liquidity_sweeps,
    get_recent_sweeps,
    get_latest_sweep
)
from src.structure.market_structure import detect_market_structure
from src.context.session_engine import detect_killzones
from src.context.mtf_context import (
    build_htf_frames,
    detect_trend_h1,
    detect_structure_m15,
    filter_signals_mtf
)
from src.order_blocks.order_block_engine import detect_order_blocks
from src.signals.signal_engine import generate_signals
from src.signals.signal_ranker import rank_signals
from src.backtesting.backtest_engine import run_backtest
from src.analytics.probability_engine import calculate_probabilities
from src.analytics.liquidity_bias import calculate_liquidity_bias
from src.fvg.fvg_engine import detect_fvg
from src.visualization.heatmap_engine import plot_liquidity_heatmap

import json
from datetime import datetime

import pandas as pd
import streamlit as st
from streamlit_autorefresh import st_autorefresh


# ===============================
# FUNCIONES AUXILIARES DASHBOARD
# ===============================
def safe_len(obj):
    try:
        return len(obj)
    except Exception:
        return 0


def get_session_bias(df):
    if df is None or len(df) == 0:
        return "Unknown"

    if "datetime" not in df.columns:
        return "Unknown"

    last_time = pd.to_datetime(df["datetime"].iloc[-1], errors="coerce")
    if pd.isna(last_time):
        return "Unknown"

    hour = last_time.hour

    if 0 <= hour <= 6:
        return "Tokyo"
    elif 7 <= hour <= 10:
        return "London"
    elif 13 <= hour <= 16:
        return "New York"
    return "Other"


def get_market_status_now():
    now = datetime.now()
    weekday = now.weekday()
    hour = now.hour

    if weekday == 5:
        return "CERRADO"

    if weekday == 6 and hour < 22:
        return "CERRADO"

    return "ABIERTO"


def get_dataset_status(df):
    if df is None or len(df) == 0 or "datetime" not in df.columns:
        return "UNKNOWN"

    last_time = pd.to_datetime(df["datetime"].iloc[-1], errors="coerce")
    if pd.isna(last_time):
        return "UNKNOWN"

    weekday = last_time.weekday()
    hour = last_time.hour

    if weekday == 5:
        return "CERRADO"

    if weekday == 6 and hour < 22:
        return "CERRADO"

    return "ABIERTO"


def is_near_signal(best_signal, min_score=2, max_distance=0.0020):
    if not isinstance(best_signal, dict):
        return False

    score = best_signal.get("score", 0)
    distance = best_signal.get("distance", 999)

    return score >= min_score and distance <= max_distance


def is_signal_aligned_with_trend(best_signal, trend_1h):
    if not isinstance(best_signal, dict):
        return False

    signal_type = best_signal.get("type")

    if trend_1h == "bullish" and signal_type == "BUY":
        return True

    if trend_1h == "bearish" and signal_type == "SELL":
        return True

    return False


def signal_id(signal):
    if not isinstance(signal, dict):
        return None

    return f"{signal.get('type')}_{signal.get('index')}_{signal.get('entry')}"


def format_price_dataframe(df_in, price_cols=None, distance_cols=None):
    if df_in is None or len(df_in) == 0:
        return df_in

    if price_cols is None:
        price_cols = ["entry", "sl", "tp", "target", "price", "level", "high", "low", "close", "exit_price"]

    if distance_cols is None:
        distance_cols = ["distance", "distance_pips", "sweep_distance_pips", "risk_distance", "reward_distance"]

    df_out = df_in.copy()

    for col in price_cols + distance_cols:
        if col in df_out.columns:
            df_out[col] = pd.to_numeric(df_out[col], errors="coerce")

    format_dict = {}

    for col in price_cols:
        if col in df_out.columns:
            format_dict[col] = "{:.5f}"

    for col in distance_cols:
        if col in df_out.columns:
            format_dict[col] = "{:.2f}"

    return df_out.style.format(format_dict)


def save_metrics(
    trades_df,
    stats,
    signals,
    best_signal,
    trend_1h,
    structure_m15,
    signals_raw=None,
    liquidity_targets=None,
    liquidity_bias=None,
    sweeps=None,
    latest_sweep=None,
    filename="dashboard_metrics.json"
):
    metrics = {
        "equity_final": None,
        "total_trades": 0,
        "wins": 0,
        "losses": 0,
        "trend_1h": trend_1h,
        "structure_m15": structure_m15,
        "stats": stats if isinstance(stats, dict) else {},
        "best_signal": best_signal if isinstance(best_signal, dict) else None,
        "signals": signals[:50] if isinstance(signals, list) else [],
        "signals_raw": signals_raw[:50] if isinstance(signals_raw, list) else [],
        "liquidity_targets": liquidity_targets[:50] if isinstance(liquidity_targets, list) else [],
        "liquidity_bias": liquidity_bias if isinstance(liquidity_bias, dict) else {},
        "sweeps": sweeps[:50] if isinstance(sweeps, list) else [],
        "latest_sweep": latest_sweep if isinstance(latest_sweep, dict) else None
    }

    if isinstance(trades_df, pd.DataFrame) and len(trades_df) > 0:
        metrics["total_trades"] = len(trades_df)

        if "equity" in trades_df.columns:
            metrics["equity_final"] = trades_df["equity"].iloc[-1]

        if "result" in trades_df.columns:
            metrics["wins"] = len(trades_df[trades_df["result"] == "win"])
            metrics["losses"] = len(trades_df[trades_df["result"] == "loss"])

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=4, ensure_ascii=False, default=str)


# ===============================
# MAIN PIPELINE
# ===============================
def main():
    st.set_page_config(page_title="Forex Liquidity Dashboard", layout="wide")

    refresh_count = st_autorefresh(
        interval=300000,
        limit=None,
        key="forex_dashboard_refresh"
    )

    st.title("Forex Liquidity Dashboard - EURUSD")
    st.caption(f"Auto refresh activo cada 5 minutos | Refresh #{refresh_count}")

    # -----------------------
    # Carga de datos
    # -----------------------
    st.write("Cargando datos EURUSD...")
    df = load_eurusd()

    if df is None or len(df) == 0:
        st.error("No se pudieron cargar datos de EURUSD.")
        return

    if "datetime" in df.columns:
        df["datetime"] = pd.to_datetime(df["datetime"], errors="coerce")

    # -----------------------
    # Contexto temporal / dataset
    # -----------------------
    last_candle = None
    if "datetime" in df.columns and len(df) > 0:
        last_candle = pd.to_datetime(df["datetime"].iloc[-1], errors="coerce")

    # -----------------------
    # Contexto MTF
    # -----------------------
    m15, h1 = build_htf_frames(df)
    trend_1h = detect_trend_h1(h1)
    structure_m15 = detect_structure_m15(m15)

    col1, col2, col3, col4, col5, col6 = st.columns(6)

    with col1:
        st.metric("Última vela", str(last_candle) if last_candle is not None else "N/A")

    with col2:
        if last_candle is not None and not pd.isna(last_candle):
            st.metric("Día dataset", last_candle.strftime("%A"))
        else:
            st.metric("Día dataset", "N/A")

    with col3:
        st.metric("Mercado ahora", get_market_status_now())

    with col4:
        st.metric("Estado última vela", get_dataset_status(df))

    with col5:
        st.metric("Trend H1", trend_1h.upper())

    with col6:
        st.metric("Structure M15", structure_m15.upper())

    st.write(f"Velas cargadas: {len(df)}")

    # -----------------------
    # Detectar liquidez
    # -----------------------
    st.write("Detectando liquidez...")
    liquidity = run_liquidity_engine(df)
    st.write(f"Liquidity detectada: {safe_len(liquidity)}")

    # -----------------------
    # Detectar sweeps de liquidez
    # -----------------------
    st.write("Detectando Liquidity Sweeps...")
    sweeps = detect_liquidity_sweeps(
        df=df,
        liquidity=liquidity,
        sweep_threshold_pips=1.0,
        close_back_inside=True,
        lookback_bars=200,
        pip_size=0.0001
    )
    latest_sweep = get_latest_sweep(sweeps)
    recent_sweeps = get_recent_sweeps(sweeps, last_n=10)
    st.write(f"Sweeps detectados: {safe_len(sweeps)}")

    # -----------------------
    # Detectar estructura base actual
    # -----------------------
    st.write("Detectando estructura de mercado...")
    structure = detect_market_structure(df)

    # -----------------------
    # Detectar OB
    # -----------------------
    st.write("Detectando Order Blocks...")
    order_blocks = detect_order_blocks(df)
    st.write(f"Order Blocks detectados: {safe_len(order_blocks)}")

    # -----------------------
    # Detectar FVG
    # -----------------------
    st.write("Detectando Fair Value Gaps (FVG)...")
    fvg_list = detect_fvg(df)
    st.write(f"FVG detectados: {safe_len(fvg_list)}")

    # -----------------------
    # Construir zonas
    # -----------------------
    st.write("Construyendo zonas institucionales...")
    zones = build_zones(liquidity, fvg_list=fvg_list)
    st.write(f"Zonas construidas: {safe_len(zones)}")

    # -----------------------
    # Detectar killzones
    # -----------------------
    st.write("Detectando killzones...")
    killzones = detect_killzones(df)
    st.write(f"Killzones detectadas: {safe_len(killzones)}")

    # -----------------------
    # Generar señales base M5
    # -----------------------
    st.write("Generando señales automáticas...")
    signals_raw = generate_signals(
        df,
        liquidity,
        structure,
        order_blocks,
        fvg_list=fvg_list,
        killzones=killzones
    )
    st.write(f"Señales base generadas: {safe_len(signals_raw)}")

    # -----------------------
    # Filtrar señales por contexto MTF
    # -----------------------
    signals_mtf = filter_signals_mtf(signals_raw, trend_1h, structure_m15)
    st.write(f"Señales después de filtro MTF: {safe_len(signals_mtf)}")

    if safe_len(signals_mtf) > 0:
        signals = signals_mtf
    else:
        st.warning("Filtro MTF dejó 0 señales. Usando señales base temporalmente para diagnóstico.")
        signals = signals_raw

    # -----------------------
    # Rankear señales
    # -----------------------
    best_signal, active_signals, discarded_signals = rank_signals(
        df,
        signals,
        latest_sweep=latest_sweep
    )
    st.write(f"Best signal: {'Sí' if best_signal is not None else 'No'}")
    st.write(f"Señales activas: {safe_len(active_signals)}")
    st.write(f"Señales descartadas: {safe_len(discarded_signals)}")

    # -----------------------
    # Persistencia de alerta
    # -----------------------
    current_signal_id = signal_id(best_signal)

    if "last_alert_signal" not in st.session_state:
        st.session_state["last_alert_signal"] = None

    # -----------------------
    # Alerta de señal cercana
    # -----------------------
    if is_near_signal(best_signal):
        signal_type = best_signal.get("type", "UNKNOWN")
        entry = best_signal.get("entry", "N/A")
        score = best_signal.get("score", "N/A")
        age = best_signal.get("age", "N/A")
        distance = best_signal.get("distance", "N/A")
        aligned = is_signal_aligned_with_trend(best_signal, trend_1h)

        if current_signal_id != st.session_state["last_alert_signal"]:
            if signal_type == "BUY":
                st.success(
                    f"NUEVA ALERTA BUY | Entry: {entry} | "
                    f"Score: {score} | Age: {age} | Distance: {distance} | "
                    f"Trend H1: {trend_1h.upper()} | Aligned: {aligned}"
                )
            elif signal_type == "SELL":
                st.error(
                    f"NUEVA ALERTA SELL | Entry: {entry} | "
                    f"Score: {score} | Age: {age} | Distance: {distance} | "
                    f"Trend H1: {trend_1h.upper()} | Aligned: {aligned}"
                )
            else:
                st.warning(
                    f"NUEVA ALERTA | Entry: {entry} | "
                    f"Score: {score} | Age: {age} | Distance: {distance} | "
                    f"Trend H1: {trend_1h.upper()} | Aligned: {aligned}"
                )

            st.session_state["last_alert_signal"] = current_signal_id

        if aligned:
            st.info(
                f"SEÑAL VIGENTE A FAVOR DE TENDENCIA H1 | "
                f"{signal_type} | Entry: {entry} | Score: {score} | Distance: {distance}"
            )
        else:
            st.warning(
                f"SEÑAL VIGENTE PERO CONTRA/NEUTRAL A TENDENCIA H1 | "
                f"{signal_type} | Entry: {entry} | Score: {score} | Distance: {distance}"
            )

    # -----------------------
    # Backtesting
    # -----------------------
    st.write("Ejecutando backtesting...")
    trades_df = run_backtest(df, signals)
    st.write(f"Trades backtest: {safe_len(trades_df)}")

    # -----------------------
    # Probabilidades históricas
    # -----------------------
    st.write("Calculando probabilidades históricas...")
    stats = calculate_probabilities(df, signals_raw if safe_len(signals_raw) > 0 else signals)

    # -----------------------
    # Liquidity Target Engine
    # -----------------------
    st.write("Calculando Liquidity Target Engine...")

    liquidity_targets = build_liquidity_targets(
        df=df,
        liquidity=liquidity,
        zones=zones,
        signals=signals,
        symbol="EURUSD",
        min_distance_pips=2,
        max_distance_pips=25
    )

    liquidity_bias = calculate_liquidity_bias(liquidity_targets)

    nearest_targets = get_nearest_targets(liquidity_targets, top_n=10)
    above_targets = get_side_targets(liquidity_targets, side="above", top_n=5)
    below_targets = get_side_targets(liquidity_targets, side="below", top_n=5)

    st.write(f"Liquidity targets: {safe_len(liquidity_targets)}")

    # -----------------------
    # Señal activa
    # -----------------------
    st.subheader("Señal activa")
    if best_signal is not None:
        best_signal_view = dict(best_signal)
        best_signal_view["trend_1h"] = trend_1h
        best_signal_view["structure_m15"] = structure_m15
        best_signal_view["aligned_with_1h"] = is_signal_aligned_with_trend(best_signal, trend_1h)

        best_signal_df = pd.DataFrame([best_signal_view])
        st.dataframe(
            format_price_dataframe(best_signal_df),
            use_container_width=True
        )
    else:
        st.info("No hay señal activa vigente.")

    # -----------------------
    # Dashboard visual
    # -----------------------
    st.subheader("Liquidity Heatmap + OB + FVG")
    try:
        heatmap_fig = plot_liquidity_heatmap(df, liquidity, zones, fvg_list)
        st.plotly_chart(heatmap_fig, use_container_width=True, key="heatmap_chart")
    except Exception as e:
        st.error(f"Error al renderizar heatmap: {e}")

    # -----------------------
    # Liquidity Sweep Detector
    # -----------------------
    st.subheader("Liquidity Sweep Detector")

    if latest_sweep is not None:
        st.success(
            f"Último sweep: {latest_sweep.get('type')} | "
            f"Nivel: {latest_sweep.get('level'):.5f} | "
            f"Dirección esperada: {latest_sweep.get('direction')} | "
            f"Distancia sweep: {latest_sweep.get('sweep_distance_pips')} pips"
        )
    else:
        st.info("No se detectaron sweeps recientes.")

    if safe_len(recent_sweeps) > 0:
        sweeps_df = pd.DataFrame(recent_sweeps)
        st.dataframe(
            format_price_dataframe(sweeps_df),
            use_container_width=True
        )
    else:
        st.info("No hay tabla de sweeps para mostrar.")

    # -----------------------
    # Liquidity Target Engine
    # -----------------------
    st.subheader("Liquidity Target Engine")

    bias_col1, bias_col2, bias_col3, bias_col4 = st.columns(4)

    bias_col1.metric("Liquidity Above", liquidity_bias.get("liquidity_above", 0))
    bias_col2.metric("Liquidity Below", liquidity_bias.get("liquidity_below", 0))
    bias_col3.metric("Bias", str(liquidity_bias.get("bias", "neutral")).upper())
    bias_col4.metric("Probable Sweep", str(liquidity_bias.get("probable_sweep", "none")).upper())

    best_target = liquidity_bias.get("best_target")

    if isinstance(best_target, dict):
        st.success(
            f"Target principal: {best_target.get('price')} | "
            f"Tipo: {best_target.get('type')} | "
            f"Dirección: {best_target.get('direction')} | "
            f"Distancia: {best_target.get('distance_pips')} pips"
        )
    else:
        st.info("No se detectó target principal.")

    pct_col1, pct_col2 = st.columns(2)

    pct_col1.metric("% Liquidity Above", f"{liquidity_bias.get('pct_above', 0)}%")
    pct_col2.metric("% Liquidity Below", f"{liquidity_bias.get('pct_below', 0)}%")

    st.subheader("Nearest Liquidity Targets")
    if len(nearest_targets) > 0:
        nearest_targets_df = pd.DataFrame(nearest_targets)
        st.dataframe(
            format_price_dataframe(nearest_targets_df),
            use_container_width=True
        )
    else:
        st.info("No hay liquidity targets cercanos.")

    col_up, col_down = st.columns(2)

    with col_up:
        st.subheader("Targets Above")
        if len(above_targets) > 0:
            above_targets_df = pd.DataFrame(above_targets)
            st.dataframe(
                format_price_dataframe(above_targets_df),
                use_container_width=True
            )
        else:
            st.info("No hay targets arriba.")

    with col_down:
        st.subheader("Targets Below")
        if len(below_targets) > 0:
            below_targets_df = pd.DataFrame(below_targets)
            st.dataframe(
                format_price_dataframe(below_targets_df),
                use_container_width=True
            )
        else:
            st.info("No hay targets abajo.")

    # -----------------------
    # Señales activas
    # -----------------------
    st.subheader("Señales activas")
    if isinstance(active_signals, list) and len(active_signals) > 0:
        active_df = pd.DataFrame(active_signals[:10])
        st.dataframe(
            format_price_dataframe(active_df),
            use_container_width=True
        )
    else:
        st.info("No hay señales activas.")

    # -----------------------
    # Señales descartadas
    # -----------------------
    st.subheader("Señales descartadas")
    if isinstance(discarded_signals, list) and len(discarded_signals) > 0:
        discarded_df = pd.DataFrame(discarded_signals[:10])
        st.dataframe(
            format_price_dataframe(discarded_df),
            use_container_width=True
        )
    else:
        st.info("No hay señales descartadas.")

    # -----------------------
    # Backtest resultados
    # -----------------------
    st.subheader("Backtest Resultados")
    if isinstance(trades_df, pd.DataFrame) and len(trades_df) > 0:
        st.dataframe(
            format_price_dataframe(trades_df.head(20)),
            use_container_width=True
        )

        equity_final = trades_df["equity"].iloc[-1] if "equity" in trades_df.columns else "N/A"
        total_trades = len(trades_df)
        wins = len(trades_df[trades_df["result"] == "win"]) if "result" in trades_df.columns else 0
        losses = len(trades_df[trades_df["result"] == "loss"]) if "result" in trades_df.columns else 0

        col_bt1, col_bt2, col_bt3, col_bt4 = st.columns(4)

        with col_bt1:
            st.metric("Equity final", equity_final)

        with col_bt2:
            st.metric("Total trades", total_trades)

        with col_bt3:
            st.metric("Wins", wins)

        with col_bt4:
            st.metric("Losses", losses)

        if "result" in trades_df.columns:
            st.write("Valores únicos en result:", trades_df["result"].astype(str).unique())

            st.subheader("Trades ganados")
            wins_df = trades_df[trades_df["result"] == "win"]
            if len(wins_df) > 0:
                st.dataframe(
                    format_price_dataframe(wins_df.head(10)),
                    use_container_width=True
                )
            else:
                st.info("No hay trades ganados.")

            st.subheader("Trades perdidos")
            losses_df = trades_df[trades_df["result"] == "loss"]
            if len(losses_df) > 0:
                st.dataframe(
                    format_price_dataframe(losses_df.head(10)),
                    use_container_width=True
                )
            else:
                st.info("No hay trades perdidos.")

    else:
        st.info("No hay resultados de backtest para mostrar.")

    # -----------------------
    # Probabilidades históricas
    # -----------------------
    st.subheader("Probabilidades históricas")
    if isinstance(stats, dict) and len(stats) > 0:
        st.write("Trades:", stats.get("trades", "N/A"))
        st.write("Win Rate:", stats.get("win_rate", "N/A"))
        st.write("RR Promedio:", stats.get("avg_rr", "N/A"))
        st.write("Expectancy:", stats.get("expectancy", "N/A"))
    else:
        st.info("No hay estadísticas históricas disponibles.")

    # -----------------------
    # Sesión actual / Bias
    # -----------------------
    st.subheader("Sesión actual / Bias")
    session_bias = get_session_bias(df)
    st.write(session_bias)

    # -----------------------
    # Guardar métricas externas
    # -----------------------
    save_metrics(
        trades_df=trades_df,
        stats=stats,
        signals=signals,
        signals_raw=signals_raw,
        best_signal=best_signal,
        trend_1h=trend_1h,
        structure_m15=structure_m15,
        liquidity_targets=liquidity_targets,
        liquidity_bias=liquidity_bias,
        sweeps=sweeps,
        latest_sweep=latest_sweep
    )

    st.success("Dashboard listo. Métricas guardadas en 'dashboard_metrics.json'")


if __name__ == "__main__":
    main()