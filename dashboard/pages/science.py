def _norm_shap(data):
    """Normalise SHAP data to list of (feature, value) tuples regardless of input format."""
    if not data:
        return []
    if isinstance(data, dict):
        # Dict keyed by feature name: {"year": 0.14, ...}
        return sorted(data.items(), key=lambda x: float(x[1]), reverse=True)
    if isinstance(data, (list, tuple)):
        try:
            first = data[0]
        except (IndexError, KeyError):
            return []
        if isinstance(first, dict):
            return [(d.get("feature", d.get(0,"")), d.get("value", d.get(1,0))) for d in data]
        if isinstance(first, (list, tuple)) and len(first) >= 2:
            return [(d[0], d[1]) for d in data]
        return list(data)
    return []


"""pages/science.py — SHAP, Climate 2050, Spatial Generalization, Model Comparison."""
import streamlit as st
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import *
from utils.helpers import aqi, LNG, get_threshold, threshold_label
from utils.models import load_artefacts
from utils.live_data import compute_live_shap, live_all
from components.ui import sec, card, info_box, _cbg, _cborder, _ctxt, _ctxt2
from components.charts import PLO





def _t(key):
    lang = LNG()
    return T.get(lang, T["en"]).get(key, T["en"].get(key, key))


def page_science():
    art = load_artefacts()
    st.markdown('<div class="as-content">', unsafe_allow_html=True)

    tab_sh, tab_cl, tab_sp, tab_mc = st.tabs([
        _t("shap_tab"), _t("climate_tab_sci"), _t("spatial_tab"), _t("model_tab"),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — SHAP
    # ══════════════════════════════════════════════════════════════════════════
    with tab_sh:
        c1, c2 = st.columns(2)
        with c1: region = st.selectbox("Region", list(CITIES.keys()), key="sh_reg2")
        with c2: city   = st.selectbox("City",   [c[0] for c in CITIES[region]], key="sh_city2")

        with st.spinner("Computing live SHAP values…"):
            live_shap = compute_live_shap()

        if live_shap:
            region_shap = live_shap; data_src = "live"
        elif art.get("region_shap"):
            region_shap = art["region_shap"]; data_src = "artefact"
        else:
            region_shap = REGION_SHAP_FALLBACK; data_src = "static"

        badge_cfg = {
            "live":     (TEAL,  "🟢 Live — computed from today's Open-Meteo forecast"),
            "artefact": (AMBER, "🟡 From saved region_shap.pkl artefact"),
            "static":   (_ctxt2(), "⚪ Static fallback — model artefacts not found"),
        }[data_src]
        st.markdown(f'<div style="font-size:.62rem;color:{badge_cfg[0]};margin-bottom:.6rem;">'
                    f'{badge_cfg[1]}</div>', unsafe_allow_html=True)

        sec("Per-Region SHAP — Climate Drivers")
        regions_list = sorted(region_shap.keys())
        n_cols = 5
        fig_grid = make_subplots(rows=2, cols=n_cols, subplot_titles=regions_list[:10],
                                 horizontal_spacing=0.06, vertical_spacing=0.18)
        for idx, reg in enumerate(regions_list[:10]):
            rw = idx // n_cols + 1; cp = idx % n_cols + 1
            data = _norm_shap(region_shap[reg])
            feats = [d[0] for d in data[:7]]; vals = [d[1] for d in data[:7]]
            color = REGION_COLORS.get(reg, TEAL)
            fig_grid.add_trace(go.Bar(y=feats[::-1], x=vals[::-1], orientation="h",
                marker=dict(color=color, opacity=0.82), showlegend=False,
                hovertemplate=f"<b>{reg}</b><br>%{{y}}: %{{x:.3f}}<extra></extra>"), row=rw, col=cp)
        fig_grid.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            height=540, showlegend=False, margin=dict(l=0,r=0,t=40,b=0),
            font=dict(family="Open Sans",color=_ctxt2(),size=8))
        for i in range(1,11):
            fig_grid.update_xaxes(gridcolor=_cborder(),gridwidth=0.5,row=(i-1)//5+1,col=(i-1)%5+1)
            fig_grid.update_yaxes(gridcolor="rgba(0,0,0,0)",row=(i-1)//5+1,col=(i-1)%5+1)
        st.plotly_chart(fig_grid, use_container_width=True)

        sec(f"Deep-Dive — {region}")
        reg_data = _norm_shap(region_shap.get(region, REGION_SHAP_FALLBACK.get(region, [])))
        if reg_data:
            max_v = reg_data[0][1] if reg_data and len(reg_data[0]) > 1 and reg_data[0][1] > 0 else 1.0
            for feat, val in reg_data:
                pct  = val / max_v * 100
                col  = REGION_COLORS.get(region, TEAL)
                desc = SHAP_DESC.get(feat, feat)
                st.markdown(f"""<div style="display:flex;align-items:center;gap:.85rem;padding:.5rem 0;
  border-bottom:1px solid {_cborder()};">
  <span style="font-size:.75rem;font-weight:600;width:165px;flex-shrink:0;">{feat}</span>
  <div style="flex:1;height:7px;background:{_cborder()};border-radius:3px;overflow:hidden;">
    <div style="width:{pct:.0f}%;height:100%;background:{col};border-radius:3px;"></div></div>
  <span style="font-size:.72rem;font-weight:700;width:50px;text-align:right;color:{col};">{val:.3f}</span>
  <span style="font-size:.65rem;color:{_ctxt2()};flex:1;">{desc}</span>
</div>""", unsafe_allow_html=True)
        info_box("<strong>Key finding:</strong> <em>year</em> dominates 7 of 10 regions — "
                 "a genuine multi-year pollution trend. <em>South</em> driven by <em>latitude</em> (SHAP≈0.23). "
                 "<em>West</em> flags <em>region_enc</em> — highland burning not in weather data.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 2 — CLIMATE 2050
    # ══════════════════════════════════════════════════════════════════════════
    with tab_cl:
        sec("Climate 2050 PM2.5 Projection — CMIP6 SSP Scenarios")
        st.markdown(f"<div style='font-size:.76rem;color:{_ctxt2()};margin-bottom:.9rem;'>"
                    "IPCC AR6 warming rates × empirical PM2.5/temperature sensitivity × "
                    "regional amplification. Indicative — not certified climate model output.</div>",
                    unsafe_allow_html=True)
        c1,c2,c3 = st.columns([2,1.5,1.5])
        with c1: ssp_sel = st.selectbox("Scenario",list(SSP_RATES.keys()),index=1,key="cl_ssp2")
        with c2: yr_sel  = st.slider("Target Year",2026,2100,2050,key="cl_yr2")
        with c3: all_ssp = st.checkbox("Compare all SSPs",value=True,key="cl_all2")

        BASE_YEAR = 2025
        _live = live_all()

        def project(base, reg, rate, yr):
            return round(base * (1 + rate * REGION_WARM.get(reg,1.0) * (yr-BASE_YEAR)/75), 2)

        rate = SSP_RATES[ssp_sel]
        sec(f"Regional Projections — {ssp_sel} @ {yr_sel}")
        reg_rows = []
        for reg, rd in sorted(REGIONS_DATA.items(), key=lambda x: x[1]["pm25"], reverse=True):
            rc   = [c[0] for c in CITIES.get(reg,[])]
            lv   = [_live[c]["mean_pm25"] for c in rc if c in _live]
            base = float(np.mean(lv)) if lv else rd["pm25"]
            proj = project(base, reg, rate, yr_sel)
            reg_rows.append((reg, base, proj, (proj-base)/base*100))

        cols = st.columns(2)
        for i, (reg, base, proj, chg) in enumerate(reg_rows):
            c = REGION_COLORS.get(reg, TEAL)
            _, aqi_col, _, _ = aqi(proj)
            with cols[i%2]:
                st.markdown(f"""<div style="background:{_cbg()};border:1px solid {_cborder()};
  border-left:3px solid {c};border-radius:8px;padding:.65rem .85rem;
  margin-bottom:.4rem;display:flex;justify-content:space-between;align-items:center;">
  <div>
    <div style="font-size:.78rem;font-weight:700;color:{c};">{reg}</div>
    <div style="font-size:.62rem;color:{_ctxt2()};margin-top:.15rem;">
      Baseline: {base:.1f} → <strong style="color:{aqi_col};">{proj:.1f} μg/m³</strong>
    </div>
  </div>
  <div style="text-align:right;">
    <div style="font-size:1.1rem;font-weight:800;color:{'#f87171' if chg>0 else GREEN};">
      {"↑" if chg>0 else "↓"}{abs(chg):.1f}%
    </div>
    <div style="font-size:.55rem;color:{_ctxt2()};">by {yr_sel}</div>
  </div>
</div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        sec("PM2.5 Trajectory 2025 → 2100")
        years = list(range(BASE_YEAR, 2101, 5))
        top3  = [r[0] for r in sorted(REGIONS_DATA.items(), key=lambda x: x[1]["pm25"], reverse=True)[:3]]
        fig_ts = go.Figure()
        ssps_to_plot = list(SSP_RATES.keys()) if all_ssp else [ssp_sel]
        for ssp_k in ssps_to_plot:
            r_ssp = SSP_RATES[ssp_k]; col = SSP_COLORS[ssp_k]
            for ri, reg in enumerate(top3):
                rc   = [c[0] for c in CITIES.get(reg,[])]
                lv   = [_live[c]["mean_pm25"] for c in rc if c in _live]
                base = float(np.mean(lv)) if lv else REGIONS_DATA[reg]["pm25"]
                traj = [project(base, reg, r_ssp, y) for y in years]
                fig_ts.add_trace(go.Scatter(x=years, y=traj, mode="lines",
                    line=dict(color=col, width=2 if ri==0 else 1.2, dash=["solid","dash","dot"][ri]),
                    name=f"{ssp_k[:8]} · {reg}",
                    hovertemplate=f"<b>{ssp_k[:9]} · {reg}</b><br>%{{x}}: %{{y:.1f}} μg/m³<extra></extra>"))
        fig_ts.add_hline(y=get_threshold(),line=dict(color=RED,width=1.5,dash="dash"),
                         annotation_text=threshold_label(),annotation_font_color=RED,annotation_font_size=9)
        fig_ts.add_hline(y=WHO_ANN,line=dict(color=AMBER,width=1,dash="dot"),
                         annotation_text="WHO Annual (5)",annotation_font_color=AMBER,annotation_font_size=9)
        fig_ts.add_vrect(x0=BASE_YEAR,x1=BASE_YEAR+1,fillcolor="rgba(100,255,218,0.07)",line_width=0,
                         annotation_text="Now",annotation_font_color=TEAL,annotation_font_size=9)
        fig_ts.update_layout(**PLO(height=320,
            yaxis=dict(gridcolor=_cborder(),title="PM2.5 (μg/m³)"),
            xaxis=dict(gridcolor=_cborder(),dtick=10,title="Year"),
            legend=dict(font=dict(size=8,color=_ctxt2()),bgcolor="rgba(0,0,0,0)",orientation="h",yanchor="bottom",y=1.02),
            hovermode="x unified"))
        st.plotly_chart(fig_ts, use_container_width=True)

        sec(f"Projected WHO Exceedance by {yr_sel} — {ssp_sel}")
        bar_regs, bar_now, bar_fut = [], [], []
        for reg, rd in sorted(REGIONS_DATA.items(), key=lambda x: x[1]["pm25"], reverse=True):
            rc   = [c[0] for c in CITIES.get(reg,[])]
            lv   = [_live[c]["mean_pm25"] for c in rc if c in _live]
            base = float(np.mean(lv)) if lv else rd["pm25"]
            proj = project(base, reg, SSP_RATES[ssp_sel], yr_sel)
            exc_now = rd.get("who_exc", min(base/get_threshold()*60,100))
            bar_regs.append(reg); bar_now.append(round(exc_now,1)); bar_fut.append(round(min(exc_now*(proj/base),100),1))
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(name="Today",x=bar_regs,y=bar_now,
            marker=dict(color=TEAL2,opacity=0.75),
            text=[f"{v:.0f}%" for v in bar_now],textposition="outside",textfont=dict(size=9,color=_ctxt2())))
        fig_bar.add_trace(go.Bar(name=str(yr_sel),x=bar_regs,y=bar_fut,
            marker=dict(color=SSP_COLORS[ssp_sel],opacity=0.82),
            text=[f"{v:.0f}%" for v in bar_fut],textposition="outside",textfont=dict(size=9,color=_ctxt2())))
        fig_bar.update_layout(**PLO(height=260,barmode="group",
            yaxis=dict(gridcolor=_cborder(),title="% days exceeding WHO 24h",range=[0,115]),
            xaxis=dict(gridcolor="rgba(0,0,0,0)"),legend=dict(font=dict(size=9,color=_ctxt2()),bgcolor="rgba(0,0,0,0)")))
        st.plotly_chart(fig_bar, use_container_width=True)
        fn_pct = SSP_RATES[ssp_sel]*REGION_WARM.get("Far North",1)*((yr_sel-BASE_YEAR)/75)*100
        info_box(f"<strong>Scenario: {ssp_sel}</strong> — {SSP_RATES[ssp_sel]:.2f} warming/decade. "
                 f"<strong>Far North rises by ~{fn_pct:.0f}% by {yr_sel}</strong> under this scenario.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — SPATIAL GENERALIZATION
    # ══════════════════════════════════════════════════════════════════════════
    with tab_sp:
        sec("Spatial Generalization — Can the Model Predict Cities It Has Never Seen?")
        st.markdown(f"""<div style="font-size:.78rem;color:{_ctxt2()};margin-bottom:1rem;line-height:1.6;">
The model was trained on <strong>40 Cameroonian cities</strong>. To test generalization,
it was applied to unseen cities at three difficulty levels:<br>
<strong style="color:{GREEN};">L1</strong> — Cameroon cities not in training set &nbsp;·&nbsp;
<strong style="color:{AMBER};">L2</strong> — Cross-border cities (N'Djamena, Chad) &nbsp;·&nbsp;
<strong style="color:{RED};">L3</strong> — Fully out-of-domain (Nairobi, Kenya)
</div>""", unsafe_allow_html=True)

        level_colors = {"L1":GREEN,"L2":AMBER,"L3":RED}

        # ── Map + donut side by side ──────────────────────────────────────────
        map_col, donut_col = st.columns([1.7, 1])

        with map_col:
            fig_sp = go.Figure()
            for reg, clist in CITIES.items():
                for cname, clat, clon in clist:
                    fig_sp.add_trace(go.Scattermapbox(
                        lat=[clat], lon=[clon], mode="markers",
                        marker=dict(size=7, color=TEAL, opacity=0.35),
                        hovertemplate=f"<b>{cname}</b><br>Training city<extra></extra>",
                        showlegend=False, name="train"))
            for entry in SPATIAL_GEN:
                lvl = entry["level"].split("—")[0].strip()
                col = level_colors.get(lvl, AMBER)
                r2_str = f"{entry['r2']:.3f}" if entry["r2"] else "—"
                fig_sp.add_trace(go.Scattermapbox(
                    lat=[entry["lat"]], lon=[entry["lon"]], mode="markers+text",
                    marker=dict(size=18, color=col, opacity=0.9),
                    text=[entry["city"]], textposition="top right",
                    textfont=dict(size=10, color=_ctxt(), family="Open Sans"),
                    hovertemplate=(f"<b>{entry['city']}</b><br>{entry['level']}<br>"
                                   f"MAE: {entry['mae']:.2f} μg/m³<br>R²: {r2_str}<extra></extra>"),
                    showlegend=False, name=entry["city"]))
            fig_sp.update_layout(
                mapbox=dict(style="carto-darkmatter", center=dict(lat=6, lon=15), zoom=3.5),
                **PLO(height=360, margin=dict(l=0,r=0,t=0,b=0), showlegend=False))
            st.plotly_chart(fig_sp, use_container_width=True)

        with donut_col:
            sec("R² by Generalization Level")

            # Compute average R² per level for donut
            from collections import defaultdict
            level_r2   = defaultdict(list)
            level_mae  = defaultdict(list)
            level_name = {"L1":"L1 — Cameroon","L2":"L2 — Cross-border","L3":"L3 — Out-of-domain"}
            for entry in SPATIAL_GEN:
                lvl = entry["level"].split("—")[0].strip()
                if entry["r2"]: level_r2[lvl].append(entry["r2"])
                level_mae[lvl].append(entry["mae"])

            donut_labels  = [level_name[lvl] for lvl in ["L1","L2","L3"]]
            donut_r2_vals = [
                round(sum(level_r2["L1"])/len(level_r2["L1"]),3) if level_r2["L1"] else 0,
                round(sum(level_r2["L2"])/len(level_r2["L2"]),3) if level_r2["L2"] else 0,
                round(sum(level_r2["L3"])/len(level_r2["L3"]),3) if level_r2["L3"] else 0,
            ]
            donut_mae_vals = [
                round(sum(level_mae["L1"])/len(level_mae["L1"]),2) if level_mae["L1"] else 0,
                round(sum(level_mae["L2"])/len(level_mae["L2"]),2) if level_mae["L2"] else 0,
                round(sum(level_mae["L3"])/len(level_mae["L3"]),2) if level_mae["L3"] else 0,
            ]
            donut_colors = [GREEN, AMBER, RED]

            # R² donut — slice size proportional to R² value
            fig_donut = go.Figure(go.Pie(
                labels=donut_labels,
                values=donut_r2_vals,
                marker=dict(colors=donut_colors,
                            line=dict(color=_cbg(), width=3)),
                hole=0.60,
                direction="clockwise",
                sort=False,
                textinfo="label+percent",
                textfont=dict(size=9, color=_ctxt(), family="Open Sans"),
                hovertemplate=(
                    "<b>%{label}</b><br>"
                    "Mean R²: %{value:.3f}<br>"
                    "Share of accuracy: %{percent}<extra></extra>"
                ),
                rotation=90,
            ))
            # Centre annotation — best R²
            best_lvl  = max(zip(donut_r2_vals, donut_labels))[1]
            best_r2   = max(donut_r2_vals)
            fig_donut.add_annotation(
                text=f"<b>{best_r2:.3f}</b><br><span style='font-size:9px'>Best R²<br>{best_lvl[:2]}</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(color=_ctxt(), size=12), align="center"
            )
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                height=220,
                margin=dict(l=0, r=0, t=8, b=0),
                showlegend=False,
                font=dict(family="Open Sans", color=_ctxt2()),
            )
            st.plotly_chart(fig_donut, use_container_width=True)

            # MAE bar chart below the donut
            sec("Mean MAE by Level")
            fig_mae = go.Figure(go.Bar(
                x=["L1","L2","L3"],
                y=donut_mae_vals,
                marker=dict(color=donut_colors, opacity=0.85),
                text=[f"{v:.2f}" for v in donut_mae_vals],
                textposition="outside",
                textfont=dict(size=10, color=_ctxt2()),
                hovertemplate="<b>%{x}</b><br>Mean MAE: %{y:.2f} μg/m³<extra></extra>",
            ))
            fig_mae.add_hline(y=MODEL_MAE, line=dict(color=TEAL, width=1.5, dash="dash"),
                              annotation_text=f"Train MAE ({MODEL_MAE})",
                              annotation_font_color=TEAL, annotation_font_size=9)
            fig_mae.update_layout(**PLO(
                height=180,
                yaxis=dict(gridcolor=_cborder(), title="MAE (μg/m³)", range=[0, 16]),
                xaxis=dict(gridcolor="rgba(0,0,0,0)"),
                showlegend=False,
                margin=dict(l=0, r=0, t=18, b=0),
            ))
            st.plotly_chart(fig_mae, use_container_width=True)

        # ── Results cards ─────────────────────────────────────────────────────
        sec("Generalization Results by City")
        for entry in SPATIAL_GEN:
            lvl = entry["level"].split("—")[0].strip()
            col = level_colors.get(lvl, AMBER)
            r2_str = f"{entry['r2']:.3f}" if entry["r2"] else "—"
            quality = "Good" if entry["mae"]<7 else ("Fair" if entry["mae"]<12 else "Poor")
            q_color = GREEN if quality=="Good" else (AMBER if quality=="Fair" else RED)
            st.markdown(f"""<div style="background:{_cbg()};border:1px solid {_cborder()};
  border-left:3px solid {col};border-radius:8px;padding:.65rem .9rem;
  margin-bottom:.3rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;">
  <div>
    <div style="font-size:.82rem;font-weight:700;color:{col};">{entry['city']}</div>
    <div style="font-size:.62rem;color:{_ctxt2()};">{entry['level']}</div>
  </div>
  <div style="display:flex;gap:1.4rem;align-items:center;">
    <div style="text-align:center;">
      <div style="font-size:.62rem;color:{_ctxt2()};">MAE</div>
      <div style="font-size:.88rem;font-weight:700;color:{_ctxt()};
        font-family:'JetBrains Mono',monospace;">{entry['mae']:.2f}</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:.62rem;color:{_ctxt2()};">R²</div>
      <div style="font-size:.88rem;font-weight:700;color:{_ctxt()};
        font-family:'JetBrains Mono',monospace;">{r2_str}</div>
    </div>
    <div style="background:{q_color}22;border:1px solid {q_color}55;color:{q_color};
      border-radius:4px;padding:.15rem .45rem;font-size:.65rem;font-weight:700;">
      {quality}
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        info_box("<strong>Key finding:</strong> The model generalises well within Cameroon (MAE 3.7–6.6 μg/m³) "
                 "and neighbouring regions (Chad). Performance degrades for fully out-of-domain cities like Nairobi "
                 "— expected given the model was calibrated on Central/West African aerosol regimes.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 4 — MODEL COMPARISON
    # ══════════════════════════════════════════════════════════════════════════
    with tab_mc:
        sec("Master Model Comparison — IndabaX 2026")
        st.markdown(f"<div style='font-size:.76rem;color:{_ctxt2()};margin-bottom:.9rem;'>"
                    "All models evaluated on the same held-out test set "
                    "(17,840 rows · 2024-10-01 → 2025-12-20 · 100% CAMS real data).</div>",
                    unsafe_allow_html=True)

        flag_colors = {"baseline":_ctxt2(),"primary":TEAL,"ensemble":AMBER,"deep":PURPLE}
        flag_labels = {"baseline":"Baseline","primary":"Primary","ensemble":"Ensemble","deep":"Deep Learning"}

        for row in MODEL_COMPARISON:
            fc = flag_colors.get(row["flag"], _ctxt2())
            fl = flag_labels.get(row["flag"], "")
            mae_str = f"{row['mae']:.3f}" if row["mae"] else "—"
            r2_str  = f"{row['r2']:.3f}"  if row["r2"]  else "—"
            hm_str  = f"{row['harm_mae']:.2f}" if row["harm_mae"] else "—"
            best = row["flag"] == "primary" and row["mae"] and row["mae"] < 6.0
            _best_bg     = "rgba(100,255,218,0.06)" if st.session_state.get("theme","light")=="dark" else "rgba(80,160,100,0.06)"
            _border_col  = "rgba(100,255,218,0.3)" if best else _cborder()
            _left_border = f"border-left:3px solid {TEAL};" if best else ""
            st.markdown(f"""<div style="background:{_best_bg if best else _cbg()};
  border:1px solid {_border_col};
  {_left_border}
  border-radius:8px;padding:.6rem .9rem;margin-bottom:.3rem;
  display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.4rem;">
  <div style="flex:1;min-width:200px;">
    <span style="font-size:.78rem;font-weight:{'700' if best else '500'};color:{fc};">{row['model']}</span>
    <span style="font-size:.58rem;color:{fc};margin-left:.5rem;opacity:.7;">{fl}</span>
  </div>
  <div style="display:flex;gap:1.4rem;">
    <div style="text-align:center;">
      <div style="font-size:.58rem;color:{_ctxt2()};">Test MAE</div>
      <div style="font-size:.82rem;font-weight:700;color:{TEAL if best else _ctxt()};
        font-family:'JetBrains Mono',monospace;">{mae_str}</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:.58rem;color:{_ctxt2()};">R²</div>
      <div style="font-size:.82rem;font-weight:700;color:{_ctxt()};
        font-family:'JetBrains Mono',monospace;">{r2_str}</div>
    </div>
    <div style="text-align:center;">
      <div style="font-size:.58rem;color:{_ctxt2()};">Harm MAE</div>
      <div style="font-size:.82rem;font-weight:700;color:{ORANGE if hm_str!='—' else _ctxt2()};
        font-family:'JetBrains Mono',monospace;">{hm_str}</div>
    </div>
  </div>
</div>""", unsafe_allow_html=True)

        # MAE bar chart
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        sec("MAE Comparison")
        valid = [r for r in MODEL_COMPARISON if r["mae"]]
        fig_mc = go.Figure(go.Bar(
            x=[r["model"][:30] for r in valid],
            y=[r["mae"] for r in valid],
            marker=dict(color=[flag_colors[r["flag"]] for r in valid], opacity=0.85),
            text=[f"{r['mae']:.2f}" for r in valid],
            textposition="outside", textfont=dict(size=9, color=_ctxt2()),
            hovertemplate="<b>%{x}</b><br>MAE: %{y:.3f} μg/m³<extra></extra>"))
        fig_mc.add_hline(y=7.521, line=dict(color=ORANGE,width=1.5,dash="dot"),
                         annotation_text="City-month baseline (7.52)",annotation_font_color=ORANGE,annotation_font_size=9)
        fig_mc.update_layout(**PLO(height=280,
            yaxis=dict(gridcolor=_cborder(),title="Test MAE (μg/m³)"),
            xaxis=dict(tickangle=-25,gridcolor="rgba(0,0,0,0)"),showlegend=False))
        st.plotly_chart(fig_mc, use_container_width=True)

        info_box("<strong>XGBoost CAMS-only (MAE=6.231)</strong> is the primary model — "
                 "trained only on real CAMS measurements, no proxy circularity. "
                 "The two-stage Harmattan model achieves the best Harmattan-season performance. "
                 "The Transformer provides interpretable multi-day uncertainty but higher MAE than XGBoost.")

    st.markdown('</div>', unsafe_allow_html=True)
