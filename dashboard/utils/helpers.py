"""utils/helpers.py — Pure computation helpers, no Streamlit."""
import numpy as np
from config import (T, WHO_24H, WHO_ANN, NORTHERN, HIGHLAND, URBAN,
                    GREEN, AMBER, ORANGE, RED, PURPLE, TEAL, TEAL2, TEXT2)
import streamlit as st

# ── PM2.5 threshold standards ─────────────────────────────────────────────────
THRESHOLD_STANDARDS = {
    "WHO 2021":  15.0,
    "EU 2024":   25.0,
    "US EPA":    35.0,
    "ECOWAS":    50.0,
    "Custom":    None,
}


def get_threshold() -> float:
    """Return the active PM2.5 24h limit from session state (falls back to WHO 15)."""
    return float(st.session_state.get("threshold", WHO_24H))


def threshold_label() -> str:
    """Return a short label like 'WHO 2021 · 15 µg/m³' for use in chart annotations."""
    std = st.session_state.get("threshold_std", "WHO 2021")
    val = get_threshold()
    return f"{std} · {val:.0f} µg/m³"


def LNG():
    """Return current UI language from Streamlit session state."""
    return st.session_state.get("lang", "en")





def aqi_thresholds():
    """Return (b1, b2, b3, b4) cut-points scaled from the active threshold.

    At WHO baseline (T=15) these equal 15 / 35 / 55 / 80.
    Every other standard scales proportionally so the colour bands always
    represent equivalent health risk relative to the chosen limit.
    """
    T_val = get_threshold()
    b1 = T_val
    b2 = round(T_val * (35 / 15), 1)
    b3 = round(T_val * (55 / 15), 1)
    b4 = round(T_val * (80 / 15), 1)
    return b1, b2, b3, b4


def aqi(pm25, lang="en"):
    b1, b2, b3, b4 = aqi_thresholds()
    if pm25 < b1:   k = "good"
    elif pm25 < b2: k = "moderate"
    elif pm25 < b3: k = "poor"
    elif pm25 < b4: k = "very_poor"
    else:           k = "hazardous"
    c = {"good":GREEN,"moderate":AMBER,"poor":ORANGE,"very_poor":RED,"hazardous":PURPLE}[k]
    l = T[lang].get(k, T["en"][k])
    i = {"good":"✅","moderate":"🟡","poor":"🟠","very_poor":"🔴","hazardous":"🟣"}[k]
    return l, c, i, k


def compute_bfai(pm25, wind, hum, region):
    pm_s = max(0, round(100 - (pm25 / 150) * 80))
    wi_s = min(100, round((wind / 8) * 60 + 20))
    hu_s = min(100, round((hum - 40) * 1.2)) if hum > 40 else 30
    return max(0, min(100, round(0.50 * pm_s + 0.25 * wi_s + 0.25 * hu_s)))


def bfai_label(score, lang="en"):
    if score >= 80: return "Excellent"
    if score >= 60: return "Good"      if lang == "en" else "Bon"
    if score >= 40: return "Moderate"  if lang == "en" else "Modéré"
    if score >= 20: return "Poor"      if lang == "en" else "Mauvais"
    return             "Hazardous"     if lang == "en" else "Dangereux"


def bfai_col(score):
    if score >= 60: return GREEN
    if score >= 40: return AMBER
    if score >= 20: return ORANGE
    return RED


SOURCE_LABELS = {
    "en": {
        "local":      ("Local Combustion",      "Traffic, generators, cooking fires"),
        "transported":("Transported Saharan Dust","Harmattan wind from Bodélé Depression"),
        "stagnation": ("Air Stagnation",          "Low wind trapping local particles"),
        "mixed":      ("Mixed Sources",            "Local + regional transport"),
    },
    "fr": {
        "local":      ("Combustion Locale",   "Trafic, générateurs, feux de cuisine"),
        "transported":("Poussière Saharienne","Transport Harmattan depuis Bodélé"),
        "stagnation": ("Stagnation de l'Air","Vent faible, particules piégées"),
        "mixed":      ("Sources Mixtes",       "Locales + transport régional"),
    },
}
SOURCE_COLORS = {"local":ORANGE,"transported":PURPLE,"stagnation":RED,"mixed":AMBER}


def classify_source(wind_speed, wind_dir, region, month):
    northern  = region in NORTHERN
    harmattan = month in [11,12,1,2] and northern and (wind_dir > 270 or wind_dir < 90)
    if harmattan and wind_speed > 3:
        return "transported", min(95, 60 + int(wind_speed * 5))
    if wind_speed < 2:
        return "stagnation",  min(90, 50 + int((2 - wind_speed) * 20))
    if region in URBAN:
        return "local",       min(85, 55 + int(wind_speed * 3))
    return "mixed", 60


def health_impact(pm25):
    return (
        round((pm25 / 10) * 3.2, 1),
        round(min(99, (pm25 / 50) * 15), 1),
        round((pm25 / 10) * 1.8, 1),
    )


