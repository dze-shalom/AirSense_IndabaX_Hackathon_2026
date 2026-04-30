"""components/charts.py — Reusable Plotly layout defaults."""
import streamlit as st
from config import BORDER, TEXT2, NAVY2


def PLO(**kw):
    """Base Plotly layout — transparent background, theme-aware grid and font."""
    is_light = st.session_state.get("theme", "light") == "light"
    grid_col  = "rgba(160,100,60,0.18)" if is_light else BORDER
    font_col  = "#5c3a1e"               if is_light else TEXT2
    tip_bg    = "#fffaf4"               if is_light else NAVY2
    tip_font  = "#1a0e04"               if is_light else TEXT2
    tip_border= "rgba(160,100,60,0.35)" if is_light else "rgba(100,255,218,0.25)"
    d = dict(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        font          = dict(family="Space Grotesk", color=font_col, size=10),
        margin        = dict(l=0, r=0, t=10, b=0),
        xaxis         = dict(gridcolor=grid_col, gridwidth=0.5),
        yaxis         = dict(gridcolor=grid_col, gridwidth=0.5),
        hoverlabel    = dict(
            bgcolor    = tip_bg,
            font_color = tip_font,
            font_size  = 11,
            font_family= "Open Sans",
            bordercolor= tip_border,
        ),
        modebar       = dict(
            bgcolor    = "rgba(0,0,0,0)",
            color      = font_col,
            activecolor= "#b5613f" if is_light else "#64ffda",
        ),
    )
    d.update(kw)
    return d

