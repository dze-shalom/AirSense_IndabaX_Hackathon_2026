"""pages/explorer.py — Forecast (7-day + historical) + Analytics + Compare."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta, date

from config import *
from utils.helpers import (aqi, compute_bfai, bfai_label, bfai_col,
                           classify_source, health_impact, live_source_attribution, LNG)
from utils.models import (load_models, load_artefacts, get_conf_interval, get_alert_prob,
                           predict_7day, predict_7day_smart, predict_compounds_today,
                           infer_region_from_lat)
from utils.api import fetch_forecast, fetch_historical, geocode_city, wmo_icon
from utils.live_data import live_city
from components.ui import sec, card, info_box, bfai_gauge_svg
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




def _t(key):
    lang = LNG()
    return T.get(lang, T["en"]).get(key, T["en"].get(key, key))


def page_explorer():
    t   = T[LNG()]
    art = load_artefacts()
    st.markdown('<div class="as-content">', unsafe_allow_html=True)

    # ── City selector ─────────────────────────────────────────────────────────
    r1, r2, r3 = st.columns([1.4, 1.4, 2.2])
    with r1: region = st.selectbox(t["select_region"], list(CITIES.keys()), key="ex_region")
    with r2:
        city_list = [c[0] for c in CITIES[region]]
        # Key includes region so the widget resets when region changes
        city = st.selectbox(t["select_city"], city_list, key=f"ex_city_{region}")
        cd   = next(c for c in CITIES[region] if c[0] == city)
        lat, lon = cd[1], cd[2]
    with r3:
        s       = live_city(city, region)
        pm25    = s["mean_pm25"]
        _, c_aqi, ico_aqi, raw_aqi = aqi(pm25, LNG())
        cat_aqi = T[LNG()].get(raw_aqi, T["en"][raw_aqi])
        ap      = get_alert_prob(pm25, art)
        q_hat   = get_conf_interval(region, art)
        tier_c  = {"High":GREEN,"Medium":AMBER,"Low":ORANGE}.get(s.get("tier","Medium"),AMBER)
        live_dot = f'<span class="as-live-dot"></span>' if s.get("live") else ""
        st.markdown(f"""<div style="padding:.35rem 0;">
  <div style="font-size:.68rem;color:{TEXT2};">{live_dot}
    <strong style="color:{TEXT1};font-size:.82rem;">{city}</strong>
    · {region} · {lat:.2f}°N {lon:.2f}°E
  </div>
  <div style="display:flex;gap:.5rem;flex-wrap:wrap;margin-top:.3rem;align-items:center;">
    <span style="background:{c_aqi}22;border:1px solid {c_aqi}55;color:{c_aqi};
      border-radius:4px;padding:.1rem .4rem;font-size:.65rem;font-weight:700;">
      {ico_aqi} {pm25:.1f} μg/m³ · {cat_aqi}
    </span>
    <span style="background:rgba(100,255,218,.07);border:1px solid rgba(100,255,218,.2);
      color:{TEAL};border-radius:4px;padding:.1rem .4rem;font-size:.62rem;">
      P(exceed) {ap*100:.0f}%
    </span>
    <span style="background:{tier_c}22;border:1px solid {tier_c}55;color:{tier_c};
      border-radius:4px;padding:.1rem .4rem;font-size:.62rem;">
      {s.get("tier","Medium")} confidence
    </span>
  </div>
