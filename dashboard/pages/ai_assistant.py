"""pages/ai_assistant.py — AirSense conversational AI (Groq streaming)."""
import math
import streamlit as st
from datetime import datetime

from config import CITY_STATS, WHO_24H, T
from utils.helpers import LNG, live_source_attribution
from utils.api import stream_groq, _groq_key
from components.ui import sec, _cbg, _cborder, _ctxt, _ctxt2

NORTHERN = {"Far North", "North", "Adamawa"}


def _aqi_label(pm25: float, lang: str) -> str:
    if pm25 < 5:   return "Good"      if lang == "en" else "Bon"
    if pm25 < 15:  return "Moderate"  if lang == "en" else "Modéré"
    if pm25 < 30:  return "Poor"      if lang == "en" else "Mauvais"
    if pm25 < 60:  return "Very Poor" if lang == "en" else "Très Mauvais"
    return         "Hazardous"        if lang == "en" else "Dangereux"


_CHART_GUIDE = """
DASHBOARD PAGES & CHARTS (so you can explain any of them):
• Overview: National map with city PM2.5 bubbles, AQI distribution donut (5 categories), regional mean PM2.5 bar chart, WHO exceedance bar chart (% days above 15 µg/m³), monthly PM2.5 heatmap (regions × 12 months), Harmattan animation (Nov–Feb NE→SW dust transport arrows).
• Explorer › Forecast: 7-day forecast cards per city, PM2.5 trend line with 90% confidence band, BFAI pollution gauge, source attribution donut (Dust / Biomass / Traffic / Industry / Secondary).
• Explorer › Analytics: Monthly seasonal profile, climate vs AQ subplots (PM2.5 / temperature / precipitation / humidity), source attribution polar radar, health impact cards (excess respiratory cases per 10k/yr, hospital admission risk %, lost workdays), Africa PM2.5 benchmark bar, city A vs B seasonal comparison.
• Science: SHAP feature importance grids per region (which weather/climate variables drive PM2.5), climate 2050 projections under SSP scenarios, XGBoost model performance vs baselines, policy simulator (how much would PM2.5 drop if a source is cut by X%).
• Alerts: Active alert cards ranked by PM2.5, calibrated risk ranking (alert probability %), seasonal risk calendar heatmap, school advisory (4-level action system), agricultural advisory, personal exposure accumulator.
""".strip()


def _build_system(lang: str) -> str:
    from utils.live_data import get_live_stats, compute_live_shap

    try:
        live = get_live_stats()
    except Exception:
        live = {}
    try:
        shap_data = compute_live_shap() or {}
    except Exception:
        shap_data = {}

    month = datetime.now().month
    harm  = month in [11, 12, 1, 2]
    season = (
        "Harmattan (dry NE winds carrying Saharan dust — main PM2.5 driver in northern Cameroon, Nov–Feb)"
        if harm else
        "Wet/transition season (lower dust, higher humidity)"
    )

    # ── Per-city data table ───────────────────────────────────────────────────
    city_lines = []
    for city, stats in sorted(live.items(), key=lambda x: -x[1].get("mean_pm25", 0)):
        pm25    = stats.get("mean_pm25", 0)
        who_exc = stats.get("who_exc", 0)
        region  = stats.get("region", "")
        prob    = 1 / (1 + math.exp(-(0.2221 * pm25 - 3.0372)))
        lbl     = _aqi_label(pm25, "en")
        north   = region in NORTHERN
        ws      = 10.0 if (harm and north) else 4.0
        wd      = 35.0 if (harm and north) else 180.0
        prc     = 0.0  if month in [11, 12, 1, 2] else 5.0
        hum     = 30.0 if (harm and north) else 65.0
        try:
            src = live_source_attribution(ws, wd, month, region, prc, hum, pm25)
            dom = max(src, key=src.get)
        except Exception:
            dom = "—"
        city_lines.append(
            f"  {city} ({region}): {pm25:.1f} µg/m³ | {lbl} | "
            f"Alert prob {prob*100:.0f}% | WHO exc {who_exc:.0f}% | Main source: {dom}"
        )

    # ── 7-day forecasts for top 6 most polluted cities ────────────────────────
    forecast_lines = []
    for city, stats in sorted(live.items(), key=lambda x: -x[1].get("mean_pm25", 0))[:6]:
        fc = stats.get("forecasts", [])[:7]
        if fc:
            fc_str = "  →  ".join(f"{p['date'][-5:]}: {p['pm25']:.0f}" for p in fc)
            forecast_lines.append(f"  {city}: {fc_str}")

    # ── SHAP top-3 predictors per region ──────────────────────────────────────
    shap_lines = []
    for region, feats in shap_data.items():
        top3 = ", ".join(f[0] for f in feats[:3])
        shap_lines.append(f"  {region}: {top3}")

    lang_name = "French" if lang == "fr" else "English"

    parts = [
        f"You are AirSense, an AI air quality assistant for Cameroon. "
        f"Today is {datetime.now().strftime('%B %d, %Y')}.\n",

        f"LIVE CITY DATA (PM2.5 | AQI level | Alert probability | WHO exceedance | Dominant source):\n"
        + "\n".join(city_lines),

        f"Current season: {season}",
        f"WHO 24h PM2.5 guideline: {WHO_24H} µg/m³",
    ]

    if forecast_lines:
        parts.append(
            "7-DAY FORECASTS for most polluted cities (MM-DD: µg/m³):\n"
            + "\n".join(forecast_lines)
        )
    if shap_lines:
        parts.append(
            "TOP PM2.5 PREDICTORS BY REGION (XGBoost SHAP analysis):\n"
            + "\n".join(shap_lines)
        )

    parts += [
        _CHART_GUIDE,
        (
            f"Your personality: warm, conversational, and concise — like a knowledgeable friend, "
            f"not a government report. Write in flowing sentences. Avoid heavy bullet lists. "
            f"Give practical, actionable advice for daily life in Cameroon. "
            f"When explaining a chart, say what it shows AND what the current data means. "
            f"Keep responses under 180 words unless the question genuinely needs more. "
            f"Respond in {lang_name} only."
        ),
    ]

    return "\n\n".join(parts)


