"""components/sidebar.py — CSS injection, top nav bar, left sidebar."""
import streamlit as st
from config import (
    NAVY, NAVY2, TEAL, TEAL2, TEXT1, TEXT2, BORDER, RED,
    WHO_24H, PAGE_KEYS, NAV_LABELS, NAV_SUBTITLES, NAV_ICONS,
    CITY_STATS, T,
)
from utils.helpers import LNG

# lazy import to avoid circular at module load time
def _get_live_stats():
    from utils.live_data import get_live_stats, compute_live_shap
    from utils.api import fetch_forecast
    return get_live_stats, compute_live_shap, fetch_forecast


# ── SVG icons used in nav bar ─────────────────────────────────────────────────
SUN_ICON  = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>'
MOON_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
WIND_ICON = '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>'

# ── Global CSS ────────────────────────────────────────────────────────────────
CSS = f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');
#MainMenu,footer,header{{visibility:hidden;}}
.stDeployButton,[data-testid="stToolbar"],[data-testid="stDecoration"]{{display:none;}}
.stApp>header{{display:none;}}
.block-container{{padding-top:0!important;}}
body,.stApp{{background:{NAVY}!important;font-family:'Space Grotesk',sans-serif!important;color:{TEXT1}!important;}}
[data-testid="stSidebar"]{{background:linear-gradient(180deg,rgba(17,34,64,0.98),rgba(10,25,47,0.99))!important;border-right:1px solid {BORDER}!important;}}
[data-testid="stSidebar"]>div:first-child{{padding:.95rem .6rem!important;}}
[data-testid="stSidebar"] button[kind="secondary"]{{width:100%!important;border-radius:6px!important;border:1px solid transparent!important;background:transparent!important;color:{TEXT2}!important;font-size:.75rem!important;padding:.32rem .45rem!important;margin-bottom:.08rem!important;transition:all .15s!important;font-weight:500!important;font-family:'Space Grotesk',sans-serif!important;}}
[data-testid="stSidebar"] button[kind="secondary"]:hover{{background:rgba(100,255,218,0.07)!important;border-color:rgba(100,255,218,0.22)!important;color:{TEXT1}!important;}}
[data-testid="stSidebar"] button[kind="primary"]{{width:100%!important;border-radius:6px!important;background:rgba(100,255,218,0.10)!important;border:1px solid {TEAL}!important;color:{TEAL}!important;font-size:.75rem!important;padding:.32rem .45rem!important;margin-bottom:.08rem!important;font-weight:600!important;box-shadow:0 0 10px rgba(100,255,218,0.14)!important;font-family:'Space Grotesk',sans-serif!important;}}
.as-fixed-nav{{position:fixed;top:0;left:0;right:0;height:48px;z-index:997;background:rgba(10,25,47,0.97);backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);border-bottom:1px solid {BORDER};display:flex;align-items:center;padding:0 1.4rem 0 22rem;justify-content:space-between;}}
.as-logo{{font-family:'JetBrains Mono',monospace;font-size:.9rem;font-weight:700;color:{TEAL};display:flex;align-items:center;gap:.4rem;white-space:nowrap;}}
.as-content{{margin-top:16px;padding:1rem 1.4rem;}}
.as-alert-badge{{background:rgba(239,68,68,0.13);border:1px solid rgba(239,68,68,0.36);color:{RED};border-radius:4px;padding:.11rem .38rem;font-size:.6rem;font-family:'JetBrains Mono',monospace;font-weight:600;}}
@keyframes as-pulse{{0%,100%{{opacity:1;transform:scale(1);}}50%{{opacity:.55;transform:scale(.78);}}}}
.as-live-dot{{width:6px;height:6px;border-radius:50%;background:{TEAL};animation:as-pulse 2.1s ease infinite;display:inline-block;}}
.as-stat-strip{{display:grid;grid-template-columns:repeat(auto-fit,minmax(105px,1fr));gap:.75rem;padding:.8rem 0;border-top:1px solid {BORDER};border-bottom:1px solid {BORDER};margin-bottom:1.2rem;}}
.as-stat-val{{font-size:1.35rem;font-weight:700;font-family:'JetBrains Mono',monospace;color:{TEAL};line-height:1;}}
.as-stat-lbl{{font-size:.55rem;color:{TEXT2};margin-top:.1rem;text-transform:uppercase;letter-spacing:.08em;}}
.as-fc-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(110px,1fr));gap:.5rem;margin-top:.8rem;}}
.as-fc-card{{background:{NAVY2};border:1px solid {BORDER};border-radius:9px;padding:.7rem;text-align:center;transition:all .18s;position:relative;}}
.as-fc-card:hover{{border-color:rgba(100,255,218,.28);transform:translateY(-2px);}}
.as-fc-card.today{{border-color:{TEAL};box-shadow:0 0 14px rgba(100,255,218,.12);}}
.as-fc-day{{font-size:.56rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:{TEXT2};margin-bottom:.22rem;}}
.as-fc-icon{{font-size:1.2rem;margin:.18rem 0;}}
.as-fc-val{{font-size:1.25rem;font-weight:700;font-family:'JetBrains Mono',monospace;}}
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
/* Hide sidebar collapse/expand arrows — nav strip handles page switching */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapsedControl"],
button[data-testid="baseButton-headerNoPadding"]{{display:none!important;}}
section[data-testid="stSidebar"] > div > button:first-child{{display:none!important;}}
@media(max-width:768px){{.as-content{{margin-top:12px;padding:.8rem .6rem!important;}}.as-stat-strip{{grid-template-columns:repeat(3,1fr);}}.as-fc-grid{{grid-template-columns:repeat(auto-fill,minmax(88px,1fr));}}}}

