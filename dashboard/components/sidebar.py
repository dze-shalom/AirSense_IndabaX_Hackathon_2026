"""components/sidebar.py — CSS injection, top nav bar, left sidebar."""
import streamlit as st
from config import (
    NAVY, NAVY2, TEAL, TEAL2, TEXT1, TEXT2, BORDER, RED,
    WHO_24H, PAGE_KEYS, NAV_LABELS, NAV_SUBTITLES, NAV_ICONS,
    CITY_STATS, T,
)
from utils.helpers import LNG, THRESHOLD_STANDARDS, get_threshold

# lazy import to avoid circular at module load time
def _get_live_stats():
    from utils.live_data import get_live_stats, compute_live_shap
    from utils.api import fetch_forecast
    return get_live_stats, compute_live_shap, fetch_forecast


def _svg_data_uri(svg_str: str, color: str) -> str:
    """Return a CSS url() value with the SVG encoded as a data URI.

    Replaces stroke="currentColor" with the actual hex color so the icon
    is visible when rendered via background-image (currentColor doesn't
    resolve in that context).
    """
    svg = svg_str.replace("currentColor", color)
    svg = svg.replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace('"', "'")
    return f"url(\"data:image/svg+xml,{svg}\")"


def _nav_icon_css(collapsed: bool, is_dark: bool) -> str:
    """Return a <style> block that places SVG icons on nav buttons via ::before."""
    inactive = TEXT2                         # "#8892b0" dark / light equivalent
    active   = TEAL                          # "#64ffda" dark / light equivalent
    if not is_dark:
        inactive = "#7a5c40"
        active   = "#b5613f"

    parts: list[str] = []
    # Base ::before setup shared by all nav buttons
    base = (
        "content:''!important;"
        "display:inline-block!important;"
        "background-size:contain!important;"
        "background-repeat:no-repeat!important;"
        "background-position:center!important;"
        "flex-shrink:0!important;"
        "vertical-align:middle!important;"
    )
    expanded_extra = "width:15px!important;height:15px!important;margin-right:7px!important;"
    collapsed_extra = "width:18px!important;height:18px!important;display:block!important;margin:0 auto!important;"

    for page, svg in NAV_ICONS.items():
        for kind, col in [("secondary", inactive), ("primary", active)]:
            uri = _svg_data_uri(svg, col)
            size_css = collapsed_extra if collapsed else expanded_extra
            # :has() selector: the element-container wrapping the marker div
            # is immediately followed by the element-container wrapping the button
            sel = (
                f"[data-testid='stSidebar'] div:has(>.as-nav-mark[data-page='{page}'])"
                f"+div button[data-testid='baseButton-{kind}'] p::before"
            )
            parts.append(f"{sel}{{{base}{size_css}background-image:{uri};}}")

    return "<style>" + "".join(parts) + "</style>"


# ── SVG icons used in nav bar ─────────────────────────────────────────────────
SUN_ICON  = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
MOON_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
WIND_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>'

