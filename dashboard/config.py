"""
config.py — AirSense Cameroon
All application constants: colours, city data, translations, nav labels.
No Streamlit calls — safe to import anywhere.
"""

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY    = "#0a192f"; NAVY2  = "#112240"; NAVY3  = "#1a365d"
TEAL    = "#64ffda"; TEAL2  = "#0891b2"; TEAL_D = "#0f7b8a"
TEXT1   = "#e6f1ff"; TEXT2  = "#8892b0"; BORDER = "#233554"
RED     = "#ef4444"; ORANGE = "#f97316"; AMBER  = "#f59e0b"
GREEN   = "#22c55e"; PURPLE = "#8b5cf6"
REGION_COLORS = {
    "Far North":"#ef4444","North":"#f97316","Adamawa":"#f59e0b",
    "West":"#8b5cf6","North West":"#ec4899","Littoral":"#0f7b8a",
    "Centre":"#06b6d4","East":"#84cc16","South West":"#22c55e","South":"#10b981",
}
NORTHERN = {"Far North","North","Adamawa"}
HIGHLAND = {"West","North West"}
URBAN    = {"Littoral","Centre"}

# ── Model / WHO thresholds ────────────────────────────────────────────────────
WHO_24H     = 15.0
WHO_ANN     = 5.0
MODEL_MAE   = 6.04
MODEL_R2    = 0.9987
MODEL_RL_F1 = 0.847