def live_source_attribution(wind_speed, wind_dir, month, region, precipitation,
                             humidity, pm25, shap_data=None):
    """Compute dynamic source attribution from live meteorological conditions.

    Returns dict {source: fraction} summing to 1.0.
    Logic:
      - Dust/Transported  : NE winds + Harmattan season + low precip
      - Biomass Burning   : dry season + highland/savanna + SHAP is_dry_season
      - Traffic/Local     : stagnation + urban region + SHAP city_enc weight
      - Industry          : South West (oil) / Littoral (port) baseline + SHAP region_enc
      - Secondary Aerosol : high humidity + solar-driven chemistry
      - Other             : residual
    """
    north   = region in NORTHERN
    highland= region in HIGHLAND
    urban   = region in URBAN
    sw      = region == "South West"

    # ── 1. Dust / Transported fraction ───────────────────────────────────────
    harmattan = month in [11, 12, 1, 2] and north
    # NE wind = bearing 0-90° (coming from Sahara)
    ne_wind   = (wind_dir <= 90 or wind_dir >= 315) if wind_dir is not None else False
    dust_base = 0.55 if north else (0.10 if highland else (0.05 if sw else 0.12))
    dust = dust_base
    if harmattan and ne_wind:
        dust += 0.15 * min(1.0, wind_speed / 10)
    if precipitation > 5:                        # rain washes dust
        dust *= max(0.3, 1 - precipitation / 30)
    dust = round(min(0.85, max(0.02, dust)), 3)

    # ── 2. Biomass burning fraction ───────────────────────────────────────────
    dry_season  = month in [11, 12, 1, 2, 3]
    bio_base    = 0.40 if highland else (0.35 if north else (0.25 if sw else 0.20))
    biomass     = bio_base
    if dry_season and not harmattan:             # savanna fires peak in dry season
        biomass += 0.10
    if precipitation > 20:                       # fires suppressed by heavy rain
        biomass *= max(0.2, 1 - precipitation / 60)
    if shap_data:                                # SHAP-weighted boost if is_dry_season matters
        shap_dict = dict(shap_data) if shap_data else {}
        dry_shap  = shap_dict.get("is_dry_season", 0)
        biomass  += min(0.12, dry_shap * 2)
    biomass = round(min(0.65, max(0.03, biomass)), 3)

    # ── 3. Traffic / Local fraction ───────────────────────────────────────────
    traffic_base = 0.50 if urban else (0.20 if highland else (0.10 if north else 0.18))
    stagnation   = wind_speed < 2
    traffic      = traffic_base
    if stagnation:                               # trapped pollution amplifies local sources
        traffic += 0.15
    if not urban and wind_speed > 8:             # strong wind disperses local sources
        traffic *= 0.6
    traffic = round(min(0.65, max(0.02, traffic)), 3)

    # ── 4. Industrial fraction ────────────────────────────────────────────────
    industry_base = 0.35 if sw else (0.15 if urban else (0.05 if north else 0.08))
    industry      = industry_base
    if shap_data:
        shap_dict  = dict(shap_data) if shap_data else {}
        reg_shap   = shap_dict.get("region_enc", 0)
        industry  += min(0.10, reg_shap * 1.5)
    industry = round(min(0.50, max(0.02, industry)), 3)

    # ── 5. Secondary aerosol fraction ─────────────────────────────────────────
    # Forms in high humidity + photochemistry; higher in wet months
    secondary_base  = 0.10
    wet_months      = month in [4, 5, 6, 7, 8, 9]
    secondary       = secondary_base
    if wet_months:
        secondary  += 0.06
    if humidity > 75:
        secondary  += min(0.05, (humidity - 75) / 100)
    secondary = round(min(0.25, max(0.03, secondary)), 3)

    # ── 6. Normalise to sum to 1.0 ────────────────────────────────────────────
    raw   = {"Dust": dust, "Biomass Burning": biomass, "Traffic": traffic,
             "Industry": industry, "Secondary": secondary}
    total = sum(raw.values())
    norm  = {k: round(v / total, 3) for k, v in raw.items()}

    # Add Other as any residual (keeps it clean)
    norm["Other"] = round(max(0, 1.0 - sum(norm.values())), 3)
    return norm