# ── Global CSS ────────────────────────────────────────────────────────────────
CSS = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Open+Sans:wght@300;400;500;600&family=Roboto+Mono:wght@400;500;600&display=swap');
#MainMenu,footer,header{{visibility:hidden;}}
.stDeployButton,[data-testid="stToolbar"],[data-testid="stDecoration"]{{display:none;}}
.stApp>header{{display:none;}}
.block-container{{padding-top:0!important;padding-bottom:1rem!important;max-width:100%!important;}}.stApp>header{{display:none!important;height:0!important;}}.main .block-container{{padding-top:0!important;margin-top:0!important;}}section.main>div.block-container{{padding-top:0!important;}}
body,.stApp{{background:{NAVY}!important;font-family:'Open Sans',sans-serif!important;color:{TEXT1}!important;font-size:16px!important;}}
[data-testid="stSidebar"]{{background:linear-gradient(180deg,rgba(17,34,64,0.98),rgba(10,25,47,0.99))!important;border-right:1px solid {BORDER}!important;}}
[data-testid="stSidebar"]>div:first-child{{padding:.95rem .6rem!important;}}
[data-testid="stSidebar"] button[kind="secondary"]{{width:100%!important;border-radius:6px!important;border:1px solid transparent!important;background:transparent!important;color:{TEXT2}!important;font-size:.75rem!important;padding:.32rem .45rem!important;margin-bottom:.08rem!important;transition:all .15s!important;font-weight:500!important;font-family:'Open Sans',sans-serif!important;}}
[data-testid="stSidebar"] button[kind="secondary"]:hover{{background:rgba(100,255,218,0.07)!important;border-color:rgba(100,255,218,0.22)!important;color:{TEXT1}!important;}}
[data-testid="stSidebar"] button[kind="primary"]{{width:100%!important;border-radius:6px!important;background:rgba(100,255,218,0.10)!important;border:1px solid {TEAL}!important;color:{TEAL}!important;font-size:.75rem!important;padding:.32rem .45rem!important;margin-bottom:.08rem!important;font-weight:600!important;box-shadow:0 0 10px rgba(100,255,218,0.14)!important;font-family:'Open Sans',sans-serif!important;}}
h1,h2,h3,h4,h5,h6{{font-family:'Montserrat',sans-serif!important;font-weight:700!important;}}.stMarkdown,.stMarkdown p,.stText{{font-family:'Open Sans',sans-serif!important;font-size:15px!important;line-height:1.6!important;}}.as-stat-val,.as-fc-val,[data-testid='metric-container'] [data-testid='stMetricValue']{{font-family:'Roboto Mono',monospace!important;}}[data-testid='metric-container'] [data-testid='stMetricLabel']{{font-family:'Open Sans',sans-serif!important;}}.as-fixed-nav{{position:fixed;top:0;left:0;right:0;height:42px;z-index:997;background:rgba(10,25,47,0.97);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid {BORDER};display:flex;align-items:center;padding:0 1.4rem 0 22rem;justify-content:space-between;}}
/* On mobile the sidebar is hidden so no 22rem offset needed */
@media(max-width:768px){{.as-fixed-nav{{padding:0 .6rem!important;}}}}
.as-logo{{font-family:'Montserrat',sans-serif;font-size:.9rem;font-weight:700;color:{TEAL};display:flex;align-items:center;gap:.4rem;white-space:nowrap;}}
.as-content{{margin-top:48px;padding:.75rem 1.5rem;}}
/* Ensure nav strip buttons wrap on very small screens */
#as-topnav-row{{flex-wrap:wrap!important;}}
.as-alert-badge{{background:rgba(239,68,68,0.13);border:1px solid rgba(239,68,68,0.36);color:{RED};border-radius:4px;padding:.11rem .38rem;font-size:.6rem;font-family:'Roboto Mono',monospace;font-weight:600;}}
@keyframes as-pulse{{0%,100%{{opacity:1;transform:scale(1);}}50%{{opacity:.55;transform:scale(.78);}}}}
.as-hamburger-btn{{width:34px;height:34px;border-radius:8px;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;border:1px solid rgba(0,0,0,0.12);background:transparent;transition:background .15s;color:inherit;}}.as-hamburger-btn:hover{{background:rgba(0,0,0,0.06);}}.as-live-dot{{width:6px;height:6px;border-radius:50%;background:{TEAL};animation:as-pulse 2.1s ease infinite;display:inline-block;}}
.as-stat-strip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(105px,1fr));gap:.75rem;padding:.8rem 0;border-top:1px solid {BORDER};border-bottom:1px solid {BORDER};margin-bottom:1.2rem;}}
.as-stat-val{{font-size:1.35rem;font-weight:700;font-family:'Roboto Mono',monospace;color:{TEAL};line-height:1;}}
.as-stat-lbl{{font-size:.55rem;color:{TEXT2};margin-top:.1rem;text-transform:uppercase;letter-spacing:.08em;}}
.as-fc-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:.5rem;margin-top:.8rem;}}
.as-fc-card{{background:{NAVY2};border:1px solid {BORDER};border-radius:9px;padding:.7rem;text-align:center;transition:all .18s;position:relative;}}
.as-fc-card:hover{{border-color:rgba(100,255,218,.28);transform:translateY(-2px);}}
.as-fc-card.today{{border-color:{TEAL};box-shadow:0 0 14px rgba(100,255,218,.12);}}
.as-fc-day{{font-size:.56rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:{TEXT2};margin-bottom:.22rem;}}
.as-fc-icon{{font-size:1.2rem;margin:.18rem 0;}}
.as-fc-val{{font-size:1.25rem;font-weight:700;font-family:'Roboto Mono',monospace;}}
.as-fc-unit{{font-size:.5rem;color:{TEXT2};}}
.as-fc-badge{{margin-top:.22rem;padding:.1rem .26rem;border-radius:3px;font-size:.54rem;font-weight:600;}}
.as-fc-meta{{font-size:.54rem;color:{TEXT2};margin-top:.22rem;}}
.as-alert-item{{display:flex;align-items:center;gap:.55rem;padding:.5rem .62rem;border-radius:7px;border:1px solid {BORDER};margin-bottom:.24rem;background:{NAVY2};flex-wrap:wrap;}}
.as-alert-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0;}}
.as-city-row{{display:flex;align-items:center;padding:.3rem .4rem;border-radius:4px;margin-bottom:.11rem;transition:background .13s;flex-wrap:wrap;gap:.22rem;}}
.as-city-row:hover{{background:rgba(100,255,218,.04);}}
.as-school-card{{border-radius:10px;padding:13px 17px;margin-bottom:7px;border:1px solid {BORDER};}}
.as-chat-user{{background:rgba(100,255,218,.08);border:1px solid rgba(100,255,218,.2);border-radius:10px 10px 2px 10px;padding:.46rem .7rem;font-size:.73rem;margin-bottom:.3rem;margin-left:2rem;}}
.as-chat-ai{{background:{NAVY2};border:1px solid {BORDER};border-left:2px solid {TEAL};border-radius:10px 10px 10px 2px;padding:.46rem .7rem;font-size:.73rem;margin-bottom:.5rem;margin-right:2rem;line-height:1.6;}}
[data-testid="stSidebar"] button p{{text-align:left!important;width:100%!important;margin:0!important;}}
[data-testid="stSidebar"] [data-testid="stSidebarNav"]{{display:none!important;}}
[data-testid="stSidebar"] button[kind="secondary"]:hover{{background:rgba(100,255,218,0.06)!important;border-color:rgba(100,255,218,0.18)!important;color:{TEXT1}!important;}}
@media(max-width:640px){{[data-testid="stSidebar"]{{width:100vw!important;min-width:100vw!important;}}.as-fixed-nav{{padding:0 1rem 0 1rem!important;}}}}
[data-testid="stSidebar"] button[kind="primary"]:before{{content:"";display:inline-block;width:3px;height:14px;background:{TEAL};border-radius:2px;margin-right:.55rem;flex-shrink:0;}}
[data-testid="stSidebar"] button[kind="secondary"]:before{{content:"";display:inline-block;width:3px;height:14px;background:transparent;border-radius:2px;margin-right:.55rem;flex-shrink:0;}}
[data-testid="stSidebar"] button[kind="secondary"]:hover:before{{background:rgba(100,255,218,0.35)!important;}}
.stSelectbox>div>div{{background:{NAVY2}!important;border:1px solid {BORDER}!important;border-radius:7px!important;color:{TEXT1}!important;}}
.stSelectbox>div>div:focus-within{{border-color:{TEAL}!important;box-shadow:0 0 0 2px rgba(100,255,218,.1)!important;}}
.stTabs [data-baseweb="tab-list"]{{background:transparent!important;border-bottom:1px solid {BORDER}!important;gap:0!important;}}
.stTabs [data-baseweb="tab"]{{background:transparent!important;color:{TEXT2}!important;border-bottom:2px solid transparent!important;padding:.4rem .88rem!important;font-size:.71rem!important;font-weight:500!important;}}
.stTabs [aria-selected="true"]{{color:{TEAL}!important;border-bottom-color:{TEAL}!important;}}
div[data-testid="metric-container"]{{background:rgba(255,255,255,.04)!important;border:1px solid {BORDER}!important;border-radius:9px!important;padding:9px!important;}}
::-webkit-scrollbar{{width:5px;}}::-webkit-scrollbar-track{{background:{NAVY};}}::-webkit-scrollbar-thumb{{background:{BORDER};border-radius:3px;}}

