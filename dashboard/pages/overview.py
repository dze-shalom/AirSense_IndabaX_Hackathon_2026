"""pages/overview.py"""
import math
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from config import *
from utils.helpers import aqi, LNG, get_threshold, threshold_label
from utils.models import load_models, load_artefacts, predict_7day
from utils.api import fetch_forecast, wmo_icon
from utils.live_data import live_all
from components.ui import sec, card, info_box, _cbg, _cborder, _ctxt, _ctxt2, _accent
from components.charts import PLO





def _t(key):
    lang = LNG()
    return T.get(lang, T["en"]).get(key, T["en"].get(key, key))


def _region_hull(region):
    try:
        from scipy.spatial import ConvexHull
        pts = np.array([(lon, lat) for _, lat, lon in CITIES.get(region, [])])
        if len(pts) < 3:
            return None, None
        hull = ConvexHull(pts)
        lons = list(pts[hull.vertices, 0]) + [pts[hull.vertices[0], 0]]
        lats = list(pts[hull.vertices, 1]) + [pts[hull.vertices[0], 1]]
        return lats, lons
    except Exception:
        return None, None


def _wind_arrow(lat, lon, wdir_deg, wspd_kmh):
    length  = max(0.12, min(0.38, 0.012 * wspd_kmh))
    head    = length * 0.38
    rad     = math.radians(wdir_deg)
    cos_lat = max(0.05, math.cos(math.radians(lat)))
    tip_lat = lat + length * math.cos(rad)
    tip_lon = lon + length * math.sin(rad) / cos_lat
    def hp(a):
        r = rad + math.radians(a)
        return tip_lat + head * math.cos(r), tip_lon + head * math.sin(r) / cos_lat
    h1l, h1o = hp(150); h2l, h2o = hp(-150)
    return ([lat, tip_lat, None, tip_lat, h1l, None, tip_lat, h2l],
            [lon, tip_lon, None, tip_lon, h1o, None, tip_lon, h2o])


def _circular_stats(stats):
    """Professional AQI distribution donut for 71 Cameroonian cities."""
    from components.ui import _cbg, _ctxt, _ctxt2, _accent
    order  = ["good","moderate","poor","very_poor","hazardous"]
    colors = {"good":GREEN,"moderate":AMBER,"poor":ORANGE,"very_poor":RED,"hazardous":PURPLE}
    labels_en = {"good":"Healthy","moderate":"Moderate","poor":"Poor",
                 "very_poor":"Critical","hazardous":"Hazardous"}
    labels_fr = {"good":"Sain","moderate":"Modéré","poor":"Mauvais",
                 "very_poor":"Critique","hazardous":"Dangereux"}
    lang  = LNG()
    lbls  = labels_fr if lang=="fr" else labels_en
    is_lt = st.session_state.get("theme", "light") == "light"

    counts = {k: 0 for k in order}
    for s in stats.values():
        pm = s["mean_pm25"]
        if   pm < 15: counts["good"]      += 1
        elif pm < 35: counts["moderate"]  += 1
        elif pm < 55: counts["poor"]      += 1
        elif pm < 80: counts["very_poor"] += 1
        else:         counts["hazardous"] += 1

    keys   = [k for k in order if counts[k] > 0]
    vals   = [counts[k] for k in keys]
    clrs   = [colors[k]  for k in keys]
    disp   = [lbls[k]    for k in keys]
    total  = sum(vals)
    above  = sum(counts[k] for k in order if k != "good")

    seg_border = "rgba(0,0,0,0.12)" if is_lt else "rgba(255,255,255,0.15)"
    ann_col    = _ctxt()
    leg_col    = _ctxt2()

    fig = go.Figure(go.Pie(
        labels=disp, values=vals,
        marker=dict(colors=clrs, line=dict(color=seg_border, width=2)),
        hole=0.64,
        direction="clockwise",
        sort=False,
        textinfo="percent",
        textposition="inside",
        insidetextfont=dict(size=10, family="Open Sans", color="white"),
        hovertemplate="<b>%{label}</b><br>%{value} cities · %{percent}<extra></extra>",
        rotation=90,
        pull=[0.05 if k in ("poor","very_poor","hazardous") else 0 for k in keys],
    ))
    fig.add_annotation(
        text=(f"<b>{above}</b><br>"
              f"<span style='font-size:11px'>{('of' if lang=='en' else 'sur')} {total}</span><br>"
              f"<span style='font-size:9px'>{'above WHO' if lang=='en' else 'dépassent OMS'}</span>"),
        x=0.5, y=0.5, showarrow=False,
        font=dict(color=ann_col, size=15, family="Montserrat"),
        align="center",
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        height=230,
        margin=dict(l=0, r=0, t=6, b=40),
        legend=dict(
            orientation="h", x=0.5, xanchor="center", y=-0.12,
            font=dict(size=9, color=leg_col, family="Open Sans"),
            itemwidth=40,
        ),
        font=dict(family="Open Sans", color=ann_col),
    )
    return fig