# ── Translations ──────────────────────────────────────────────────────────────
T = {
    "en": {
        # AQI levels
        "good":"Good","moderate":"Moderate","poor":"Poor",
        "very_poor":"Very Poor","hazardous":"Hazardous",
        # Prompts
        "select_region":"Select Region","select_city":"Select City","today":"Today",
        "loading":"Fetching 7-day forecast…","no_data":"No forecast data available.",
        "who_exceeded":"WHO Exceeded","who_safe":"WHO Safe",
        # Health advisories
        "health_good":"Air quality satisfactory. No health impacts expected.",
        "health_moderate":"Sensitive individuals may experience minor symptoms.",
        "health_poor":"Sensitive groups should avoid outdoor activities.",
        "health_very_poor":"Everyone may experience more serious health effects.",
        "health_hazardous":"Health emergency. Stay indoors immediately.",
        # ── Overview ──
        "national_map":"National PM2.5 Map — Cameroon",
        "most_polluted":"Most Polluted Cities",
        "cleanest":"Cleanest Cities",
        "per_region_analysis":"Per-Region PM2.5 Analysis",
        "pollution_heatmap":"Pollution Heatmap — Monthly PM2.5 by Region",
        "filter_regions":"Filter Regions","filter_aqi":"Filter AQI",
        "map_layer":"Map Layer",
        "cities_heatmap":"Cities + Heatmap","cities_only":"Cities only","heatmap_only":"Heatmap only",
        "search_worldwide":"Search any city worldwide",
        "search_placeholder":"e.g. Kumba, N'Djamena, Bangui…",
        "search_btn":"Search","jump_city":"Or jump to a known city →",
        "open_forecast":"Open Forecast →","show_sparkline":"Show 7-day sparkline for city",
        "wind_speed":"Wind","heatmap_guide":"Sep = cleanest (peak rainfall). Feb = peak Harmattan Far North (54 μg/m³).",
        "bubble_note":"Bubble size ∝ pollution level","wind_note":"↑ Wind direction",
        # ── Explorer ──
        "forecast_tab":"7-Day Forecast","analytics_tab":"Analytics","compare_tab":"Compare Cities",
        "mode_forecast":"7-Day Forecast","mode_historical":"Historical Date",
        "start_date":"Start date","end_date":"End date","max_range_warn":"Max 30-day range for historical mode.",
        "fetching_archive":"Fetching historical weather from Open-Meteo archive…",
        "pm25_today":"PM2.5 Today","bfai_score":"BFAI Score",
        "alert_risk":"Alert Risk","conf_interval":"Conf. Interval","source_label":"Source",
        "outdoor_safety":"/100 outdoor safety","p_exceed":"% P(exceed WHO)",
        "confidence":"Confidence","attributed":"% attributed",
        "bfai_hdr":"Breath of Fresh Air Index (BFAI)","source_hdr":"Pollution Source Attribution",
        "forecast_trend_hdr":"PM2.5 Trend — 90% Calibrated Confidence Band",
        "seasonal_tab":"Seasonal","climate_tab":"Climate vs AQ","compounds_tab":"Compounds",
        "source_tab":"Source","health_tab":"Health","africa_tab":"Africa",
        "seasonal_hdr":"Monthly PM2.5","who_cal_hdr":"Monthly WHO Exceedance Calendar",
        "climate_hdr":"Climate Factors vs PM2.5","compound_hdr":"8-Compound Profile",
        "source_fp_hdr":"Source Fingerprint","health_hdr":"Health Impact",
        "africa_hdr":"Cameroon vs Africa — PM2.5 Benchmark",
        "compare_hdr":"Compare Two Cities",
        "region_a":"Region A","city_a":"City A","region_b":"Region B","city_b":"City B",
        "excess_resp":"Excess Resp. Cases","per_10k":"per 10,000 people",
        "hospital_risk":"Hospital Risk","lost_days":"Lost Work Days","per_10k_workers":"per 10,000 workers",
        "running_compounds":"Running compound models…",
        "live_compounds":"🟢 Live predictions from trained XGBoost compound models.",
        "static_compounds":"🟡 Estimated values — place models_multi.pkl in models/ for real predictions.",
        # ── Alerts ──
        "alert_centre_tab":"Alert Centre","health_calc_tab":"Health Calculator",
        "active_alerts_hdr":"Active Alerts — Cities Above WHO 24h",
        "calibrated_alert_hdr":"Calibrated Alert System — P(Exceed WHO) per City",
        "school_agri_hdr":"School & Agricultural Advisory",
        "sms_preview_hdr":"SMS Alert Preview — Automated Bilingual Format",
        "seasonal_cal_hdr":"Seasonal Advisory Calendar",
        "school_advisory":"School Advisory","agri_advisory":"Agricultural Advisory",
        "health_calc_hdr":"Health Impact Calculator — WHO Concentration-Response",
        "pop_exposed":"Population Exposed (thousands)","daily_hours":"Daily Exposure Hours",
        "pm25_level":"PM2.5 Level (μg/m³)","sensitivity":"Sensitivity Group",
        "calculate":"Calculate",
        "general_public":"General Public","children_elderly":"Children & Elderly",
        "resp_patients":"Respiratory Patients",
        "annual_cases":"Est. Annual Cases","resp_cases_yr":"resp. cases/yr",
        "alert_prob":"Alert Prob.","excess_resp_10k":"Excess Resp.",
        "safe_outdoor":"Safe — All outdoor activities normal",
        "caution_outdoor":"Caution — Limit vigorous outdoor activity",
        "restricted_outdoor":"Restricted — No PE outdoors; short breaks only",
        "close_outdoor":"Close Outdoor Areas — Indoors only",
        "active_alerts_label":"Active alerts",
        # ── Science ──
        "shap_tab":"SHAP — Climate Drivers","climate_tab_sci":"Climate 2050",
        "spatial_tab":"Spatial Generalization","model_tab":"Model Comparison",
        # ── Sidebar ──
        "refresh_live":"Refresh","cities_live":"cities live",
        "alerts_label":"Active alerts",
    },
    "fr": {
        # Niveaux IQA
        "good":"Bon","moderate":"Modéré","poor":"Mauvais",
        "very_poor":"Très Mauvais","hazardous":"Dangereux",
        # Invites
        "select_region":"Sélectionner la Région","select_city":"Sélectionner la Ville","today":"Aujourd'hui",
        "loading":"Récupération de la prévision 7 jours…","no_data":"Aucune donnée disponible.",
        "who_exceeded":"Limite OMS Dépassée","who_safe":"Dans les Normes OMS",
        # Avis sanitaires
        "health_good":"Qualité de l'air satisfaisante. Aucun impact sanitaire prévu.",
        "health_moderate":"Les personnes sensibles peuvent ressentir des symptômes mineurs.",
        "health_poor":"Les groupes sensibles devraient éviter les activités extérieures.",
        "health_very_poor":"Tout le monde peut ressentir des effets graves.",
        "health_hazardous":"Urgence sanitaire. Restez à l'intérieur immédiatement.",
        # ── Vue nationale ──
        "national_map":"Carte PM2.5 Nationale — Cameroun",
        "most_polluted":"Villes les Plus Polluées",
        "cleanest":"Villes les Plus Propres",
        "per_region_analysis":"Analyse PM2.5 par Région",
        "pollution_heatmap":"Carte Thermique — PM2.5 Mensuel par Région",
        "filter_regions":"Filtrer les Régions","filter_aqi":"Filtrer IQA",
        "map_layer":"Couche Carte",
        "cities_heatmap":"Villes + Carte Thermique","cities_only":"Villes uniquement","heatmap_only":"Carte Thermique uniquement",
        "search_worldwide":"Rechercher une ville mondiale",
        "search_placeholder":"ex : Kumba, N'Djaména, Bangui…",
        "search_btn":"Rechercher","jump_city":"Ou accéder à une ville connue →",
        "open_forecast":"Voir Prévision →","show_sparkline":"Graphique 7 jours pour la ville",
        "wind_speed":"Vent","heatmap_guide":"Sep = plus propre (pics de pluie). Fév = pic Harmattan Extrême-Nord (54 μg/m³).",
        "bubble_note":"Taille bulle ∝ niveau pollution","wind_note":"↑ Direction du vent",
        # ── Explorateur ──
        "forecast_tab":"Prévision 7 Jours","analytics_tab":"Analyses","compare_tab":"Comparer les Villes",
        "mode_forecast":"Prévision 7 Jours","mode_historical":"Date Historique",
        "start_date":"Date de début","end_date":"Date de fin","max_range_warn":"Plage maximale 30 jours en mode historique.",
        "fetching_archive":"Récupération météo historique depuis l'archive Open-Meteo…",
        "pm25_today":"PM2.5 Aujourd'hui","bfai_score":"Indice BFAI",
        "alert_risk":"Risque d'Alerte","conf_interval":"Intervalle Conf.","source_label":"Source",
        "outdoor_safety":"/100 sécurité extérieure","p_exceed":"% P(dépasser OMS)",
        "confidence":"Confiance","attributed":"% attribué",
        "bfai_hdr":"Indice Air Frais (BFAI)","source_hdr":"Attribution de Source de Pollution",
        "forecast_trend_hdr":"Tendance PM2.5 — Bande de Confiance 90% Calibrée",
        "seasonal_tab":"Saisonnalité","climate_tab":"Climat vs QA","compounds_tab":"Composés",
        "source_tab":"Source","health_tab":"Santé","africa_tab":"Afrique",
        "seasonal_hdr":"PM2.5 Mensuel","who_cal_hdr":"Calendrier Dépassements OMS Mensuels",
        "climate_hdr":"Facteurs Climatiques vs PM2.5","compound_hdr":"Profil 8 Composés",
        "source_fp_hdr":"Empreinte de Source","health_hdr":"Impact Sanitaire",
        "africa_hdr":"Cameroun vs Afrique — PM2.5",
        "compare_hdr":"Comparer Deux Villes",
        "region_a":"Région A","city_a":"Ville A","region_b":"Région B","city_b":"Ville B",
        "excess_resp":"Cas Resp. Excédentaires","per_10k":"pour 10 000 personnes",
        "hospital_risk":"Risque Hospitalier","lost_days":"Jours Travail Perdus","per_10k_workers":"pour 10 000 travailleurs",
        "running_compounds":"Exécution des modèles de composés…",
        "live_compounds":"🟢 Prédictions en direct depuis les modèles XGBoost composés.",
        "static_compounds":"🟡 Valeurs estimées — placez models_multi.pkl dans models/ pour des prédictions réelles.",
        # ── Alertes ──
        "alert_centre_tab":"Centre d'Alertes","health_calc_tab":"Calculateur Santé",
        "active_alerts_hdr":"Alertes Actives — Villes au-dessus OMS 24h",
        "calibrated_alert_hdr":"Système d'Alerte Calibré — P(Dépasser OMS) par Ville",
        "school_agri_hdr":"Avis Scolaires et Agricoles",
        "sms_preview_hdr":"Aperçu SMS d'Alerte — Format Bilingue Automatisé",
        "seasonal_cal_hdr":"Calendrier d'Avis Saisonniers",
        "school_advisory":"Avis Scolaire","agri_advisory":"Avis Agricole",
        "health_calc_hdr":"Calculateur d'Impact Sanitaire — Réponse OMS",
        "pop_exposed":"Population Exposée (milliers)","daily_hours":"Heures d'Exposition Quotidienne",
        "pm25_level":"Niveau PM2.5 (μg/m³)","sensitivity":"Groupe de Sensibilité",
        "calculate":"Calculer",
        "general_public":"Grand Public","children_elderly":"Enfants et Personnes Âgées",
        "resp_patients":"Patients Respiratoires",
        "annual_cases":"Cas Annuels Estimés","resp_cases_yr":"cas resp./an",
        "alert_prob":"Prob. Alerte","excess_resp_10k":"Resp. Excédentaires",
        "safe_outdoor":"Sécurisé — Toutes activités extérieures normales",
        "caution_outdoor":"Prudence — Limiter l'activité extérieure vigoureuse",
        "restricted_outdoor":"Restreint — Pas d'EP dehors ; courtes pauses uniquement",
        "close_outdoor":"Fermer les Espaces Extérieurs — En intérieur uniquement",
        "active_alerts_label":"Alertes actives",
        # ── Science ──
        "shap_tab":"SHAP — Facteurs Climatiques","climate_tab_sci":"Climat 2050",
        "spatial_tab":"Généralisation Spatiale","model_tab":"Comparaison des Modèles",
        # ── Barre latérale ──
        "refresh_live":"Actualiser","cities_live":"villes en direct",
        "alerts_label":"Alertes actives",
    },
}