</div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin-top:.5rem;'></div>", unsafe_allow_html=True)

    tab_fc, tab_an, tab_cmp = st.tabs(["Forecast","Analytics","Compare"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — FORECAST  (7-day + historical date picker)
    # ══════════════════════════════════════════════════════════════════════════
    with tab_fc:
        model, enc, fi = load_models()

        # ── Mode toggle ───────────────────────────────────────────────────────
        mode_col, ref_col = st.columns([3, 1])
        with mode_col:
            fc_mode = st.radio("Mode", ["7-Day Forecast", "Historical Date"],
                               horizontal=True, key="fc_mode")
        with ref_col:
            if st.button("↺", key="ex_ref", help="Refresh forecast"): fetch_forecast.clear(); st.rerun()

        if fc_mode == "7-Day Forecast":
            with st.spinner(t["loading"]):
                fd = fetch_forecast(lat, lon)
            forecasts = predict_7day_smart(fd, city, region, lat, lon, model, enc, fi) if fd and model else None
            date_label = "7-Day Forecast"
        else:
            # Historical mode
            hc1, hc2 = st.columns(2)
            with hc1:
                hist_start = st.date_input("Start date", value=datetime.today() - timedelta(days=14),
                                           max_value=datetime.today() - timedelta(days=1),
                                           key="hist_start")
            with hc2:
                hist_end = st.date_input("End date",
                                         value=datetime.today() - timedelta(days=1),
                                         max_value=datetime.today() - timedelta(days=1),
                                         key="hist_end")
            if (hist_end - hist_start).days > 30:
                st.warning("Max 30-day range for historical mode.")
                hist_end = hist_start + timedelta(days=30)
            with st.spinner("Fetching historical weather from Open-Meteo archive…"):
                fd = fetch_historical(lat, lon, str(hist_start), str(hist_end))
            forecasts = predict_7day(fd, city, region, lat, lon, model, enc, fi) if fd and model else None
            date_label = f"Historical: {hist_start} → {hist_end}"

        # ── Show why forecasts are unavailable ───────────────────────────────
        if not model:
            st.error("⚠ Model not loaded — check that `models/xgb_pm25.json` and "
                     "`models/label_encoders.pkl` and `models/features.json` exist in your repo.")
        elif not fd:
            st.warning("⚠ Weather forecast unavailable — Open-Meteo API may be down. "
                       "Try refreshing with ↺")
        elif not forecasts:
            st.error("⚠ Prediction failed — check logs for feature mismatch errors.")

        # ── KPI cards ─────────────────────────────────────────────────────────
        if forecasts:
            today = forecasts[0]
            fc_pm25 = today["pm25"]; wind = today["wind"]; hum = today["humidity"]
            wdir    = fd["daily"].get("wind_direction_10m_dominant",[180])[0] if fd else 180
            month_now = datetime.strptime(today["date"],"%Y-%m-%d").month
        else:
            fc_pm25 = pm25; wind = 6; hum = 65; wdir = 180
            month_now = datetime.now().month

        _, fc_col, fc_ico, fc_raw = aqi(fc_pm25, LNG())
        bfai_sc = compute_bfai(fc_pm25, wind, hum, region)
        src_type, src_pct = classify_source(wind, wdir, region, month_now)
        src_lbl, src_sub  = {"local":("Local Sources","Traffic, burning, industry"),
                              "transported":("Transported Dust","Harmattan long-range"),
                              "stagnation":("Stagnation","Low wind, trapped pollution"),
                              "mixed":("Mixed Sources","Combination of factors")}[src_type]
        src_col = {"local":"#f97316","transported":"#c084fc",
                   "stagnation":"#f87171","mixed":"#fbbf24"}[src_type]

        k1,k2,k3,k4,k5 = st.columns(5)
        with k1: card("PM2.5 Today",f"{fc_pm25:.1f}","μg/m³",
                      badge=f"{fc_ico} {T[LNG()].get(fc_raw,fc_raw)}",badge_col=fc_col,accent=fc_col)
        with k2: card("BFAI Score",f"{bfai_sc}","/100 outdoor safety",
                      badge=bfai_label(bfai_sc),badge_col=bfai_col(bfai_sc),accent=bfai_col(bfai_sc))
        with k3: card("Alert Risk",f"{get_alert_prob(fc_pm25,art)*100:.0f}","% P(exceed WHO)",
                      badge=f"Confidence: {s.get('tier','Medium')}",badge_col=tier_c,
                      accent=RED if get_alert_prob(fc_pm25,art)>.5 else (AMBER if get_alert_prob(fc_pm25,art)>.25 else GREEN))
        with k4: card("Conf. Interval",f"±{q_hat:.0f}","μg/m³ (90%)",
                      badge=region,badge_col=TEAL2,accent=TEAL2)
        with k5: card("Source",src_lbl[:18],src_sub[:30],
                      badge=f"{src_pct}% attributed",badge_col=src_col,accent=src_col)

        # ── BFAI gauge ────────────────────────────────────────────────────────
        st.markdown("<div style='margin-top:.9rem;'></div>", unsafe_allow_html=True)
        ga, gb = st.columns(2)
        with ga:
            sec(_t("bfai_hdr"))
            if forecasts:
                st.markdown(
                    f'<div style="font-size:.58rem;color:{TEAL};margin-bottom:.3rem;">' +
                    ('🟢 Live — today\'s forecast' if LNG()=='en' else '🟢 En direct — prévision du jour') +
                    '</div>', unsafe_allow_html=True)
            st.markdown(bfai_gauge_svg(bfai_sc, bfai_label(bfai_sc, LNG()), bfai_col(bfai_sc)),
                        unsafe_allow_html=True)
        with gb:
            sec("Pollution Source Attribution")
            rgb = {"local":"249,115,22","transported":"192,132,252",
                   "stagnation":"248,113,113","mixed":"251,191,36"}[src_type]
            st.markdown(f"""<div style="background:rgba({rgb},0.07);border:1px solid rgba({rgb},0.22);
  border-radius:12px;padding:16px 20px;min-height:140px;display:flex;
  align-items:center;justify-content:space-between;">
  <div>
    <div style="font-size:.9rem;font-weight:700;color:{src_col};">{src_lbl}</div>
    <div style="font-size:.72rem;color:{TEXT2};margin-top:5px;">{src_sub}</div>
    <div style="font-size:.65rem;color:{TEXT2};margin-top:8px;">Wind: {wind:.1f} km/h · Month {month_now}</div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:2.4rem;font-weight:900;color:{src_col};">{src_pct}%</div>
    <div style="font-size:.65rem;color:{TEXT2};">attributed</div>
  </div>
</div>""", unsafe_allow_html=True)

        # ── Forecast cards + trend ─────────────────────────────────────────────
        if forecasts:
            st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
            sec(f"{date_label} — {city}")
            cards_html = '<div class="as-fc-grid">'
            for i, fc in enumerate(forecasts):
                _, cfc, ifc, rk = aqi(fc["pm25"], LNG())
                cf  = T[LNG()].get(rk, T["en"][rk])
                dt  = datetime.strptime(fc["date"],"%Y-%m-%d")
                lbl = "Today" if (i==0 and fc_mode=="7-Day Forecast") else dt.strftime("%a %d")
                cards_html += f"""<div class="as-fc-card {'today' if i==0 and fc_mode==_t('mode_forecast') else ''}">
  <div class="as-fc-day">{lbl}</div>
  <div class="as-fc-icon">{wmo_icon(fc.get('wmo_code',3))}</div>
  <div class="as-fc-val" style="color:{cfc};">{fc['pm25']:.1f}</div>
  <div class="as-fc-unit">μg/m³</div>
  <div class="as-fc-badge" style="background:{cfc}22;color:{cfc};">{ifc} {cf}</div>
  <div class="as-fc-meta">💧{fc['humidity']:.0f}% 💨{fc['wind']:.0f}km/h</div>
</div>"""
            st.markdown(cards_html + "</div>", unsafe_allow_html=True)

            sec("PM2.5 Trend — 90% Calibrated Confidence Band")
            dates = [fc["date"] for fc in forecasts]
            pms   = [fc["pm25"] for fc in forecasts]
            lows  = [max(0, p-q_hat) for p in pms]
            highs = [p+q_hat for p in pms]
            fig_fc = go.Figure()
            fig_fc.add_trace(go.Scatter(x=dates+dates[::-1], y=highs+lows[::-1],
                fill="toself", fillcolor="rgba(100,255,218,0.06)",
                line=dict(color="rgba(0,0,0,0)"), showlegend=False))
            fig_fc.add_hline(y=WHO_24H, line=dict(color=RED,width=1.5,dash="dash"),
                             annotation_text="WHO 24h", annotation_font_color=RED)
            fig_fc.add_trace(go.Scatter(x=dates, y=pms, mode="lines+markers",
                line=dict(color=TEAL,width=2.5),
                marker=dict(size=10, color=[aqi(p)[1] for p in pms],
                            line=dict(color=TEAL,width=2)),
                hovertemplate="<b>%{x}</b><br>PM2.5: %{y:.1f} μg/m³<extra></extra>"))
            fig_fc.update_layout(**PLO(height=240,
                yaxis=dict(gridcolor=BORDER,title="PM2.5 (μg/m³)"),
                hovermode="x unified", showlegend=False))
            st.plotly_chart(fig_fc, use_container_width=True)
            info_box(f"<strong>±{q_hat:.0f} μg/m³</strong> calibrated 90% conformal interval for {region}. "
                     "Empirical coverage: 97.4%.")
        else:
            st.info(t["no_data"])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — ANALYTICS
    # ══════════════════════════════════════════════════════════════════════════
    with tab_an:
        months = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]

        an_tabs = st.tabs(["Seasonal","Climate vs AQ","Compounds","Source","Health","Africa"])

        # ── Seasonal ──────────────────────────────────────────────────────────
        with an_tabs[0]:
            sec(f"Monthly PM2.5 — {city} · {region}")
            seasonal = city_monthly_profile(city, region)
            fig_s = go.Figure()
            fig_s.add_trace(go.Scatter(x=months, y=seasonal, mode="lines+markers",
                line=dict(color=TEAL,width=2.5),
                marker=dict(size=8,color=[aqi(v)[1] for v in seasonal],
                            line=dict(color=TEAL,width=1.5)),
                fill="tozeroy", fillcolor="rgba(100,255,218,0.06)",
                hovertemplate="<b>%{x}</b><br>PM2.5: %{y:.1f} μg/m³<extra></extra>"))
            fig_s.add_hline(y=WHO_24H, line=dict(color=RED,width=1.5,dash="dash"),
                            annotation_text="WHO 24h (15)", annotation_font_color=RED,
                            annotation_position="top right")
            fig_s.add_hline(y=WHO_ANN, line=dict(color=AMBER,width=1,dash="dot"),
                            annotation_text="WHO Annual (5)", annotation_font_color=AMBER,
                            annotation_position="bottom right")
            if region in NORTHERN | HIGHLAND:
                fig_s.add_vrect(x0="Nov", x1="Feb",
                    fillcolor="rgba(245,158,11,0.07)", line_width=0,
                    annotation_text="Harmattan", annotation_font_color=AMBER)
            fig_s.update_layout(**PLO(height=260,
                yaxis=dict(gridcolor=BORDER,title="PM2.5 (μg/m³)"),showlegend=False))
            st.plotly_chart(fig_s, use_container_width=True)

            # WHO exceedance calendar — per-city monthly
            sec(f"Monthly WHO Exceedance Calendar — {city}")
            exc_vals = [round(max(0, (v - WHO_24H) / WHO_24H * 100), 1) if v > WHO_24H else 0
                        for v in seasonal]
            fig_cal = go.Figure(go.Bar(
                x=months, y=exc_vals,
                marker=dict(color=[RED if v>50 else ORANGE if v>20 else AMBER if v>0 else GREEN
                                   for v in exc_vals], opacity=0.82),
                text=[f"{v:.0f}%" if v>0 else "OK" for v in exc_vals],
                textposition="outside", textfont=dict(size=9,color=TEXT2),
                hovertemplate="<b>%{x}</b><br>%{y:.1f}% above WHO<extra></extra>"))
            fig_cal.update_layout(**PLO(height=200,
                yaxis=dict(gridcolor=BORDER,title="% above WHO 24h"),
                xaxis=dict(gridcolor="rgba(0,0,0,0)"),showlegend=False))
            st.plotly_chart(fig_cal, use_container_width=True)

        # ── Climate vs AQ ─────────────────────────────────────────────────────
        with an_tabs[1]:
            sec(_t("climate_hdr") + f" — {city}")

            # Fetch real monthly climate from Open-Meteo archive (past 12 months)

            @st.cache_data(ttl=86400)
            def _monthly_climate(lat, lon):
                """Return (temp_m, prec_m, hum_m) 12-month lists from archive."""
                from datetime import date as _date
                today   = _date.today()
                # Use previous full calendar year for stable monthly aggregates
                yr      = today.year - 1
                fd_hist = fetch_historical(lat, lon, f"{yr}-01-01", f"{yr}-12-31")
                if not fd_hist:
                    return None, None, None
                daily = fd_hist.get("daily", {})
                dates_raw = daily.get("time", [])
                temps  = daily.get("temperature_2m_mean", [])
                precs  = daily.get("precipitation_sum", [])
                hums   = daily.get("relative_humidity_2m_mean", [])
                if not dates_raw:
                    return None, None, None
                from collections import defaultdict
                mt, mp, mh = defaultdict(list), defaultdict(list), defaultdict(list)
                for i, d in enumerate(dates_raw):
                    m = int(d[5:7])
                    if i < len(temps) and temps[i] is not None:  mt[m].append(temps[i])
                    if i < len(precs) and precs[i] is not None:  mp[m].append(precs[i])
                    if i < len(hums)  and hums[i]  is not None:  mh[m].append(hums[i])
                def avg(d, m): return round(sum(d[m])/len(d[m]),1) if d.get(m) else None
                def tot(d, m): return round(sum(d[m]),1) if d.get(m) else None
                t_m = [avg(mt, m) for m in range(1,13)]
                p_m = [tot(mp, m) for m in range(1,13)]
                h_m = [avg(mh, m) for m in range(1,13)]
                return t_m, p_m, h_m

            with st.spinner("Fetching real climate data…" if LNG()=="en" else "Récupération des données climatiques…"):
                temp_m_raw, prec_m_raw, hum_m_raw = _monthly_climate(lat, lon)

            # Fallback to regional estimates if archive unavailable
            is_n = region in NORTHERN
            if any(v is None for v in (temp_m_raw, prec_m_raw, hum_m_raw)) or temp_m_raw is None:
                temp_m = [32,34,36,35,33,29,27,27,28,30,33,32] if is_n else [26,27,28,28,27,25,24,24,24,25,26,26]
                prec_m = [1,0,2,8,25,60,90,95,80,35,5,1]        if is_n else [15,20,35,80,140,160,200,190,160,100,30,12]
                hum_m  = [25,22,28,42,55,70,82,85,80,65,38,28]  if is_n else [55,52,58,72,80,88,90,91,88,80,65,55]
                data_note = ("🟡 Regional estimates (archive unavailable)"
                             if LNG()=="en" else "🟡 Estimations régionales (archive indisponible)")
            else:
                temp_m = [v if v is not None else 25.0 for v in temp_m_raw]
                prec_m = [v if v is not None else 0.0  for v in prec_m_raw]
                hum_m  = [v if v is not None else 60.0 for v in hum_m_raw]
                data_note = (f"🟢 Real data — Open-Meteo archive ({datetime.today().year-1})"
                             if LNG()=="en" else f"🟢 Données réelles — Open-Meteo archive ({datetime.today().year-1})")
            info_box(data_note)
            seasonal_c = city_monthly_profile(city, region)
            fig_cl = make_subplots(rows=2,cols=2,
                subplot_titles=["PM2.5 (μg/m³)","Temperature (°C)","Precipitation (mm)","Humidity (%)"],
                vertical_spacing=0.2,horizontal_spacing=0.1)
            fig_cl.add_trace(go.Scatter(x=months,y=seasonal_c,mode="lines+markers",
                line=dict(color=TEAL,width=2),
                marker=dict(size=5,color=[aqi(v)[1] for v in seasonal_c]),
                showlegend=False),row=1,col=1)
            fig_cl.add_hline(y=WHO_24H,line=dict(color=RED,width=1,dash="dash"),row=1,col=1)
            fig_cl.add_trace(go.Scatter(x=months,y=temp_m,mode="lines+markers",
                line=dict(color=ORANGE,width=2),marker=dict(size=5,color=ORANGE),
                showlegend=False),row=1,col=2)
            fig_cl.add_trace(go.Bar(x=months,y=prec_m,
                marker=dict(color=TEAL2,opacity=0.75),showlegend=False),row=2,col=1)
            fig_cl.add_trace(go.Scatter(x=months,y=hum_m,mode="lines+markers",
                line=dict(color=PURPLE,width=2),marker=dict(size=5,color=PURPLE),
                fill="tozeroy",fillcolor="rgba(139,92,246,0.08)",
                showlegend=False),row=2,col=2)
            fig_cl.update_layout(paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                height=370,showlegend=False,margin=dict(l=0,r=0,t=38,b=0),
                font=dict(family="Space Grotesk",color=TEXT2,size=9))
            for ri in [1,2]:
                for ci in [1,2]:
                    fig_cl.update_xaxes(gridcolor=BORDER,gridwidth=0.5,row=ri,col=ci)
                    fig_cl.update_yaxes(gridcolor=BORDER,gridwidth=0.5,row=ri,col=ci)
            st.plotly_chart(fig_cl, use_container_width=True)

        # ── Compounds ─────────────────────────────────────────────────────────
        with an_tabs[2]:
            sec(f"8-Compound Profile — {city}")
            with st.spinner("Running compound models…"):
                fd_now = fetch_forecast(lat, lon)
                comp_vals = predict_compounds_today(fd_now, city, region, lat, lon, enc, fi) if fd_now else None

            if comp_vals:
                info_box("🟢 <strong>Live predictions</strong> from trained XGBoost compound models "
                         f"(models_multi.pkl · {len(comp_vals)} compounds predicted).")
            else:
                # Fallback: estimate from PM2.5 ratios
                comp_vals = {
                    "pm2_5_target": pm25,
                    "pm10_target":  pm25 * 1.8,
                    "dust_target":  pm25 * 1.2 if region in NORTHERN else pm25 * 0.4,
                    "co_target":    pm25 * 12,
                    "no2_target":   pm25 * 0.15,
                    "o3_target":    pm25 * 1.5,
                    "so2_target":   pm25 * 0.05,
                    "aod_target":   pm25 / 200,
                }
                info_box("🟡 <strong>Estimated values</strong> — place models_multi.pkl in models/ "
                         "for real compound predictions.")

            keys   = [k for k in COMPOUND_KEYS if k in comp_vals]
            labels = [COMPOUND_LABELS[k] for k in keys]
            vals   = [comp_vals[k] for k in keys]
            colors = [COMPOUND_COLORS[k] for k in keys]

            fig_cpd = go.Figure(go.Bar(
                x=labels, y=vals,
                marker=dict(color=colors, opacity=0.85),
                text=[f"{v:.1f}" for v in vals], textposition="outside",
                textfont=dict(size=9),
                hovertemplate="<b>%{x}</b><br>%{y:.2f} %{customdata}<extra></extra>",
                customdata=[COMPOUND_UNITS.get(k,"") for k in keys]))
            fig_cpd.update_layout(**PLO(height=230, yaxis_title="Concentration",
                xaxis=dict(gridcolor="rgba(0,0,0,0)"), showlegend=False))
            st.plotly_chart(fig_cpd, use_container_width=True)

            # Detail rows with WHO comparison
            for k in keys:
                v   = comp_vals[k]
                lim = COMPOUND_WHO.get(k)
                col = COMPOUND_COLORS[k]
                pct = min(v/(lim*2)*100,100) if lim else min(v/max(vals)*100,100)
                exceed = lim and v > lim
                flag   = (f'<span style="font-size:.6rem;color:{RED};font-weight:700;margin-left:.4rem;">'
                          f'EXCEEDS</span>') if exceed else ""
                mae_note = f"MAE={COMPOUND_TEST_MAE.get(k,'?'):.2f}  R²={COMPOUND_TEST_R2.get(k,'?'):.3f}" if comp_vals else ""
                st.markdown(f"""<div style="display:flex;align-items:center;gap:.8rem;padding:.38rem 0;
  border-bottom:1px solid rgba(35,53,84,.5);">
  <span style="font-size:.68rem;color:{TEXT2};width:52px;flex-shrink:0;
    font-family:'JetBrains Mono',monospace;">{COMPOUND_LABELS[k]}</span>
  <div style="flex:1;height:5px;background:{BORDER};border-radius:3px;overflow:hidden;">
    <div style="width:{pct:.0f}%;height:100%;background:{col};border-radius:3px;"></div></div>
  <span style="font-size:.68rem;font-family:'JetBrains Mono',monospace;
    color:{'#f87171' if exceed else TEXT1};width:72px;text-align:right;">{v:.2f} {COMPOUND_UNITS.get(k,'')}</span>
  <span style="font-size:.6rem;color:{TEXT2};width:60px;">
    {"WHO: "+str(lim) if lim else "No limit"}</span>
  <span style="font-size:.58rem;color:{TEXT2};">{mae_note}</span>
  {flag}
</div>""", unsafe_allow_html=True)

        # ── Source ────────────────────────────────────────────────────────────
        with an_tabs[3]:
            sec(_t("source_fp_hdr") + f" — {city}")

            # Fetch live weather conditions for this city
            with st.spinner(_t("loading")):
                fd_src = fetch_forecast(lat, lon)

            if fd_src:
                daily_src = fd_src.get("daily", {})
                wind_spd  = (daily_src.get("wind_speed_10m_max",        [6]  ) or [6]  )[0] or 6
                wind_dir  = (daily_src.get("wind_direction_10m_dominant",[180]) or [180])[0] or 180
                precip    = (daily_src.get("precipitation_sum",          [0]  ) or [0]  )[0] or 0
                hum       = (daily_src.get("relative_humidity_2m_mean",  [65] ) or [65] )[0] or 65
                from datetime import datetime as _dt2
                month_src = _dt2.today().month

                # SHAP weights for this region (if available)
                from utils.live_data import compute_live_shap as _cshap
                _ls = _cshap() or {}
                shap_data = _ls.get(region)

                src = live_source_attribution(
                    wind_speed=wind_spd, wind_dir=wind_dir,
                    month=month_src,    region=region,
                    precipitation=precip, humidity=hum,
                    pm25=pm25, shap_data=shap_data,
                )
                harmattan_flag = month_src in [11,12,1,2] and region in NORTHERN
                season_note = ("🌬 Harmattan" if harmattan_flag
                               else "🌧 Wet season" if month_src in [5,6,7,8,9]
                               else "☀ Dry season" if month_src in [11,12,1,2,3]
                               else "🌤 Transitional")
                info_box(
                    f"🟢 <strong>Live attribution</strong> computed from today's weather — "
                    f"Wind: <strong>{wind_spd:.1f} km/h</strong> from {wind_dir:.0f}°, "
                    f"Precip: {precip:.1f} mm, Humidity: {hum:.0f}% · {season_note}."
                )
            else:
                # Fallback to region-type static estimates
                from utils.helpers import city_profile as _cp
                src = _cp(city, region, pm25)["src"]
                # Rename keys to match live attribution labels
                src = {
                    "Dust":            src.get("Dust", 0.12),
                    "Biomass Burning": src.get("Biomass", 0.25),
                    "Traffic":         src.get("Traffic", 0.20),
                    "Industry":        src.get("Industry", 0.10),
                    "Secondary":       src.get("Secondary", 0.15),
                    "Other":           src.get("Other", 0.05),
                }
                info_box("🟡 <strong>Estimated attribution</strong> (static) — live forecast unavailable.")

            SRC_COLORS = {
                "Dust":            "#f59e0b",
                "Biomass Burning": "#f97316",
                "Traffic":         "#8b5cf6",
                "Industry":        "#06b6d4",
                "Secondary":       "#22c55e",
                "Other":           "#8892b0",
            }
            cats  = list(src.keys())
            vals_s = [v * 100 for v in src.values()]

            col_r, col_b = st.columns([1.1, 1])
            with col_r:
                cats_c = cats + [cats[0]]; vals_c = vals_s + [vals_s[0]]
                fig_r = go.Figure(go.Scatterpolar(
                    r=vals_c, theta=cats_c, fill="toself",
                    fillcolor="rgba(100,255,218,0.07)",
                    line=dict(color=TEAL, width=2.5),
                    hovertemplate="<b>%{theta}</b><br>%{r:.1f}%<extra></extra>"))
                fig_r.update_layout(
                    polar=dict(bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0, 70], ticksuffix="%",
                            tickfont=dict(color=TEXT2, size=8), gridcolor=BORDER),
                        angularaxis=dict(tickfont=dict(color=TEXT1, size=9), gridcolor=BORDER)),
                    paper_bgcolor="rgba(0,0,0,0)", height=295, showlegend=False,
                    margin=dict(l=40, r=40, t=25, b=15))
                st.plotly_chart(fig_r, use_container_width=True)

            with col_b:
                dom = max(src, key=src.get)
                for src_k in sorted(src, key=src.get, reverse=True):
                    pct_v  = src[src_k] * 100
                    is_dom = src_k == dom
                    sc     = SRC_COLORS.get(src_k, TEAL)
                    st.markdown(f"""<div style="padding:.35rem 0;border-bottom:1px solid rgba(35,53,84,.4);">
  <div style="display:flex;justify-content:space-between;margin-bottom:.2rem;align-items:center;">
    <span style="font-size:.72rem;font-weight:{'700' if is_dom else '500'};
      color:{'#e6f1ff' if is_dom else TEXT2};">{src_k}</span>
    <span style="font-family:'JetBrains Mono',monospace;font-size:.75rem;
      font-weight:700;color:{sc};">{pct_v:.0f}%</span>
  </div>
  <div style="height:4px;background:{BORDER};border-radius:2px;overflow:hidden;">
    <div style="width:{pct_v:.0f}%;height:100%;background:{sc};
      opacity:{'.9' if is_dom else '.5'};border-radius:2px;"></div></div>
</div>""", unsafe_allow_html=True)

        # ── Health ────────────────────────────────────────────────────────────
        with an_tabs[4]:
            sec(f"Health Impact — {city} · PM2.5 {pm25:.1f} μg/m³")
            er,hr,ld = health_impact(pm25)
            h1,h2,h3 = st.columns(3)
            with h1: card("Excess Resp. Cases",f"{er:.1f}","per 10,000 people",accent=c_aqi)
            with h2: card("Hospital Risk",f"{hr:.1f}","%",
                          badge="High" if hr>10 else "Moderate",
                          badge_col=RED if hr>10 else AMBER,
                          accent=RED if hr>10 else AMBER)
            with h3: card("Lost Work Days",f"{ld:.1f}","per 10,000 workers",accent=ORANGE)

        # ── Africa benchmark ──────────────────────────────────────────────────
        with an_tabs[5]:
            sec("Cameroon vs Africa — PM2.5 Benchmark")
            cities_b,vals_b,cols_b,is_cm = zip(*AFRICA_BENCHMARK)
            fig_af = go.Figure(go.Bar(
                y=list(cities_b),x=list(vals_b),orientation="h",
                marker=dict(color=list(cols_b),opacity=0.85,
                    line=dict(color=[TEAL if cm else "rgba(0,0,0,0)" for cm in is_cm],
                              width=[2 if cm else 0 for cm in is_cm])),
                text=[f"{v} μg/m³" for v in vals_b],textposition="outside",
                textfont=dict(color=TEXT2,size=10)))
            fig_af.add_vline(x=WHO_24H,line=dict(color=RED,width=1.5,dash="dash"),
                             annotation_text="WHO 24h (15)",annotation_font_color=RED)
            fig_af.update_layout(**PLO(height=370,margin=dict(l=0,r=70,t=10,b=10),
                xaxis_title="Annual Mean PM2.5 (μg/m³)",
                yaxis=dict(gridcolor="rgba(0,0,0,0)"),showlegend=False))
            st.plotly_chart(fig_af, use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — COMPARE
    # ══════════════════════════════════════════════════════════════════════════
    with tab_cmp:
        sec("Compare Two Cities")
        cc1, cc2 = st.columns(2)
        with cc1:
            cmp_ra = st.selectbox("Region A", list(CITIES.keys()), key="cmp_ra2")
            cmp_ca = st.selectbox("City A",   [c[0] for c in CITIES[cmp_ra]], key="cmp_ca2")
        with cc2:
            cmp_rb = st.selectbox("Region B", list(CITIES.keys()), index=3, key="cmp_rb2")
            cmp_cb = st.selectbox("City B",   [c[0] for c in CITIES[cmp_rb]], key="cmp_cb2")

        sa2 = live_city(cmp_ca, cmp_ra)
        sb2 = live_city(cmp_cb, cmp_rb)
        _,cola2,ia2,rka2 = aqi(sa2["mean_pm25"],LNG())
        _,colb2,ib2,rkb2 = aqi(sb2["mean_pm25"],LNG())

        m1,m2,m3,m4 = st.columns(4)
        with m1: card(f"{cmp_ca} PM2.5",f"{sa2['mean_pm25']:.1f}","μg/m³",
                      badge=f"{ia2} {T[LNG()].get(rka2,rka2)}",badge_col=cola2,accent=cola2)
        with m2: card(f"{cmp_cb} PM2.5",f"{sb2['mean_pm25']:.1f}","μg/m³",
                      badge=f"{ib2} {T[LNG()].get(rkb2,rkb2)}",badge_col=colb2,accent=colb2)
        with m3: card(f"{cmp_ca} WHO Exc",f"{sa2['who_exc']:.1f}","%",
                      accent=RED if sa2["who_exc"]>50 else AMBER)
        with m4: card(f"{cmp_cb} WHO Exc",f"{sb2['who_exc']:.1f}","%",
                      accent=RED if sb2["who_exc"]>50 else AMBER)

        months2 = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        sea_a = city_monthly_profile(cmp_ca, cmp_ra)
        sea_b = city_monthly_profile(cmp_cb, cmp_rb)
        fig_cmp = go.Figure()
        fig_cmp.add_trace(go.Scatter(x=months2,y=sea_a,mode="lines+markers",
            line=dict(color=cola2,width=2.5),marker=dict(size=6,color=cola2),
            name=cmp_ca,fill="tozeroy",fillcolor="rgba(0,0,0,0.07)"))
        fig_cmp.add_trace(go.Scatter(x=months2,y=sea_b,mode="lines+markers",
            line=dict(color=colb2,width=2.5,dash="dash"),marker=dict(size=6,color=colb2),
            name=cmp_cb,fill="tozeroy",fillcolor="rgba(0,0,0,0.05)"))
        fig_cmp.add_hline(y=WHO_24H,line=dict(color=RED,width=1.5,dash="dash"),
                          annotation_text="WHO 24h",annotation_font_color=RED)
        fig_cmp.update_layout(**PLO(height=250,yaxis_title="PM2.5 (μg/m³)",
            legend=dict(font=dict(size=9),bgcolor="rgba(0,0,0,0)"),hovermode="x unified"))
        st.plotly_chart(fig_cmp, use_container_width=True)
        diff = sa2["mean_pm25"] - sb2["mean_pm25"]
        worse = cmp_ca if diff>0 else cmp_cb; better = cmp_cb if diff>0 else cmp_ca
        info_box(f"<strong>{worse}</strong> is {abs(diff):.1f} μg/m³ worse than <strong>{better}</strong>.")

    st.markdown('</div>', unsafe_allow_html=True)
