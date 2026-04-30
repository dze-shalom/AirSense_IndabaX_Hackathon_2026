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
from components.ui import sec, card, info_box, _cbg, _cborder, _ctxt, _ctxt2, _accent
from utils.helpers import city_profile, health_impact
from utils.api import call_claude
from utils.models import get_alert_prob
from components.charts import PLO





def _t(key):
    lang = LNG()
    return T.get(lang, T["en"]).get(key, T["en"].get(key, key))


def page_science():
    art = load_artefacts()
    st.markdown('<div class="as-content">', unsafe_allow_html=True)

    tab_sh, tab_cl, tab_sp, tab_mc, tab_pol, tab_brief = st.tabs([
        _t("shap_tab"), _t("climate_tab_sci"), _t("spatial_tab"), _t("model_tab"),
        _t("policy_sim_tab"), _t("policy_brief_tab"),
    ])

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 1 — SHAP
    # ══════════════════════════════════════════════════════════════════════════
    with tab_sh:
        c1, c2 = st.columns(2)
        with c1: region = st.selectbox(_t("select_region"), list(CITIES.keys()), key="sh_reg2")
        with c2: city   = st.selectbox(_t("select_city"),   [c[0] for c in CITIES[region]], key="sh_city2")

        with st.spinner(_t("computing_shap")):
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

        sec(_t("per_region_shap"))
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

        with st.expander(f"{_t('deep_dive')} — {region}", expanded=False):
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
        sec(_t("climate_2050_hdr"))
        c1,c2,c3 = st.columns([2,1.5,1.5])
        with c1: ssp_sel = st.selectbox(_t("scenario_label"),list(SSP_RATES.keys()),index=1,key="cl_ssp2")
        with c2: yr_sel  = st.slider(_t("target_year"),2026,2100,2050,key="cl_yr2")
        with c3: all_ssp = st.checkbox(_t("compare_all_ssps"),value=True,key="cl_all2")

        BASE_YEAR = 2025
        _live = live_all()

        def project(base, reg, rate, yr):
            return round(base * (1 + rate * REGION_WARM.get(reg,1.0) * (yr-BASE_YEAR)/75), 2)

        rate = SSP_RATES[ssp_sel]
        sec(f"{_t('regional_projections')} — {ssp_sel} @ {yr_sel}")
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
        sec(_t("pm25_trajectory"))
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

        sec(f"{_t('projected_exceedance')} {yr_sel} — {ssp_sel}")
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
        sec(_t("spatial_hdr"))
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
            sec(_t("r2_by_level"))

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
            sec(_t("mean_mae_by_level"))
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
        sec(_t("spatial_results_by_city"))
        for entry in SPATIAL_GEN:
            lvl = entry["level"].split("—")[0].strip()
            col = level_colors.get(lvl, AMBER)
            r2_str = f"{entry['r2']:.3f}" if entry["r2"] else "—"
            quality = _t("quality_good") if entry["mae"]<7 else (_t("quality_fair") if entry["mae"]<12 else _t("quality_poor"))
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
        sec(_t("model_comparison_hdr"))
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
            _best_bg    = "rgba(100,255,218,0.06)" if st.session_state.get("theme","light")=="dark" else "rgba(80,160,100,0.06)"
            _card_bg    = _best_bg if best else _cbg()
            _border_col = "rgba(100,255,218,0.3)" if best else _cborder()
            _card_style = (f"background:{_card_bg};border:1px solid {_border_col};"
                           f"{'border-left:3px solid '+TEAL+';' if best else ''}"
                           f"border-radius:8px;padding:.6rem .9rem;margin-bottom:.3rem;"
                           f"display:flex;justify-content:space-between;align-items:center;"
                           f"flex-wrap:wrap;gap:.4rem;")
            _fw = "700" if best else "500"
            _val_col = TEAL if best else _ctxt()
            st.markdown(
                f'<div style="{_card_style}">'
                f'<div style="flex:1;min-width:200px;">'
                f'<span style="font-size:.78rem;font-weight:{_fw};color:{fc};">{row["model"]}</span>'
                f'<span style="font-size:.58rem;color:{fc};margin-left:.5rem;opacity:.7;">{fl}</span>'
                f'</div>'
                f'<div style="display:flex;gap:1.4rem;">'
                f'<div style="text-align:center;">'
                f'<div style="font-size:.58rem;color:{_ctxt2()};">Test MAE</div>'
                f'<div style="font-size:.82rem;font-weight:700;color:{_val_col};font-family:\'JetBrains Mono\',monospace;">{mae_str}</div>'
                f'</div>'
                f'<div style="text-align:center;">'
                f'<div style="font-size:.58rem;color:{_ctxt2()};">R²</div>'
                f'<div style="font-size:.82rem;font-weight:700;color:{_ctxt()};font-family:\'JetBrains Mono\',monospace;">{r2_str}</div>'
                f'</div>'
                f'<div style="text-align:center;">'
                f'<div style="font-size:.58rem;color:{_ctxt2()};">Harm MAE</div>'
                f'<div style="font-size:.82rem;font-weight:700;color:{ORANGE if hm_str != "—" else _ctxt2()};font-family:\'JetBrains Mono\',monospace;">{hm_str}</div>'
                f'</div>'
                f'</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        # MAE bar chart
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        sec(_t("mae_comparison"))
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

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 5 — POLICY SCENARIO SIMULATOR
    # ══════════════════════════════════════════════════════════════════════════
    with tab_pol:
        sec(_t("policy_sim_hdr"))
        lang = LNG()

        c1, c2 = st.columns(2)
        with c1: pol_region = st.selectbox(_t("select_region"), list(CITIES.keys()), key="pol_reg")
        with c2: pol_city   = st.selectbox(_t("select_city"),   [c[0] for c in CITIES[pol_region]], key="pol_city")

        with st.form("policy_sim_form"):
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                traffic_pct  = st.slider(_t("traffic_reduction"),  0, 80, 20, key="pol_traffic")
            with fc2:
                industry_pct = st.slider(_t("industry_reduction"), 0, 80, 10, key="pol_industry")
            with fc3:
                biomass_pct  = st.slider(_t("biomass_reduction"),  0, 60, 15, key="pol_biomass")
            submitted = st.form_submit_button(_t("simulate_btn"), use_container_width=True)

        # Always show results (recalculate on every render)
        _live_pol = live_all()
        base_pm = _live_pol.get(pol_city, CITY_STATS.get(pol_city, {})).get("mean_pm25", 25.0)
        profile  = city_profile(pol_city, pol_region, base_pm)
        src      = profile["src"]

        traffic_red  = base_pm * src.get("Traffic", 0.2)  * (traffic_pct / 100)
        industry_red = base_pm * src.get("Industry", 0.1) * (industry_pct / 100)
        biomass_red  = base_pm * src.get("Biomass Burning", src.get("Biomass", 0.2)) * (biomass_pct / 100)
        new_pm       = max(WHO_ANN, base_pm - traffic_red - industry_red - biomass_red)
        pm_delta     = base_pm - new_pm

        # Health impact difference
        hi_base = health_impact(base_pm)
        hi_new  = health_impact(new_pm)
        cases_prevented = round(hi_base[0] - hi_new[0], 1)

        # ── 4 metric cards ────────────────────────────────────────────────────
        m1, m2, m3, m4 = st.columns(4)
        _card_style = (f"background:{_cbg()};border:1px solid {_cborder()};"
                       f"border-radius:10px;padding:.75rem 1rem;text-align:center;")
        with m1:
            st.markdown(f'<div style="{_card_style}">'
                        f'<div style="font-size:.65rem;color:{_ctxt2()};">{_t("before_pm")} PM2.5</div>'
                        f'<div style="font-size:1.5rem;font-weight:800;color:{_ctxt()};">{base_pm:.1f}</div>'
                        f'<div style="font-size:.65rem;color:{_ctxt2()};">µg/m³</div>'
                        f'</div>', unsafe_allow_html=True)
        with m2:
            new_col = GREEN if new_pm < WHO_24H else AMBER if new_pm < 35 else RED
            st.markdown(f'<div style="{_card_style}">'
                        f'<div style="font-size:.65rem;color:{_ctxt2()};">{_t("after_pm")} PM2.5</div>'
                        f'<div style="font-size:1.5rem;font-weight:800;color:{new_col};">{new_pm:.1f}</div>'
                        f'<div style="font-size:.65rem;color:{_ctxt2()};">µg/m³</div>'
                        f'</div>', unsafe_allow_html=True)
        with m3:
            st.markdown(f'<div style="{_card_style}">'
                        f'<div style="font-size:.65rem;color:{_ctxt2()};">{_t("pm_reduction")}</div>'
                        f'<div style="font-size:1.5rem;font-weight:800;color:{TEAL};">−{pm_delta:.1f}</div>'
                        f'<div style="font-size:.65rem;color:{_ctxt2()};">µg/m³</div>'
                        f'</div>', unsafe_allow_html=True)
        with m4:
            st.markdown(f'<div style="{_card_style}">'
                        f'<div style="font-size:.65rem;color:{_ctxt2()};">{_t("lives_saved")}</div>'
                        f'<div style="font-size:1.5rem;font-weight:800;color:{GREEN};">{cases_prevented:.1f}</div>'
                        f'<div style="font-size:.65rem;color:{_ctxt2()};"> / 10k / yr</div>'
                        f'</div>', unsafe_allow_html=True)

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)

        # ── Before/after source breakdown bar chart ───────────────────────────
        src_keys   = [k for k, v in src.items() if v > 0.02]
        before_vals = [src[k] * base_pm for k in src_keys]

        # Adjusted source contributions after policy levers
        after_src = dict(src)
        if "Traffic" in after_src:
            raw_t = after_src["Traffic"] * base_pm * (1 - traffic_pct / 100)
            after_src["Traffic"] = raw_t / base_pm if base_pm > 0 else after_src["Traffic"]
        if "Industry" in after_src:
            raw_i = after_src["Industry"] * base_pm * (1 - industry_pct / 100)
            after_src["Industry"] = raw_i / base_pm if base_pm > 0 else after_src["Industry"]
        for bk in ("Biomass Burning", "Biomass"):
            if bk in after_src:
                raw_b = after_src[bk] * base_pm * (1 - biomass_pct / 100)
                after_src[bk] = raw_b / base_pm if base_pm > 0 else after_src[bk]

        after_vals = [after_src.get(k, src[k]) * new_pm for k in src_keys]
        bar_colors = [TEAL, AMBER, ORANGE, RED, PURPLE, _ctxt2()][:len(src_keys)]

        fig_pol = go.Figure()
        fig_pol.add_trace(go.Bar(
            name=_t("before_pm"), y=src_keys, x=before_vals,
            orientation="h", marker=dict(color=bar_colors, opacity=0.55),
            hovertemplate="%{y}: %{x:.2f} µg/m³<extra>Before</extra>"))
        fig_pol.add_trace(go.Bar(
            name=_t("after_pm"), y=src_keys, x=after_vals,
            orientation="h", marker=dict(color=bar_colors, opacity=0.9),
            hovertemplate="%{y}: %{x:.2f} µg/m³<extra>After</extra>"))
        fig_pol.update_layout(**PLO(
            height=280, barmode="group",
            xaxis=dict(gridcolor=_cborder(), title="PM2.5 contribution (µg/m³)"),
            yaxis=dict(gridcolor="rgba(0,0,0,0)"),
            legend=dict(font=dict(size=9, color=_ctxt2()), bgcolor="rgba(0,0,0,0)",
                        orientation="h", yanchor="bottom", y=1.02),
        ))
        st.plotly_chart(fig_pol, use_container_width=True)

        # ── AQI advisory text ─────────────────────────────────────────────────
        if new_pm < WHO_24H:
            adv_col, adv_key = GREEN, "health_good"
        elif new_pm < 35:
            adv_col, adv_key = AMBER, "health_moderate"
        elif new_pm < 55:
            adv_col, adv_key = ORANGE, "health_poor"
        elif new_pm < 80:
            adv_col, adv_key = RED, "health_very_poor"
        else:
            adv_col, adv_key = PURPLE, "health_hazardous"

        st.markdown(
            f'<div style="background:{adv_col}18;border:1px solid {adv_col}44;'
            f'border-left:3px solid {adv_col};border-radius:8px;'
            f'padding:.65rem .9rem;margin-top:.5rem;font-size:.78rem;color:{_ctxt()};">'
            f'<strong style="color:{adv_col};">Advisory (post-policy):</strong> {_t(adv_key)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 6 — AI POLICY BRIEF
    # ══════════════════════════════════════════════════════════════════════════
    with tab_brief:
        sec(_t("policy_brief_hdr"))
        lang = LNG()

        st.markdown(f'<div style="font-size:.78rem;color:{_ctxt2()};margin-bottom:.8rem;">'
                    f'{_t("policy_context")}</div>', unsafe_allow_html=True)

        b1, b2 = st.columns(2)
        with b1: brief_region = st.selectbox(_t("select_region"), list(CITIES.keys()), key="brief_reg")
        with b2: brief_city   = st.selectbox(_t("select_city"),   [c[0] for c in CITIES[brief_region]], key="brief_city")

        if st.button(_t("generate_brief_btn"), use_container_width=True, key="gen_brief_btn"):
            with st.spinner(_t("generating_brief")):
                _live_brief = live_all()
                pm25_brief  = _live_brief.get(brief_city, CITY_STATS.get(brief_city, {})).get("mean_pm25", 25.0)
                art_brief   = load_artefacts()
                prob_brief  = get_alert_prob(pm25_brief, art_brief)
                prof_brief  = city_profile(brief_city, brief_region, pm25_brief)

                src_brief   = prof_brief["src"]
                top_sources = ", ".join(
                    f"{k} {v*100:.0f}%"
                    for k, v in sorted(src_brief.items(), key=lambda x: -x[1])
                    if v > 0.05
                )

                prompt = (
                    f"Write a 2-paragraph policy brief for Cameroon health officials about air quality "
                    f"in {brief_city} ({brief_region} region). "
                    f"Current PM2.5: {pm25_brief:.1f} µg/m³ (WHO 24h limit: 15 µg/m³). "
                    f"Exceedance probability: {prob_brief*100:.0f}%. "
                    f"Main pollution sources: {top_sources}. "
                    f"Paragraph 1: current situation and health risk. "
                    f"Paragraph 2: 3 concrete policy recommendations. "
                    f"Be specific to Cameroon context. Keep it under 200 words."
                )

                brief_text = call_claude(prompt, brief_city, brief_region, pm25_brief, lang)

            # Display brief in styled card
            if brief_text:
                st.session_state["_last_brief"] = brief_text
                st.session_state["_last_brief_city"] = brief_city

        # Render the brief if stored
        brief_text = st.session_state.get("_last_brief", "")
        brief_city_stored = st.session_state.get("_last_brief_city", "")
        if brief_text and brief_city_stored == brief_city:
            _acc = _accent()
            st.markdown(
                f'<div style="background:{_cbg()};border:1px solid {_cborder()};"
                f"border-left:4px solid {_acc};border-radius:10px;"
                f"padding:1.1rem 1.3rem;margin-top:.8rem;">'
                f'<div style="font-size:.65rem;font-weight:700;letter-spacing:.08em;'
                f'color:{_acc};text-transform:uppercase;margin-bottom:.6rem;">'
                f'POLICY BRIEF — {brief_city.upper()}</div>'
                f'<div style="font-size:.82rem;line-height:1.7;color:{_ctxt()};">'
                f'{brief_text.replace(chr(10), "<br>")}'
                f'</div>'
                f'<div style="margin-top:.75rem;font-size:.65rem;color:{_ctxt2()};">'
                f'💡 Tip: Copy the text above to share with health officials.</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # WhatsApp share link
            wa_text = (
                f"AirSense Policy Brief — {brief_city}: "
                f"PM2.5 {st.session_state.get('_last_brief_pm25', pm25_brief):.1f} µg/m³. "
                f"{brief_text[:200]}…"
            )
            import urllib.parse
            wa_url = "https://wa.me/?text=" + urllib.parse.quote(wa_text)
            st.markdown(
                f'<a href="{wa_url}" target="_blank" style="display:inline-block;margin-top:.5rem;'
                f'background:#25D366;color:#fff;border-radius:6px;padding:.35rem .9rem;'
                f'font-size:.72rem;font-weight:600;text-decoration:none;">'
                f'Share via WhatsApp</a>',
                unsafe_allow_html=True,
            )
        elif not brief_text:
            st.markdown(
                f'<div style="background:{_cbg()};border:1px dashed {_cborder()};'
                f'border-radius:10px;padding:1.5rem;text-align:center;'
                f'font-size:.78rem;color:{_ctxt2()};">'
                f'Press <strong>{_t("generate_brief_btn")}</strong> to generate an AI-powered policy brief.'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)