# ── Navigation ────────────────────────────────────────────────────────────────
PAGE_KEYS = ["overview","explorer","alerts","science","ai","about"]

NAV_LABELS = {
    "en": {
        "overview":"Overview","explorer":"City Explorer",
        "alerts":"Alerts & Health","science":"Science & Climate",
        "ai":"AI Assistant","about":"About",
    },
    "fr": {
        "overview":"Vue Nationale","explorer":"Explorateur",
        "alerts":"Alertes & Santé","science":"Science & Climat",
        "ai":"Assistant IA","about":"À propos",
    },
}

NAV_SUBTITLES = {
    "en": {
        "overview":"National air quality map",
        "explorer":"Forecast · Analytics · Compare",
        "alerts":"Active alerts · Health calculator",
        "science":"SHAP drivers · 2050 projections",
        "ai":"Ask about air quality",
        "about":"Model · Innovations · Team",
    },
    "fr": {
        "overview":"Carte nationale qualité air",
        "explorer":"Prévision · Analyse · Comparer",
        "alerts":"Alertes actives · Santé",
        "science":"Drivers SHAP · Projections 2050",
        "ai":"Poser une question",
        "about":"Modèle · Innovations · Équipe",
    },
}

NAV_ICONS = {
    "overview":'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21"/><line x1="9" y1="3" x2="9" y2="18"/><line x1="15" y1="6" x2="15" y2="21"/></svg>',
    "explorer":'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"/></svg>',
    "alerts":  '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>',
    "science": '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3H5a2 2 0 0 0-2 2v4m6-6h10a2 2 0 0 1 2 2v4M9 3v11m0 0a3 3 0 1 0 6 0m-6 0h6"/></svg>',
    "ai":      '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>',
    "about":   '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>',
}

