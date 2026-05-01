"""pages/alerts.py"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import urllib.parse as _up

from config import *
from utils.live_data import live_all, live_city
from utils.helpers import (aqi, compute_bfai, bfai_label, bfai_col,
                            classify_source, health_impact, city_profile,
                            SOURCE_LABELS, SOURCE_COLORS, LNG,
                            get_threshold, threshold_label)
from utils.models import (load_models, load_artefacts, get_conf_interval,
                           get_alert_prob, predict_7day, infer_region_from_lat)
from utils.api import fetch_forecast, geocode_city, wmo_icon
from components.ui import sec, card, info_box, bfai_gauge_svg, harmattan_gauge_svg, \
    _cbg, _cborder, _ctxt, _ctxt2, _accent
from components.charts import PLO




def _t(key):
    lang = LNG()
    return T.get(lang, T["en"]).get(key, T["en"].get(key, key))


def page_alerts_health():
    st.markdown('<div class="as-content">', unsafe_allow_html=True)

    # ── Live data ─────────────────────────────────────────────────────────────
    with st.spinner("Loading live predictions…"):
        _stats = live_all()

    tab_al, tab_hc, tab_exp = st.tabs([
        _t("alert_centre_tab"), _t("health_calc_tab"), _t("exposure_tab")
    ])

    with tab_al:
        # city selector
        c1,c2 = st.columns(2)
        with c1: adv_region = st.selectbox(_t("select_region"), list(CITIES.keys()), key="al_reg")
        with c2: adv_city   = st.selectbox(_t("select_city"), [c[0] for c in CITIES[adv_region]], key="al_city")
        adv_s  = _stats.get(adv_city, CITY_STATS.get(adv_city, {"mean_pm25":15.0,"region":adv_region}))
        adv_pm = adv_s["mean_pm25"]
        _,adv_col,adv_ico,adv_raw = aqi(adv_pm, LNG())

        a1,a2 = st.columns(2)
        with a1:
            sec(f"{_t('active_alerts_hdr').split('—')[0].strip()} — {threshold_label()}")
            for city,s in sorted([(c,s) for c,s in _stats.items() if s["mean_pm25"]>get_threshold()],
                                   key=lambda x: x[1]["mean_pm25"],reverse=True)[:12]:
                _,col,ico,_ = aqi(s["mean_pm25"])
                st.markdown(f"""<div class="as-alert-item">
  <div class="as-alert-dot" style="background:{col};box-shadow:0 0 5px {col}80;"></div>
  <div><div style="font-size:.78rem;font-weight:600;">{city}</div>
  <div style="font-size:.63rem;color:{_ctxt2()};">{s["region"]} · {s["who_exc"]:.0f}% days exceed WHO</div></div>
  <span style="margin-left:auto;font-family:'JetBrains Mono',monospace;font-size:.76rem;
    font-weight:600;color:{col};">{s["mean_pm25"]:.1f} μg/m³</span>
  <span style="font-size:.85rem;">{ico}</span>
