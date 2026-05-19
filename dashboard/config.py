"""
config.py — AirSense Cameroon
All application constants: colours, city data, translations, nav labels.
No Streamlit calls — safe to import anywhere.
"""

# ── Colour palette ────────────────────────────────────────────────────────────
NAVY    = "#0a192f"; NAVY2  = "#112240"; NAVY3  = "#1a365d"
TEAL    = "#64ffda"; TEAL2  = "#0891b2"; TEAL_D = "#0f7b8a"
TEXT1   = "#e6f1ff"; TEXT2  = "#8892b0"; BORDER = "#233554"
# ── AQI colours — competition design guide ───────────────────────────────
# Healthy(<15) Moderate(15-35) Poor(35-55) Critical(55-80) Hazardous(>80)
GREEN  = "#22c55e"   # Healthy   — competition: Vert
AMBER  = "#eab308"   # Moderate  — competition: Jaune (true yellow)
ORANGE = "#f97316"   # Poor      — competition: Orange
RED    = "#ef4444"   # Critical  — competition: Rouge
PURPLE = "#8b5cf6"   # Hazardous — extreme (beyond competition scale)
# Region colours follow competition AQI palette based on mean PM2.5
# Moderate (15-35): #eab308  |  Healthy (<15): #22c55e
REGION_COLORS = {
    "Far North": "#ef4444",  # 24.1 — deepest red, highest exceedance (73%)
    "North":     "#f97316",  # 21.5 — orange, second highest (66%)
    "West":      "#eab308",  # 22.6 — amber/yellow (60%)
    "North West":"#eab308",  # 21.2 — amber (55%)
    "East":      "#eab308",  # 17.9 — amber (49%)
    "Adamawa":   "#eab308",  # 17.8 — amber (49%)
    "Littoral":  "#eab308",  # 17.2 — amber (47%)
    "South West":"#eab308",  # 17.0 — amber (44%)
    "Centre":    "#eab308",  # 16.0 — amber (42%)
    "South":     "#22c55e",  # 13.3 — GREEN, only region below WHO 24h limit
}
NORTHERN = {"Far North","North","Adamawa"}
HIGHLAND = {"West","North West"}
URBAN    = {"Littoral","Centre"}

# ── Model / WHO thresholds ────────────────────────────────────────────────────
WHO_24H     = 15.0
WHO_ANN     = 5.0
MODEL_MAE   = 6.27
MODEL_R2    = 0.603
MODEL_RL_F1 = 0.847