@media(max-width:768px){{
  .as-content{{margin-top:48px;padding:.5rem .6rem!important;}}
  .as-stat-strip{{grid-template-columns:repeat(3,1fr);gap:.45rem;}}
  .as-fc-grid{{grid-template-columns:repeat(auto-fill,minmax(88px,1fr));gap:.35rem;}}
  .as-fc-card{{padding:.5rem .4rem;}}
  .as-fc-val{{font-size:1.05rem;}}
  .as-alert-item{{padding:.38rem .45rem;gap:.38rem;}}
  div[data-testid="metric-container"]{{padding:7px!important;}}
  [data-testid="stMetricValue"]{{font-size:1.1rem!important;}}
  .stTabs [data-baseweb="tab"]{{padding:.35rem .55rem!important;font-size:.65rem!important;}}
}}
@media(max-width:480px){{
  .as-stat-strip{{grid-template-columns:repeat(2,1fr);}}
  .as-fc-grid{{grid-template-columns:repeat(auto-fill,minmax(76px,1fr));}}
  .as-stat-val{{font-size:1.1rem;}}
  .as-content{{padding:.4rem .4rem!important;}}
  h1{{font-size:1.1rem!important;}}
  h2{{font-size:1rem!important;}}
  h3{{font-size:.92rem!important;}}
  .stMarkdown,.stMarkdown p{{font-size:13px!important;}}
  [data-testid="stMetricValue"]{{font-size:.95rem!important;}}
  .as-school-card{{padding:10px 12px;}}
  .as-chat-user,.as-chat-ai{{margin-left:.5rem;margin-right:.5rem;}}
  .stButton>button{{font-size:.72rem!important;padding:.3rem .5rem!important;}}
  .as-alert-badge{{font-size:.55rem;padding:.08rem .28rem;}}
}}
@media(max-width:360px){{
  .as-fixed-nav .as-logo span:not(:first-child){{display:none;}}
  .as-fc-grid{{grid-template-columns:repeat(3,1fr);}}
  .as-stat-strip{{grid-template-columns:repeat(2,1fr);}}
}}
@media(display-mode:standalone){{
  .as-fixed-nav{{padding-top:env(safe-area-inset-top,0px);}}
  .as-content{{padding-bottom:env(safe-area-inset-bottom,0px);}}
}}
.stTabs [data-baseweb="tab-list"]{{overflow-x:auto!important;-webkit-overflow-scrolling:touch!important;flex-wrap:nowrap!important;}}
.stTabs [data-baseweb="tab-list"]::-webkit-scrollbar{{height:2px;}}