</style>"""

# ── Particle background ───────────────────────────────────────────────────────
PARTICLES = """<div id="asp"></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/particles.js/2.0.0/particles.min.js"></script>
<script>(function t(){if(typeof particlesJS==='undefined'){setTimeout(t,400);return;}
var e=document.getElementById('asp');if(!e)return;
e.style.cssText='position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:0;pointer-events:none;';
particlesJS('asp',{particles:{number:{value:50,density:{enable:true,value_area:900}},
color:{value:'#64ffda'},shape:{type:'circle'},opacity:{value:.06,random:true},size:{value:2,random:true},
line_linked:{enable:true,distance:145,color:'#64ffda',opacity:.04,width:1},
move:{enable:true,speed:.5,random:true,out_mode:'out'}},
interactivity:{detect_on:'canvas',events:{onhover:{enable:true,mode:'grab'},onclick:{enable:false},resize:true},
modes:{grab:{distance:90,line_linked:{opacity:.18}}}},retina_detect:true});})();</script>"""

def inject_css():
    """Inject global CSS and particle background."""
    st.markdown(CSS, unsafe_allow_html=True)
    # ── Global button styles (all buttons, not just sidebar) ─────────────────
    st.markdown(f"""<style>
button[kind="secondary"], .stButton>button {{
    background: {NAVY2} !important;
    border: 1px solid {BORDER} !important;
    color: {TEXT2} !important;
    border-radius: 6px !important;
    transition: all .18s !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
button[kind="secondary"]:hover, .stButton>button:hover {{
    background: rgba(100,255,218,0.08) !important;
    border-color: {TEAL} !important;
    color: {TEXT1} !important;
}}
button[kind="primary"] {{
    background: rgba(100,255,218,0.10) !important;
    border: 1px solid {TEAL} !important;
    color: {TEAL} !important;
    border-radius: 6px !important;
    font-weight: 600 !important;
    font-family: 'Space Grotesk', sans-serif !important;
}}
button[kind="primary"]:hover {{
    background: rgba(100,255,218,0.18) !important;
    box-shadow: 0 0 12px rgba(100,255,218,0.2) !important;
}}
/* Checkbox ticks */
.stCheckbox > label > div[data-testid="stMarkdownContainer"] > p {{
    color: {TEXT1} !important; font-size: .73rem !important;
}}
.stCheckbox {{accent-color: {TEAL};}}
</style>""", unsafe_allow_html=True)

    if st.session_state.get("theme", "dark") == "light":
        # Claude Light: warm parchment content area, sidebar stays dark
        st.markdown(f"""<style>
@keyframes bgParchment{{0%,100%{{background-position:0% 50%;}}50%{{background-position:100% 50%;}}}}
/* Main app background — warm parchment */
body,.stApp{{
    background:linear-gradient(-45deg,#fdf8f2,#f5ede0,#fdf3e8,#f8ede0,#fdf7f1)!important;
    background-size:300% 300%!important;
    animation:bgParchment 16s ease infinite!important;
    color:#1c0f05!important;
    font-family:'Söhne',ui-sans-serif,'Helvetica Neue',sans-serif!important;
}}
/* Sidebar stays dark — Claude's sidebar is always dark */
[data-testid="stSidebar"]{{
    background:linear-gradient(180deg,rgba(17,34,64,0.98),rgba(10,25,47,0.99))!important;
    border-right:1px solid {BORDER}!important;
}}
[data-testid="stSidebar"] *{{color:{TEXT2}!important;}}
[data-testid="stSidebar"] button[kind="primary"]{{
    color:{TEAL}!important;background:rgba(100,255,218,0.10)!important;
    border-color:{TEAL}!important;
}}
[data-testid="stSidebar"] button[kind="secondary"]{{color:{TEXT2}!important;}}
/* Content area cards and surfaces */
.as-fc-card,.as-alert-item,.as-chat-ai{{
    background:rgba(255,252,248,0.90)!important;
    border-color:rgba(160,100,60,0.18)!important;
    color:#1c0f05!important;
}}
div[data-testid="metric-container"]{{background:rgba(255,252,248,0.85)!important;border-color:rgba(160,100,60,0.18)!important;}}
/* Fixed nav */
.as-fixed-nav{{background:rgba(253,248,242,0.96)!important;backdrop-filter:blur(20px)!important;border-bottom-color:rgba(160,100,60,0.18)!important;}}
.as-logo{{color:#b5613f!important;-webkit-text-fill-color:#b5613f!important;}}
/* Inputs */
.stSelectbox>div>div{{background:rgba(255,252,248,0.9)!important;color:#1c0f05!important;border-color:rgba(160,100,60,0.25)!important;}}
/* Tabs */
.stTabs [data-baseweb="tab"]{{color:#6b4530!important;}}
.stTabs [aria-selected="true"]{{color:#b5613f!important;border-bottom-color:#b5613f!important;}}
/* Stat strip values */
.as-stat-val{{color:#b5613f!important;}}
/* Main content buttons — warm, not dark navy */
button[kind="secondary"],.stButton>button{{
    background:rgba(255,252,248,0.85)!important;
    border-color:rgba(160,100,60,0.28)!important;
    color:#5c3a1e!important;
}}
button[kind="secondary"]:hover,.stButton>button:hover{{
    background:rgba(181,97,63,0.10)!important;
    border-color:rgba(181,97,63,0.50)!important;
    color:#b5613f!important;
}}
/* Scrollbar */
::-webkit-scrollbar-thumb{{background:rgba(181,97,63,0.35)!important;}}
</style>""", unsafe_allow_html=True)
    st.markdown(PARTICLES, unsafe_allow_html=True)


def render_nav():
    """Fixed top bar + always-visible horizontal page nav strip."""
    page     = st.session_state.page
    lang     = LNG()
    labels   = NAV_LABELS[lang]
    page_lbl = labels.get(page, page.title())
    try:
        from utils.live_data import get_live_stats
        live     = get_live_stats()
        n_alerts = sum(1 for s in live.values() if s.get("mean_pm25", 0) > WHO_24H)
    except Exception:
        n_alerts = sum(1 for s in CITY_STATS.values() if s["mean_pm25"] > WHO_24H)

    # ── Fixed decorative top bar ──────────────────────────────────────────────
    st.markdown(f"""
<div class="as-fixed-nav">
  <div style="display:flex;align-items:center;gap:.6rem;">
    <div class="as-logo">
      <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24"
        fill="none" stroke="{TEAL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/>
      </svg>
      AirSense Cameroon
    </div>
    <div style="width:1px;height:18px;background:{BORDER};"></div>
    <span style="font-size:.75rem;color:{TEXT2};">{page_lbl}</span>
  </div>
  <div style="display:flex;align-items:center;gap:.6rem;">
    <span class="as-alert-badge">{n_alerts} {'alerts' if lang=='en' else 'alertes'}</span>
    <span style="font-size:.62rem;color:{TEXT2};font-family:'JetBrains Mono',monospace;
      display:flex;align-items:center;gap:.25rem;">
      <span class="as-live-dot"></span>Live
    </span>
  </div>
</div>""", unsafe_allow_html=True)

    # ── Always-visible page navigation (fallback when sidebar collapsed) ────
    nav_labels = NAV_LABELS[lang]
    # Scoped CSS — only affects buttons inside the as-topnav div
    st.markdown(f"""<style>
#as-topnav .stButton > button {{
    padding: .22rem .5rem !important;
    font-size: .65rem !important;
    border-radius: 5px !important;
    white-space: nowrap !important;
    min-height: 0 !important;
    line-height: 1.3 !important;
    width: 100% !important;
}}
</style>
<div id="as-topnav" style="display:none"></div>
""", unsafe_allow_html=True)

    nav_cols = st.columns(len(PAGE_KEYS))
    for col, key in zip(nav_cols, PAGE_KEYS):
        lbl = nav_labels[key]
        with col:
            is_active = (page == key)
            if st.button(lbl, key=f"topnav_{key}",
                         type="primary" if is_active else "secondary",
                         use_container_width=True):
                st.session_state.page = key
                st.rerun()
    st.markdown(
        f"<div style='height:1px;background:{BORDER};margin:.2rem 0 .5rem;'></div>",
        unsafe_allow_html=True,
    )

def render_sidebar():
    """Left sidebar — ordered nav + settings gear in header."""
    lang    = LNG()
    is_dark = st.session_state.theme == "dark"
    labels  = NAV_LABELS[lang]
    subs    = NAV_SUBTITLES[lang]

    with st.sidebar:
        # ── Brand header with settings gear ──────────────────────────────────
        h1, h2 = st.columns([5, 1])
        with h1:
            st.markdown(f"""<div style="display:flex;align-items:center;gap:.45rem;
  padding:.25rem 0 .7rem;">
  <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" viewBox="0 0 24 24"
    fill="none" stroke="{TEAL}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/>
  </svg>
  <span style="font-family:'JetBrains Mono',monospace;font-size:.85rem;
    font-weight:700;color:{TEAL};">AirSense CM</span>
</div>""", unsafe_allow_html=True)
        with h2:
            if st.button("⚙", key="sb_gear", help="Settings",
                         use_container_width=True):
                st.session_state.show_settings = not st.session_state.get("show_settings", False)

        # ── Settings panel (collapsible) ──────────────────────────────────────
        if st.session_state.get("show_settings", False):
            st.markdown(f"""<div style="background:rgba(100,255,218,0.05);
  border:1px solid rgba(100,255,218,0.15);border-radius:8px;
  padding:.6rem .7rem;margin-bottom:.6rem;">
  <div style="font-size:.58rem;color:{TEAL};font-weight:700;
    text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem;">
    ⚙ Settings
  </div>""", unsafe_allow_html=True)
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
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(f"<div style='height:1px;background:{BORDER};margin-bottom:.5rem;'></div>",
                    unsafe_allow_html=True)

        # ── Ordered navigation ────────────────────────────────────────────────
        # Single st.button per page — styled left-aligned via CSS.
        # No duplicate HTML. SVG icons injected via CSS content on button label.
        sections = [
            ("EXPLORE",  ["overview", "explorer"]),
            ("TOOLS",    ["alerts", "ai"]),
            ("RESEARCH", ["science", "about"]),
        ]
        for section_label, keys in sections:
            st.markdown(
                f'<p style="font-size:.47rem;font-weight:700;text-transform:uppercase;'                f'letter-spacing:.15em;color:{BORDER};padding:.5rem 0 .18rem;'                f'margin:0;line-height:1;">{section_label}</p>',
                unsafe_allow_html=True,
            )
            for key in keys:
                active = st.session_state.page == key
                label  = labels[key]
                sub    = subs[key]
                if st.button(
                    label,
                    key=f"sb_{key}",
                    use_container_width=True,
                    type="primary" if active else "secondary",
                    help=sub,
                ):
                    st.session_state.page = key
                    st.rerun()

        # ── Live data footer ──────────────────────────────────────────────────
        try:
            get_live_stats, compute_live_shap, fetch_forecast = _get_live_stats()
            live = get_live_stats()
            n_live    = len(live)
            n_alerts  = sum(1 for s in live.values() if s.get("mean_pm25", 0) > WHO_24H)
            last_upd  = st.session_state.get("last_refresh", "—")
            data_note = f"<strong style='color:{TEAL};'>{n_live}</strong>/40 {T.get(lang,T['en']).get('cities_live','cities live')}"
        except Exception:
            n_alerts  = sum(1 for s in CITY_STATS.values() if s["mean_pm25"] > WHO_24H)
            data_note = f"<span style='color:{TEXT2};'>static baseline</span>"
            last_upd  = "—"

        st.markdown(f"""<div style="margin-top:.8rem;padding:.5rem .1rem 0;
  border-top:1px solid {BORDER};">
  <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.25rem;">
    <span style="font-size:.56rem;color:{TEXT2};text-transform:uppercase;letter-spacing:.07em;">
      {T.get(lang, T["en"]).get("alerts_label","Active alerts")}
    </span>
    <span style="font-size:.9rem;font-weight:700;color:{RED};
      font-family:'JetBrains Mono',monospace;">{n_alerts}</span>
  </div>
  <div style="font-size:.49rem;color:{TEXT2};line-height:1.8;margin-bottom:.45rem;">
    {data_note}<br>
    XGBoost · Platt Alerts · SHAP<br>
    Conformal Prediction · CMIP6<br>
    Claude AI · IndabaX Cameroon 2026
  </div>
</div>""", unsafe_allow_html=True)

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