# ── Translations ──────────────────────────────────────────────────────────────
T = {
    "en": {
        # AQI levels
        "good":"Healthy","moderate":"Moderate","poor":"Poor",
        "very_poor":"Critical","hazardous":"Hazardous",
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
        "mode_label":"Mode","mode_forecast":"7-Day Forecast","mode_historical":"Historical Date",
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
        "per_region_shap":"Per-Region SHAP — Climate Drivers",
        "computing_shap":"Computing live SHAP values…",
        "deep_dive":"Deep-Dive",
        "climate_2050_hdr":"Climate 2050 PM2.5 Projection — CMIP6 SSP Scenarios",
        "scenario_label":"Scenario","target_year":"Target Year",
        "compare_all_ssps":"Compare all SSPs",
        "regional_projections":"Regional Projections",
        "pm25_trajectory":"PM2.5 Trajectory 2025 → 2100",
        "projected_exceedance":"Projected WHO Exceedance",
        "spatial_hdr":"Spatial Generalization — Can the Model Predict Unseen Cities?",
        "r2_by_level":"R² by Generalization Level",
        "mean_mae_by_level":"Mean MAE by Level",
        "spatial_results_by_city":"Generalization Results by City",
        "quality_good":"Good","quality_fair":"Fair","quality_poor":"Poor",
        "model_comparison_hdr":"Master Model Comparison",
        "mae_comparison":"MAE Comparison",
        # ── AI Assistant ──
        "ai_assistant_hdr":"AI Health Assistant — Powered by Claude (Anthropic)",
        "quick_questions":"Quick questions:",
        "ai_input_label":"Ask about air quality, health, or pollution…",
        "ai_placeholder":"e.g. What precautions for asthma patients?",
        "send":"Send","clear":"Clear",
        "ai_about":"<strong>About:</strong> AirSense AI is grounded in real PM2.5 data for the selected city. Not a substitute for medical advice.",
        "asking_about":"Asking about",
        "thinking":"Thinking…",
        # ── Sidebar ──
        "refresh_live":"Refresh","cities_live":"cities live",
        "alerts_label":"Active alerts",
        # ── Policy Simulator & Brief ──
        "policy_sim_tab":"Policy Simulator",
        "policy_brief_tab":"Policy Brief",
        "policy_sim_hdr":"Air Quality Policy Simulator",
        "traffic_reduction":"Traffic reduction (%)",
        "industry_reduction":"Industrial reduction (%)",
        "biomass_reduction":"Biomass burning reduction (%)",
        "simulate_btn":"Simulate",
        "policy_brief_hdr":"AI Policy Brief Generator",
        "generate_brief_btn":"Generate Brief",
        "generating_brief":"Generating policy brief…",
        "policy_context":"Select a city to generate a tailored brief for health officials.",
        "before_pm":"Before",
        "after_pm":"After",
        "pm_reduction":"Reduction",
        "lives_saved":"Cases Prevented",
        # ── Harmattan animation ──
        "harmattan_anim_hdr":"Harmattan Dust Front — Monthly Animation",
        # ── Exposure tracker ──
        "exposure_tab":"My Exposure",
        "exposure_hdr":"Personal Daily Exposure Tracker",
        "exposure_info":"Track your cumulative PM2.5 exposure across multiple locations throughout the day.",
        "hours_spent":"Hours spent there",
        "add_location":"Add Location",
        "daily_exposure":"Daily Avg PM2.5",
        "total_hours":"Hours tracked",
        "who_exceedance":"WHO Exceedance",
        "locations_visited":"Locations",
        "cities":"cities",
        "clear_log":"Clear Log",
    },
    "fr": {
        # Niveaux IQA
        "good":"Sain","moderate":"Modéré","poor":"Mauvais",
        "very_poor":"Critique","hazardous":"Dangereux",
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
        "mode_label":"Mode","mode_forecast":"Prévision 7 Jours","mode_historical":"Date Historique",
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
        "per_region_shap":"SHAP par Région — Facteurs Climatiques",
        "computing_shap":"Calcul des valeurs SHAP en direct…",
        "deep_dive":"Analyse Approfondie",
        "climate_2050_hdr":"Projection PM2.5 Climat 2050 — Scénarios CMIP6 SSP",
        "scenario_label":"Scénario","target_year":"Année Cible",
        "compare_all_ssps":"Comparer tous les SSP",
        "regional_projections":"Projections Régionales",
        "pm25_trajectory":"Trajectoire PM2.5 2025 → 2100",
        "projected_exceedance":"Dépassement OMS Projeté",
        "spatial_hdr":"Généralisation Spatiale — Le Modèle Peut-il Prédire des Villes Inconnues ?",
        "r2_by_level":"R² par Niveau de Généralisation",
        "mean_mae_by_level":"MAE Moyen par Niveau",
        "spatial_results_by_city":"Résultats de Généralisation par Ville",
        "quality_good":"Bon","quality_fair":"Acceptable","quality_poor":"Faible",
        "model_comparison_hdr":"Comparaison Principale des Modèles",
        "mae_comparison":"Comparaison MAE",
        # ── Assistant IA ──
        "ai_assistant_hdr":"Assistant Santé IA — Propulsé par Claude (Anthropic)",
        "quick_questions":"Questions rapides :",
        "ai_input_label":"Posez une question sur la qualité de l'air, la santé ou la pollution…",
        "ai_placeholder":"ex : Quelles précautions pour les asthmatiques ?",
        "send":"Envoyer","clear":"Effacer",
        "ai_about":"<strong>À propos :</strong> L'IA AirSense est fondée sur des données PM2.5 réelles pour la ville sélectionnée. Ne remplace pas un avis médical.",
        "asking_about":"Question sur",
        "thinking":"Réflexion en cours…",
        # ── Barre latérale ──
        "refresh_live":"Actualiser","cities_live":"villes en direct",
        "alerts_label":"Alertes actives",
        # ── Simulateur & Rapport ──
        "policy_sim_tab":"Simulateur de politique",
        "policy_brief_tab":"Rapport politique",
        "policy_sim_hdr":"Simulateur de politique qualité de l'air",
        "traffic_reduction":"Réduction du trafic (%)",
        "industry_reduction":"Réduction industrielle (%)",
        "biomass_reduction":"Réduction feux de biomasse (%)",
        "simulate_btn":"Simuler",
        "policy_brief_hdr":"Générateur de rapport IA",
        "generate_brief_btn":"Générer le rapport",
        "generating_brief":"Génération du rapport…",
        "policy_context":"Sélectionnez une ville pour générer un rapport pour les autorités sanitaires.",
        "before_pm":"Avant",
        "after_pm":"Après",
        "pm_reduction":"Réduction",
        "lives_saved":"Cas évités",
        # ── Animation Harmattan ──
        "harmattan_anim_hdr":"Front de Poussière Harmattan — Animation Mensuelle",
        # ── Suivi d'exposition ──
        "exposure_tab":"Mon Exposition",
        "exposure_hdr":"Suivi d'exposition quotidienne",
        "exposure_info":"Suivez votre exposition cumulative aux PM2.5 sur plusieurs lieux.",
        "hours_spent":"Heures passées",
        "add_location":"Ajouter un lieu",
        "daily_exposure":"PM2.5 moy. journalier",
        "total_hours":"Heures suivies",
        "who_exceedance":"Dépassement OMS",
        "locations_visited":"Lieux",
        "cities":"villes",
        "clear_log":"Effacer le journal",
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
        ("Bogo",10.738,14.611),
        ("Kaélé",10.105,14.449),
        ("Kousséri",12.077,15.03),
        ("Maroua",10.591,14.316),
        ("Mokolo",10.741,13.797),
        ("Mora",11.045,14.143),
    ],
    "North": [
        ("Bibémi",9.574,14.044),
        ("Figuil",9.754,13.96),
        ("Garoua",9.302,13.396),
        ("Guider",9.931,13.948),
        ("Lagdo",9.048,13.657),
    ],
    "Adamawa": [
        ("Banyo",6.751,11.82),
        ("Meiganga",6.519,14.299),
        ("Ngaoundéré",7.33,13.584),
    ],
    "West": [
        ("Babadjou",5.617,10.25),
        ("Bafang",5.152,10.178),
        ("Bafoussam",5.478,10.417),
        ("Baham",5.397,10.333),
        ("Bandjoun",5.383,10.417),
        ("Bangangté",5.141,10.528),
        ("Bazou",5.233,10.583),
        ("Dschang",5.447,10.059),
        ("Foumban",5.724,10.907),
        ("Foumbot",5.483,10.65),
        ("Mbouda",5.624,10.254),
    ],
    "North West": [
        ("Babessi",5.983,10.417),
        ("Bafut",6.1,10.1),
        ("Bakou",6.267,10.067),
        ("Bali",5.897,10.003),
        ("Bamenda",5.959,10.159),
        ("Fundong",6.264,10.178),
        ("Kumbo",6.2,10.667),
        ("Mbengwi",6.017,10.001),
    ],
    "Littoral": [
        ("Dizangué",3.767,10.033),
        ("Douala",4.048,9.704),
        ("Edéa",3.8,10.13),
        ("Loum",4.719,9.735),
        ("Manjo",4.846,9.821),
        ("Mbanga",4.502,9.572),
        ("Melong",5.12,9.96),
    ],
    "Centre": [
        ("Afanloum",4.333,12.417),
        ("Akono",3.7,11.417),
        ("Akonolinga",3.774,12.249),
        ("Ayos",3.906,12.524),
        ("Bafia",4.75,11.233),
        ("Eséka",3.651,10.767),
        ("Mbalmayo",3.516,11.497),
        ("Mbandjock",4.45,11.933),
        ("Monatélé",4.259,11.204),
        ("Yaoundé",3.848,11.502),
    ],
    "East": [
        ("Abong-Mbang",3.983,13.183),
        ("Batouri",4.432,14.37),
        ("Bélabo",4.934,13.29),
        ("Bertoua",4.577,13.685),
        ("Bétaré-Oya",5.517,14.083),
        ("Doumé",4.236,13.446),
        ("Garoua-Boulaï",5.878,14.547),
    ],
    "South West": [
        ("Akwaya",6.017,9.717),
        ("Bangem",5.12,9.783),
        ("Buéa",4.154,9.241),
        ("Fontem",5.517,9.85),
        ("Kumba",4.636,9.447),
        ("Limbé",4.017,9.212),
        ("Mamfé",5.768,9.298),
    ],
    "South": [
        ("Akoéman",2.783,10.833),
        ("Akom II",2.733,10.397),
        ("Ambam",2.385,11.268),
        ("Campo",2.367,9.817),
        ("Ebolowa",2.9,11.15),
        ("Kribi",2.94,9.91),
        ("Lolodorf",3.235,10.73),
    ],
}

