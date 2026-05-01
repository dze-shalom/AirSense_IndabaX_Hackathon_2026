"""pages/ai_assistant.py — AirSense conversational AI (Groq streaming)."""
import streamlit as st
from datetime import datetime

from config import CITY_STATS, WHO_24H, T
from utils.helpers import LNG
from utils.api import stream_groq, _groq_key
from components.ui import sec, _cbg, _cborder, _ctxt, _ctxt2


def _aqi_label(pm25: float, lang: str) -> str:
    if pm25 < 5:   return "Good" if lang == "en" else "Bon"
    if pm25 < 15:  return "Moderate" if lang == "en" else "Modéré"
    if pm25 < 30:  return "Poor" if lang == "en" else "Mauvais"
    if pm25 < 60:  return "Very Poor" if lang == "en" else "Très Mauvais"
    return "Hazardous" if lang == "en" else "Dangereux"


def _build_system(lang: str) -> str:
    """Build a rich system prompt with live multi-city data."""
    from utils.live_data import get_live_stats
    try:
        live = get_live_stats()
    except Exception:
        live = {}

    month = datetime.now().month
    harm = month in [11, 12, 1, 2]
    season = (
        "Harmattan (dry NE winds carrying Saharan dust — main pollution driver in northern Cameroon)"
        if harm else
        "Wet/transition season (reduced dust, higher humidity)"
    )

    city_lines = []
    for city, stats in sorted(live.items(), key=lambda x: -x[1].get("mean_pm25", 0))[:12]:
        pm25   = stats.get("mean_pm25", 0)
        region = stats.get("region", "")
        lbl    = _aqi_label(pm25, "en")
        city_lines.append(f"  {city} ({region}): {pm25:.1f} µg/m³ — {lbl}")

    city_block = "\n".join(city_lines) if city_lines else "  (live data unavailable)"
    lang_name  = "French" if lang == "fr" else "English"

    return (
        f"You are AirSense, an AI air quality assistant for Cameroon. "
        f"Today is {datetime.now().strftime('%B %d, %Y')}.\n\n"
        f"LIVE PM2.5 DATA:\n{city_block}\n\n"
        f"WHO 24h PM2.5 guideline: {WHO_24H} µg/m³\n"
        f"Current season: {season}\n\n"
        f"Personality: warm, conversational, and concise — like a knowledgeable friend, "
        f"not a government report. Avoid heavy bullet lists; write in flowing sentences. "
        f"Give practical, actionable advice tailored to daily life in Cameroon. "
        f"When the user asks about a city, reference its live PM2.5 from the data above. "
        f"Keep responses under 150 words unless the question genuinely needs more detail. "
        f"Respond in {lang_name} only."
    )


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
