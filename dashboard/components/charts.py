"""components/charts.py — Reusable Plotly layout defaults."""
from config import BORDER, TEXT2


def PLO(**kw):
    """Base Plotly layout — transparent background, dark grid."""
    d = dict(
        paper_bgcolor = "rgba(0,0,0,0)",
        plot_bgcolor  = "rgba(0,0,0,0)",
        font          = dict(family="Space Grotesk", color=TEXT2, size=10),
        margin        = dict(l=0, r=0, t=10, b=0),
        xaxis         = dict(gridcolor=BORDER, gridwidth=0.5),
        yaxis         = dict(gridcolor=BORDER, gridwidth=0.5),
    )
    d.update(kw)
    return d