# ── Geographic and model data ─────────────────────────────────────────────────
CITIES = {
    "Far North": [
        ("Maroua",10.591,14.316),("Kousseri",12.077,15.030),("Mokolo",10.741,13.797),
        ("Yagoua",10.342,15.237),("Mora",11.045,14.143),("Kaélé",10.105,14.449),
        ("Mindif",10.402,14.435),("Koza",10.878,13.874),("Meri",10.717,14.195),
        ("Bogo",10.738,14.611),
    ],
    "North": [
        ("Garoua",9.302,13.396),("Guider",9.931,13.948),("Poli",8.479,13.239),
        ("Touboro",7.773,15.370),("Ngong",9.121,13.641),("Figuil",9.754,13.960),
        ("Rey Bouba",8.672,14.180),("Lagdo",9.048,13.657),
    ],
    "Adamawa": [
        ("Ngaoundere",7.330,13.584),("Meiganga",6.519,14.299),("Tibati",6.469,12.629),
        ("Tignere",7.367,12.654),("Banyo",6.751,11.820),("Galim",6.933,12.517),
        ("Nganha",7.317,13.217),("Djohong",6.817,14.717),
    ],
    "West": [
        ("Bafoussam",5.478,10.417),("Dschang",5.447,10.059),("Foumban",5.724,10.907),
        ("Mbouda",5.624,10.254),("Bangangte",5.141,10.528),("Bafang",5.152,10.178),
        ("Nkondjock",4.946,10.132),("Koutaba",5.641,10.734),("Bamendjou",5.466,10.373),
    ],
    "North West": [
        ("Bamenda",5.959,10.159),("Kumbo",6.208,10.678),("Mbengwi",6.017,10.001),
        ("Wum",6.376,10.066),("Nkambe",6.650,10.665),("Fundong",6.264,10.178),
        ("Bali",5.897,10.003),("Batibo",5.934,9.854),("Ndop",5.978,10.449),
    ],
    "Littoral": [
        ("Douala",4.048,9.704),("Edea",3.800,10.130),("Loum",4.719,9.735),
        ("Nkongsamba",4.954,9.937),("Mbanga",4.502,9.572),("Penja",4.618,9.678),
        ("Manjo",4.846,9.821),("Yabassi",4.451,9.974),("Melong",5.120,9.960),
    ],
    "Centre": [
        ("Yaounde",3.848,11.502),("Bafia",4.750,11.233),("Mbalmayo",3.516,11.497),
        ("Akonolinga",3.774,12.249),("Obala",4.166,11.531),("Eseka",3.651,10.767),
        ("Nanga Eboko",4.685,12.369),("Monatele",4.259,11.204),("Ntui",4.448,11.634),
    ],
    "East": [
        ("Bertoua",4.593,13.681),("Batouri",4.432,14.370),("Abong-Mbang",3.992,13.181),
        ("Yokadouma",3.526,15.049),("Belabo",4.934,13.290),("Dimako",4.655,13.771),
        ("Doume",4.236,13.446),("Ndelele",3.984,14.929),
    ],
    "South West": [
        ("Buea",4.154,9.241),("Kumba",4.636,9.447),("Limbe",4.017,9.212),
        ("Mamfe",5.768,9.298),("Mundemba",4.960,8.883),("Tiko",4.075,9.360),
        ("Muyuka",4.288,9.422),("Ekondo Titi",4.726,8.980),("Idenao",4.047,9.102),
    ],
    "South": [
        ("Ebolowa",2.900,11.150),("Ambam",2.385,11.268),("Kribi",2.940,9.910),
        ("Sangmelima",2.939,11.975),("Lolodorf",3.235,10.730),("Mvangan",2.746,12.021),
        ("Djoum",2.675,12.668),("Meyomessala",3.186,12.095),("Oveng",2.479,10.965),
    ],
}