CITY_STATS = {
    "Bogo":  {"mean_pm25":26.4,"who_exc":64.8,"region":"Far North","tier":"Low"},
    "Kaélé":  {"mean_pm25":25.8,"who_exc":63.7,"region":"Far North","tier":"Low"},
    "Kousséri":  {"mean_pm25":31.2,"who_exc":75.8,"region":"Far North","tier":"Low"},
    "Maroua":  {"mean_pm25":27.4,"who_exc":68.2,"region":"Far North","tier":"Low"},
    "Mokolo":  {"mean_pm25":30.4,"who_exc":74.1,"region":"Far North","tier":"Low"},
    "Mora":  {"mean_pm25":28.9,"who_exc":70.2,"region":"Far North","tier":"Low"},
    "Bibémi":  {"mean_pm25":23.8,"who_exc":47.6,"region":"North","tier":"Medium"},
    "Figuil":  {"mean_pm25":22.7,"who_exc":54.2,"region":"North","tier":"Medium"},
    "Garoua":  {"mean_pm25":27.3,"who_exc":67.9,"region":"North","tier":"Low"},
    "Guider":  {"mean_pm25":24.5,"who_exc":59.7,"region":"North","tier":"Medium"},
    "Lagdo":  {"mean_pm25":22.3,"who_exc":53.0,"region":"North","tier":"Medium"},
    "Banyo":  {"mean_pm25":17.2,"who_exc":36.9,"region":"Adamawa","tier":"Medium"},
    "Meiganga":  {"mean_pm25":17.8,"who_exc":38.4,"region":"Adamawa","tier":"Medium"},
    "Ngaoundéré":  {"mean_pm25":19.2,"who_exc":42.1,"region":"Adamawa","tier":"Medium"},
    "Babadjou":  {"mean_pm25":24.5,"who_exc":49.0,"region":"West","tier":"Medium"},
    "Bafang":  {"mean_pm25":23.1,"who_exc":55.6,"region":"West","tier":"Medium"},
    "Bafoussam":  {"mean_pm25":25.1,"who_exc":61.8,"region":"West","tier":"Low"},
    "Baham":  {"mean_pm25":23.2,"who_exc":46.4,"region":"West","tier":"Medium"},
    "Bandjoun":  {"mean_pm25":22.5,"who_exc":45.0,"region":"West","tier":"Medium"},
    "Bangangté":  {"mean_pm25":23.6,"who_exc":57.3,"region":"West","tier":"Medium"},
    "Bazou":  {"mean_pm25":23.5,"who_exc":47.0,"region":"West","tier":"Medium"},
    "Dschang":  {"mean_pm25":24.8,"who_exc":60.4,"region":"West","tier":"Low"},
    "Foumban":  {"mean_pm25":24.2,"who_exc":58.9,"region":"West","tier":"Medium"},
    "Foumbot":  {"mean_pm25":23.1,"who_exc":46.2,"region":"West","tier":"Medium"},
    "Mbouda":  {"mean_pm25":25.4,"who_exc":62.1,"region":"West","tier":"Low"},
    "Babessi":  {"mean_pm25":21.9,"who_exc":43.8,"region":"North West","tier":"Medium"},
    "Bafut":  {"mean_pm25":20.0,"who_exc":40.0,"region":"North West","tier":"Medium"},
    "Bakou":  {"mean_pm25":20.7,"who_exc":41.4,"region":"North West","tier":"Medium"},
    "Bali":  {"mean_pm25":21.1,"who_exc":49.6,"region":"North West","tier":"Medium"},
    "Bamenda":  {"mean_pm25":22.9,"who_exc":54.8,"region":"North West","tier":"Medium"},
    "Fundong":  {"mean_pm25":19.9,"who_exc":45.8,"region":"North West","tier":"Medium"},
    "Kumbo":  {"mean_pm25":21.4,"who_exc":50.3,"region":"North West","tier":"Medium"},
    "Mbengwi":  {"mean_pm25":20.8,"who_exc":48.7,"region":"North West","tier":"Medium"},
    "Dizangué":  {"mean_pm25":14.5,"who_exc":29.0,"region":"Littoral","tier":"High"},
    "Douala":  {"mean_pm25":14.6,"who_exc":36.3,"region":"Littoral","tier":"Medium"},
    "Edéa":  {"mean_pm25":13.5,"who_exc":29.4,"region":"Littoral","tier":"Medium"},
    "Loum":  {"mean_pm25":14.1,"who_exc":32.7,"region":"Littoral","tier":"High"},
    "Manjo":  {"mean_pm25":14.9,"who_exc":35.2,"region":"Littoral","tier":"Medium"},
    "Mbanga":  {"mean_pm25":13.2,"who_exc":28.6,"region":"Littoral","tier":"High"},
    "Melong":  {"mean_pm25":15.3,"who_exc":37.1,"region":"Littoral","tier":"Medium"},
    "Afanloum":  {"mean_pm25":15.1,"who_exc":30.2,"region":"Centre","tier":"Medium"},
    "Akono":  {"mean_pm25":13.5,"who_exc":27.0,"region":"Centre","tier":"High"},
    "Akonolinga":  {"mean_pm25":13.1,"who_exc":28.0,"region":"Centre","tier":"High"},
    "Ayos":  {"mean_pm25":12.6,"who_exc":25.2,"region":"Centre","tier":"High"},
    "Bafia":  {"mean_pm25":14.8,"who_exc":34.6,"region":"Centre","tier":"Medium"},
    "Eséka":  {"mean_pm25":12.9,"who_exc":26.4,"region":"Centre","tier":"High"},
    "Mbalmayo":  {"mean_pm25":13.7,"who_exc":30.8,"region":"Centre","tier":"High"},
    "Mbandjock":  {"mean_pm25":14.5,"who_exc":29.0,"region":"Centre","tier":"High"},
    "Monatélé":  {"mean_pm25":13.5,"who_exc":29.7,"region":"Centre","tier":"High"},
    "Yaoundé":  {"mean_pm25":14.0,"who_exc":28.0,"region":"Centre","tier":"High"},
    "Abong-Mbang":  {"mean_pm25":15.9,"who_exc":35.4,"region":"East","tier":"Medium"},
    "Batouri":  {"mean_pm25":16.8,"who_exc":37.9,"region":"East","tier":"Medium"},
    "Bélabo":  {"mean_pm25":16.4,"who_exc":36.7,"region":"East","tier":"Medium"},
    "Bertoua":  {"mean_pm25":17.2,"who_exc":39.8,"region":"East","tier":"Medium"},
    "Bétaré-Oya":  {"mean_pm25":14.9,"who_exc":29.8,"region":"East","tier":"High"},
    "Doumé":  {"mean_pm25":15.6,"who_exc":34.2,"region":"East","tier":"Medium"},
    "Garoua-Boulaï":  {"mean_pm25":17.5,"who_exc":35.0,"region":"East","tier":"Medium"},
    "Akwaya":  {"mean_pm25":14.6,"who_exc":29.2,"region":"South West","tier":"High"},
    "Bangem":  {"mean_pm25":13.9,"who_exc":27.8,"region":"South West","tier":"High"},
    "Buéa":  {"mean_pm25":12.8,"who_exc":26.7,"region":"South West","tier":"High"},
    "Fontem":  {"mean_pm25":14.3,"who_exc":28.6,"region":"South West","tier":"High"},
    "Kumba":  {"mean_pm25":13.4,"who_exc":29.0,"region":"South West","tier":"High"},
    "Limbé":  {"mean_pm25":13.2,"who_exc":28.1,"region":"South West","tier":"High"},
    "Mamfé":  {"mean_pm25":12.6,"who_exc":25.9,"region":"South West","tier":"High"},
    "Akoéman":  {"mean_pm25":9.6,"who_exc":19.2,"region":"South","tier":"High"},
    "Akom II":  {"mean_pm25":11.3,"who_exc":22.6,"region":"South","tier":"High"},
    "Ambam":  {"mean_pm25":10.4,"who_exc":15.1,"region":"South","tier":"High"},
    "Campo":  {"mean_pm25":12.0,"who_exc":24.0,"region":"South","tier":"High"},
    "Ebolowa":  {"mean_pm25":10.2,"who_exc":14.3,"region":"South","tier":"High"},
    "Kribi":  {"mean_pm25":8.7,"who_exc":13.6,"region":"South","tier":"High"},
    "Lolodorf":  {"mean_pm25":9.8,"who_exc":13.1,"region":"South","tier":"High"},
}