def page_overview():
    st.markdown('<div class="as-content">', unsafe_allow_html=True)
    lang = LNG()

    with st.spinner(_t("loading")):
        _stats = live_all()

    # ── Headline ──────────────────────────────────────────────────────────────
    headline = ("51.9% of city-days in Cameroon exceed the WHO 24h PM2.5 limit."
                if lang == "en" else
                "51,9% des jours-villes au Cameroun dépassent la limite OMS PM2.5 24h.")
    sub = (f'The Far North averages <strong style="color:{RED};">24.1 μg/m³</strong> — '
           f'nearly <strong style="color:{RED};">6× the WHO annual guideline</strong> of 5 μg/m³.'
           if lang == "en" else
           f'L\'Extrême-Nord est à <strong style="color:{RED};">28,7 μg/m³</strong> — '
           f'près de <strong style="color:{RED};">6× la limite OMS annuelle</strong> de 5 μg/m³.')
    st.markdown(f"""<div style="padding:.8rem 0 .5rem;">
  <div style="font-size:1.3rem;font-weight:700;color:{_ctxt()};line-height:1.3;">{headline}</div>
  <div style="font-size:.78rem;color:{_ctxt2()};margin-top:.3rem;">{sub}</div>
</div>""", unsafe_allow_html=True)

    # ── Stat strip ────────────────────────────────────────────────────────────
    st.markdown(f"""<div class="as-stat-strip">
  <div style="text-align:center;"><div class="as-stat-val">71</div>
    <div class="as-stat-lbl">{"Cities" if lang=="en" else "Villes"}</div></div>
  <div style="text-align:center;"><div class="as-stat-val">10</div>
    <div class="as-stat-lbl">{"Regions" if lang=="en" else "Régions"}</div></div>
  <div style="text-align:center;"><div class="as-stat-val">51.9%</div>
    <div class="as-stat-lbl">{"WHO Exceedance" if lang=="en" else "Dépassement OMS"}</div></div>
  <div style="text-align:center;"><div class="as-stat-val">18.9</div>
    <div class="as-stat-lbl">{"Mean PM2.5" if lang=="en" else "PM2.5 Moyen"}</div></div>
  <div style="text-align:center;"><div class="as-stat-val">51.9%</div>
    <div class="as-stat-lbl">{"Above WHO 24h" if lang=="en" else "Au-dessus OMS 24h"}</div></div>
  <div style="text-align:center;"><div class="as-stat-val">0.847</div>
    <div class="as-stat-lbl">{"Alert F1" if lang=="en" else "F1 Alerte"}</div></div>
</div>""", unsafe_allow_html=True)

    # ── Layout: map | right panel ─────────────────────────────────────────────
    map_col, right_col = st.columns([1.65, 1])

    with map_col:
        # ── Region filter as compact checkboxes ───────────────────────────────
        sec(_t("filter_regions"))
        all_regions = list(CITIES.keys())

        # Select All / Deselect All toggle buttons
        cb1, cb2, cb3 = st.columns([1, 1, 5])
        with cb1:
            if st.button("All" if lang=="en" else "Tout", key="ov_all",
                         use_container_width=True):
                for r in all_regions:
                    st.session_state[f"ov_r_{r}"] = True
        with cb2:
            if st.button("Clear" if lang=="en" else "Effacer", key="ov_none",
                         use_container_width=True):
                for r in all_regions:
                    st.session_state[f"ov_r_{r}"] = False

        # Compact two-column checkbox grid
        n_cols = 2
        reg_cols = st.columns(n_cols)
        sel_regions = []
        for i, reg in enumerate(all_regions):
            default = st.session_state.get(f"ov_r_{reg}", True)
            with reg_cols[i % n_cols]:
                dot_col = REGION_COLORS.get(reg, TEAL)
                checked = st.checkbox(
                    reg, value=default, key=f"ov_r_{reg}",
                    help=f"{len(CITIES[reg])} cities"
                )
            if checked:
                sel_regions.append(reg)

        # AQI + Layer filters on one row
        fa1, fa2 = st.columns(2)
        with fa1:
            aqi_opts_en = ["All","Good","Moderate","Poor","Very Poor","Hazardous"]
            aqi_opts_fr = ["Tous","Bon","Modéré","Mauvais","Très Mauvais","Dangereux"]
            aqi_opts = aqi_opts_fr if lang == "fr" else aqi_opts_en
            aqi_f    = st.selectbox(_t("filter_aqi"), aqi_opts, key="ov_aqi")
            aqi_f_en = aqi_opts_en[aqi_opts.index(aqi_f)] if aqi_f in aqi_opts else "All"
        with fa2:
            layer_opts = [_t("cities_heatmap"), _t("cities_only"), _t("heatmap_only")]
            map_layer  = st.selectbox(_t("map_layer"), layer_opts, key="ov_layer")

        # ── Build city dataframe ──────────────────────────────────────────────
        rows = []
        for reg in sel_regions:
            for cname, clat, clon in CITIES.get(reg, []):
                s = _stats.get(cname, CITY_STATS.get(cname, {"mean_pm25":15.0,"who_exc":40.0}))
                pm = s["mean_pm25"]
                l, col, ico, raw = aqi(pm, lang)
                l_en = aqi(pm, "en")[0]
                if aqi_f_en != "All" and l_en.lower() != aqi_f_en.lower():
                    continue
                bsize = max(8, min(24, 8 + pm / 4))
                rows.append({"city":cname,"region":reg,"lat":clat,"lon":clon,
                             "pm25":pm,"who_exc":s["who_exc"],"label":l,
                             "col":col,"ico":ico,"bsize":bsize,
                             "tier":s.get("tier","Medium"),"live":s.get("live",False)})
        df_map = (pd.DataFrame(rows) if rows
                  else pd.DataFrame(columns=["city","region","lat","lon","pm25",
                                             "who_exc","label","col","ico","bsize","tier","live"]))

        # ── Build map ─────────────────────────────────────────────────────────
        fig = go.Figure()
        show_heat = map_layer != _t("cities_only")
        show_city = map_layer != _t("heatmap_only")

        # Layer 1 — density heatmap
        if show_heat and not df_map.empty:
            fig.add_trace(go.Densitymapbox(
                lat=df_map["lat"], lon=df_map["lon"], z=df_map["pm25"],
                radius=42, opacity=0.42,
                colorscale=[[0,"rgba(0,20,40,0)"],[0.2,"rgba(34,197,94,0.38)"],
                            [0.5,"rgba(245,158,11,0.55)"],[0.75,"rgba(249,115,22,0.68)"],
                            [1.0,"rgba(239,68,68,0.82)"]],
                zmin=0, zmax=60, showscale=False, hoverinfo="skip", name="heatmap"))

        # Layer 2 — region outlines
        for reg in sel_regions:
            hlats, hlons = _region_hull(reg)
            if hlats:
                rc = REGION_COLORS.get(reg, TEAL)
                # Fill polygon lightly
                fig.add_trace(go.Scattermapbox(
                    lat=hlats, lon=hlons, mode="lines",
                    line=dict(color=rc, width=1.5), opacity=0.30,
                    fill="toself",
                    fillcolor="rgba({},{},{},0.04)".format(
                        int(rc[1:3],16),int(rc[3:5],16),int(rc[5:7],16)),
                    showlegend=False, hoverinfo="skip", name=f"r_{reg}"))

        # Layer 3 — wind arrows (every 3rd city to avoid clutter)
        all_alats, all_alons = [], []
        for _, r in df_map.iloc[::3].iterrows():
            fd_w = fetch_forecast(r["lat"], r["lon"])
            if fd_w:
                daily_w = fd_w.get("daily", {})
                wdir = (daily_w.get("wind_direction_10m_dominant",[None]) or [None])[0]
                wspd = (daily_w.get("wind_speed_10m_max",[0]) or [0])[0] or 0
                if wdir is not None and wspd > 2:
                    al, ao = _wind_arrow(r["lat"], r["lon"], wdir, wspd)
                    all_alats.extend(al + [None])
                    all_alons.extend(ao + [None])
        if all_alats:
            fig.add_trace(go.Scattermapbox(
                lat=all_alats, lon=all_alons, mode="lines",
                line=dict(color="rgba(100,255,218,0.65)" if st.session_state.get("theme","light")=="dark" else "rgba(60,120,90,0.75)", width=1.8),
                showlegend=False, hoverinfo="skip", name="wind"))

        # Layer 4 — city bubbles
        if show_city and not df_map.empty:
            for _, r in df_map.iterrows():
                live_note = " ●" if r["live"] else ""
                fig.add_trace(go.Scattermapbox(
                    lat=[r["lat"]], lon=[r["lon"]], mode="markers+text",
                    marker=dict(size=r["bsize"], color=r["col"], opacity=0.9),
                    text=[r["city"]], textposition="top center",
                    textfont=dict(size=8, color="#ffffff"),
                    hovertemplate=(f"<b>{r['city']}{live_note}</b><br>{r['region']}<br>"
                                   f"PM2.5: {r['pm25']:.1f} μg/m³<br>"
                                   f"WHO Exc: {r['who_exc']:.1f}%<br>"
                                   f"{r['ico']} {r['label']}<extra></extra>"),
                    showlegend=False, name=r["city"]))

        fig.update_layout(
            mapbox=dict(style="carto-darkmatter", center=dict(lat=5.5, lon=12.3), zoom=4.8),
            **PLO(height=430, margin=dict(l=0,r=0,t=0,b=0), showlegend=False))
        sec(_t("national_map"))
        st.plotly_chart(fig, use_container_width=True)

        # ── Legend — competition guide colours ────────────────────────────────
        _is_lt = st.session_state.get("theme","light") == "light"
        _ltxt  = "#5c3a1e" if _is_lt else TEXT2
        _wclr  = "rgba(80,160,120,0.9)" if _is_lt else "rgba(100,255,218,0.8)"
        st.markdown(f"""<div style="display:flex;gap:.7rem;flex-wrap:wrap;margin-top:.25rem;
            padding:.35rem .5rem;border-radius:6px;
            background:{'rgba(255,252,248,0.7)' if _is_lt else 'rgba(10,25,47,0.5)'};
            border:1px solid {'rgba(160,100,60,0.15)' if _is_lt else 'rgba(100,255,218,0.08)'};">
  <span style="font-size:.62rem;color:{_ltxt};">●<span style="color:{GREEN};font-weight:700;"> Healthy</span> &lt;15 µg/m³</span>
  <span style="font-size:.62rem;color:{_ltxt};">●<span style="color:{AMBER};font-weight:700;"> Moderate</span> 15-35</span>
  <span style="font-size:.62rem;color:{_ltxt};">●<span style="color:{ORANGE};font-weight:700;"> Poor</span> 35-55</span>
  <span style="font-size:.62rem;color:{_ltxt};">●<span style="color:{RED};font-weight:700;"> Critical</span> 55-80</span>
  <span style="font-size:.62rem;color:{_ltxt};">●<span style="color:{PURPLE};font-weight:700;"> Hazardous</span> &gt;80</span>
  <span style="font-size:.62rem;color:{_wclr};">
    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="{_wclr}"
      stroke-width="2.5" stroke-linecap="round" style="vertical-align:middle;margin-right:2px;">
      <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
    </svg>{_t('wind_note')}
  </span>
  <span style="font-size:.62rem;color:{_ltxt};">● {_t('bubble_note')}</span>
</div>""", unsafe_allow_html=True)

        # ── City selector — Cameroon only ────────────────────────────────────
        st.markdown("<div style='margin-top:.6rem;'></div>", unsafe_allow_html=True)
        sec("Explore a City" if lang=="en" else "Explorer une Ville")

        # Group cities by region for the selectbox
        city_options = [""] + [
            f"{cname}  ({reg})"
            for reg, clist in CITIES.items()
            for cname, _, _ in clist
        ]
        sel_display = st.selectbox(
            "Select city for forecast & sparkline" if lang=="en"
            else "Sélectionner une ville pour prévision & graphique",
            city_options, key="ov_city_pick"
        )
        sel_fc = sel_display.split("  (")[0].strip() if sel_display else ""

        if sel_fc:
            pc1, pc2 = st.columns(2)
            with pc1:
                if st.button("Open Forecast" if lang=="en" else "Voir Prévision",
                             key="ov_fc_btn", use_container_width=True):
                    st.session_state.update({"page":"explorer","fc_city":sel_fc})
                    for reg, clist in CITIES.items():
                        if any(c[0]==sel_fc for c in clist):
                            st.session_state.fc_region = reg; break
                    st.rerun()

        # ── City sparkline ────────────────────────────────────────────────────
        detail_city = sel_fc  # sparkline driven by same selector
        if detail_city:
            cd = next((c for _, cl in CITIES.items() for c in cl if c[0]==detail_city), None)
            if cd:
                _, dlat, dlon = cd
                dreg = next((r for r, cl in CITIES.items() if any(c[0]==detail_city for c in cl)), "Centre")
                with st.spinner(_t("loading")):
                    fd2 = fetch_forecast(dlat, dlon)
                model, enc, fi = load_models()
                preds2 = predict_7day(fd2, detail_city, dreg, dlat, dlon, model, enc, fi) if fd2 and model else None
                if preds2:
                    dates2 = [p["date"] for p in preds2]; pms2 = [p["pm25"] for p in preds2]
                    fig_sp = go.Figure()
                    fig_sp.add_trace(go.Scatter(x=dates2, y=pms2, mode="lines+markers",
                        line=dict(color=TEAL, width=2),
                        marker=dict(size=9, color=[aqi(p)[1] for p in pms2],
                                    line=dict(color=TEAL, width=1.5)),
                        fill="tozeroy", fillcolor="rgba(100,255,218,0.06)",
                        hovertemplate="<b>%{x}</b><br>%{y:.1f} μg/m³<extra></extra>"))
                    fig_sp.add_hline(y=get_threshold(), line=dict(color=RED, width=1.5, dash="dash"),
                                     annotation_text=threshold_label(), annotation_font_color=RED,
                                     annotation_font_size=9)
                    fig_sp.update_layout(**PLO(height=155,
                        yaxis=dict(title="PM2.5"),
                        margin=dict(l=0,r=0,t=18,b=0), showlegend=False,
                        title=dict(text=f"7-Day — {detail_city}",
                                   font=dict(size=11, color=_ctxt2()), x=0)))
                    st.plotly_chart(fig_sp, use_container_width=True)

    # ── Right panel ───────────────────────────────────────────────────────────
    with right_col:

        # ── Circular AQI distribution ─────────────────────────────────────────
        sec("AQI Distribution" if lang=="en" else "Distribution IQA")
        st.plotly_chart(_circular_stats(_stats), use_container_width=True)

        # ── Mini KPI cards ────────────────────────────────────────────────────
        live_count = sum(1 for s in _stats.values() if s.get("live"))
        above_who  = sum(1 for s in _stats.values() if s["mean_pm25"] > get_threshold())
        mean_pm    = np.mean([s["mean_pm25"] for s in _stats.values()])
        kc1, kc2 = st.columns(2)
        with kc1:
            st.markdown(f"""<div style="background:{_cbg()};border:1px solid {_cborder()};
  border-radius:8px;padding:.5rem .7rem;text-align:center;margin-bottom:.4rem;">
  <div style="font-size:1.2rem;font-weight:700;font-family:'JetBrains Mono',monospace;
    color:{RED};">{above_who}</div>
  <div style="font-size:.52rem;color:{_ctxt2()};text-transform:uppercase;letter-spacing:.07em;">
    {"Above WHO" if lang=="en" else "Dépassant OMS"}</div>
</div>""", unsafe_allow_html=True)
        with kc2:
            st.markdown(f"""<div style="background:{_cbg()};border:1px solid {_cborder()};
  border-radius:8px;padding:.5rem .7rem;text-align:center;margin-bottom:.4rem;">
  <div style="font-size:1.2rem;font-weight:700;font-family:'JetBrains Mono',monospace;
    color:{_accent()};">{live_count}</div>
  <div style="font-size:.52rem;color:{_ctxt2()};text-transform:uppercase;letter-spacing:.07em;">
    {"Live Cities" if lang=="en" else "Villes en Direct"}</div>
</div>""", unsafe_allow_html=True)

        # ── Rankings ──────────────────────────────────────────────────────────
        sec(_t("most_polluted"))
        top8 = sorted(_stats.items(), key=lambda x: x[1]["mean_pm25"], reverse=True)[:8]
        mx   = top8[0][1]["mean_pm25"] if top8 else 1
        for i, (city, s) in enumerate(top8):
            _, col, _, _ = aqi(s["mean_pm25"])
            pct = s["mean_pm25"] / mx * 100
            live_dot = f' <span style="font-size:.5rem;color:{_accent()};">●</span>' if s.get("live") else ""
            st.markdown(f"""<div class="as-city-row">
  <span style="font-size:.58rem;color:{_ctxt2()};width:14px;">{i+1}</span>
  <span style="font-size:.72rem;flex:1;">{city}{live_dot}</span>
  <div style="flex:1;min-width:50px;height:3px;background:{_cborder()};border-radius:2px;margin:0 .4rem;overflow:hidden;">
    <div style="width:{pct:.0f}%;height:100%;background:{col};border-radius:2px;"></div></div>
  <span style="font-size:.66rem;font-family:'JetBrains Mono',monospace;color:{col};">{s['mean_pm25']:.1f}</span>
</div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:.6rem;'></div>", unsafe_allow_html=True)
        sec(_t("cleanest"))
        for i, (city, s) in enumerate(sorted(_stats.items(), key=lambda x: x[1]["mean_pm25"])[:5]):
            _, col, _, _ = aqi(s["mean_pm25"])
            pct = s["mean_pm25"] / 20 * 100
            st.markdown(f"""<div class="as-city-row">
  <span style="font-size:.58rem;color:{_ctxt2()};width:14px;">{i+1}</span>
  <span style="font-size:.72rem;flex:1;">{city}</span>
  <div style="flex:1;min-width:50px;height:3px;background:{_cborder()};border-radius:2px;margin:0 .4rem;overflow:hidden;">
    <div style="width:{pct:.0f}%;height:100%;background:{col};border-radius:2px;"></div></div>
  <span style="font-size:.66rem;font-family:'JetBrains Mono',monospace;color:{col};">{s['mean_pm25']:.1f}</span>
</div>""", unsafe_allow_html=True)

    # ── Regional bar charts ────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    sec(_t("per_region_analysis"))
    b1, b2 = st.columns(2)
    srt = sorted(REGIONS_DATA.items(), key=lambda x: x[1]["pm25"], reverse=True)
    with b1:
        fig_bar = go.Figure(go.Bar(
            y=[r[0] for r in srt], x=[r[1]["pm25"] for r in srt], orientation="h",
            marker=dict(color=[REGION_COLORS.get(r[0], TEAL) for r in srt], opacity=0.82),
            text=[f"{r[1]['pm25']:.1f}" for r in srt], textposition="outside",
            textfont=dict(color=_ctxt2(), size=10)))
        fig_bar.add_vline(x=get_threshold(), line=dict(color=RED,width=1.5,dash="dash"),
                          annotation_text=threshold_label(),annotation_font_color=RED,annotation_font_size=9)
        fig_bar.add_vline(x=WHO_ANN, line=dict(color=AMBER,width=1,dash="dot"),
                          annotation_text="WHO Annual (5)",annotation_font_color=AMBER,annotation_font_size=9)
        fig_bar.update_layout(**PLO(height=280, margin=dict(l=0,r=55,t=8,b=8),
            xaxis_title="Mean PM2.5 (μg/m³)", showlegend=False,
            yaxis=dict(gridcolor="rgba(0,0,0,0)")))
        st.plotly_chart(fig_bar, use_container_width=True)
    with b2:
        re = {"Far North":73,"North":66,"West":60,"North West":55,"East":49,"Adamawa":49,
              "Littoral":47,"South West":44,"Centre":42,"South":32}
        exc_lbl = "% Jours Dépassant OMS 24h" if lang=="fr" else "% Days Exceeding WHO 24h"
        fig_exc = go.Figure(go.Bar(
            y=list(re.keys()), x=list(re.values()), orientation="h",
            marker=dict(color=[REGION_COLORS.get(r, TEAL) for r in re], opacity=0.70),
            text=[f"{v:.0f}%" for v in re.values()], textposition="outside",
            textfont=dict(color=_ctxt2(), size=10)))
        fig_exc.update_layout(**PLO(height=280, margin=dict(l=0,r=55,t=8,b=8),
            xaxis=dict(title=exc_lbl,range=[0,100]),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"), showlegend=False))
        st.plotly_chart(fig_exc, use_container_width=True)

    # ── Monthly heatmap ────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
    sec(_t("pollution_heatmap"))
    months = (["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
              if lang=="fr" else
              ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"])
    _is_lt = st.session_state.get("theme","light") == "light"
    _hm_cs = ([[0.0,"#fdf8f2"],[0.2,"#f0d8c0"],[0.45,AMBER],[0.72,ORANGE],[1.0,RED]] if _is_lt
              else [[0.0,NAVY2],[0.2,BORDER],[0.45,AMBER],[0.72,ORANGE],[1.0,RED]])
    fig_h = go.Figure(data=go.Heatmap(
        z=list(MONTHLY_BY_REGION.values()), x=months, y=list(MONTHLY_BY_REGION.keys()),
        colorscale=_hm_cs,
        text=[[f"{v}" for v in row] for row in MONTHLY_BY_REGION.values()],
        texttemplate="%{text}", textfont={"size":10,"color":_ctxt()},
        hovertemplate="<b>%{y}</b> — %{x}<br>PM2.5: %{z:.0f} μg/m³<extra></extra>",
        colorbar=dict(title=dict(text="PM2.5<br>μg/m³", font=dict(color=_ctxt2())),
                      tickfont=dict(color=_ctxt2()))))
    fig_h.update_layout(**PLO(height=295, xaxis=dict(side="top")))
    st.plotly_chart(fig_h, use_container_width=True)
    info_box(_t("heatmap_guide"))

    st.markdown('</div>', unsafe_allow_html=True)