CITY_STATS = {
    # Far North — high dust, Harmattan-dominated
    "Maroua":      {"mean_pm25":27.4,"who_exc":68.2,"region":"Far North",   "tier":"Low"},
    "Kousseri":    {"mean_pm25":31.2,"who_exc":75.8,"region":"Far North",   "tier":"Low"},
    "Mokolo":      {"mean_pm25":30.4,"who_exc":74.1,"region":"Far North",   "tier":"Low"},
    "Yagoua":      {"mean_pm25":26.1,"who_exc":65.3,"region":"Far North",   "tier":"Low"},
    "Mora":        {"mean_pm25":28.9,"who_exc":70.2,"region":"Far North",   "tier":"Low"},
    "Kaélé":       {"mean_pm25":25.8,"who_exc":63.7,"region":"Far North",   "tier":"Low"},
    "Mindif":      {"mean_pm25":24.6,"who_exc":60.1,"region":"Far North",   "tier":"Low"},
    "Koza":        {"mean_pm25":29.3,"who_exc":71.4,"region":"Far North",   "tier":"Low"},
    "Meri":        {"mean_pm25":27.1,"who_exc":67.5,"region":"Far North",   "tier":"Low"},
    "Bogo":        {"mean_pm25":26.4,"who_exc":64.8,"region":"Far North",   "tier":"Low"},
    # North
    "Garoua":      {"mean_pm25":27.3,"who_exc":67.9,"region":"North",       "tier":"Low"},
    "Guider":      {"mean_pm25":24.5,"who_exc":59.7,"region":"North",       "tier":"Medium"},
    "Poli":        {"mean_pm25":21.8,"who_exc":52.3,"region":"North",       "tier":"Medium"},
    "Touboro":     {"mean_pm25":19.4,"who_exc":44.6,"region":"North",       "tier":"Medium"},
    "Ngong":       {"mean_pm25":23.1,"who_exc":55.8,"region":"North",       "tier":"Medium"},
    "Figuil":      {"mean_pm25":22.7,"who_exc":54.2,"region":"North",       "tier":"Medium"},
    "Rey Bouba":   {"mean_pm25":20.9,"who_exc":49.1,"region":"North",       "tier":"Medium"},
    "Lagdo":       {"mean_pm25":22.3,"who_exc":53.0,"region":"North",       "tier":"Medium"},
    # Adamawa
    "Ngaoundere":  {"mean_pm25":19.2,"who_exc":42.1,"region":"Adamawa",     "tier":"Medium"},
    "Meiganga":    {"mean_pm25":17.8,"who_exc":38.4,"region":"Adamawa",     "tier":"Medium"},
    "Tibati":      {"mean_pm25":16.9,"who_exc":35.7,"region":"Adamawa",     "tier":"Medium"},
    "Tignere":     {"mean_pm25":18.3,"who_exc":40.2,"region":"Adamawa",     "tier":"Medium"},
    "Banyo":       {"mean_pm25":17.2,"who_exc":36.9,"region":"Adamawa",     "tier":"Medium"},
    "Galim":       {"mean_pm25":16.4,"who_exc":33.8,"region":"Adamawa",     "tier":"Medium"},
    "Nganha":      {"mean_pm25":18.9,"who_exc":41.5,"region":"Adamawa",     "tier":"Medium"},
    "Djohong":     {"mean_pm25":17.5,"who_exc":37.6,"region":"Adamawa",     "tier":"Medium"},
    # West — highland burning
    "Bafoussam":   {"mean_pm25":25.1,"who_exc":61.8,"region":"West",        "tier":"Low"},
    "Dschang":     {"mean_pm25":24.8,"who_exc":60.4,"region":"West",        "tier":"Low"},
    "Foumban":     {"mean_pm25":24.2,"who_exc":58.9,"region":"West",        "tier":"Medium"},
    "Mbouda":      {"mean_pm25":25.4,"who_exc":62.1,"region":"West",        "tier":"Low"},
    "Bangangte":   {"mean_pm25":23.6,"who_exc":57.3,"region":"West",        "tier":"Medium"},
    "Bafang":      {"mean_pm25":23.1,"who_exc":55.6,"region":"West",        "tier":"Medium"},
    "Nkondjock":   {"mean_pm25":20.4,"who_exc":47.2,"region":"West",        "tier":"Medium"},
    "Koutaba":     {"mean_pm25":22.8,"who_exc":54.1,"region":"West",        "tier":"Medium"},
    "Bamendjou":   {"mean_pm25":24.0,"who_exc":58.2,"region":"West",        "tier":"Medium"},
    # North West
    "Bamenda":     {"mean_pm25":22.9,"who_exc":54.8,"region":"North West",  "tier":"Medium"},
    "Kumbo":       {"mean_pm25":21.4,"who_exc":50.3,"region":"North West",  "tier":"Medium"},
    "Mbengwi":     {"mean_pm25":20.8,"who_exc":48.7,"region":"North West",  "tier":"Medium"},
    "Wum":         {"mean_pm25":19.6,"who_exc":44.2,"region":"North West",  "tier":"Medium"},
    "Nkambe":      {"mean_pm25":20.2,"who_exc":46.5,"region":"North West",  "tier":"Medium"},
    "Fundong":     {"mean_pm25":19.9,"who_exc":45.8,"region":"North West",  "tier":"Medium"},
    "Bali":        {"mean_pm25":21.1,"who_exc":49.6,"region":"North West",  "tier":"Medium"},
    "Batibo":      {"mean_pm25":20.5,"who_exc":47.9,"region":"North West",  "tier":"Medium"},
    "Ndop":        {"mean_pm25":21.7,"who_exc":51.2,"region":"North West",  "tier":"Medium"},
    # Littoral
    "Douala":      {"mean_pm25":14.6,"who_exc":36.3,"region":"Littoral",    "tier":"Medium"},
    "Edea":        {"mean_pm25":13.5,"who_exc":29.4,"region":"Littoral",    "tier":"Medium"},
    "Loum":        {"mean_pm25":14.1,"who_exc":32.7,"region":"Littoral",    "tier":"High"},
    "Nkongsamba":  {"mean_pm25":15.8,"who_exc":38.9,"region":"Littoral",    "tier":"Medium"},
    "Mbanga":      {"mean_pm25":13.2,"who_exc":28.6,"region":"Littoral",    "tier":"High"},
    "Penja":       {"mean_pm25":13.7,"who_exc":30.1,"region":"Littoral",    "tier":"High"},
    "Manjo":       {"mean_pm25":14.9,"who_exc":35.2,"region":"Littoral",    "tier":"Medium"},
    "Yabassi":     {"mean_pm25":13.0,"who_exc":27.3,"region":"Littoral",    "tier":"High"},
    "Melong":      {"mean_pm25":15.3,"who_exc":37.1,"region":"Littoral",    "tier":"Medium"},
    # Centre
    "Yaounde":     {"mean_pm25":13.9,"who_exc":31.5,"region":"Centre",      "tier":"High"},
    "Bafia":       {"mean_pm25":14.8,"who_exc":34.6,"region":"Centre",      "tier":"Medium"},
    "Mbalmayo":    {"mean_pm25":13.7,"who_exc":30.8,"region":"Centre",      "tier":"High"},
    "Akonolinga":  {"mean_pm25":13.1,"who_exc":28.0,"region":"Centre",      "tier":"High"},
    "Obala":       {"mean_pm25":14.3,"who_exc":33.2,"region":"Centre",      "tier":"High"},
    "Eseka":       {"mean_pm25":12.9,"who_exc":26.4,"region":"Centre",      "tier":"High"},
    "Nanga Eboko": {"mean_pm25":15.2,"who_exc":36.8,"region":"Centre",      "tier":"Medium"},
    "Monatele":    {"mean_pm25":13.5,"who_exc":29.7,"region":"Centre",      "tier":"High"},
    "Ntui":        {"mean_pm25":14.0,"who_exc":31.9,"region":"Centre",      "tier":"High"},
    # East
    "Bertoua":     {"mean_pm25":17.2,"who_exc":39.8,"region":"East",        "tier":"Medium"},
    "Batouri":     {"mean_pm25":16.8,"who_exc":37.9,"region":"East",        "tier":"Medium"},
    "Abong-Mbang": {"mean_pm25":15.9,"who_exc":35.4,"region":"East",        "tier":"Medium"},
    "Yokadouma":   {"mean_pm25":15.1,"who_exc":32.6,"region":"East",        "tier":"High"},
    "Belabo":      {"mean_pm25":16.4,"who_exc":36.7,"region":"East",        "tier":"Medium"},
    "Dimako":      {"mean_pm25":16.1,"who_exc":35.9,"region":"East",        "tier":"Medium"},
    "Doume":       {"mean_pm25":15.6,"who_exc":34.2,"region":"East",        "tier":"Medium"},
    "Ndelele":     {"mean_pm25":15.3,"who_exc":33.1,"region":"East",        "tier":"High"},
    # South West
    "Buea":        {"mean_pm25":12.8,"who_exc":26.7,"region":"South West",  "tier":"High"},
    "Kumba":       {"mean_pm25":13.4,"who_exc":29.0,"region":"South West",  "tier":"High"},
    "Limbe":       {"mean_pm25":13.2,"who_exc":28.1,"region":"South West",  "tier":"High"},
    "Mamfe":       {"mean_pm25":12.6,"who_exc":25.9,"region":"South West",  "tier":"High"},
    "Mundemba":    {"mean_pm25":11.8,"who_exc":22.4,"region":"South West",  "tier":"High"},
    "Tiko":        {"mean_pm25":13.0,"who_exc":27.5,"region":"South West",  "tier":"High"},
    "Muyuka":      {"mean_pm25":12.4,"who_exc":24.8,"region":"South West",  "tier":"High"},
    "Ekondo Titi": {"mean_pm25":11.5,"who_exc":21.2,"region":"South West",  "tier":"High"},
    "Idenao":      {"mean_pm25":12.1,"who_exc":23.6,"region":"South West",  "tier":"High"},
    # South — forest, cleanest
    "Ebolowa":     {"mean_pm25":10.2,"who_exc":14.3,"region":"South",       "tier":"High"},
    "Ambam":       {"mean_pm25":10.4,"who_exc":15.1,"region":"South",       "tier":"High"},
    "Kribi":       {"mean_pm25": 8.7,"who_exc":13.6,"region":"South",       "tier":"High"},
    "Sangmelima":  {"mean_pm25":11.4,"who_exc":18.2,"region":"South",       "tier":"High"},
    "Lolodorf":    {"mean_pm25": 9.8,"who_exc":13.1,"region":"South",       "tier":"High"},
    "Mvangan":     {"mean_pm25":10.7,"who_exc":16.4,"region":"South",       "tier":"High"},
    "Djoum":       {"mean_pm25": 9.4,"who_exc":12.8,"region":"South",       "tier":"High"},
    "Meyomessala": {"mean_pm25":10.9,"who_exc":17.2,"region":"South",       "tier":"High"},
    "Oveng":       {"mean_pm25": 9.1,"who_exc":12.1,"region":"South",       "tier":"High"},
}

