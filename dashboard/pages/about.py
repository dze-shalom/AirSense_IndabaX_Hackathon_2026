"""pages/about.py — Clean product description."""
import streamlit as st
from config import *
from utils.helpers import LNG
from components.ui import sec, info_box
from components.charts import PLO
import plotly.graph_objects as go


# Inline SVG helpers — no emojis
def _icon(path_d, size=16, stroke=None):
    s = stroke or TEAL
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="{s}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
            f'{path_d}</svg>')


ICONS = {
    "map":      '<polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/>',
    "forecast": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "shield":   '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "chart":    '<line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>',
    "globe":    '<circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>',
    "flask":    '<path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v11m0 0a3 3 0 1 0 6 0m-6 0h6"/>',
    "brain":    '<path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96-.46 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.88A2.5 2.5 0 0 1 9.5 2Z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.88A2.5 2.5 0 0 0 14.5 2Z"/>',
    "alert":    '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
    "message":  '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>',
    "leaf":     '<path d="M2 22 16 8"/><path d="M16 8c0 4.4-3.6 8-8 8s-8-3.6-8-8 3.6-8 8-8 8 3.6 8 8z"/>',
    "clock":    '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "check":    '<polyline points="20 6 9 17 4 12"/>',
}


def page_about():
    lang = LNG()
    st.markdown('<div class="as-content">', unsafe_allow_html=True)

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(f"""
<div style="background:linear-gradient(135deg,{NAVY2},{NAVY3});
  border:1px solid {BORDER};border-radius:14px;
  padding:1.6rem 1.8rem;margin-bottom:1.4rem;position:relative;overflow:hidden;">
  <div style="position:absolute;top:0;left:0;right:0;height:3px;
    background:linear-gradient(90deg,{TEAL},{TEAL2},transparent);"></div>
  <div style="position:absolute;right:1.5rem;top:50%;transform:translateY(-50%);
    opacity:0.06;font-size:7rem;line-height:1;">
    {_icon(ICONS['globe'], 96, TEAL)}
  </div>
  <div style="font-size:1.5rem;font-weight:700;color:{TEXT1};margin-bottom:.4rem;">
    AirSense Cameroon
  </div>
  <div style="font-size:.8rem;color:{TEAL};font-weight:600;margin-bottom:.8rem;letter-spacing:.04em;">
    {"AI-Powered Air Quality Intelligence for Cameroon" if lang=="en"
     else "Intelligence de Qualité de l'Air par IA pour le Cameroun"}
  </div>
  <div style="font-size:.78rem;color:{TEXT2};line-height:1.75;max-width:680px;">
    {"AirSense monitors and predicts PM2.5 air pollution across 88 cities in all 10 regions "
     "of Cameroon — covering over 12 million people. It combines six years of satellite and "
     "weather data with an XGBoost model trained on real CAMS measurements, delivering daily "
     "forecasts, health advisories, school alerts, and climate projections in English and French."
     if lang=="en" else
     "AirSense surveille et prédit la pollution PM2.5 dans 88 villes de toutes les 10 régions "
     "du Cameroun — couvrant plus de 12 millions de personnes. Il combine six années de données "
     "satellitaires et météo avec un modèle XGBoost entraîné sur des mesures CAMS réelles, "
     "fournissant des prévisions quotidiennes, des avis sanitaires et des projections climatiques "
     "en anglais et en français."}
  </div>
</div>""", unsafe_allow_html=True)

    # ── What it does — feature cards ─────────────────────────────────────────
    sec("What AirSense Does" if lang=="en" else "Ce que fait AirSense")

    features_en = [
        ("map",     "National Air Quality Map",
         "Live PM2.5 heatmap across 88 Cameroonian cities with wind arrows, density overlay, "
         "and per-city 7-day sparklines. Cities colour-coded by AQI level."),
        ("forecast","7-Day + Historical Forecast",
         "XGBoost predictions for any day — either a 7-day future forecast from Open-Meteo "
         "weather, or historical reconstruction for any past date going back to 2020."),
        ("flask",   "8-Compound Pollution Profile",
         "Separate trained models for PM2.5, PM10, Dust, CO, NO₂, O₃, SO₂, and AOD. "
         "Each compound compared to WHO guidelines with model accuracy shown inline."),
        ("chart",   "Real-Time Source Attribution",
         "Dynamically attributes pollution to Dust, Biomass Burning, Traffic, Industry, "
         "and Secondary Aerosol using live wind speed, direction, precipitation, and humidity."),
        ("shield",  "Calibrated Alert System",
         "Platt-calibrated P(exceed WHO 24h) per city. Alert F1=0.847. Conformal prediction "
         "intervals give 90% coverage with region-specific uncertainty bounds."),
        ("alert",   "School & Agricultural Advisories",
         "Four-level school outdoor guidance (Safe/Caution/Restricted/Close) and agricultural "
         "dust alerts for the Far North, North, and Adamawa cattle corridor."),
        ("brain",   "SHAP Climate Drivers",
         "Per-region TreeExplainer SHAP analysis — shows which climate variables (year trend, "
         "rainfall, Harmattan, latitude) drive PM2.5 in each region differently."),
        ("globe",   "Climate 2050 Projections",
         "IPCC AR6 SSP scenarios (1.9 to 8.5) projected to 2100 using regional warming "
         "amplification factors. Far North shows the highest sensitivity."),
        ("globe",   "Spatial Generalization",
         "Tested on cities never seen during training — including cross-border cities in Chad. "
         "MAE 3.7–6.6 μg/m³ for unseen Cameroonian cities."),
        ("message", "Claude AI Health Assistant",
         "Claude-powered Q&A answers health questions in context — knowing the current city, "
         "PM2.5 level, and WHO status. Bilingual EN/FR responses."),
        ("clock",   "Harmattan Early Warning",
         "Two-stage model switches to a dedicated Harmattan regressor during Nov–Feb for "
         "northern regions, improving accuracy during peak pollution season."),
        ("leaf",    "Africa Benchmark",
         "Cameroon cities benchmarked against 12 African capitals. Maroua's annual mean "
         "exceeds Lagos and is 5× worse than Nairobi."),
    ]

    features_fr = [
        ("map",     "Carte Nationale de Qualité de l'Air",
         "Carte PM2.5 en direct pour 88 villes camerounaises avec flèches de vent, superposition "
         "de densité et graphiques 7 jours par ville."),
        ("forecast","Prévision 7 Jours + Historique",
         "Prédictions XGBoost pour n'importe quel jour — prévision future ou reconstruction "
         "historique jusqu'en 2020 via l'archive Open-Meteo."),
        ("flask",   "Profil 8 Composés de Pollution",
         "Modèles distincts pour PM2.5, PM10, Poussière, CO, NO₂, O₃, SO₂ et AOD. "
         "Chaque composé comparé aux lignes directrices OMS."),
        ("chart",   "Attribution de Source en Temps Réel",
         "Attribue dynamiquement la pollution à la Poussière, la Biomasse, le Trafic, "
         "l'Industrie et les Aérosols Secondaires à partir de la météo en direct."),
        ("shield",  "Système d'Alerte Calibré",
         "P(dépasser OMS 24h) calibré par Platt. F1 alerte = 0,847. Intervalles de prédiction "
         "conformaux avec couverture empirique de 97,4%."),
        ("alert",   "Avis Scolaires et Agricoles",
         "Guidance scolaire à quatre niveaux et alertes agricoles pour le couloir pastoral "
         "de l'Extrême-Nord, Nord et Adamaoua."),
        ("brain",   "Pilotes Climatiques SHAP",
         "Analyse SHAP par région — montre quelles variables climatiques pilotent le PM2.5 "
         "différemment dans chaque région."),
        ("globe",   "Projections Climatiques 2050",
         "Scénarios SSP GIEC AR6 projetés jusqu'en 2100 avec facteurs d'amplification "
         "du réchauffement régionaux."),
        ("globe",   "Généralisation Spatiale",
         "Testé sur des villes jamais vues à l'entraînement, y compris des villes "
         "transfrontalières au Tchad."),
        ("message", "Assistant Santé IA Claude",
         "Questions-réponses santé propulsées par Claude, contextualisées avec la ville, "
         "le niveau PM2.5 et le statut OMS. Réponses bilingues."),
        ("clock",   "Alerte Précoce Harmattan",
         "Modèle à deux étapes qui bascule vers un régresseur Harmattan dédié en "
         "Nov–Fév pour les régions du nord."),
        ("leaf",    "Comparaison Africaine",
         "Villes camerounaises comparées à 12 capitales africaines. Maroua est 5× "
         "plus polluée que Nairobi."),
    ]

    features = features_fr if lang == "fr" else features_en

    # 3-column grid of feature cards
    for row_start in range(0, len(features), 3):
        cols = st.columns(3)
        for col_i, feat in enumerate(features[row_start:row_start+3]):
            ico_key, title, desc = feat
            with cols[col_i]:
                st.markdown(f"""<div style="background:{NAVY2};border:1px solid {BORDER};
  border-radius:10px;padding:.85rem 1rem;margin-bottom:.5rem;height:100%;
  transition:border-color .2s;">
  <div style="display:flex;align-items:center;gap:.5rem;margin-bottom:.4rem;">
    <div style="width:28px;height:28px;border-radius:7px;flex-shrink:0;
      background:rgba(100,255,218,0.09);border:1px solid rgba(100,255,218,0.2);
      display:flex;align-items:center;justify-content:center;">
      {_icon(ICONS[ico_key], 14)}
    </div>
    <span style="font-size:.72rem;font-weight:700;color:{TEXT1};">{title}</span>
  </div>
  <div style="font-size:.63rem;color:{TEXT2};line-height:1.65;">{desc}</div>
</div>""", unsafe_allow_html=True)

    # ── Model stats strip ─────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    sec("Model Performance" if lang=="en" else "Performance du Modèle")

    stats = [
        ("MAE", f"{MODEL_MAE} μg/m³", "PM2.5 test error" if lang=="en" else "Erreur test PM2.5", TEAL),
        ("R²",  f"{MODEL_R2}",        "Log-space accuracy" if lang=="en" else "Précision log-space", TEAL),
        ("F1",  f"{MODEL_RL_F1}",     "Alert F1 @ P=0.50", GREEN),
        ("COV", "97.4%",              "Conformal coverage" if lang=="en" else "Couverture conforme", TEAL2),
        ("MAE↓","+26.5%",             "vs naive baseline" if lang=="en" else "vs référence naïve", AMBER),
        ("CIT", "88",                 "Cities covered" if lang=="en" else "Villes couvertes", TEXT2),
    ]
    stat_cols = st.columns(len(stats))
    for col, (abbr, val, lbl, col_c) in zip(stat_cols, stats):
        with col:
            st.markdown(f"""<div style="background:{NAVY2};border:1px solid {BORDER};
  border-radius:9px;padding:.6rem;text-align:center;">
  <div style="font-size:1.15rem;font-weight:700;font-family:'JetBrains Mono',monospace;
    color:{col_c};">{val}</div>
  <div style="font-size:.52rem;color:{TEXT2};text-transform:uppercase;letter-spacing:.07em;
    margin-top:.1rem;">{lbl}</div>
</div>""", unsafe_allow_html=True)

    # ── Data sources ──────────────────────────────────────────────────────────
    st.markdown("<div style='margin-top:1rem;'></div>", unsafe_allow_html=True)
    sec("Data Sources" if lang=="en" else "Sources de Données")
    sources = [
        ("CAMS Atmosphere", "Copernicus Atmosphere Monitoring Service — PM2.5, PM10, Dust, CO, NO₂, O₃, SO₂, AOD historical (2020–2025)"),
        ("Open-Meteo", "20+ meteorological variables: temperature, precipitation, wind, humidity, pressure, soil moisture — forecast + archive"),
        ("Sentinel-2 / MODIS", "Satellite-derived aerosol optical depth (AOD) for proxy validation in CAMS coverage gaps"),
        ("Claude API", "Anthropic claude-sonnet-4 — contextual health Q&A assistant for PM2.5 advisories"),
        ("OpenStreetMap / Nominatim", "Geocoding for global city search — predict air quality anywhere in the world"),
    ] if lang == "en" else [
        ("CAMS Atmosphere", "Service de Surveillance de l'Atmosphère Copernicus — PM2.5, PM10, Poussière, CO, NO₂, O₃, SO₂, AOD (2020–2025)"),
        ("Open-Meteo", "20+ variables météo: température, précipitations, vent, humidité, pression — prévisions + archives"),
        ("Sentinel-2 / MODIS", "Profondeur optique des aérosols dérivée de satellites pour validation des lacunes CAMS"),
        ("Claude API", "Anthropic claude-sonnet-4 — assistant Q&R santé contextuel pour les avis PM2.5"),
        ("OpenStreetMap / Nominatim", "Géocodage pour la recherche de villes mondiales"),
    ]

    for name, desc in sources:
        st.markdown(f"""<div style="display:flex;gap:.7rem;padding:.4rem 0;
  border-bottom:1px solid {BORDER};align-items:flex-start;">
  <div style="width:7px;height:7px;border-radius:50%;background:{TEAL};
    flex-shrink:0;margin-top:.3rem;box-shadow:0 0 4px {TEAL};"></div>
  <div>
    <span style="font-size:.7rem;font-weight:600;color:{TEXT1};">{name}</span>
    <span style="font-size:.65rem;color:{TEXT2};margin-left:.4rem;">{desc}</span>
  </div>
</div>""", unsafe_allow_html=True)

    info_box(
        "Built for <strong>IndabaX Cameroon 2026</strong> · "
        "<em>AI for Climate and Health Resilience in Cameroon</em> · "
        "Author: <strong>Dze-Kum Shalom Chow</strong>"
        if lang=="en" else
        "Conçu pour <strong>IndabaX Cameroun 2026</strong> · "
        "<em>L'IA au service de la résilience climatique et sanitaire au Cameroun</em> · "
        "Auteur: <strong>Dze-Kum Shalom Chow</strong>"
    )

    st.markdown('</div>', unsafe_allow_html=True)