</div>""", unsafe_allow_html=True)

            # WhatsApp share link for selected city alert
            _city_sms = (f"AIRSENSE-CM: {adv_city} — PM2.5 = {adv_pm:.1f} µg/m³. "
                         f"{'Exceeded WHO limit' if adv_pm > get_threshold() else 'Within limit'}. "
                         f"airsense-cm.org")
            _wa = f"https://wa.me/?text={_up.quote(_city_sms)}"
            lang = LNG()
            st.markdown(
                f'<div style="margin-top:.5rem;">'
                f'<a href="{_wa}" target="_blank" rel="noopener" '
                f'style="font-size:.65rem;color:#25D366;text-decoration:none;display:inline-flex;'
                f'align-items:center;gap:4px;">📲 '
                + ('Share alert via WhatsApp' if lang == 'en' else 'Partager l\'alerte WhatsApp')
                + '</a></div>',
                unsafe_allow_html=True)

        with a2:
            sec(_t("calibrated_alert_hdr"))
            art_al = load_artefacts()
            for city,s in sorted(_stats.items(),
                                  key=lambda x: get_alert_prob(x[1]["mean_pm25"],load_artefacts()),
                                  reverse=True)[:12]:
                prob  = get_alert_prob(s["mean_pm25"],art_al)
                tc    = RED if prob>.70 else (ORANGE if prob>.40 else (AMBER if prob>.20 else GREEN))
                tl    = "Red" if prob>.70 else ("Amber" if prob>.40 else ("Watch" if prob>.20 else "Green"))
                _,col,_,_ = aqi(s["mean_pm25"])
                st.markdown(f"""<div class="as-alert-item">
  <div class="as-alert-dot" style="background:{col};"></div>
  <div style="flex:1;"><div style="font-size:.76rem;font-weight:600;">{city}</div>
  <div style="font-size:.62rem;color:{_ctxt2()};">{s.get("region","—")} · {s["mean_pm25"]:.1f} μg/m³</div></div>
  <div style="display:flex;align-items:center;gap:.5rem;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:.82rem;color:{_ctxt()};">{prob*100:.0f}%</div>
    <div title="{tl}" style="width:13px;height:13px;border-radius:50%;background:{tc};
      box-shadow:0 0 6px {tc}99;flex-shrink:0;"></div>
  </div>
</div>""", unsafe_allow_html=True)
            info_box(f"P(PM2.5 > 15 μg/m³) = sigmoid(0.222 × PM2.5 − 3.037). "
                     f"City-specific Platt calibration. Alert F1 = <strong>{MODEL_RL_F1}</strong> @ P=0.50.")

        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        sec(f"{_t('school_agri_hdr')} — {adv_city} · PM2.5 {adv_pm:.1f} μg/m³")
        import datetime as _dtt
        lang = LNG()
        temp_c = 28.0; o3_proxy = max(0,30+(temp_c-25)*2.8)
        if adv_pm<=15 and o3_proxy<=60:      sl,sc,sb=_t("safe_outdoor"),"#4ade80","rgba(74,222,128,0.08)"
        elif adv_pm<=35 and o3_proxy<=80:    sl,sc,sb=_t("caution_outdoor"),"#fbbf24","rgba(251,191,36,0.08)"
        elif adv_pm<=55 or o3_proxy>100:     sl,sc,sb=_t("restricted_outdoor"),"#f97316","rgba(249,115,22,0.08)"
        else:                                 sl,sc,sb=_t("close_outdoor"),"#f87171","rgba(248,113,113,0.08)"
        is_cattle = adv_region in NORTHERN
        _dust_storm   = "ALERTE TEMPÊTE DE SABLE — Abriter le bétail" if lang=="fr" else "DUST STORM ALERT — Shelter livestock"
        _drought_risk = "RISQUE SÉCHERESSE + POUSSIÈRE — Surveiller irrigation" if lang=="fr" else "DROUGHT + DUST RISK — Monitor irrigation"
        _normal_cattle= "Normal — couloir pastoral" if lang=="fr" else "Normal — cattle corridor"
        _no_agri      = "Aucune alerte agricole" if lang=="fr" else "No agricultural dust alert"
        agri_m,agri_c = ((_dust_storm,RED) if adv_pm>80 else
                         (_drought_risk,ORANGE) if adv_pm>40 else
                         (_normal_cattle,GREEN)) if is_cattle else (_no_agri,AMBER)
        sa_c,sb_c = st.columns(2)
        with sa_c:
            st.markdown(f"""<div class="as-school-card" style="background:{sb};border-color:{sc};">
  <div style="font-size:.62rem;color:{sc};text-transform:uppercase;letter-spacing:.7px;font-weight:700;">{_t("school_advisory")}</div>
  <div style="font-size:.88rem;font-weight:700;color:{sc};margin:6px 0;">{sl}</div>
  <div style="font-size:.68rem;color:{_ctxt2()};">PM2.5: {adv_pm:.1f} μg/m³ · O₃ est.: {o3_proxy:.0f} μg/m³</div>
