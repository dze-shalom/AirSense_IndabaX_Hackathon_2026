"""components/ui.py — Reusable Streamlit UI primitives and SVG gauges."""
import numpy as np
import streamlit as st
from config import NAVY2, NAVY3, BORDER, TEAL, TEXT1, TEXT2, GREEN, AMBER, ORANGE, RED


def sec(title):
    """Teal-dot section header."""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:.5rem;margin:.9rem 0 .6rem;">'
        f'<div style="width:5px;height:5px;border-radius:50%;background:{TEAL};'
        f'box-shadow:0 0 6px {TEAL};flex-shrink:0;"></div>'
        f'<span style="font-size:.65rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:.13em;color:{TEXT2};">{title}</span>'
        f'<div style="flex:1;height:1px;background:linear-gradient(90deg,{BORDER},transparent);"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def card(label, value, unit, badge=None, badge_col=None, accent=None):
    """Metric card with optional badge."""
    accent = accent or TEAL
    badge_html = (
        f'<div style="display:inline-flex;align-items:center;gap:.25rem;'
        f'padding:.18rem .45rem;border-radius:4px;font-size:.66rem;font-weight:600;'
        f'margin-top:.4rem;background:{badge_col}18;color:{badge_col or accent};">'
        f'{badge}</div>'
    ) if badge else ""
    st.markdown(
        f'<div style="background:{NAVY2};border:1px solid {BORDER};border-radius:10px;'
        f'padding:1rem;position:relative;overflow:hidden;">'
        f'<div style="position:absolute;top:0;left:0;right:0;height:2px;'
        f'background:{accent};border-radius:10px 10px 0 0;"></div>'
        f'<div style="font-size:.62rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:.12em;color:{TEXT2};margin-bottom:.35rem;">{label}</div>'
        f'<div style="font-size:1.85rem;font-weight:700;line-height:1;'
        f'color:{accent};font-family:JetBrains Mono,monospace;">{value}</div>'
        f'<div style="font-size:.65rem;color:{TEXT2};margin-top:.18rem;">{unit}</div>'
        f'{badge_html}</div>',
        unsafe_allow_html=True,
    )


def info_box(html):
    """Teal left-border info panel."""
    st.markdown(
        f'<div style="background:rgba(100,255,218,0.04);'
        f'border:1px solid rgba(100,255,218,0.16);border-left:3px solid {TEAL};'
        f'border-radius:0 7px 7px 0;padding:.6rem .85rem;font-size:.74rem;'
        f'color:{TEXT2};margin-top:.6rem;line-height:1.65;">{html}</div>',
        unsafe_allow_html=True,
    )


def bfai_gauge_svg(score, label, col):
    """Semicircular BFAI gauge as inline SVG string."""
    ang    = min(180, score / 100 * 180)
    rad    = np.deg2rad(180 - ang)
    nx, ny = 100 + 68 * np.cos(rad), 100 - 68 * np.sin(rad)
    circ   = 213.6
    offset = circ * (1 - ang / 180)
    return (
        '<div style="display:flex;justify-content:center;">'
        '<svg viewBox="0 0 200 120" width="200" height="120" style="overflow:visible;">'
        '<defs><linearGradient id="bfai_g" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%"   stop-color="{RED}"/>'
        f'<stop offset="35%"  stop-color="{ORANGE}"/>'
        f'<stop offset="60%"  stop-color="{AMBER}"/>'
        f'<stop offset="80%"  stop-color="{GREEN}"/>'
        f'<stop offset="100%" stop-color="{TEAL}"/>'
        '</linearGradient></defs>'
        f'<path d="M 22 100 A 78 78 0 0 1 178 100" fill="none" stroke="{BORDER}" stroke-width="14" stroke-linecap="round"/>'
        f'<path d="M 22 100 A 78 78 0 0 1 178 100" fill="none" stroke="url(#bfai_g)" stroke-width="14"'
        f' stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"/>'
        f'<line x1="100" y1="100" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{col}" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="100" cy="100" r="5" fill="{col}"/>'
        f'<text x="100" y="87" text-anchor="middle" fill="{col}" font-family="JetBrains Mono,monospace" font-size="24" font-weight="700">{score}</text>'
        f'<text x="100" y="100" text-anchor="middle" fill="{TEXT2}" font-family="Space Grotesk,sans-serif" font-size="8">/100 BFAI</text>'
        f'<text x="100" y="112" text-anchor="middle" fill="{col}" font-family="Space Grotesk,sans-serif" font-size="9" font-weight="600">{label}</text>'
        f'<text x="14"  y="113" fill="{TEXT2}" font-size="7" font-family="JetBrains Mono,monospace">0</text>'
        f'<text x="180" y="113" fill="{TEXT2}" font-size="7" font-family="JetBrains Mono,monospace">100</text>'
        '</svg></div>'
    )


def harmattan_gauge_svg(risk, status, col):
    """Semicircular Harmattan risk gauge as inline SVG string."""
    ang    = min(180, risk / 100 * 180)
    rad    = np.deg2rad(180 - ang)
    nx, ny = 100 + 68 * np.cos(rad), 100 - 68 * np.sin(rad)
    circ   = 213.6
    offset = circ * (1 - ang / 180)
    return (
        '<div style="display:flex;justify-content:center;">'
        '<svg viewBox="0 0 200 120" width="200" height="120" style="overflow:visible;">'
        '<defs><linearGradient id="hw_g" x1="0%" y1="0%" x2="100%" y2="0%">'
        f'<stop offset="0%"   stop-color="{GREEN}"/>'
        f'<stop offset="40%"  stop-color="{AMBER}"/>'
        f'<stop offset="70%"  stop-color="{ORANGE}"/>'
        f'<stop offset="100%" stop-color="{RED}"/>'
        '</linearGradient></defs>'
        f'<path d="M 22 100 A 78 78 0 0 1 178 100" fill="none" stroke="{BORDER}" stroke-width="14" stroke-linecap="round"/>'
        f'<path d="M 22 100 A 78 78 0 0 1 178 100" fill="none" stroke="url(#hw_g)" stroke-width="14"'
        f' stroke-linecap="round" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{offset:.1f}"/>'
        f'<line x1="100" y1="100" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{col}" stroke-width="3" stroke-linecap="round"/>'
        f'<circle cx="100" cy="100" r="5" fill="{col}"/>'
        f'<text x="100" y="87" text-anchor="middle" fill="{col}" font-family="JetBrains Mono,monospace" font-size="24" font-weight="700">{risk}</text>'
        f'<text x="100" y="100" text-anchor="middle" fill="{TEXT2}" font-family="Space Grotesk,sans-serif" font-size="8">/100 Risk</text>'
        f'<text x="100" y="112" text-anchor="middle" fill="{col}" font-family="Space Grotesk,sans-serif" font-size="8" font-weight="600">{status}</text>'
        '</svg></div>'
    )
