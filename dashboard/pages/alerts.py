"""pages/alerts.py"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

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

    tab_al, tab_hc = st.tabs([_t("alert_centre_tab"), _t("health_calc_tab")])

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
  <div style="text-align:right;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:.82rem;font-weight:700;color:{tc};">{prob*100:.0f}%</div>
    <div style="font-size:.55rem;color:{tc};font-weight:600;">{tl}</div>
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

    st.markdown('</div>', unsafe_allow_html=True)