REGIONS_DATA = {
    "Far North": {"lat":10.5,"lon":14.5,"pm25":24.1,"who_exc":73},
    "North":     {"lat":9.2, "lon":13.6,"pm25":21.5,"who_exc":66},
    "Adamawa":   {"lat":7.0, "lon":13.5,"pm25":17.8,"who_exc":49},
    "West":      {"lat":5.5, "lon":10.4,"pm25":22.6,"who_exc":60},
    "North West":{"lat":6.1, "lon":10.2,"pm25":21.2,"who_exc":55},
    "Littoral":  {"lat":4.0, "lon":9.8, "pm25":17.2,"who_exc":47},
    "Centre":    {"lat":4.0, "lon":11.5,"pm25":16.0,"who_exc":42},
    "East":      {"lat":4.3, "lon":13.8,"pm25":17.9,"who_exc":49},
    "South West":{"lat":4.3, "lon":9.3, "pm25":17.0,"who_exc":44},
    "South":     {"lat":3.0, "lon":11.2,"pm25":13.3,"who_exc":32},
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
# Per-standard concentration limits for each compound.
# Sources: WHO 2021 AQGs, EU Air Quality Directive 2024, US EPA NAAQS, ECOWAS/WHO-2005 IT-1.
# All values in μg/m³ (24-h mean unless noted).  None = no guideline defined.
COMPOUND_STANDARDS = {
    "WHO 2021": {
        "pm2_5_target": 15,    # AQG 24-h
        "pm10_target":  45,    # AQG 24-h
        "dust_target":  None,
        "co_target":    4000,  # AQG 24-h (≈ 3.5 mg/m³ rounded)
        "no2_target":   25,    # AQG 24-h
        "o3_target":    100,   # AQG peak-season 8-h
        "so2_target":   40,    # AQG 24-h
        "aod_target":   None,
    },
    "EU 2024": {
        "pm2_5_target": 25,    # Directive annual mean limit
        "pm10_target":  50,    # Directive 24-h limit
        "dust_target":  None,
        "co_target":    10000, # Directive 8-h daily maximum
        "no2_target":   40,    # Directive annual mean
        "o3_target":    120,   # Directive 8-h daily max target value
        "so2_target":   125,   # Directive 24-h limit
        "aod_target":   None,
    },
    "US EPA": {
        "pm2_5_target": 35,    # NAAQS 24-h primary standard
        "pm10_target":  150,   # NAAQS 24-h primary standard
        "dust_target":  None,
        "co_target":    10000, # NAAQS 8-h (9 ppm ≈ 10 mg/m³)
        "no2_target":   100,   # NAAQS annual (53 ppb ≈ 100 μg/m³)
        "o3_target":    140,   # NAAQS 8-h (70 ppb ≈ 140 μg/m³)
        "so2_target":   196,   # NAAQS 1-h primary (75 ppb ≈ 196 μg/m³)
        "aod_target":   None,
    },
    "ECOWAS": {
        "pm2_5_target": 50,    # WHO 2005 IT-1 adopted regionally
        "pm10_target":  100,   # WHO 2005 IT-1
        "dust_target":  None,
        "co_target":    4000,  # WHO 2005 guideline
        "no2_target":   40,    # WHO 2005 annual guideline
        "o3_target":    120,   # WHO 2005 8-h guideline
        "so2_target":   125,   # WHO 2005 24-h guideline
        "aod_target":   None,
    },
    "Custom": {
        "pm2_5_target": None,  # Driven by session-state threshold
        "pm10_target":  None,
        "dust_target":  None,
        "co_target":    None,
        "no2_target":   None,
        "o3_target":    None,
        "so2_target":   None,
        "aod_target":   None,
    },
}
# Backward-compat alias
COMPOUND_WHO = COMPOUND_STANDARDS["WHO 2021"]
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
