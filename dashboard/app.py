"""
AirSense Cameroon — IndabaX 2026
Author: Dze-Kum Shalom Chow

Entry point. Routing only — all logic lives in pages/, components/, utils/.
Run: streamlit run dashboard/app.py
"""
import streamlit as st

# ── Page config must be the very first Streamlit call ─────────────────────────
st.set_page_config(
    page_title="AirSense Cameroon",
    page_icon="🌬",
    layout="wide",
    initial_sidebar_state="expanded",
)

from config import PAGE_KEYS
from components.sidebar import inject_css, render_nav, render_sidebar
from pages.overview      import page_overview
from pages.explorer      import page_explorer
from pages.alerts        import page_alerts_health
from pages.science       import page_science
from pages.ai_assistant  import page_ai
from pages.about         import page_about

# ── Session state defaults ────────────────────────────────────────────────────
_DEFAULTS = {
    "lang":          "en",
    "page":          "overview",
    "theme":         "dark",
    "ai_history":    [],
    "show_settings": False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Render shell ──────────────────────────────────────────────────────────────
def main():
    inject_css()
    render_nav()
    render_sidebar()

    page = st.session_state.page
    if   page == "overview":  page_overview()
    elif page == "explorer":  page_explorer()
    elif page == "alerts":    page_alerts_health()
    elif page == "science":   page_science()
    elif page == "ai":        page_ai()
    elif page == "about":     page_about()
    else:                     page_overview()


if __name__ == "__main__":
    main()
