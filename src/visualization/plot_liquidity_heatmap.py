# plot_liquidity_heatmap.py

import pandas as pd
import numpy as np
import plotly.graph_objects as go


def plot_liquidity_heatmap(
    df: pd.DataFrame,
    price_col: str = "close",
    time_col: str = "time",
    bins: int = 40,
    max_rows: int = 5000
):
    """
    Genera un heatmap liviano de liquidez basado en frecuencia de precios por tiempo.
    Evita pivots gigantes y reduce carga para Streamlit.
    """

    if df is None or df.empty:
        raise ValueError("El DataFrame está vacío.")

    df = df.copy()

    if time_col not in df.columns:
        raise ValueError(f"No existe la columna '{time_col}'")
    if price_col not in df.columns:
        raise ValueError(f"No existe la columna '{price_col}'")

    # Limitar tamaño para evitar cuelgues
    if len(df) > max_rows:
        df = df.tail(max_rows).copy()

    # Asegurar formato fecha
    df[time_col] = pd.to_datetime(df[time_col], errors="coerce")
    df = df.dropna(subset=[time_col, price_col])

    if df.empty:
        raise ValueError("No hay datos válidos tras limpiar fechas/precios.")

    # Índice temporal simplificado
    df = df.sort_values(time_col).reset_index(drop=True)
    df["time_idx"] = np.arange(len(df))

    # Crear bins de precio
    price_min = df[price_col].min()
    price_max = df[price_col].max()

    if price_min == price_max:
        price_max = price_min + 0.0001

    price_bins = np.linspace(price_min, price_max, bins + 1)
    df["price_bin"] = pd.cut(df[price_col], bins=price_bins, include_lowest=True, labels=False)

    # Tabla heatmap liviana: conteo por time_idx y bin
    heatmap_df = (
        df.groupby(["price_bin", "time_idx"])
        .size()
        .unstack(fill_value=0)
    )

    if heatmap_df.empty:
        raise ValueError("No se pudo construir el heatmap.")

    # Eje Y con niveles de precio aproximados
    y_labels = []
    for i in heatmap_df.index:
        low = price_bins[int(i)]
        high = price_bins[int(i) + 1]
        y_labels.append(round((low + high) / 2, 5))

    fig = go.Figure(
        data=go.Heatmap(
            z=heatmap_df.values,
            x=heatmap_df.columns,
            y=y_labels,
            hoverongaps=False
        )
    )

    fig.update_layout(
        title="Liquidity Heatmap",
        xaxis_title="Secuencia temporal",
        yaxis_title="Precio",
        template="plotly_dark",
        height=700
    )

    return fig