import pandas as pd
import plotly.graph_objects as go


def _get_time_series(df: pd.DataFrame) -> pd.Series:
    """
    Obtiene la serie temporal sin asumir una estructura rígida.
    Prioridad:
    1) columna datetime
    2) columna time
    3) index del DataFrame
    """
    if "datetime" in df.columns:
        return pd.to_datetime(df["datetime"], errors="coerce")
    if "time" in df.columns:
        return pd.to_datetime(df["time"], errors="coerce")

    if isinstance(df.index, pd.DatetimeIndex):
        return pd.Series(df.index, index=df.index)

    return pd.to_datetime(pd.Series(df.index, index=df.index), errors="coerce")


def _safe_get(item, *keys, default=None):
    if item is None:
        return default

    if isinstance(item, dict):
        for key in keys:
            if key in item and item[key] is not None:
                return item[key]

    return default


def _safe_float(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _extract_price_levels(items, preferred_keys):
    levels = []

    if not isinstance(items, list):
        return levels

    for item in items:
        if isinstance(item, (int, float)):
            levels.append(float(item))
            continue

        if isinstance(item, dict):
            value = _safe_get(item, *preferred_keys)
            if value is not None:
                value = _safe_float(value)
                if value is not None:
                    levels.append(value)

    return levels


def _extract_zone_bounds(zone):
    if not isinstance(zone, dict):
        return None, None

    top = _safe_get(zone, "top", "high", "upper", "max_price")
    bottom = _safe_get(zone, "bottom", "low", "lower", "min_price")

    top = _safe_float(top)
    bottom = _safe_float(bottom)

    if top is None or bottom is None:
        return None, None

    if bottom > top:
        bottom, top = top, bottom

    return top, bottom


def _extract_fvg_bounds(fvg):
    if not isinstance(fvg, dict):
        return None, None

    top = _safe_get(fvg, "high", "top", "upper")
    bottom = _safe_get(fvg, "low", "bottom", "lower")

    top = _safe_float(top)
    bottom = _safe_float(bottom)

    if top is None or bottom is None:
        return None, None

    if bottom > top:
        bottom, top = top, bottom

    return top, bottom


def _pip_size_for_symbol(symbol="EURUSD"):
    if str(symbol).upper().endswith("JPY"):
        return 0.01
    return 0.0001


def _is_near_price(level, current_price, max_distance_pips, pip_size):
    if level is None or current_price is None:
        return False

    distance_pips = abs(level - current_price) / pip_size
    return distance_pips <= max_distance_pips


def _is_zone_near_price(top, bottom, current_price, max_distance_pips, pip_size):
    if top is None or bottom is None or current_price is None:
        return False

    if bottom <= current_price <= top:
        return True

    nearest_edge = min(abs(top - current_price), abs(bottom - current_price))
    distance_pips = nearest_edge / pip_size
    return distance_pips <= max_distance_pips


def _deduplicate_levels(levels, pip_size, merge_threshold_pips=1.2):
    if not levels:
        return []

    levels = sorted(levels)
    out = [levels[0]]
    threshold = merge_threshold_pips * pip_size

    for level in levels[1:]:
        if abs(level - out[-1]) > threshold:
            out.append(level)

    return out


def _filter_near_levels(levels, current_price, pip_size, max_distance_pips=30, max_levels=8):
    if not levels:
        return []

    filtered = [
        lvl for lvl in levels
        if _is_near_price(lvl, current_price, max_distance_pips, pip_size)
    ]

    filtered = _deduplicate_levels(filtered, pip_size=pip_size, merge_threshold_pips=1.2)
    filtered = sorted(filtered, key=lambda lvl: abs(lvl - current_price))
    return filtered[:max_levels]


def _filter_near_zones(zones, current_price, pip_size, max_distance_pips=35, max_zones=4):
    if not isinstance(zones, list) or not zones:
        return []

    kept = []

    for zone in zones:
        top, bottom = _extract_zone_bounds(zone)
        if top is None or bottom is None:
            continue

        if _is_zone_near_price(top, bottom, current_price, max_distance_pips, pip_size):
            zone_copy = dict(zone)
            zone_copy["_top"] = top
            zone_copy["_bottom"] = bottom

            if bottom <= current_price <= top:
                distance = 0.0
            else:
                distance = min(abs(top - current_price), abs(bottom - current_price)) / pip_size

            zone_copy["_distance_pips"] = distance
            kept.append(zone_copy)

    kept = sorted(kept, key=lambda z: z.get("_distance_pips", 999999))
    return kept[:max_zones]


def _filter_near_fvg(fvg_list, current_price, pip_size, max_distance_pips=35, max_fvg=4):
    if not isinstance(fvg_list, list) or not fvg_list:
        return []

    kept = []

    for fvg in fvg_list:
        top, bottom = _extract_fvg_bounds(fvg)
        if top is None or bottom is None:
            continue

        if _is_zone_near_price(top, bottom, current_price, max_distance_pips, pip_size):
            fvg_copy = dict(fvg)
            fvg_copy["_top"] = top
            fvg_copy["_bottom"] = bottom

            if bottom <= current_price <= top:
                distance = 0.0
            else:
                distance = min(abs(top - current_price), abs(bottom - current_price)) / pip_size

            fvg_copy["_distance_pips"] = distance
            kept.append(fvg_copy)

    kept = sorted(kept, key=lambda z: z.get("_distance_pips", 999999))
    return kept[:max_fvg]


def _add_horizontal_levels(fig, x0, x1, levels, name, color, dash="dot", width=1):
    if not levels:
        return

    for i, level in enumerate(levels):
        fig.add_trace(
            go.Scattergl(
                x=[x0, x1],
                y=[level, level],
                mode="lines",
                name=name if i == 0 else None,
                legendgroup=name,
                showlegend=(i == 0),
                line=dict(color=color, width=width, dash=dash),
                hovertemplate=f"{name}: {level:.5f}<extra></extra>",
            )
        )


def _add_zone_bands(fig, x0, x1, zones, name, fillcolor, linecolor):
    if not isinstance(zones, list) or not zones:
        return

    count = 0
    for zone in zones:
        top = zone.get("_top")
        bottom = zone.get("_bottom")

        if top is None or bottom is None:
            top, bottom = _extract_zone_bounds(zone)

        if top is None or bottom is None:
            continue

        fig.add_trace(
            go.Scatter(
                x=[x0, x1, x1, x0, x0],
                y=[bottom, bottom, top, top, bottom],
                mode="lines",
                fill="toself",
                fillcolor=fillcolor,
                line=dict(color=linecolor, width=1),
                name=name if count == 0 else None,
                legendgroup=name,
                showlegend=(count == 0),
                hovertemplate=(
                    f"{name}<br>"
                    f"Bottom: {bottom:.5f}<br>"
                    f"Top: {top:.5f}<extra></extra>"
                ),
            )
        )
        count += 1


def _add_fvg_bands(fig, x0, x1, fvg_list):
    if not isinstance(fvg_list, list) or not fvg_list:
        return

    count = 0
    for fvg in fvg_list:
        top = fvg.get("_top")
        bottom = fvg.get("_bottom")

        if top is None or bottom is None:
            top, bottom = _extract_fvg_bounds(fvg)

        if top is None or bottom is None:
            continue

        fig.add_trace(
            go.Scatter(
                x=[x0, x1, x1, x0, x0],
                y=[bottom, bottom, top, top, bottom],
                mode="lines",
                fill="toself",
                fillcolor="rgba(255, 193, 7, 0.10)",
                line=dict(color="rgba(255, 193, 7, 0.45)", width=1),
                name="FVG" if count == 0 else None,
                legendgroup="FVG",
                showlegend=(count == 0),
                hovertemplate=(
                    f"FVG<br>"
                    f"Bottom: {bottom:.5f}<br>"
                    f"Top: {top:.5f}<extra></extra>"
                ),
            )
        )
        count += 1


def _build_dynamic_y_range(plot_df, current_price, pip_size, buffer_pips=12):
    recent_low = _safe_float(plot_df["low"].min(), default=current_price)
    recent_high = _safe_float(plot_df["high"].max(), default=current_price)

    buffer_price = buffer_pips * pip_size

    y_min = min(recent_low, current_price) - buffer_price
    y_max = max(recent_high, current_price) + buffer_price

    return [y_min, y_max]


def plot_liquidity_heatmap(df, liquidity=None, zones=None, fvg_list=None, *args, **kwargs):
    """
    Heatmap optimizado para EURUSD M5:
    - filtra niveles lejanos al precio actual
    - limita cantidad de zonas/FVG
    - mantiene eje Y cercano al contexto actual
    """
    if df is None or len(df) == 0:
        return go.Figure()

    liquidity = liquidity or {}
    zones = zones or {}
    fvg_list = fvg_list or []

    symbol = kwargs.get("symbol", "EURUSD")
    pip_size = _pip_size_for_symbol(symbol)

    max_candles = 300
    plot_df = df.tail(max_candles).copy()

    current_price = _safe_float(plot_df["close"].iloc[-1], default=None)
    if current_price is None:
        return go.Figure()

    time_series = _get_time_series(plot_df)

    if time_series.isna().all():
        x = list(range(len(plot_df)))
        x0 = x[0]
        x1 = x[-1]
    else:
        x = time_series
        x0 = x.iloc[0]
        x1 = x.iloc[-1]

    fig = go.Figure()

    fig.add_trace(
        go.Candlestick(
            x=x,
            open=plot_df["open"],
            high=plot_df["high"],
            low=plot_df["low"],
            close=plot_df["close"],
            name="EURUSD",
        )
    )

    equal_highs_raw = _extract_price_levels(
        liquidity.get("equal_highs", []),
        ("price", "level", "high", "top")
    )

    equal_lows_raw = _extract_price_levels(
        liquidity.get("equal_lows", []),
        ("price", "level", "low", "bottom")
    )

    equal_highs = _filter_near_levels(
        equal_highs_raw,
        current_price=current_price,
        pip_size=pip_size,
        max_distance_pips=30,
        max_levels=6
    )

    equal_lows = _filter_near_levels(
        equal_lows_raw,
        current_price=current_price,
        pip_size=pip_size,
        max_distance_pips=30,
        max_levels=6
    )

    buy_zones = _filter_near_zones(
        zones.get("buy_zones", []),
        current_price=current_price,
        pip_size=pip_size,
        max_distance_pips=35,
        max_zones=3
    )

    sell_zones = _filter_near_zones(
        zones.get("sell_zones", []),
        current_price=current_price,
        pip_size=pip_size,
        max_distance_pips=35,
        max_zones=3
    )

    near_fvg = _filter_near_fvg(
        fvg_list,
        current_price=current_price,
        pip_size=pip_size,
        max_distance_pips=35,
        max_fvg=3
    )

    _add_horizontal_levels(
        fig=fig,
        x0=x0,
        x1=x1,
        levels=equal_highs,
        name="Equal Highs",
        color="rgba(255, 77, 77, 0.80)",
        dash="dot",
        width=1
    )

    _add_horizontal_levels(
        fig=fig,
        x0=x0,
        x1=x1,
        levels=equal_lows,
        name="Equal Lows",
        color="rgba(77, 166, 255, 0.80)",
        dash="dot",
        width=1
    )

    _add_zone_bands(
        fig=fig,
        x0=x0,
        x1=x1,
        zones=buy_zones,
        name="Buy Zones",
        fillcolor="rgba(46, 204, 113, 0.10)",
        linecolor="rgba(46, 204, 113, 0.45)"
    )

    _add_zone_bands(
        fig=fig,
        x0=x0,
        x1=x1,
        zones=sell_zones,
        name="Sell Zones",
        fillcolor="rgba(231, 76, 60, 0.10)",
        linecolor="rgba(231, 76, 60, 0.45)"
    )

    _add_fvg_bands(
        fig=fig,
        x0=x0,
        x1=x1,
        fvg_list=near_fvg
    )

    y_range = _build_dynamic_y_range(
        plot_df=plot_df,
        current_price=current_price,
        pip_size=pip_size,
        buffer_pips=12
    )

    fig.update_layout(
        title="EURUSD Liquidity Heatmap",
        template="plotly_dark",
        height=750,
        xaxis_title="Time",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        hovermode="x unified",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0
        ),
        margin=dict(l=20, r=20, t=60, b=20)
    )

    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        fixedrange=False,
        range=y_range
    )

    return fig