_SUGGESTIONS_EN = [
    "How is the air quality in Yaoundé today?",
    "Which city has the worst air right now?",
    "What does PM2.5 actually mean?",
    "How can I protect my family from pollution?",
    "Is Harmattan affecting northern Cameroon?",
    "What mask should I wear when pollution is high?",
]
_SUGGESTIONS_FR = [
    "Quelle est la qualité de l'air à Yaoundé aujourd'hui ?",
    "Quelle ville a le pire air en ce moment ?",
    "Que signifie vraiment PM2.5 ?",
    "Comment protéger ma famille de la pollution ?",
    "L'Harmattan affecte-t-il le nord du Cameroun ?",
    "Quel masque porter quand la pollution est élevée ?",
]


def page_ai():
    lang = LNG()
    st.markdown('<div class="as-content">', unsafe_allow_html=True)

    if "ai_history" not in st.session_state:
        st.session_state.ai_history = []

    has_key = bool(_groq_key())

    # ── Welcome screen ────────────────────────────────────────────────────────
    if not st.session_state.ai_history:
        st.markdown(
            f'<div style="text-align:center;padding:2.5rem 1rem 1.2rem;">'
            f'<div style="font-size:3rem;margin-bottom:.5rem;">🌬</div>'
            f'<h2 style="margin:0;font-size:1.7rem;color:{_ctxt()};">AirSense AI</h2>'
            f'<p style="color:{_ctxt2()};margin:.5rem 0 0;font-size:.95rem;">'
            + ("Your personal air quality assistant for Cameroon"
               if lang == "en" else
               "Votre assistant personnel pour la qualité de l'air au Cameroun")
            + '</p></div>',
            unsafe_allow_html=True,
        )

        if not has_key:
            st.info(
                "**AI not configured.** Add `GROQ_API_KEY` to `.streamlit/secrets.toml` "
                "to enable conversational AI. Get a free key at **console.groq.com**."
                if lang == "en" else
                "**IA non configurée.** Ajoutez `GROQ_API_KEY` dans `.streamlit/secrets.toml`. "
                "Clé gratuite sur **console.groq.com**."
            )

        sugg = _SUGGESTIONS_FR if lang == "fr" else _SUGGESTIONS_EN
        cols = st.columns(2)
        for i, s in enumerate(sugg):
            with cols[i % 2]:
                if st.button(s, key=f"sugg_{i}", use_container_width=True):
                    st.session_state.ai_history.append({"role": "user", "content": s})
                    st.rerun()

    # ── Chat history ──────────────────────────────────────────────────────────
    else:
        for msg in st.session_state.ai_history:
            with st.chat_message(msg["role"],
                                 avatar="🌬" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

    # ── Chat input ────────────────────────────────────────────────────────────
    placeholder = (
        "Ask me anything about air quality in Cameroon…"
        if lang == "en" else
        "Posez-moi n'importe quelle question sur la qualité de l'air au Cameroun…"
    )
    if prompt := st.chat_input(placeholder):
        st.session_state.ai_history.append({"role": "user", "content": prompt})
        st.rerun()

    # ── Stream response for the latest unanswered user message ───────────────
    history = st.session_state.ai_history
    if history and history[-1]["role"] == "user":
        system = _build_system(lang)
        with st.chat_message("assistant", avatar="🌬"):
            response = st.write_stream(stream_groq(history, system))
        st.session_state.ai_history.append({"role": "assistant", "content": response})

    # ── Clear button ──────────────────────────────────────────────────────────
    if st.session_state.ai_history:
        st.markdown("<div style='margin-top:.5rem;'></div>", unsafe_allow_html=True)
        if st.button("🗑 " + ("Clear chat" if lang == "en" else "Effacer la conversation"),
                     key="ai_clear"):
            st.session_state.ai_history = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