REGIONS_DATA = {
    "Far North":{"lat":10.5,"lon":14.5,"pm25":28.7},
    "North":    {"lat":9.2, "lon":13.6,"pm25":24.4},
    "Adamawa":  {"lat":7.0, "lon":13.5,"pm25":19.4},
    "West":     {"lat":5.5, "lon":10.4,"pm25":25.0},
    "North West":{"lat":6.1,"lon":10.2,"pm25":22.5},
    "Littoral": {"lat":4.0, "lon":9.8, "pm25":15.9},
    "Centre":   {"lat":4.0, "lon":11.5,"pm25":14.2},
    "East":     {"lat":4.3, "lon":13.8,"pm25":17.2},
    "South West":{"lat":4.3,"lon":9.3, "pm25":14.8},
    "South":    {"lat":3.0, "lon":11.2,"pm25":10.3},
}

AFRICA_BENCHMARK = [
    ("Maroua, CM",      78,  "#c084fc", True),
    ("Lagos, NG",       62,  "#f87171", False),
    ("Kano, NG",        58,  "#f87171", False),
    ("Dakar, SN",       48,  "#f97316", False),
    ("Douala, CM",      42,  "#f97316", True),
    ("Bamako, ML",      38,  "#fbbf24", False),
    ("Abidjan, CI",     35,  "#fbbf24", False),
    ("Accra, GH",       32,  "#a3e635", False),
    ("Addis Ababa, ET", 22,  "#4ade80", False),
    ("Nairobi, KE",     16,  "#34d399", False),
    ("Buea, CM",        14,  "#2dd4bf", True),
    ("Cape Town, ZA",   12,  "#2dd4bf", False),
]