</style>"""

# ── Particle background ───────────────────────────────────────────────────────
def _particles_html(is_light: bool) -> str:
    col  = "#b5613f" if is_light else "#64ffda"
    op   = 0.07     if is_light else 0.06
    lop  = 0.05     if is_light else 0.04
    return (f"""<div id="asp"></div>"""
            f"""<script src="https://cdnjs.cloudflare.com/ajax/libs/particles.js/2.0.0/particles.min.js"></script>"""
            f"""<script>(function t(){{if(typeof particlesJS==='undefined'){{setTimeout(t,400);return;}}"""
            f"""var e=document.getElementById('asp');if(!e)return;"""
            f"""e.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';"""
            f"""particlesJS('asp',{{particles:{{number:{{value:50,density:{{enable:true,value_area:900}}}},"""
            f"""color:{{value:'{col}'}},shape:{{type:'circle'}},opacity:{{value:{op},random:true}},size:{{value:2,random:true}},"""
            f"""line_linked:{{enable:true,distance:145,color:'{col}',opacity:{lop},width:1}},"""
            f"""move:{{enable:true,speed:.5,random:true,out_mode:'out'}}}},"""
            f"""interactivity:{{detect_on:'canvas',events:{{onhover:{{enable:true,mode:'grab'}},onclick:{{enable:false}},resize:true}},"""
            f"""modes:{{grab:{{distance:90,line_linked:{{opacity:.18}}}}}}}},retina_detect:true}});}})()</script>""")

def inject_css():
    """Inject global CSS and particle background."""
    # Viewport + PWA meta — critical for mobile/installable app
    st.markdown(
        '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">'
        '<meta name="mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-capable" content="yes">'
        '<meta name="apple-mobile-web-app-status-bar-style" content="default">'
        '<meta name="apple-mobile-web-app-title" content="AirSense CM">'
        '<link rel="manifest" href="manifest.json">'
        '<meta name="theme-color" content="#1a3c5e">',
        unsafe_allow_html=True)
    st.markdown("""<script>
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/app/static/sw.js')
    .catch(function(err) {
      // registration failed — silently ignore (Streamlit hosting may block it)
    });
}
</script>""", unsafe_allow_html=True)
    st.markdown(CSS, unsafe_allow_html=True)
    is_light = st.session_state.get("theme", "light") == "light"
    st.markdown(_particles_html(is_light), unsafe_allow_html=True)
    # ── Global button base styles — theme-neutral structure only ────────────
    st.markdown(f"""<style>
button[kind="secondary"], .stButton>button {{
    border-radius: 6px !important;
    transition: all .18s !important;
    font-family: 'Open Sans', sans-serif !important;
    font-size: .78rem !important;
}}
button[kind="primary"] {{
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-family: 'Open Sans', sans-serif !important;
}}
</style>""", unsafe_allow_html=True)

    # ── LIGHT THEME (default) — competition palette ───────────────────────────
    if st.session_state.get("theme", "light") == "light":
        st.markdown(f"""<style>
/* Background */
body,.stApp{{
    background:#fdf8f2!important;
    color:#1a0e04!important;
    font-family:'Open Sans',sans-serif!important;
}}
/* Streamlit's own text containers — leave inline style="" colours intact */
[data-testid="stText"],[data-testid="stText"] *,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] em,
.stAlert p,.stAlert li,
.stSuccess p,.stInfo p,.stWarning p,.stException p,
p,li,td,th,caption,figcaption{{
    color:#1a0e04!important;
}}
/* Section headers (sec() function) */
.as-city-row,.as-city-row *,
.as-stat-strip .as-stat-lbl{{ color:#5c3a1e!important; }}
/* Keep AQI badge text white (coloured backgrounds) */
.as-fc-badge,.as-alert-dot + span{{ color:#fff!important; }}
/* Keep sidebar text dark-themed */
[data-testid="stSidebar"] *{{ color:unset; }}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div{{ color:#8892b0!important; }}
/* Headings */
h1,h2,h3,h4,h5,h6{{
    color:#1a0e04!important;
    font-family:'Montserrat',sans-serif!important;
    font-weight:700!important;
}}
/* Sidebar stays DARK — untouched */
[data-testid="stSidebar"]{{
    background:linear-gradient(180deg,{NAVY2} 0%,{NAVY} 100%)!important;
    border-right:1px solid {BORDER}!important;
}}
[data-testid="stSidebar"] *{{ color:{TEXT2}!important; }}
[data-testid="stSidebar"] .as-stat-val{{ color:{TEAL}!important; }}
[data-testid="stSidebar"] button[kind="primary"]{{
    color:{TEAL}!important;
    background:rgba(100,255,218,0.10)!important;
    border-color:{TEAL}!important;
}}
[data-testid="stSidebar"] button[kind="secondary"]{{ color:{TEXT2}!important; }}
/* Cards and surfaces */
.as-fc-card,.as-alert-item,.as-chat-ai,.as-school-card,
div[data-testid="metric-container"]{{
    background:rgba(255,252,248,0.92)!important;
    border-color:rgba(160,100,60,0.18)!important;
}}
.as-fc-card *,.as-alert-item *,.as-chat-ai *{{ color:#1a0e04!important; }}
/* AQI badge colours — keep competition colours, just darken text */
.as-fc-badge{{ color:#fff!important; }}
/* Top bar */
.as-fixed-nav{{
    background:rgba(253,248,242,0.97)!important;
    border-bottom:1px solid rgba(160,100,60,0.2)!important;
}}
.as-logo{{ color:#b5613f!important; }}
.as-alert-badge{{
    background:rgba(181,97,63,0.12)!important;
    border-color:rgba(181,97,63,0.35)!important;
    color:#b5613f!important;
}}
.as-live-dot{{ background:#b5613f!important; }}
/* Data values */
.as-stat-val,.as-fc-val,
[data-testid="stMetricValue"],[data-testid="stMetricValue"] *{{
    color:#b5613f!important;
    font-family:'Roboto Mono',monospace!important;
}}
.as-stat-lbl{{ color:#5c3a1e!important; }}
/* Inputs */
.stSelectbox>div>div{{
    background:#fff8f2!important;
    color:#1a0e04!important;
    border-color:rgba(160,100,60,0.3)!important;
}}
.stSelectbox [data-testid="stMarkdownContainer"] p{{ color:#1a0e04!important; }}
.stTextInput input,.stTextArea textarea{{
    background:#fff8f2!important; color:#1a0e04!important;
    border-color:rgba(160,100,60,0.3)!important;
}}
/* Tabs */
.stTabs [data-baseweb="tab"]{{ color:#5c3a1e!important; }}
.stTabs [aria-selected="true"]{{ color:#b5613f!important; border-bottom-color:#b5613f!important; }}
.stTabs [data-baseweb="tab-list"]{{ border-bottom-color:rgba(160,100,60,0.2)!important; }}
/* Buttons */
button[kind="secondary"],.stButton>button{{
    background:rgba(255,252,248,0.92)!important;
    border-color:rgba(160,100,60,0.28)!important;
    color:#5c3a1e!important;
}}
button[kind="secondary"]:hover,.stButton>button:hover{{
    background:rgba(181,97,63,0.08)!important;
    border-color:#b5613f!important; color:#b5613f!important;
}}
button[kind="primary"]{{
    background:rgba(181,97,63,0.12)!important;
    border-color:rgba(181,97,63,0.5)!important; color:#b5613f!important;
}}
/* Checkboxes */
.stCheckbox label,.stCheckbox label *{{ color:#1a0e04!important; }}
.stCheckbox{{ accent-color:#b5613f; }}
/* Scrollbar */
::-webkit-scrollbar-track{{ background:#fdf5ee!important; }}
::-webkit-scrollbar-thumb{{ background:rgba(181,97,63,0.3)!important; }}
/* Chat input */
[data-testid="stChatInputContainer"]{{
    background:#fff8f2!important;
    border:1px solid rgba(160,100,60,0.3)!important;
    border-radius:10px!important;
}}
[data-testid="stChatInputContainer"] textarea{{
    background:#fff8f2!important;
    color:#1a0e04!important;
    font-family:'Open Sans',sans-serif!important;
}}
[data-testid="stChatInputContainer"] textarea::placeholder{{
    color:rgba(92,58,30,0.5)!important;
}}
.stChatFloatingInputContainer{{
    background:rgba(253,248,242,0.97)!important;
    border-top:1px solid rgba(160,100,60,0.15)!important;
    padding-bottom:.5rem!important;
}}
</style>""", unsafe_allow_html=True)

    # ── DARK THEME — original navy/teal palette ───────────────────────────────
    else:
        st.markdown(f"""<style>
/* Background */
body,.stApp{{ background:{NAVY}!important; color:{TEXT1}!important; font-family:'Open Sans',sans-serif!important; }}
/* All text white on dark */
.stApp p,.stApp span,.stApp div,.stApp label,.stApp li,
.stMarkdown,.stMarkdown *,[data-testid="stMarkdownContainer"] *{{ color:{TEXT1}; }}
h1,h2,h3,h4,h5,h6{{ color:{TEXT1}!important; font-family:'Montserrat',sans-serif!important; }}
/* Data values */
.as-stat-val,.as-fc-val,[data-testid="stMetricValue"] *{{
    color:{TEAL}!important; font-family:'Roboto Mono',monospace!important;
}}
/* Cards */
.as-fc-card,.as-alert-item,.as-chat-ai,.as-school-card{{
    background:{NAVY2}!important; border-color:{BORDER}!important;
}}
.as-fc-card *,.as-alert-item *{{ color:{TEXT1}!important; }}
/* Inputs */
.stSelectbox>div>div{{ background:{NAVY2}!important; color:{TEXT1}!important; border-color:{BORDER}!important; }}
.stSelectbox [data-testid="stMarkdownContainer"] p{{ color:{TEXT1}!important; }}
.stTextInput input,.stTextArea textarea{{ background:{NAVY2}!important; color:{TEXT1}!important; border-color:{BORDER}!important; }}
/* Tabs */
.stTabs [data-baseweb="tab"]{{ color:{TEXT2}!important; }}
.stTabs [aria-selected="true"]{{ color:{TEAL}!important; border-bottom-color:{TEAL}!important; }}
/* Buttons */
button[kind="secondary"],.stButton>button{{
    background:{NAVY2}!important; border-color:{BORDER}!important; color:{TEXT2}!important;
}}
button[kind="secondary"]:hover,.stButton>button:hover{{
    background:rgba(100,255,218,0.08)!important; border-color:{TEAL}!important; color:{TEXT1}!important;
}}
button[kind="primary"]{{
    background:rgba(100,255,218,0.10)!important; border-color:{TEAL}!important; color:{TEAL}!important;
}}
/* Metric containers */
div[data-testid="metric-container"]{{ background:{NAVY2}!important; border-color:{BORDER}!important; }}
/* Checkboxes */
.stCheckbox label,.stCheckbox label *{{ color:{TEXT1}!important; }}
.stCheckbox{{ accent-color:{TEAL}; }}
/* Scrollbar */
::-webkit-scrollbar-track{{ background:{NAVY}; }}
::-webkit-scrollbar-thumb{{ background:{BORDER};border-radius:3px; }}
/* Chat input */
[data-testid="stChatInputContainer"]{{
    background:{NAVY2}!important;
    border:1px solid {BORDER}!important;
    border-radius:10px!important;
}}
[data-testid="stChatInputContainer"] textarea{{
    background:{NAVY2}!important;
    color:{TEXT1}!important;
    font-family:'Open Sans',sans-serif!important;
}}
[data-testid="stChatInputContainer"] textarea::placeholder{{
    color:{TEXT2}!important;
    opacity:0.6!important;
}}
.stChatFloatingInputContainer{{
    background:{NAVY}!important;
    border-top:1px solid {BORDER}!important;
    padding-bottom:.5rem!important;
}}
</style>""", unsafe_allow_html=True)

    # ── Sidebar width + transition (always inject, value depends on state) ──────
    _collapsed = st.session_state.get("sidebar_collapsed", False)
    _is_dark   = st.session_state.get("theme", "light") == "dark"
    _sb_w      = "64px"  if _collapsed else "220px"
    _nav_pl    = "76px"  if _collapsed else "232px"
    st.markdown(f"""<style>
[data-testid="stSidebar"]{{
    width:{_sb_w}!important;min-width:{_sb_w}!important;max-width:{_sb_w}!important;
    transition:width .22s cubic-bezier(.4,0,.2,1)!important;
    overflow-x:hidden!important;overflow-y:auto!important;
}}
[data-testid="stSidebar"]>div:first-child{{
    padding:{'0.4rem 0.14rem' if _collapsed else '.95rem .6rem'}!important;
    overflow-x:hidden!important;overflow-y:visible!important;
}}
.as-fixed-nav{{padding-left:{_nav_pl}!important;}}
.as-nav-mark{{display:none!important;height:0!important;margin:0!important;padding:0!important;}}
{('''[data-testid="stSidebar"] button{
    text-align:center!important;justify-content:center!important;
    padding:.45rem .14rem!important;margin:0 auto .1rem!important;}
.as-sb-section-lbl,.as-sb-footer,.as-sb-brand-text,.as-sb-settings-panel{display:none!important;}
.as-sb-brand{justify-content:center!important;}
[data-testid="stSidebar"] .stSelectbox,[data-testid="stSidebar"] .stNumberInput{display:none!important;}
[data-testid="stSidebar"] [data-testid="element-container"]:first-child button{
    background:rgba(100,255,218,0.12)!important;border:1px solid rgba(100,255,218,0.5)!important;
    color:#64ffda!important;font-size:1.1rem!important;font-weight:700!important;
    box-shadow:0 0 10px rgba(100,255,218,0.25)!important;}''') if _collapsed else ''}
</style>""", unsafe_allow_html=True)


def render_nav():
    """Fixed top bar."""
    page     = st.session_state.page
    lang     = LNG()
    labels   = NAV_LABELS[lang]
    page_lbl = labels.get(page, page.title())
    is_light = st.session_state.get("theme", "light") == "light"
    try:
        from utils.live_data import get_live_stats
        live     = get_live_stats()
        source   = live if live else CITY_STATS
        n_alerts = sum(1 for s in source.values() if s.get("mean_pm25", 0) > get_threshold())
    except Exception:
        n_alerts = sum(1 for s in CITY_STATS.values() if s["mean_pm25"] > get_threshold())

    # Explicit colours — never rely on CSS inheritance so theme can't hide text
    logo_col  = "#b5613f" if is_light else TEAL
    text_col  = "#3d1f06" if is_light else TEXT1
    muted_col = "#7a5c40" if is_light else TEXT2
    live_word = "LIVE" if lang == "en" else "EN DIRECT"
    alert_lbl = "alerts" if lang == "en" else "alertes"

    nav_html = (
        '<div class="as-fixed-nav">'
        '<div style="display:flex;align-items:center;gap:.5rem;">'
        f'<div class="as-logo" style="color:{logo_col};">'
        '<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"'
        f' fill="none" stroke="{logo_col}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        '<path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/>'
        '</svg>'
        f'<span style="color:{logo_col};font-family:Montserrat,sans-serif;font-size:.9rem;font-weight:700;">AirSense Cameroon</span>'
        '</div>'
        f'<div style="width:1px;height:16px;background:rgba(0,0,0,0.15);margin:0 .2rem;"></div>'
        f'<span style="font-size:.72rem;color:{muted_col};">{page_lbl}</span>'
        '</div>'
        '<div style="display:flex;align-items:center;gap:.5rem;">'
        f'<span class="as-alert-badge" style="color:{RED};">{n_alerts} {alert_lbl}</span>'
        f'<span style="font-size:.55rem;color:{muted_col};display:flex;align-items:center;gap:3px;">'
        '<span class="as-live-dot"></span>'
        f'<span style="color:{muted_col};">{live_word}</span>'
        '</span>'
        '</div>'
        '</div>'
    )
    st.markdown(nav_html, unsafe_allow_html=True)

    # ── Hide Streamlit's own collapse controls — we use our own toggle ─────────
    st.markdown("""<style>
[data-testid="stSidebarCollapsedControl"],[data-testid="collapsedControl"]{display:none!important;}
</style>""", unsafe_allow_html=True)



def render_sidebar():
    """Left sidebar — collapsible icon-rail or full nav."""
    lang      = LNG()
    is_dark   = st.session_state.get("theme", "light") == "dark"
    labels    = NAV_LABELS[lang]
    subs      = NAV_SUBTITLES[lang]
    collapsed = st.session_state.get("sidebar_collapsed", False)

    with st.sidebar:
        # ── Collapse / expand toggle ──────────────────────────────────────────
        tog_icon = "›" if collapsed else "‹"
        tog_help = ("Expand sidebar" if collapsed else "Collapse sidebar") if lang == "en" else ("Développer" if collapsed else "Réduire")

        if collapsed:
            # Full-width prominent button — the only interactive element visible
            if st.button(tog_icon, key="sb_collapse", help=tog_help, use_container_width=True):
                st.session_state.sidebar_collapsed = False
                st.rerun()
        else:
            # Small chevron in the top-right corner next to the brand
            _, tc2 = st.columns([5, 1])
            with tc2:
                if st.button(tog_icon, key="sb_collapse", help=tog_help, use_container_width=True):
                    st.session_state.sidebar_collapsed = True
                    st.rerun()

        if not collapsed:
            # ── Brand header with settings gear ──────────────────────────────
            h1, h2 = st.columns([5, 1])
            with h1:
                st.markdown(
                    f'<div class="as-sb-brand" style="display:flex;align-items:center;gap:.45rem;padding:.1rem 0 .6rem;">'
                    f'<svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"'
                    f' fill="none" stroke="{TEAL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                    f'<path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/>'
                    f'</svg>'
                    f'<span class="as-sb-brand-text" style="font-family:\'Roboto Mono\',monospace;font-size:.85rem;font-weight:700;color:{TEAL};">AirSense CM</span>'
                    f'</div>',
                    unsafe_allow_html=True)
            with h2:
                if st.button("⚙", key="sb_gear", help="Settings",
                             use_container_width=True):
                    st.session_state.show_settings = not st.session_state.get("show_settings", False)

        if not collapsed:
            # ── Settings panel (collapsible) ──────────────────────────────────
            if st.session_state.get("show_settings", False):
                st.markdown(
                    f'<div class="as-sb-settings-panel" style="background:rgba(100,255,218,0.05);'
                    f'border:1px solid rgba(100,255,218,0.15);border-radius:8px;'
                    f'padding:.6rem .7rem;margin-bottom:.6rem;">'
                    f'<div style="font-size:.58rem;color:{TEAL};font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem;">⚙ Settings</div>',
                    unsafe_allow_html=True)
                sc1, sc2 = st.columns(2)
                with sc1:
                    theme_lbl = ("Light mode" if is_dark else "Dark mode")
                    if st.button(theme_lbl, key="sb_theme", use_container_width=True):
                        st.session_state.theme = "light" if is_dark else "dark"
                        st.rerun()
                with sc2:
                    lang_lbl = "FR" if lang == "en" else "EN"
                    if st.button(lang_lbl, key="sb_lang", use_container_width=True):
                        st.session_state.lang = "fr" if lang == "en" else "en"
                        st.rerun()

                std_names = list(THRESHOLD_STANDARDS.keys())
                cur_std   = st.session_state.get("threshold_std", "WHO 2021")
                cur_idx   = std_names.index(cur_std) if cur_std in std_names else 0
                new_std   = st.selectbox("PM2.5 Standard", std_names,
                                         index=cur_idx, key="sb_std")
                if new_std != cur_std:
                    st.session_state.threshold_std = new_std
                    if THRESHOLD_STANDARDS[new_std] is not None:
                        st.session_state.threshold = THRESHOLD_STANDARDS[new_std]
                    st.rerun()

                if THRESHOLD_STANDARDS[new_std] is None:
                    custom_val = st.number_input(
                        "Custom limit (µg/m³)", min_value=1.0, max_value=500.0,
                        value=float(st.session_state.get("threshold", 15.0)),
                        step=1.0, key="sb_custom_thr")
                    if custom_val != st.session_state.get("threshold"):
                        st.session_state.threshold = custom_val
                        st.rerun()
                else:
                    thr = THRESHOLD_STANDARDS[new_std]
                    st.markdown(
                        f"<div style='font-size:.55rem;color:{TEAL};margin-top:-.3rem;"
                        f"margin-bottom:.2rem;'>Limit: {thr:.0f} µg/m³</div>",
                        unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown(f"<div style='height:1px;background:{BORDER};margin-bottom:.5rem;'></div>",
                        unsafe_allow_html=True)

        # ── Ordered navigation ────────────────────────────────────────────────
        sections = [
            ("EXPLORE",  ["overview", "explorer"]),
            ("TOOLS",    ["alerts", "ai"]),
            ("RESEARCH", ["science", "about"]),
        ]
        # Icon labels — embedded directly so they always render
        NAV_ICON_LABELS = {
            "overview": "⊕",
            "explorer": "≋",
            "alerts":   "⚡",
            "science":  "◆",
            "ai":       "◈",
            "about":    "○",
        }

        for section_label, keys in sections:
            if not collapsed:
                st.markdown(
                    f'<p class="as-sb-section-lbl" style="font-size:.47rem;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:.15em;color:{BORDER};'
                    f'padding:.5rem 0 .18rem;margin:0;line-height:1;">{section_label}</p>',
                    unsafe_allow_html=True)
            for key in keys:
                active = st.session_state.page == key
                icon   = NAV_ICON_LABELS.get(key, "·")
                # Collapsed: show icon only. Expanded: icon + label
                btn_label = icon if collapsed else f"{icon}  {labels[key]}"
                if st.button(
                    btn_label,
                    key=f"sb_{key}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                    help=subs[key],
                ):
                    st.session_state.page = key
                    st.rerun()

        # ── Live data footer ──────────────────────────────────────────────────
        try:
            get_live_stats, compute_live_shap, fetch_forecast = _get_live_stats()
            live = get_live_stats()
            n_live    = len(live)
            src       = live if live else CITY_STATS
            n_alerts  = sum(1 for s in src.values() if s.get("mean_pm25", 0) > get_threshold())
            last_upd  = st.session_state.get("last_refresh", "—")
            data_note = (f"<strong style='color:{TEAL};'>{n_live}</strong>/40 {T.get(lang,T['en']).get('cities_live','cities live')}"
                         if live else f"<span style='color:{TEXT2};'>static baseline</span>")
        except Exception:
            n_alerts  = sum(1 for s in CITY_STATS.values() if s["mean_pm25"] > get_threshold())
            data_note = f"<span style='color:{TEXT2};'>static baseline</span>"
            last_upd  = "—"

        if not collapsed:
            st.markdown(
                f'<div class="as-sb-footer" style="margin-top:.8rem;padding:.5rem .1rem 0;border-top:1px solid {BORDER};">'
                f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.25rem;">'
                f'<span style="font-size:.56rem;color:{TEXT2};text-transform:uppercase;letter-spacing:.07em;">'
                f'{T.get(lang, T["en"]).get("alerts_label","Active alerts")}</span>'
                f'<span style="font-size:.9rem;font-weight:700;color:{RED};font-family:\'Roboto Mono\',monospace;">{n_alerts}</span>'
                f'</div>'
                f'<div style="font-size:.49rem;color:{TEXT2};line-height:1.8;margin-bottom:.45rem;">'
                f'{data_note}<br>'
                f'PM2.5 Prediction · Health Alerts · SHAP Analysis<br>'
                f'Climate Projections · AI Health Assistant<br>'
                f'<strong style="color:{TEAL};">AirSense Team · IndabaX 2026</strong>'
                f'</div></div>',
                unsafe_allow_html=True)

        # Refresh button — clears all caches and reruns
        if st.button(T.get(lang, T["en"]).get("refresh_live", "Refresh"), key="sb_refresh", use_container_width=True):
            try:
                get_live_stats, compute_live_shap, fetch_forecast = _get_live_stats()
                get_live_stats.clear()
                compute_live_shap.clear()
                fetch_forecast.clear()
                import datetime as _dt
                st.session_state["last_refresh"] = _dt.datetime.now().strftime("%H:%M")
            except Exception:
                pass
            st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# PAGE — CITY EXPLORER  (forecast + analytics + compare in tabs)
# ══════════════════════════════════════════════════════════════════════════════