</div>""", unsafe_allow_html=True)
        with sb_c:
            st.markdown(f"""<div class="as-school-card" style="border-color:{agri_c};">
  <div style="font-size:.62rem;color:{agri_c};text-transform:uppercase;letter-spacing:.7px;font-weight:700;">{_t("agri_advisory")}</div>
  <div style="font-size:.88rem;font-weight:600;color:{agri_c};margin:6px 0;">{agri_m}</div>
  <div style="font-size:.68rem;color:{_ctxt2()};">{"Région" if lang=="fr" else "Region"}: {adv_region}</div>
</div>""", unsafe_allow_html=True)

        # SMS preview
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        with st.expander(_t("sms_preview_hdr"), expanded=False):
            alert_prob_sms = get_alert_prob(adv_pm, load_artefacts())
            now = _dtt.datetime.now()
            sms = (f"AIRSENSE-CM ALERT: {adv_city} — PM2.5 = {adv_pm:.1f} μg/m³ "
                   f"[{adv_raw.replace('_',' ').upper()}]. "
                   f"Exceedance risk: {alert_prob_sms*100:.0f}%. "
                   f"Vulnerable groups: avoid prolonged outdoor exposure. airsense-cm.org")
            st.markdown(f"""<div style="background:{_cbg()};border:1px solid {_cborder()};border-radius:12px;padding:14px;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
    <div style="width:34px;height:34px;background:{_accent()};border-radius:50%;display:flex;
      align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#fff;flex-shrink:0;">AS</div>
    <div><div style="font-size:.8rem;font-weight:700;color:{_ctxt()};">AirSense-CM</div>
    <div style="font-size:.62rem;color:{_ctxt2()};">Ministry of Public Health · Automated</div></div>
    <div style="margin-left:auto;font-size:.65rem;color:{_ctxt2()};">{now.strftime('%H:%M')}</div>
  </div>
  <div style="font-size:.76rem;line-height:1.65;color:{_ctxt()};">{sms}</div>