REGION_SHAP_FALLBACK = {
    "Far North":  [("year",0.140),("daylight_duration",0.128),("precipitation",0.112),("is_dust_event",0.108),("latitude",0.095)],
    "North":      [("precipitation",0.114),("year",0.098),("daylight_duration",0.087),("is_dust_event",0.082),("humidity",0.071)],
    "Adamawa":    [("precipitation",0.103),("year",0.082),("humidity",0.068),("daylight_duration",0.063),("region_enc",0.057)],
    "West":       [("region_enc",0.127),("year",0.098),("precipitation",0.091),("surface_pressure",0.078),("daylight_duration",0.062)],
    "North West": [("year",0.097),("precipitation",0.091),("surface_pressure",0.083),("humidity",0.078),("daylight_duration",0.072)],
    "Littoral":   [("year",0.119),("precipitation",0.087),("humidity",0.071),("day_of_year",0.068),("is_dry_season",0.063)],
    "Centre":     [("year",0.104),("precipitation",0.083),("region_enc",0.072),("month_sin",0.068),("humidity",0.062)],
    "East":       [("year",0.088),("precipitation",0.083),("humidity",0.057),("month_sin",0.054),("daylight_duration",0.051)],
    "South West": [("year",0.126),("precipitation",0.091),("longitude",0.082),("day_of_year",0.071),("humidity",0.067)],
    "South":      [("latitude",0.232),("year",0.113),("precipitation",0.098),("humidity",0.062),("doy_sin",0.058)],
}

SHAP_DESC = {
    "year":             "Multi-year trend (2020–2025)",
    "precipitation":    "Rainfall — particle washout",
    "humidity":         "Humidity — hygroscopic growth / Harmattan precursor",
    "daylight_duration":"Daylight hours — seasonal convective mixing",
    "latitude":         "Latitude — North–South pollution gradient",
    "is_dust_event":    "Dust storm flag — Harmattan extreme events",
    "is_dry_season":    "Dry season — no rainfall to wash particles",
    "region_enc":       "Region encoding — burning activity not in weather data",
    "longitude":        "Longitude — coastal / inland contrast (South West)",
    "surface_pressure": "Atmospheric pressure — particle trapping inversions",
    "month_sin":        "Cyclic month encoding — seasonal signal",
    "day_of_year":      "Day of year — continuous seasonal signal",
    "doy_sin":          "Cyclic day-of-year encoding",
    "is_harmattan":     "Harmattan season flag (Nov–Feb, northern regions)",
}

SSP_RATES   = {"SSP1-1.9 (Low)":0.10,"SSP2-4.5 (Intermediate)":0.22,
               "SSP3-7.0 (High)":0.35,"SSP5-8.5 (Very High)":0.48}

SSP_COLORS  = {"SSP1-1.9 (Low)":GREEN,"SSP2-4.5 (Intermediate)":AMBER,
               "SSP3-7.0 (High)":ORANGE,"SSP5-8.5 (Very High)":RED}

REGION_WARM = {"Far North":1.45,"North":1.38,"Adamawa":1.25,"West":1.05,
               "North West":1.05,"Littoral":0.95,"Centre":1.00,
               "East":0.90,"South West":0.88,"South":0.85}

PM25_SENS   = {"Far North":2.8,"North":2.5,"Adamawa":1.9,"West":1.4,
               "North West":1.3,"Littoral":0.9,"Centre":0.8,
               "East":0.7,"South West":0.6,"South":0.5}

# ── Monthly PM2.5 by region (from 87,240-row training set analysis) ───────────
MONTHLY_BY_REGION = {
    "Far North":  [48,54,32,28,24,19,14,13,13,22,34,47],
    "North":      [43,48,28,23,18,15,12,12,11,18,28,40],
    "Adamawa":    [33,40,24,17,14,13,10,10, 9,13,21,30],
    "West":       [37,45,30,23,21,19,15,14,15,19,27,37],
    "North West": [36,44,28,20,18,15,12,12,12,16,24,35],
    "Littoral":   [22,25,16,13,11,10, 9, 9, 8,10,15,21],
    "Centre":     [20,23,15,12,10, 9, 8, 8, 7, 9,14,19],
    "East":       [26,30,19,14,12,11, 9, 9, 8,11,18,24],
    "South West": [18,21,14,11, 9, 9, 8, 8, 7, 9,13,17],
    "South":      [15,20,12, 9, 9, 9, 8, 8, 5, 6, 9,14],
}

