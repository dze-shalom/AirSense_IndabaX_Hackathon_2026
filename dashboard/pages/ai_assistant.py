"""pages/ai_assistant.py"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

from config import *
from utils.api import call_claude
from utils.helpers import (aqi, compute_bfai, bfai_label, bfai_col,
                            classify_source, health_impact, city_profile,
                            SOURCE_LABELS, SOURCE_COLORS, LNG)
from utils.models import (load_models, load_artefacts, get_conf_interval,
                           get_alert_prob, predict_7day, infer_region_from_lat)
from utils.api import fetch_forecast, geocode_city, wmo_icon
from components.ui import sec, card, info_box, bfai_gauge_svg, harmattan_gauge_svg
from components.charts import PLO

def _cbg():
    """Card background — adapts to current theme."""
    import streamlit as st
    if st.session_state.get("theme","light") == "light":
        return "rgba(255,252,248,0.95)"
    from config import NAVY2
    return NAVY2

def _cborder():
    """Card border — adapts to current theme."""
    import streamlit as st
    if st.session_state.get("theme","light") == "light":
        return "rgba(160,100,60,0.2)"
    from config import BORDER
    return BORDER

def _ctxt():
    """Primary text — adapts to current theme."""
    import streamlit as st
    if st.session_state.get("theme","light") == "light":
        return "#1a0e04"
    from config import TEXT1
    return TEXT1

def _ctxt2():
    """Secondary text — adapts to current theme."""
    import streamlit as st
    if st.session_state.get("theme","light") == "light":
        return "#5c3a1e"
    from config import TEXT2
    return TEXT2




def page_ai():
    t = T[LNG()]
    st.markdown('<div class="as-content">', unsafe_allow_html=True)
    sec("AI Health Assistant — Powered by Claude (Anthropic)")
    c1,c2=st.columns(2)
    with c1: ai_reg  = st.selectbox(t["select_region"], list(CITIES.keys()), key="ai_reg")
    with c2: ai_city = st.selectbox(t["select_city"],   [c[0] for c in CITIES[ai_reg]], key="ai_city")
    ai_s  = CITY_STATS.get(ai_city,{"mean_pm25":15.0})
    ai_pm = ai_s["mean_pm25"]
    _,ai_col,ai_ico,ai_raw = aqi(ai_pm,LNG())
    ai_cat = T[LNG()].get(ai_raw,T["en"][ai_raw])

    st.markdown(f"""<div style="background:{_cbg()};border:1px solid {_cborder()};border-radius:10px;
  padding:.75rem;margin-bottom:.85rem;">
  <div style="font-size:.72rem;color:{TEXT2};">Asking about <strong style="color:{TEXT1};">{ai_city}</strong>
  ({ai_reg}) · PM2.5: <strong style="color:{ai_col};">{ai_pm:.1f} μg/m³</strong> · {ai_ico}
  <strong style="color:{ai_col};">{ai_cat}</strong></div>
</div>""", unsafe_allow_html=True)

    qs=["Is it safe to exercise outdoors today?","Main pollution sources here?",
        "Best month to visit?","Should children wear masks outside?"]
    st.markdown(f"<div style='font-size:.6rem;color:{TEXT2};margin-bottom:.3rem;'>Quick questions:</div>",
                unsafe_allow_html=True)
    qcols = st.columns(len(qs))
    for qcol,q in zip(qcols,qs):
        with qcol:
            if st.button(q[:28]+"…" if len(q)>28 else q, key=f"q_{q[:8]}", use_container_width=True):
                st.session_state.ai_pending=q

    for msg in st.session_state.ai_history[-8:]:
        if msg["role"]=="user":
            st.markdown(f'<div class="as-chat-user">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="as-chat-ai"><div style="font-size:.58rem;color:{TEAL};font-weight:700;letter-spacing:.08em;margin-bottom:.2rem;">AIRSENSE AI</div>{msg["content"]}</div>',
                        unsafe_allow_html=True)

    ui = st.text_input("Ask about air quality, health, or pollution…", key="ai_inp",
                        placeholder="e.g. What precautions for asthma patients?")
    cs,cc = st.columns([.15,.85])
    with cs: send = st.button("Send", key="ai_snd", use_container_width=True, type="primary")
    with cc:
        if st.button("Clear", key="ai_clr"): st.session_state.ai_history=[]; st.rerun()

    if "ai_pending" in st.session_state: ui=st.session_state.pop("ai_pending"); send=True
    if send and ui.strip():
        st.session_state.ai_history.append({"role":"user","content":ui})
        with st.spinner("Thinking…"):
            reply = call_claude(ui, ai_city, ai_reg, ai_pm, LNG())
        if reply: st.session_state.ai_history.append({"role":"assistant","content":reply})
        else:
            fb=T[LNG()].get(f"health_{ai_raw}",T["en"].get(f"health_{ai_raw}","Consult local health authorities."))
            st.session_state.ai_history.append({"role":"assistant",
                "content":f"Based on PM2.5 of {ai_pm:.1f} μg/m³ in {ai_city}: {fb}"})
        st.rerun()
    info_box("<strong>About:</strong> AirSense AI is grounded in real PM2.5 data for the selected city. "
             "Not a substitute for medical advice.")
    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 9 — HEALTH CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════