</div>""", unsafe_allow_html=True)
            wa_text = _up.quote(sms)
            wa_url  = f"https://wa.me/?text={wa_text}"
            st.markdown(
                f'<a href="{wa_url}" target="_blank" rel="noopener" '
                f'style="display:inline-flex;align-items:center;gap:6px;margin-top:.6rem;'
                f'background:#25D366;color:#fff;padding:.4rem .9rem;border-radius:8px;'
                f'text-decoration:none;font-size:.75rem;font-weight:600;">'
                f'<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">'
                f'<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15'
                f'-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475'
                f'-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52'
                f'.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207'
                f'-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372'
                f'-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2'
                f' 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719'
                f' 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347z"/>'
                f'<path d="M12 0C5.373 0 0 5.373 0 12c0 2.122.555 4.112 1.528 5.837L0 24l6.335-1.508'
                f'A11.945 11.945 0 0 0 12 24c6.627 0 12-5.373 12-12S18.627 0 12 0zm0 21.818'
                f'a9.818 9.818 0 0 1-5.006-1.374l-.36-.214-3.728.888.916-3.618-.236-.373'
                f'A9.818 9.818 0 0 1 2.182 12c0-5.426 4.392-9.818 9.818-9.818 5.426 0 9.818 4.392'
                f' 9.818 9.818 0 0 1-9.818 9.818z"/></svg>'
                f'{"Share on WhatsApp" if lang=="en" else "Partager sur WhatsApp"}</a>',
                unsafe_allow_html=True
            )

        # Seasonal advisory calendar
        st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
        sec(_t("seasonal_cal_hdr"))
        months_cal=["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
        cal={"Far North":[48,54,32,28,24,19,14,13,13,22,34,47],"North":[43,48,28,23,18,15,12,12,11,18,28,40],
             "Adamawa":[33,40,24,17,14,13,10,10,9,13,21,30],"West":[37,45,30,23,21,19,15,14,15,19,27,37],
             "North West":[36,44,28,20,18,15,12,12,12,16,24,35],"South":[15,20,12,9,9,9,8,8,5,6,9,14]}
        _is_lt = st.session_state.get("theme","light") == "light"
        _hm_cs = ([[0.0,"#fdf8f2"],[0.3,"#f0d8c0"],[0.5,AMBER],[0.75,ORANGE],[1.0,RED]] if _is_lt
                  else [[0.0,NAVY2],[0.3,BORDER],[0.5,AMBER],[0.75,ORANGE],[1.0,RED]])
        fig_cal=go.Figure(data=go.Heatmap(
            z=list(cal.values()),x=months_cal,y=list(cal.keys()),
            colorscale=_hm_cs,
            text=[[f"{v}" for v in row] for row in cal.values()],texttemplate="%{text}",
            textfont={"size":10,"color":_ctxt()},
            hovertemplate="<b>%{y}</b> — %{x}<br>PM2.5: %{z:.0f} μg/m³<extra></extra>",
            colorbar=dict(title=dict(text="PM2.5<br>μg/m³",font=dict(color=_ctxt2())),tickfont=dict(color=_ctxt2()))))
        fig_cal.update_layout(**PLO(height=260,xaxis=dict(side="top")))
        st.plotly_chart(fig_cal, use_container_width=True)

    with tab_hc:
        sec(_t("health_calc_hdr"))
        with st.form("hf2"):
            c1,c2 = st.columns(2)
            with c1:
                pop   = st.slider(_t("pop_exposed"),1,1000,100,key="hf_pop2")
                hrs   = st.slider(_t("daily_hours"),1,24,8,key="hf_hrs2")
                pm_sl = st.slider(_t("pm25_level"),0,100,25,key="hf_pm2")
            with c2:
                _sens_opts = [_t("general_public"), _t("children_elderly"), _t("resp_patients")]
                sens  = st.selectbox(_t("sensitivity"), _sens_opts, key="hf_sens2")
            ok = st.form_submit_button(_t("calculate"), use_container_width=True)
        smult={_t("general_public"):1.0, _t("children_elderly"):1.4, _t("resp_patients"):1.8}
        if ok or "hf_res2" in st.session_state:
            if ok:
                risk  = max(0,(pm_sl-WHO_ANN)*0.002)
                cases = (0.05+risk)*smult.get(sens,1.0)*pop*365*(hrs/24)
                er,hr,ld = health_impact(pm_sl); ap = get_alert_prob(pm_sl,None)
                st.session_state.hf_res2={"pm":pm_sl,"cases":cases,"er":er,"hr":hr,"ld":ld,"ap":ap}
            r=st.session_state.hf_res2; pm_sl=r["pm"]
            _,rc_aqi,_,_ = aqi(pm_sl)
            k1,k2,k3,k4=st.columns(4)
            with k1: card(_t("annual_cases"),f"{r['cases']:.0f}",_t("resp_cases_yr"),
                          accent=RED if r["cases"]>500 else AMBER)
            with k2: card(_t("excess_resp_10k"),f"{r['er']:.1f}",_t("per_10k"),accent=ORANGE)
            with k3: card(_t("hospital_risk"),f"{r['hr']:.1f}","%",
                          accent=RED if r["hr"]>10 else AMBER)
            with k4: card(_t("alert_prob"),f"{r['ap']*100:.0f}",_t("p_exceed"),
                          accent=RED if r["ap"]>.5 else (AMBER if r["ap"]>.25 else GREEN))
            _lang = LNG()
            if pm_sl<WHO_ANN:
                rec,rc=("Excellent. Aucune restriction." if _lang=="fr" else "Excellent. No restrictions."),GREEN
            elif pm_sl<get_threshold():
                rec,rc=("Modéré. Groupes sensibles vigilants." if _lang=="fr" else "Moderate. Sensitive groups monitor."),AMBER
            elif pm_sl<30:
                rec,rc=("Malsain pour groupes sensibles." if _lang=="fr" else "Unhealthy for sensitive groups."),ORANGE
            elif pm_sl<60:
                rec,rc=("Malsain. Éviter l'effort extérieur." if _lang=="fr" else "Unhealthy. Avoid outdoor exertion."),RED
            else:
                rec,rc=("Très malsain. Restez à l'intérieur." if _lang=="fr" else "Very unhealthy. Stay indoors."),PURPLE
            st.markdown(f"""<div style="background:{_cbg()};border:1px solid {_cborder()};
  border-left:3px solid {rc};border-radius:0 9px 9px 0;padding:.8rem 1rem;
  margin-top:.85rem;font-size:.8rem;color:{_ctxt2()};">{rec}</div>""", unsafe_allow_html=True)
            info_box(f"<strong>Alert formula:</strong> P(exceed WHO) = sigmoid(0.222 × PM2.5 − 3.037) "
                     f"= <strong style='color:{_accent()};'>{r['ap']*100:.1f}%</strong> at {pm_sl} μg/m³.")

    # ══════════════════════════════════════════════════════════════════════════
    # TAB 3 — PERSONAL EXPOSURE ACCUMULATOR
    # ══════════════════════════════════════════════════════════════════════════
    with tab_exp:
        lang = LNG()
        sec(_t("exposure_hdr"))
        info_box(_t("exposure_info"))

        if "exposure_log" not in st.session_state:
            st.session_state.exposure_log = []

        with st.form("exp_form", clear_on_submit=True):
            ec1, ec2, ec3 = st.columns(3)
            with ec1:
                exp_region = st.selectbox(_t("select_region"), list(CITIES.keys()), key="exp_reg")
            with ec2:
                exp_city = st.selectbox(_t("select_city"), [c[0] for c in CITIES[exp_region]], key="exp_city")
            with ec3:
                exp_hours = st.slider(_t("hours_spent"), 0.5, 16.0, 2.0, step=0.5, key="exp_hrs")
            add_ok = st.form_submit_button(_t("add_location"), use_container_width=True)

        if add_ok:
            pm_val = _stats.get(exp_city, CITY_STATS.get(exp_city, {"mean_pm25": 20.0}))["mean_pm25"]
            st.session_state.exposure_log.append({
                "city": exp_city, "region": exp_region,
                "hours": exp_hours, "pm25": pm_val,
            })

        if st.session_state.exposure_log:
            log         = st.session_state.exposure_log
            total_hours = sum(e["hours"] for e in log)
            weighted_pm = sum(e["pm25"] * e["hours"] for e in log) / total_hours
            exceed_pct  = max(0.0, (weighted_pm - WHO_24H) / WHO_24H * 100)

            # Entry list
            for entry in log:
                _, ecol, eico, _ = aqi(entry["pm25"])
                st.markdown(
                    f'<div class="as-alert-item">'
                    f'<div class="as-alert-dot" style="background:{ecol};"></div>'
                    f'<div style="flex:1;">'
                    f'<div style="font-size:.78rem;font-weight:600;">{entry["city"]}</div>'
                    f'<div style="font-size:.62rem;color:{_ctxt2()};">'
                    f'{entry["region"]} · {entry["hours"]:.1f}h · {entry["pm25"]:.1f} µg/m³</div>'
                    f'</div><span style="font-size:.8rem;">{eico}</span></div>',
                    unsafe_allow_html=True)

            st.markdown("<div style='margin-top:.8rem;'></div>", unsafe_allow_html=True)
            m1, m2, m3, m4 = st.columns(4)
            with m1: card(_t("daily_exposure"),   f"{weighted_pm:.1f}", "µg/m³",
                          accent=RED if weighted_pm > WHO_24H else GREEN)
            with m2: card(_t("total_hours"),      f"{total_hours:.1f}", "hrs",   accent=TEAL)
            with m3: card(_t("who_exceedance"),   f"{exceed_pct:.0f}",  "%",
                          accent=RED if exceed_pct > 0 else GREEN)
            with m4: card(_t("locations_visited"), str(len(log)),       _t("cities"), accent=AMBER)

            # Per-location bar chart
            fig_exp = go.Figure(go.Bar(
                x=[e["city"] for e in log],
                y=[e["pm25"] for e in log],
                marker_color=[aqi(e["pm25"])[1] for e in log],
                text=[f"{e['hours']:.1f}h" for e in log],
                textposition="outside",
            ))
            fig_exp.add_hline(y=WHO_24H, line_dash="dash", line_color=GREEN,
                              annotation_text="WHO 15 µg/m³",
                              annotation_font_color=GREEN)
            fig_exp.update_layout(**PLO(height=220, yaxis_title="PM2.5 µg/m³"))
            st.plotly_chart(fig_exp, use_container_width=True)

            # Health advisory
            if weighted_pm <= WHO_24H:
                rec = ("✅ Your exposure today is within safe limits." if lang == "en"
                       else "✅ Votre exposition aujourd'hui est dans les limites sûres.")
                rc = GREEN
            elif weighted_pm <= 35:
                rec = ("⚠️ Moderate exposure — sensitive groups should limit outdoor time." if lang == "en"
                       else "⚠️ Exposition modérée — groupes sensibles: limiter le temps extérieur.")
                rc = AMBER
            elif weighted_pm <= 55:
                rec = ("🟠 High exposure — consider wearing a mask and reducing outdoor activities." if lang == "en"
                       else "🟠 Exposition élevée — envisagez un masque et réduisez les activités extérieures.")
                rc = ORANGE
            else:
                rec = ("🔴 Very high exposure — stay indoors and consult a doctor if symptoms develop." if lang == "en"
                       else "🔴 Exposition très élevée — restez à l'intérieur si possible.")
                rc = RED

            st.markdown(
                f'<div style="border-left:3px solid {rc};padding:.7rem 1rem;'
                f'border-radius:0 8px 8px 0;margin-top:.5rem;font-size:.8rem;color:{_ctxt2()};">'
                f'{rec}</div>',
                unsafe_allow_html=True)

            # WhatsApp share
            _exp_wa_msg = (
                f"My air quality exposure today: {weighted_pm:.1f} µg/m³ avg "
                f"across {len(log)} location{'s' if len(log)!=1 else ''} "
                f"({'EXCEEDS' if weighted_pm > WHO_24H else 'within'} WHO limit). "
                f"Tracked via AirSense CM — airsense-cm.org"
            )
            _exp_wa_url = f"https://wa.me/?text={_up.quote(_exp_wa_msg)}"
            st.markdown(
                f'<a href="{_exp_wa_url}" target="_blank" rel="noopener" '
                f'style="font-size:.65rem;color:#25D366;text-decoration:none;'
                f'display:inline-flex;align-items:center;gap:4px;margin-top:.4rem;">'
                f'📲 '
                + ("Share my daily exposure" if lang == "en" else "Partager mon exposition")
                + "</a>",
                unsafe_allow_html=True)

            st.markdown("<div style='margin-top:.5rem;'></div>", unsafe_allow_html=True)
            if st.button(_t("clear_log"), key="exp_clear"):
                st.session_state.exposure_log = []
                st.rerun()
        else:
            st.markdown(
                f'<div style="text-align:center;padding:2rem;color:{_ctxt2()};font-size:.8rem;">'
                + ("Add locations above to track your daily air quality exposure."
                   if lang == "en" else
                   "Ajoutez des lieux ci-dessus pour suivre votre exposition quotidienne.")
                + "</div>",
                unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)