def city_monthly_profile(city, region):
    """Per-city monthly PM2.5 — city mean scaled from real regional pattern."""
    s        = CITY_STATS.get(city, {})
    mean_pm  = s.get("mean_pm25", 15.0)
    regional = MONTHLY_BY_REGION.get(region, [15]*12)
    reg_mean = sum(regional) / 12
    return [round(v * mean_pm / max(reg_mean, 1), 1) for v in regional]

# ── Compound model metadata ───────────────────────────────────────────────────
COMPOUND_KEYS   = ["pm2_5_target","pm10_target","dust_target","co_target",
                   "no2_target","o3_target","so2_target","aod_target"]
COMPOUND_LABELS = {"pm2_5_target":"PM2.5","pm10_target":"PM10","dust_target":"Dust",
                   "co_target":"CO","no2_target":"NO₂","o3_target":"O₃",
                   "so2_target":"SO₂","aod_target":"AOD"}
COMPOUND_UNITS  = {"pm2_5_target":"μg/m³","pm10_target":"μg/m³","dust_target":"μg/m³",
                   "co_target":"μg/m³","no2_target":"μg/m³","o3_target":"μg/m³",
                   "so2_target":"μg/m³","aod_target":"(550nm)"}
COMPOUND_WHO    = {"pm2_5_target":15,"pm10_target":45,"dust_target":None,
                   "co_target":4000,"no2_target":25,"o3_target":100,
                   "so2_target":40,"aod_target":None}
COMPOUND_COLORS = {"pm2_5_target":"#ef4444","pm10_target":"#f97316",
                   "dust_target":"#f59e0b","co_target":"#0891b2",
                   "no2_target":"#8b5cf6","o3_target":"#22c55e",
                   "so2_target":"#ec4899","aod_target":"#06b6d4"}
COMPOUND_TEST_MAE = {"pm2_5_target":5.91,"pm10_target":13.25,"dust_target":17.26,
                     "co_target":38.67,"no2_target":1.71,"o3_target":10.86,
                     "so2_target":0.30,"aod_target":0.08}
COMPOUND_TEST_R2  = {"pm2_5_target":0.665,"pm10_target":0.660,"dust_target":0.733,
                     "co_target":0.648,"no2_target":-0.18,"o3_target":0.518,
                     "so2_target":0.337,"aod_target":0.616}

# ── Master model comparison (from Step 11 notebook output) ───────────────────
MODEL_COMPARISON = [
    {"model":"Starter formula (baseline)",    "mae":9.047,"r2":0.208,"harm_mae":13.53, "flag":"baseline"},
    {"model":"City-month mean (baseline)",    "mae":7.521,"r2":0.454,"harm_mae":None,  "flag":"baseline"},
    {"model":"XGBoost CAMS-only",             "mae":6.231,"r2":0.615,"harm_mae":9.84,  "flag":"primary"},
    {"model":"XGBoost + Optuna (final)",      "mae":5.897,"r2":0.662,"harm_mae":None,  "flag":"primary"},
    {"model":"Two-Stage Harmattan",           "mae":5.90, "r2":0.662,"harm_mae":7.50,  "flag":"primary"},
    {"model":"Ensemble (XGB+LGB+Ridge)",      "mae":5.90, "r2":0.662,"harm_mae":None,  "flag":"ensemble"},
    {"model":"LightGBM alone",                "mae":6.085,"r2":0.632,"harm_mae":None,  "flag":"ensemble"},
    {"model":"Transformer Day+1",             "mae":7.047,"r2":0.582,"harm_mae":None,  "flag":"deep"},
    {"model":"Transformer Day+2",             "mae":7.211,"r2":0.552,"harm_mae":None,  "flag":"deep"},
    {"model":"Transformer Day+3",             "mae":7.412,"r2":0.527,"harm_mae":None,  "flag":"deep"},
    {"model":"GNN (GraphSAGE, 40 cities)",    "mae":None, "r2":None, "harm_mae":None,  "flag":"deep"},
]

# ── Spatial generalization results (Step 9e notebook output) ─────────────────
SPATIAL_GEN = [
    {"city":"Kumba",      "lat":4.636,"lon":9.447, "level":"L1 — Cameroon (unseen)",  "mae":5.17, "r2":0.677,"country":"CM"},
    {"city":"Foumban",    "lat":5.724,"lon":10.907,"level":"L1 — Cameroon (unseen)",  "mae":6.62, "r2":0.575,"country":"CM"},
    {"city":"Ebolowa",    "lat":2.900,"lon":11.150,"level":"L1 — Cameroon (unseen)",  "mae":3.72, "r2":0.666,"country":"CM"},
    {"city":"Meiganga",   "lat":6.519,"lon":14.299,"level":"L1 — Cameroon (unseen)",  "mae":4.75, "r2":0.513,"country":"CM"},
    {"city":"N'Djamena",  "lat":12.107,"lon":15.044,"level":"L2 — Cross-border (Chad)","mae":12.90,"r2":0.094,"country":"TD"},
    {"city":"Nairobi",    "lat":-1.286,"lon":36.817,"level":"L3 — Out-of-domain",     "mae":7.10, "r2":0.510,"country":"KE"},
]