# ── City-specific source adjustments ─────────────────────────────────────────
# Deltas applied on top of the region-level meteorological base.
# Values are relative boosts (+) or suppression (-); re-normalised after blending.
# Sources: known industrial sites, urban density, proximity to refinery/port/savanna.
_CITY_SOURCE_DELTA = {
    # Far North — dust-dominated but Kousseri is busiest border crossing
    "Kousseri":    {"Dust": +0.10, "Traffic": +0.08},
    "Maroua":      {"Dust": +0.05, "Traffic": +0.05},
    "Yagoua":      {"Biomass Burning": +0.08, "Dust": -0.05},
    "Mokolo":      {"Biomass Burning": +0.06},
    # North
    "Garoua":      {"Traffic": +0.08, "Industry": +0.04},
    "Guider":      {"Biomass Burning": +0.06},
    "Touboro":     {"Biomass Burning": +0.10, "Dust": -0.05},
    # Adamawa
    "Ngaoundere":  {"Traffic": +0.06, "Biomass Burning": +0.05},
    "Meiganga":    {"Biomass Burning": +0.10},
    "Tibati":      {"Biomass Burning": +0.08},
    # Littoral — port + industry
    "Douala":      {"Traffic": +0.12, "Industry": +0.10, "Dust": -0.05},
    "Edea":        {"Industry": +0.18, "Traffic": -0.05},   # aluminium smelter
    "Nkongsamba":  {"Biomass Burning": +0.08, "Traffic": -0.05},
    # Centre
    "Yaounde":     {"Traffic": +0.10, "Industry": +0.04},
    "Mbalmayo":    {"Biomass Burning": +0.06},
    # South West — oil & gas
    "Limbe":       {"Industry": +0.20, "Traffic": +0.04},   # Sonara refinery
    "Buea":        {"Industry": +0.08, "Biomass Burning": +0.05},
    "Kumba":       {"Biomass Burning": +0.08},
    "Mamfe":       {"Biomass Burning": +0.10},
    # West / North West — highland biomass burning
    "Bafoussam":   {"Traffic": +0.08, "Biomass Burning": +0.06},
    "Bamenda":     {"Biomass Burning": +0.10, "Traffic": +0.04},
    "Dschang":     {"Biomass Burning": +0.10},
    "Kumbo":       {"Biomass Burning": +0.12},
    "Wum":         {"Biomass Burning": +0.08},
    # South
    "Kribi":       {"Industry": +0.06, "Secondary": +0.06},  # deepwater port
    "Ebolowa":     {"Biomass Burning": +0.06},
}


def city_source_attribution(city, region, wind_speed, wind_dir, month,
                             precipitation, humidity, pm25, shap_data=None):
    """Per-city source attribution: meteorological base + city-specific adjustments."""
    base = live_source_attribution(
        wind_speed=wind_speed, wind_dir=wind_dir, month=month, region=region,
        precipitation=precipitation, humidity=humidity, pm25=pm25, shap_data=shap_data,
    )
    deltas = _CITY_SOURCE_DELTA.get(city, {})
    if not deltas:
        return base
    adjusted = {}
    for src, frac in base.items():
        adjusted[src] = max(0.0, frac + deltas.get(src, 0.0))
    total = sum(adjusted.values())
    if total == 0:
        return base
    return {k: round(v / total, 3) for k, v in adjusted.items()}



    north = region in NORTHERN
    high  = region in HIGHLAND
    m = ([1.8,2.1,1.4,1.0,0.8,0.65,0.55,0.55,0.50,0.65,1.2,1.6] if north else
         [1.6,1.8,1.3,1.0,0.9,0.75,0.65,0.65,0.60,0.70,1.1,1.4] if high else
         [1.3,1.5,1.2,0.9,0.75,0.65,0.55,0.55,0.45,0.60,0.9,1.2])
    seasonal = [base * x for x in m]
    if north:
        cpd = {"PM2.5":base,"PM10":base*2.5,"Dust":base*1.8,"CO":280,"NO₂":1.2,"O₃":52,"SO₂":0.4,"AOD":0.3}
        src = {"Dust":0.55,"Traffic":0.10,"Biomass":0.15,"Industry":0.05,"Secondary":0.10,"Other":0.05}
    elif region == "Littoral":
        cpd = {"PM2.5":base,"PM10":base*1.5,"Dust":base*0.3,"CO":320,"NO₂":3.8,"O₃":48,"SO₂":0.5,"AOD":0.22}
        src = {"Dust":0.08,"Traffic":0.50,"Biomass":0.12,"Industry":0.15,"Secondary":0.10,"Other":0.05}
    elif region == "South West":
        cpd = {"PM2.5":base,"PM10":base*1.5,"Dust":base*0.2,"CO":260,"NO₂":1.5,"O₃":45,"SO₂":1.2,"AOD":0.20}
        src = {"Dust":0.05,"Traffic":0.20,"Biomass":0.20,"Industry":0.35,"Secondary":0.15,"Other":0.05}
    elif high:
        cpd = {"PM2.5":base,"PM10":base*1.6,"Dust":base*0.5,"CO":250,"NO₂":2.0,"O₃":50,"SO₂":0.3,"AOD":0.25}
        src = {"Dust":0.10,"Traffic":0.20,"Biomass":0.45,"Industry":0.05,"Secondary":0.15,"Other":0.05}
    else:
        cpd = {"PM2.5":base,"PM10":base*1.4,"Dust":base*0.4,"CO":265,"NO₂":1.8,"O₃":47,"SO₂":0.5,"AOD":0.23}
        src = {"Dust":0.15,"Traffic":0.15,"Biomass":0.40,"Industry":0.08,"Secondary":0.17,"Other":0.05}
    return {"seasonal":seasonal,"cpd":cpd,"src":src}
