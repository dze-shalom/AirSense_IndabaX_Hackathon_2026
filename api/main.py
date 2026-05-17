"""
AirSense Cameroon — FastAPI Backend v2
=======================================
Author: Dze-Kum Shalom Chow

Run:  uvicorn api.main:app --reload --port 8000
Docs: http://localhost:8000/docs

Endpoints
---------
System
  GET  /                          Health check + loaded artefact status
  GET  /health                    Detailed service health

Reference data
  GET  /regions                   All regions, cities, coordinates

Prediction
  GET  /predict                   Predict PM2.5 for a city on a date
  GET  /forecast/{city}           7-day forecast (XGBoost + Open-Meteo)

Alerts & thresholds
  GET  /alert-status/{city}       Current AQI level + RL threshold
  GET  /leaderboard               Top-N most polluted cities

Innovations (match dashboard pages 1:1)
  GET  /bfai/{city}               Breath of Fresh Air Index (0–100)
  GET  /source/{city}             Pollution source attribution
  GET  /conformal/{city}          Calibrated 90% prediction interval
  GET  /confidence/{city}         City model confidence tier (H/M/L)
  GET  /alert-prob/{city}         Platt-scaled P(exceed WHO 24h)
  GET  /harmattan/{city}          Harmattan early-warning risk score
  GET  /school-advisory/{city}    School outdoor action level (1–4)
  GET  /agri-advisory/{city}      Agricultural dust/drought alert
  GET  /sms-preview/{city}        Bilingual SMS alert text
  GET  /explain/{city}            Region-specific SHAP fingerprint
  GET  /climate/{city}            CMIP6 climate 2050 projections
  GET  /health-impact/{city}      WHO concentration-response estimates
  GET  /africa-benchmark          Cameroon vs 12 African cities
  GET  /compare                   Side-by-side seasonal profile of 2 cities

IoT
  POST /ingest                    ESP32 sensor data ingestion
  GET  /sensor-feed               Recent sensor readings buffer

Outreach
  GET  /summary/{city}           Shareable plain-text bulletin (WhatsApp/SMS)
  GET  /embed/{city}             Embeddable iframe widget HTML
  POST /push/subscribe           Store Web Push subscription
  POST /push/notify              Send push notification to subscribers
  POST /email/subscribe          Add email to digest list
  GET  /email/digest             Preview today's HTML email digest
  POST /email/send-digest        Send digest to all subscribers
  POST /webhook/whatsapp         Africa's Talking WhatsApp bot webhook
  POST /webhook/sms              Africa's Talking SMS bot webhook
"""

from __future__ import annotations

import json
import logging
import math
import os
import pickle
import sys
import time
from contextlib import asynccontextmanager
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import requests as http_req
import xgboost as xgb
from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s  %(levelname)s  %(message)s",
                    datefmt="%H:%M:%S")
logger = logging.getLogger("airsense_api")

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT   = Path(__file__).parent.parent          # project root
MODELS = ROOT / "models"

# ── Constants (keep in sync with dashboard/config.py) ─────────────────────────
WHO_24H   = 15.0
WHO_ANN   = 5.0
NORTHERN  = {"Far North", "North", "Adamawa"}
HIGHLAND  = {"West", "North West"}
URBAN     = {"Littoral", "Centre"}

SSP_RATES = {
    "SSP1-1.9 (Low)":          0.10,
    "SSP2-4.5 (Intermediate)": 0.22,
    "SSP3-7.0 (High)":         0.35,
    "SSP5-8.5 (Very High)":    0.48,
}
REGION_WARM = {
    "Far North":1.45,"North":1.38,"Adamawa":1.25,"West":1.05,
    "North West":1.05,"Littoral":0.95,"Centre":1.00,
    "East":0.90,"South West":0.88,"South":0.85,
}
PM25_SENS = {
    "Far North":2.8,"North":2.5,"Adamawa":1.9,"West":1.4,
    "North West":1.3,"Littoral":0.9,"Centre":0.8,
    "East":0.7,"South West":0.6,"South":0.5,
}

CITIES: Dict[str, List[tuple]] = {
    "Far North": [("Kousseri",11.85,15.03),("Maroua",10.59,14.32),
                  ("Mokolo",10.74,13.80),("Yagoua",10.34,15.24)],
    "North":     [("Garoua",9.30,13.40),("Guider",9.93,13.95),
                  ("Poli",8.48,13.24),("Touboro",7.77,15.37)],
    "Adamawa":   [("Ngaoundere",7.33,13.58),("Meiganga",6.52,14.30),
                  ("Tibati",6.47,12.63),("Tignere",7.37,12.65)],
    "West":      [("Bafoussam",5.48,10.42),("Dschang",5.45,10.06),
                  ("Foumban",5.72,10.91),("Mbouda",5.62,10.25)],
    "North West":[("Bamenda",5.96,10.16),("Kumbo",6.21,10.68),
                  ("Mbengwi",6.02,10.00),("Wum",6.37,10.07)],
    "Littoral":  [("Douala",4.05,9.70),("Edea",3.80,10.13),
                  ("Loum",4.72,9.74),("Nkongsamba",4.95,9.94)],
    "Centre":    [("Yaounde",3.85,11.50),("Bafia",4.75,11.23),
                  ("Mbalmayo",3.52,11.50),("Akonolinga",3.77,12.25)],
    "East":      [("Bertoua",4.59,13.68),("Batouri",4.43,14.37),
                  ("Abong-Mbang",3.99,13.18),("Yokadouma",3.53,15.05)],
    "South West":[("Buea",4.15,9.24),("Kumba",4.64,9.45),
                  ("Limbe",4.02,9.21),("Mamfe",5.77,9.30)],
    "South":     [("Ebolowa",2.90,11.15),("Ambam",2.38,11.27),
                  ("Kribi",2.94,9.91),("Sangmelima",2.94,11.98)],
}

# Flat lookup: city_name → (lat, lon, region)
CITY_LOOKUP: Dict[str, tuple] = {
    c.lower(): (lat, lon, reg)
    for reg, cities in CITIES.items()
    for c, lat, lon in cities
}

AFRICA_BENCHMARK = [
    ("Maroua, CM",78,True),("Lagos, NG",62,False),("Kano, NG",58,False),
    ("Dakar, SN",48,False),("Douala, CM",42,True),("Bamako, ML",38,False),
    ("Abidjan, CI",35,False),("Accra, GH",32,False),
    ("Addis Ababa, ET",22,False),("Nairobi, KE",16,False),
    ("Buea, CM",14,True),("Cape Town, ZA",12,False),
]

CITY_STATS: Dict[str, Dict] = {
    "Kousseri":  {"mean_pm25":31.2,"who_exc":75.8,"region":"Far North","tier":"Low"},
    "Mokolo":    {"mean_pm25":30.4,"who_exc":74.1,"region":"Far North","tier":"Low"},
    "Maroua":    {"mean_pm25":27.4,"who_exc":68.2,"region":"Far North","tier":"Low"},
    "Garoua":    {"mean_pm25":27.3,"who_exc":67.9,"region":"North","tier":"Low"},
    "Yagoua":    {"mean_pm25":26.1,"who_exc":65.3,"region":"Far North","tier":"Low"},
    "Mbouda":    {"mean_pm25":25.4,"who_exc":62.1,"region":"West","tier":"Low"},
    "Bafoussam": {"mean_pm25":25.1,"who_exc":61.8,"region":"West","tier":"Low"},
    "Dschang":   {"mean_pm25":24.8,"who_exc":60.4,"region":"West","tier":"Low"},
    "Guider":    {"mean_pm25":24.5,"who_exc":59.7,"region":"North","tier":"Medium"},
    "Foumban":   {"mean_pm25":24.2,"who_exc":58.9,"region":"West","tier":"Medium"},
    "Ngaoundere":{"mean_pm25":19.2,"who_exc":42.1,"region":"Adamawa","tier":"Medium"},
    "Douala":    {"mean_pm25":14.6,"who_exc":36.3,"region":"Littoral","tier":"Medium"},
    "Yaounde":   {"mean_pm25":13.9,"who_exc":31.5,"region":"Centre","tier":"High"},
    "Mbalmayo":  {"mean_pm25":13.7,"who_exc":30.8,"region":"Centre","tier":"High"},
    "Edea":      {"mean_pm25":13.5,"who_exc":29.4,"region":"Littoral","tier":"Medium"},
    "Limbe":     {"mean_pm25":13.2,"who_exc":28.1,"region":"South West","tier":"High"},
    "Buea":      {"mean_pm25":12.8,"who_exc":26.7,"region":"South West","tier":"High"},
    "Sangmelima":{"mean_pm25":11.4,"who_exc":18.2,"region":"South","tier":"High"},
    "Ambam":     {"mean_pm25":10.4,"who_exc":15.1,"region":"South","tier":"High"},
    "Ebolowa":   {"mean_pm25":10.2,"who_exc":14.3,"region":"South","tier":"High"},
    "Kribi":     {"mean_pm25": 8.7,"who_exc":13.6,"region":"South","tier":"High"},
}

REGION_SHAP_FALLBACK: Dict[str, List] = {
    "Far North":  [("year",0.140),("daylight_duration",0.128),("precipitation",0.112),
                   ("is_dust_event",0.108),("latitude",0.095),("humidity",0.071),("wind_speed",0.058)],
    "North":      [("precipitation",0.114),("year",0.098),("daylight_duration",0.087),
                   ("is_dust_event",0.082),("humidity",0.071),("latitude",0.065),("is_harmattan",0.052)],
    "Adamawa":    [("precipitation",0.103),("year",0.082),("humidity",0.068),
                   ("daylight_duration",0.063),("region_enc",0.057),("wind_speed",0.048),("temp_mean",0.044)],
    "West":       [("region_enc",0.127),("year",0.098),("precipitation",0.091),
                   ("surface_pressure",0.078),("daylight_duration",0.062),("humidity",0.055),("month_sin",0.049)],
    "North West": [("year",0.097),("precipitation",0.091),("surface_pressure",0.083),
                   ("humidity",0.078),("daylight_duration",0.072),("latitude",0.063),("wind_speed",0.055)],
    "Littoral":   [("year",0.119),("precipitation",0.087),("humidity",0.071),
                   ("day_of_year",0.068),("is_dry_season",0.063),("temp_mean",0.058),("cloud_cover",0.044)],
    "Centre":     [("year",0.104),("precipitation",0.083),("region_enc",0.072),
                   ("month_sin",0.068),("humidity",0.062),("daylight_duration",0.055),("wind_speed",0.047)],
    "East":       [("year",0.088),("precipitation",0.083),("humidity",0.057),
                   ("month_sin",0.054),("daylight_duration",0.051),("temp_mean",0.046),("is_dry_season",0.039)],
    "South West": [("year",0.126),("precipitation",0.091),("longitude",0.082),
                   ("day_of_year",0.071),("humidity",0.067),("wind_speed",0.058),("cloud_cover",0.048)],
    "South":      [("latitude",0.232),("year",0.113),("precipitation",0.098),
                   ("humidity",0.062),("doy_sin",0.058),("daylight_duration",0.051),("temp_mean",0.043)],
}

CONFORMAL_FALLBACK = {
    "global_q_hat": 30.8,
    "empirical_coverage": 0.978,
    "region_intervals": {
        "South":14.1,"East":17.3,"Centre":19.2,"South West":22.4,
        "Littoral":23.6,"Adamawa":26.2,"West":30.9,"North West":41.4,
        "North":48.8,"Far North":56.6,
    },
}

OPEN_METEO_WEATHER_VARS = ",".join([
    "temperature_2m_max","temperature_2m_min","temperature_2m_mean",
    "precipitation_sum","precipitation_hours","wind_speed_10m_max",
    "wind_direction_10m_dominant","shortwave_radiation_sum",
    "et0_fao_evapotranspiration","weather_code","relative_humidity_2m_mean",
    "dew_point_2m_mean","surface_pressure_mean","cloud_cover_mean",
    "wind_speed_100m_max","soil_moisture_0_to_7cm_mean",
    "soil_temperature_0_to_7cm_mean","wet_bulb_temperature_2m_mean",
    "vapour_pressure_deficit_max","daylight_duration","sunshine_duration",
])

# ── AQI helpers (identical to app.py) ─────────────────────────────────────────
AQI_LEVELS = {
    "good":      {"en":"Good",      "fr":"Bon",          "color":"#22c55e","emoji":"✅"},
    "moderate":  {"en":"Moderate",  "fr":"Modéré",       "color":"#f59e0b","emoji":"🟡"},
    "poor":      {"en":"Poor",      "fr":"Mauvais",      "color":"#f97316","emoji":"🟠"},
    "very_poor": {"en":"Very Poor", "fr":"Très Mauvais", "color":"#ef4444","emoji":"🔴"},
    "hazardous": {"en":"Hazardous", "fr":"Dangereux",    "color":"#8b5cf6","emoji":"🟣"},
}

HEALTH_ADVISORY = {
    "good":      {"en":"Air quality is satisfactory. No health impacts expected.",
                  "fr":"La qualité de l'air est satisfaisante."},
    "moderate":  {"en":"Sensitive individuals may experience minor symptoms.",
                  "fr":"Les individus sensibles peuvent ressentir des symptômes mineurs."},
    "poor":      {"en":"General public may experience symptoms. Sensitive groups should avoid outdoors.",
                  "fr":"Les groupes sensibles devraient éviter les activités extérieures."},
    "very_poor": {"en":"Everyone may experience serious health effects. Avoid outdoor activities.",
                  "fr":"Tout le monde peut ressentir des effets graves sur la santé."},
    "hazardous": {"en":"Health emergency. Stay indoors and seek medical advice immediately.",
                  "fr":"Urgence sanitaire. Restez à l'intérieur immédiatement."},
}

def get_aqi_level(pm25: float) -> str:
    if pm25 < 5:    return "good"
    if pm25 < 15:   return "moderate"
    if pm25 < 30:   return "poor"
    if pm25 < 60:   return "very_poor"
    return "hazardous"


# ══════════════════════════════════════════════════════════════════════════════
# APP STARTUP — load all artefacts once
# ══════════════════════════════════════════════════════════════════════════════

# Global state
STATE: Dict[str, Any] = {
    "model":       None,   # xgb.XGBRegressor
    "le_city":     None,   # LabelEncoder
    "le_region":   None,   # LabelEncoder
    "features":    [],     # list of feature names
    "conformal":   None,   # conformal_intervals.json
    "city_conf":   None,   # city_confidence_tiers.json
    "platt":       None,   # platt_alert_calibration.json
    "region_shap": None,   # region_shap.pkl
    "climate":     None,   # climate_projections.json
    "rl":          None,   # rl_thresholds.json
}

sensor_buffer: List[Dict] = []   # ESP32 readings ring buffer

# ── Outreach module-level state ────────────────────────────────────────────────
_PUSH_SUBSCRIPTIONS: Dict[str, dict] = {}   # Web Push endpoint → subscription object
_EMAIL_SUBS: List[str] = []                 # email digest subscriber list

# pywebpush optional dependency
try:
    from pywebpush import webpush, WebPushException  # type: ignore
    _WEBPUSH_AVAILABLE = True
except ImportError:
    _WEBPUSH_AVAILABLE = False
    logger.warning("pywebpush not installed — /push/notify will be disabled")


def _load_artefacts() -> None:
    logger.info("Loading AirSense artefacts from %s …", MODELS)

    # XGBoost model
    try:
        mp = MODELS / "xgb_pm25.json"
        STATE["model"] = xgb.XGBRegressor()
        STATE["model"].load_model(str(mp))
        logger.info("✓ XGBoost model loaded from %s", mp)
    except Exception as e:
        logger.warning("✗ XGBoost model not loaded: %s", e)

    # Label encoders
    try:
        with open(MODELS / "label_encoders.pkl", "rb") as f:
            enc = pickle.load(f)
        STATE["le_city"]   = enc["city"]
        STATE["le_region"] = enc["region"]
        logger.info("✓ Label encoders loaded  (%d cities, %d regions)",
                    len(STATE["le_city"].classes_), len(STATE["le_region"].classes_))
    except Exception as e:
        logger.warning("✗ Label encoders not loaded: %s", e)

    # Features list
    try:
        with open(MODELS / "features.json") as f:
            fi = json.load(f)
        STATE["features"] = fi["features"]
        logger.info("✓ Feature list loaded  (%d features)", len(STATE["features"]))
    except Exception as e:
        logger.warning("✗ Features not loaded: %s", e)

    # Conformal intervals
    try:
        with open(MODELS / "conformal_intervals.json") as f:
            STATE["conformal"] = json.load(f)
        logger.info("✓ Conformal intervals loaded")
    except Exception as e:
        logger.warning("✗ Conformal — using fallback: %s", e)
        STATE["conformal"] = CONFORMAL_FALLBACK

    # City confidence tiers
    try:
        with open(MODELS / "city_confidence_tiers.json") as f:
            STATE["city_conf"] = json.load(f)
        logger.info("✓ City confidence tiers loaded (%d cities)", len(STATE["city_conf"]))
    except Exception as e:
        logger.warning("✗ City confidence not loaded: %s", e)

    # Platt alert calibration
    try:
        with open(MODELS / "platt_alert_calibration.json") as f:
            STATE["platt"] = json.load(f)
        logger.info("✓ Platt calibration loaded  coef=%.4f", STATE["platt"]["coef"])
    except Exception as e:
        logger.warning("✗ Platt not loaded — using defaults: %s", e)
        STATE["platt"] = {"coef": 0.2221, "intercept": -3.0372}

    # Region SHAP
    try:
        with open(MODELS / "region_shap.pkl", "rb") as f:
            STATE["region_shap"] = pickle.load(f)
        logger.info("✓ Region SHAP loaded  (%d regions)", len(STATE["region_shap"]))
    except Exception as e:
        logger.warning("✗ Region SHAP not loaded — using fallback: %s", e)
        STATE["region_shap"] = REGION_SHAP_FALLBACK

    # Climate projections
    try:
        with open(MODELS / "climate_projections.json") as f:
            STATE["climate"] = json.load(f)
        logger.info("✓ Climate projections loaded")
    except Exception as e:
        logger.warning("✗ Climate projections not loaded: %s", e)

    # RL thresholds
    try:
        with open(MODELS / "rl_thresholds.json") as f:
            STATE["rl"] = json.load(f)
        thrs = STATE["rl"].get("thresholds", {})
        logger.info("✓ RL thresholds loaded  (%d cities)", len(thrs))
    except Exception as e:
        logger.warning("✗ RL thresholds not loaded: %s", e)

    logger.info("AirSense API ready.")


@asynccontextmanager
async def lifespan(app_: FastAPI):
    _load_artefacts()
    yield


app = FastAPI(
    title="AirSense Cameroon API",
    description="AI-powered air quality prediction for Cameroon",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ══════════════════════════════════════════════════════════════════════════════
# CORE HELPERS (mirror app.py functions exactly)
# ══════════════════════════════════════════════════════════════════════════════

def lookup_city(city: str) -> tuple:
    """Returns (lat, lon, region) or raises 404."""
    key = city.lower()
    if key not in CITY_LOOKUP:
        raise HTTPException(404, f"City '{city}' not found. See GET /regions for valid names.")
    return CITY_LOOKUP[key]


def get_rl_threshold(city: str) -> float:
    """REINFORCE-learned alert threshold for a city, or formula fallback."""
    if STATE["rl"]:
        thrs = STATE["rl"].get("thresholds", {})
        if city in thrs:
            return float(thrs[city])
    # Fallback: match app.py formula
    stats = CITY_STATS.get(city, {})
    base  = stats.get("mean_pm25", 20.0)
    return round(min(max(base * 1.4, 10.0), 90.0), 1)


def get_conf_interval(region: str) -> float:
    """90% conformal prediction interval half-width for a region."""
    if STATE["conformal"]:
        c = STATE["conformal"]
        # Accept both 'global_q_hat' (full save) and 'q_hat' (simplified save)
        global_q = c.get("global_q_hat") or c.get("q_hat", 30.8)
        return float(c.get("region_intervals", {}).get(region, global_q))
    return CONFORMAL_FALLBACK["region_intervals"].get(region, 30.8)


def get_alert_prob(pm25: float) -> float:
    """Platt-scaled P(PM2.5 > WHO 24h) — matches app.py get_alert_prob()."""
    p    = STATE["platt"] or {"coef": 0.2221, "intercept": -3.0372}
    z    = p["coef"] * pm25 + p["intercept"]
    return float(1 / (1 + math.exp(-z)))


def compute_bfai(pm25: float, wind: float, hum: float, region: str) -> int:
    """Breath of Fresh Air Index 0–100 — keep in sync with dashboard/utils/helpers.py."""
    pm_s  = max(0, round(100 - (pm25 / 150) * 80))
    wi_s  = min(100, round((wind / 8) * 60 + 20))
    hu_s  = min(100, round((hum - 40) * 1.2)) if hum > 40 else 30
    return max(0, min(100, round(0.50 * pm_s + 0.25 * wi_s + 0.25 * hu_s)))


def classify_source(wind_speed: float, wind_dir: float,
                    region: str, month: int) -> tuple:
    """Source attribution — keep in sync with dashboard/utils/helpers.py."""
    north     = region in NORTHERN
    harmattan = month in [11, 12, 1, 2] and north and (wind_dir > 270 or wind_dir < 90)
    if harmattan and wind_speed > 3:
        return "transported", min(95, 60 + int(wind_speed * 5))
    if wind_speed < 2:
        return "stagnation",  min(90, 50 + int((2 - wind_speed) * 20))
    if region in URBAN:
        return "local",       min(85, 55 + int(wind_speed * 3))
    return "mixed", 60


def health_impact(pm25: float) -> tuple:
    """WHO concentration-response (excess_resp, hospital_risk_pct, lost_days)."""
    return (
        round((pm25 / 10) * 3.2,  1),
        round(min(99, (pm25 / 50) * 15), 1),
        round((pm25 / 10) * 1.8,  1),
    )


def project_pm25(base: float, region: str, year: int, rate: float) -> float:
    """CMIP6 PM2.5 projection — identical to app.py project()."""
    decades  = (year - 2025) / 10.0
    amp      = REGION_WARM.get(region, 1.0)
    sens     = PM25_SENS.get(region, 1.0)
    delta_T  = rate * decades * amp
    delta_pm = delta_T * sens
    dry_amp  = 1 + max(0, (rate - 0.22) * 0.45) if region in NORTHERN else 1.0
    return max(base * 0.9, base + delta_pm * dry_amp)


def seasonal_profile(region: str, base_pm25: float) -> List[float]:
    """Monthly PM2.5 multipliers — identical to app.py city_profile()."""
    north = region in NORTHERN
    high  = region in HIGHLAND
    m = ([1.8,2.1,1.4,1.0,0.8,0.65,0.55,0.55,0.50,0.65,1.2,1.6] if north else
         [1.6,1.8,1.3,1.0,0.9,0.75,0.65,0.65,0.60,0.70,1.1,1.4] if high else
         [1.3,1.5,1.2,0.9,0.75,0.65,0.55,0.55,0.45,0.60,0.9,1.2])
    return [round(base_pm25 * x, 2) for x in m]


def harmattan_risk_score(pm25: float, wind: float, wind_dir: float,
                         hum: float, region: str, month: int) -> int:
    """0–100 Harmattan risk — identical to page_forecast() logic in app.py."""
    north     = region in NORTHERN
    north_dir = max(0.0, math.cos(math.radians(wind_dir)))
    nc        = north_dir * wind
    s_bonus   = 30 if month in [11, 12, 1, 2] else 0
    r_bonus   = 30 if north else 0
    h_bonus   = max(0, (50 - hum) * 0.8)
    return min(100, round(nc * 5 + s_bonus + r_bonus + h_bonus))


def build_feature_vector(
    date_str: str, lat: float, lon: float,
    city_enc: int, region_enc: int, region: str,
    weather: Dict[str, Any], feature_list: List[str],
) -> np.ndarray:
    """
    Construct the 44-feature vector in the exact order expected by the model.
    Mirrors build_features() in app.py 1:1.
    """
    dt    = pd.to_datetime(date_str)
    month = dt.month; doy = dt.dayofyear; year = dt.year
    ws    = weather.get("wind_speed_10m_max", 10)
    rad   = math.radians(weather.get("wind_direction_10m_dominant", 180))
    tdm   = weather.get("temperature_2m_mean", 25)
    dp    = weather.get("dew_point_2m_mean", 15)
    prec  = weather.get("precipitation_sum", 0) or 0
    sh    = weather.get("sunshine_duration", 30000) or 30000
    dl    = weather.get("daylight_duration", 43200) or 43200
    north = region in NORTHERN

    def tet(T): return 0.6108 * math.exp((17.27 * T) / (T + 237.3))
    vpd = max(0.0, tet(tdm) - tet(dp))

    feats = {
        "latitude":             lat,
        "longitude":            lon,
        "region_enc":           region_enc,
        "city_enc":             city_enc,
        "month":                month,
        "day_of_year":          doy,
        "year":                 year,
        "month_sin":            math.sin(2 * math.pi * month / 12),
        "month_cos":            math.cos(2 * math.pi * month / 12),
        "doy_sin":              math.sin(2 * math.pi * doy / 365),
        "doy_cos":              math.cos(2 * math.pi * doy / 365),
        "temp_max":             weather.get("temperature_2m_max", 30),
        "temp_min":             weather.get("temperature_2m_min", 18),
        "temp_mean":            tdm,
        "apparent_temp_mean":   weather.get("apparent_temperature_mean", tdm),
        "precipitation":        prec,
        "precipitation_hours":  weather.get("precipitation_hours", 0) or 0,
        "wind_speed":           ws,
        "wind_direction":       weather.get("wind_direction_10m_dominant", 180),
        "wind_u":               -ws * math.sin(rad),
        "wind_v":               -ws * math.cos(rad),
        "solar_radiation":      weather.get("shortwave_radiation_sum", 18),
        "evapotranspiration":   weather.get("et0_fao_evapotranspiration", 5),
        "daylight_duration":    dl,
        "weather_code_cat":     min(weather.get("weather_code", 3) or 3, 9),
        "humidity":             weather.get("relative_humidity_2m_mean", 60),
        "dew_point":            dp,
        "surface_pressure":     weather.get("surface_pressure_mean", 950),
        "cloud_cover":          weather.get("cloud_cover_mean", 50),
        "wind_100m":            weather.get("wind_speed_100m_max", 20),
        "soil_moisture":        weather.get("soil_moisture_0_to_7cm_mean", 0.2) or 0.2,
        "soil_temp":            weather.get("soil_temperature_0_to_7cm_mean", 25),
        "wet_bulb_temp":        weather.get("wet_bulb_temperature_2m_mean", 20),
        "vpd":                  round(vpd, 4),
        "vpd_max":              weather.get("vapour_pressure_deficit_max", 2.0) or 2.0,
        "temp_range":           weather.get("temperature_2m_max", 30) - weather.get("temperature_2m_min", 18),
        "sunshine_ratio":       min(sh / max(dl, 1), 1.0),
        "is_harmattan":         int(month in [11, 12, 1, 2] and north),
        "is_dry_season":        int(month in [11, 12, 1, 2, 3]),
        "is_no_rain":           int(prec == 0),
        "is_no_wind":           int(ws < 2),
        "is_heat_stress":       int(tdm > 40),
        "is_dust_event":        0,
        "is_haze_fog":          int(weather.get("weather_code", 3) in [45, 48]),
    }
    return np.array([[feats.get(f, 0) for f in feature_list]])


def fetch_open_meteo(lat: float, lon: float) -> Optional[Dict]:
    """Fetch 7-day forecast from Open-Meteo — same as app.py fetch_forecast()."""
    try:
        r = http_req.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon,
                "daily":    OPEN_METEO_WEATHER_VARS,
                "timezone": "Africa/Douala",
                "forecast_days": 7,
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("Open-Meteo failed: %s", e)
        return None


def predict_day(date_str: str, lat: float, lon: float,
                city: str, region: str, weather: Dict) -> Dict:
    """Run model for one day, return pm25 + confidence interval."""
    model   = STATE["model"]
    le_c    = STATE["le_city"]
    le_r    = STATE["le_region"]
    feats   = STATE["features"]

    if not (model and le_c and le_r and feats):
        # Fall back to city stat if model unavailable
        return {
            "pm25": CITY_STATS.get(city, {}).get("mean_pm25", 15.0),
            "source": "fallback_stat",
        }

    try:
        ce = list(le_c.classes_).index(city) if city in le_c.classes_ else 0
        re = list(le_r.classes_).index(region) if region in le_r.classes_ else 0
    except Exception:
        ce = re = 0

    fv    = build_feature_vector(date_str, lat, lon, ce, re, region, weather, feats)
    pred  = float(np.expm1(model.predict(fv)[0]))
    pred  = max(0.5, pred)
    return {"pm25": round(pred, 2), "source": "xgboost"}


# ══════════════════════════════════════════════════════════════════════════════
# Pydantic models
# ══════════════════════════════════════════════════════════════════════════════

class ESP32Payload(BaseModel):
    device_id:   str
    city:        str
    timestamp:   str
    pm25:        Optional[float] = None
    temperature: Optional[float] = None
    humidity:    Optional[float] = None
    wind_speed:  Optional[float] = None
    lat:         Optional[float] = None
    lon:         Optional[float] = None


# ══════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ══════════════════════════════════════════════════════════════════════════════

# ── System ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["System"])
def root():
    return {
        "service": "AirSense Cameroon API v2.0",
        "status":  "running",
        "artefacts": {
            "xgboost_model":       STATE["model"] is not None,
            "label_encoders":      STATE["le_city"] is not None,
            "features":            len(STATE["features"]),
            "conformal_intervals": STATE["conformal"] is not None,
            "city_confidence":     STATE["city_conf"] is not None,
            "platt_calibration":   STATE["platt"] is not None,
            "region_shap":         STATE["region_shap"] is not None,
            "climate_projections": STATE["climate"] is not None,
            "rl_thresholds":       STATE["rl"] is not None,
        },
        "docs": "/docs",
    }


@app.get("/health", tags=["System"])
def health():
    return {
        "status":    "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "artefacts": {k: (v is not None) for k, v in STATE.items()},
        "sensor_buffer_size": len(sensor_buffer),
    }


# ── Reference data ────────────────────────────────────────────────────────────

@app.get("/regions", tags=["Reference"])
def get_regions():
    """All regions, cities, coordinates and baseline stats."""
    out = {}
    for region, clist in CITIES.items():
        out[region] = [
            {
                "city":    c,
                "lat":     lat,
                "lon":     lon,
                "stats":   CITY_STATS.get(c, {}),
                "rl_threshold": get_rl_threshold(c),
            }
            for c, lat, lon in clist
        ]
    return {"regions": out, "total_cities": sum(len(v) for v in CITIES.values())}


# ── Prediction ────────────────────────────────────────────────────────────────

@app.get("/predict", tags=["Prediction"])
def predict(
    city:  str = Query(..., example="Douala"),
    date:  str = Query(..., example="2025-06-15"),
    lang:  str = Query("en"),
):
    """Predict PM2.5 for a city on a specific date."""
    lat, lon, region = lookup_city(city)
    try:
        dt = pd.to_datetime(date)
    except Exception:
        raise HTTPException(400, "Invalid date — use YYYY-MM-DD")

    # Build a minimal weather dict from climatological defaults
    month    = dt.month
    is_north = region in NORTHERN
    weather  = {
        "temperature_2m_max": 34 if is_north else 28,
        "temperature_2m_min": 20 if is_north else 17,
        "temperature_2m_mean":27 if is_north else 24,
        "precipitation_sum":  2 if month in [11,12,1,2] else 60,
        "wind_speed_10m_max": 10 if region in NORTHERN else 6,
        "relative_humidity_2m_mean": 35 if is_north and month in [11,12,1,2] else 70,
        "weather_code": 3,
    }

    result    = predict_day(date, lat, lon, city, region, weather)
    pm25      = result["pm25"]
    level     = get_aqi_level(pm25)
    rl_thr    = get_rl_threshold(city)
    alert_p   = get_alert_prob(pm25)
    q_hat     = get_conf_interval(region)

    return {
        "city":       city,
        "region":     region,
        "date":       date,
        "pm25":       pm25,
        "unit":       "μg/m³",
        "source":     result["source"],
        "aqi": {
            "level":   level,
            "label":   AQI_LEVELS[level][lang] if lang in ("en","fr") else AQI_LEVELS[level]["en"],
            "color":   AQI_LEVELS[level]["color"],
            "emoji":   AQI_LEVELS[level]["emoji"],
            "advisory":HEALTH_ADVISORY[level][lang] if lang in ("en","fr") else HEALTH_ADVISORY[level]["en"],
        },
        "who_24h_exceeded":      pm25 > WHO_24H,
        "rl_alert_threshold":    rl_thr,
        "rl_alert_triggered":    pm25 > rl_thr,
        "alert_probability_pct": round(alert_p * 100, 1),
        "conformal_interval":    {
            "half_width": q_hat,
            "lower":      round(max(0, pm25 - q_hat), 2),
            "upper":      round(pm25 + q_hat, 2),
            "coverage":   "90%",
        },
    }


@app.get("/forecast/{city}", tags=["Prediction"])
def forecast(
    city: str,
    lang: str = Query("en"),
):
    """
    7-day XGBoost forecast using live Open-Meteo weather data.
    Identical pipeline to app.py predict_7day().
    """
    lat, lon, region = lookup_city(city)
    fd = fetch_open_meteo(lat, lon)
    q_hat = get_conf_interval(region)

    if not fd or "daily" not in fd:
        raise HTTPException(503, "Open-Meteo API unavailable — try again shortly")

    daily  = fd["daily"]
    dates  = daily.get("time", [])
    result = []

    for i, date_str in enumerate(dates):
        weather = {k: (v[i] if isinstance(v, list) and i < len(v) else None)
                   for k, v in daily.items() if k != "time"}

        pred  = predict_day(date_str, lat, lon, city, region, weather)
        pm25  = pred["pm25"]
        conf  = max(3.0, 1.5 * (i + 1))   # growing uncertainty
        level = get_aqi_level(pm25)
        wind  = weather.get("wind_speed_10m_max") or 10
        hum   = weather.get("relative_humidity_2m_mean") or 60
        wdir  = weather.get("wind_direction_10m_dominant") or 180
        month = pd.to_datetime(date_str).month

        src_type, src_pct = classify_source(wind, wdir, region, month)
        bfai_score        = compute_bfai(pm25, wind, hum, region)
        harm_risk         = harmattan_risk_score(pm25, wind, wdir, hum, region, month)

        result.append({
            "date":        date_str,
            "pm25":        pm25,
            "pm25_low":    round(max(0, pm25 - q_hat), 2),
            "pm25_high":   round(pm25 + q_hat, 2),
            "naive_low":   round(max(0, pm25 - conf), 2),
            "naive_high":  round(pm25 + conf, 2),
            "aqi": {
                "level":  level,
                "label":  AQI_LEVELS[level][lang] if lang in ("en","fr") else AQI_LEVELS[level]["en"],
                "color":  AQI_LEVELS[level]["color"],
                "emoji":  AQI_LEVELS[level]["emoji"],
            },
            "weather": {
                "temp_max":  weather.get("temperature_2m_max"),
                "temp_min":  weather.get("temperature_2m_min"),
                "precip_mm": weather.get("precipitation_sum"),
                "humidity":  hum,
                "wind_kmh":  wind,
                "wmo_code":  weather.get("weather_code"),
            },
            "bfai":            bfai_score,
            "harmattan_risk":  harm_risk,
            "source_type":     src_type,
            "source_pct":      src_pct,
            "alert_prob_pct":  round(get_alert_prob(pm25) * 100, 1),
            "rl_alert":        pm25 > get_rl_threshold(city),
            "who_exceeded":    pm25 > WHO_24H,
        })

    return {
        "city":                city,
        "region":              region,
        "lat":                 lat,
        "lon":                 lon,
        "conformal_q_hat":     q_hat,
        "conformal_coverage":  "90%",
        "rl_threshold":        get_rl_threshold(city),
        "forecast":            result,
    }


# ── Alerts & thresholds ───────────────────────────────────────────────────────

@app.get("/alert-status/{city}", tags=["Alerts"])
def alert_status(city: str, lang: str = Query("en")):
    """Current alert level + RL threshold + alert probability for a city."""
    lat, lon, region = lookup_city(city)
    stats  = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25   = stats["mean_pm25"]
    level  = get_aqi_level(pm25)
    rl_thr = get_rl_threshold(city)
    _conf_entry = (STATE["city_conf"] or {}).get(city, stats.get("tier", "Medium"))
    tier = _conf_entry.get("tier", "Medium") if isinstance(_conf_entry, dict) else str(_conf_entry)

    return {
        "city":                  city,
        "region":                region,
        "pm25":                  pm25,
        "who_exc_pct":           stats.get("who_exc", 0),
        "aqi": {
            "level":   level,
            "label":   AQI_LEVELS[level][lang] if lang in ("en","fr") else AQI_LEVELS[level]["en"],
            "color":   AQI_LEVELS[level]["color"],
            "emoji":   AQI_LEVELS[level]["emoji"],
            "advisory":HEALTH_ADVISORY[level][lang] if lang in ("en","fr") else HEALTH_ADVISORY[level]["en"],
        },
        "rl_threshold":          rl_thr,
        "rl_alert_triggered":    pm25 > rl_thr,
        "alert_probability_pct": round(get_alert_prob(pm25) * 100, 1),
        "conformal_q_hat":       get_conf_interval(region),
        "model_confidence_tier": tier,
    }


@app.get("/leaderboard", tags=["Alerts"])
def leaderboard(
    top_n: int = Query(10, le=40),
    lang:  str = Query("en"),
):
    """Top-N most polluted cities with full alert context."""
    ranked = sorted(CITY_STATS.items(), key=lambda x: -x[1]["mean_pm25"])[:top_n]
    out    = []
    for i, (city_name, stats) in enumerate(ranked):
        pm25  = stats["mean_pm25"]
        level = get_aqi_level(pm25)
        out.append({
            "rank":    i + 1,
            "city":    city_name,
            "region":  stats["region"],
            "pm25":    pm25,
            "who_exc": stats["who_exc"],
            "tier":    stats.get("tier", "Medium"),
            "aqi": {
                "level": level,
                "label": AQI_LEVELS[level][lang] if lang in ("en","fr") else AQI_LEVELS[level]["en"],
                "color": AQI_LEVELS[level]["color"],
                "emoji": AQI_LEVELS[level]["emoji"],
            },
            "rl_threshold":       get_rl_threshold(city_name),
            "alert_prob_pct":     round(get_alert_prob(pm25) * 100, 1),
            "conformal_q_hat":    get_conf_interval(stats["region"]),
        })
    return {"leaderboard": out, "generated_at": datetime.utcnow().isoformat() + "Z"}


# ── Innovations (match all dashboard pages) ───────────────────────────────────

@app.get("/bfai/{city}", tags=["Innovations"])
def bfai_endpoint(city: str, lang: str = Query("en")):
    """
    Breath of Fresh Air Index (Innovation #1).
    Composite 0–100 outdoor safety score: PM2.5 (50%) + Wind (25%) + Humidity (25%).
    """
    lat, lon, region = lookup_city(city)
    stats = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25  = stats["mean_pm25"]
    wind  = 5.0
    hum   = 65.0
    score = compute_bfai(pm25, wind, hum, region)
    pm_s  = max(0, round(100 - (pm25 / 150) * 80))
    wi_s  = min(100, round((wind / 8) * 60 + 20))
    hu_s  = min(100, round((hum - 40) * 1.2)) if hum > 40 else 30

    labels = {"en": ["Hazardous","Poor","Moderate","Good","Excellent"],
              "fr": ["Dangereux","Mauvais","Modéré","Bon","Excellent"]}
    idx    = 0 if score<20 else 1 if score<40 else 2 if score<60 else 3 if score<80 else 4
    lbl_l  = labels.get(lang, labels["en"])

    return {
        "city":    city,
        "region":  region,
        "bfai":    score,
        "label":   lbl_l[idx],
        "components": {
            "pm25_score":    pm_s,
            "wind_score":    wi_s,
            "humidity_score":hu_s,
        },
        "interpretation": {
            "en": "Safe for outdoor activities" if score>=60 else
                  "Limit outdoor time" if score>=40 else "Stay indoors",
            "fr": "Activités extérieures sûres" if score>=60 else
                  "Limitez le temps dehors" if score>=40 else "Restez à l'intérieur",
        }.get(lang, "en"),
    }


@app.get("/source/{city}", tags=["Innovations"])
def source_attribution(city: str, lang: str = Query("en")):
    """
    Pollution source attribution (Innovation #2).
    Classifies as: transported (Saharan dust), local, stagnation, or mixed.
    """
    lat, lon, region = lookup_city(city)
    month  = datetime.now().month
    wind   = 5.0
    wdir   = 45.0 if region in NORTHERN else 180.0

    src_type, pct = classify_source(wind, wdir, region, month)

    SOURCE_EN = {
        "transported": ("Transported Saharan Dust",
                        "Harmattan wind from the Bodélé Depression (Chad)"),
        "local":       ("Local Combustion",
                        "Traffic, generators, cooking fires, industry"),
        "stagnation":  ("Air Stagnation",
                        "Low wind trapping local particulate matter"),
        "mixed":       ("Mixed Sources",
                        "Local emissions combined with regional transport"),
    }
    SOURCE_FR = {
        "transported": ("Poussière Saharienne Transportée",
                        "Vent Harmattan depuis la Dépression du Bodélé"),
        "local":       ("Combustion Locale",
                        "Trafic, générateurs, feux de cuisine, industrie"),
        "stagnation":  ("Stagnation de l'Air",
                        "Vent faible piégeant les particules locales"),
        "mixed":       ("Sources Mixtes",
                        "Émissions locales + transport régional"),
    }
    src_dict = SOURCE_FR if lang == "fr" else SOURCE_EN
    title, desc = src_dict[src_type]

    return {
        "city":                city,
        "region":              region,
        "source_type":         src_type,
        "attribution_pct":     pct,
        "title":               title,
        "description":         desc,
        "is_harmattan_season": month in [11, 12, 1, 2] and region in NORTHERN,
        "wind_speed_kmh":      wind,
        "wind_direction_deg":  wdir,
    }


@app.get("/conformal/{city}", tags=["Innovations"])
def conformal_endpoint(city: str):
    """
    Calibrated 90% conformal prediction interval (Innovation #3).
    Returns region-specific half-width ± μg/m³.
    """
    lat, lon, region = lookup_city(city)
    q_hat = get_conf_interval(region)
    stats = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25  = stats["mean_pm25"]
    meta  = STATE["conformal"] or CONFORMAL_FALLBACK

    return {
        "city":               city,
        "region":             region,
        "q_hat":              q_hat,
        "unit":               "μg/m³",
        "coverage_target":    "90%",
        "empirical_coverage": meta.get("empirical_coverage", 0.978),
        "example": {
            "predicted_pm25": pm25,
            "interval_lower": round(max(0, pm25 - q_hat), 2),
            "interval_upper": round(pm25 + q_hat, 2),
        },
        "calibration_size": meta.get("calibration_size", 7280),
        "interpretation": (
            f"For {region}, any prediction carries ±{q_hat:.1f} μg/m³ "
            f"uncertainty at 90% confidence. "
            + ("Wider than global average — Harmattan episodicity makes "
               "northern cities harder to predict precisely."
               if region in NORTHERN else
               "Below global average — southern regions have stable "
               "meteorological drivers.")
        ),
    }


@app.get("/confidence/{city}", tags=["Innovations"])
def confidence_tier(city: str):
    """
    City model confidence tier (Innovation #4).
    High = MAE ≤ 4.6 μg/m³ | Medium = ≤ 6.9 | Low = above 6.9.
    """
    lat, lon, region = lookup_city(city)
    conf = STATE["city_conf"] or {}
    info = conf.get(city, CITY_STATS.get(city, {}).get("tier"))

    if isinstance(info, dict):
        tier = info.get("tier", "Medium")
        mae  = info.get("mae")
    else:
        tier = info or "Medium"
        mae  = None

    TIER_DESC = {
        "High":   {"en":"Model predictions are highly reliable for this city. "
                        "MAE ≤ 4.6 μg/m³.",
                   "fr":"Les prévisions du modèle sont très fiables pour cette ville."},
        "Medium": {"en":"Moderate reliability. MAE between 4.6 and 6.9 μg/m³.",
                   "fr":"Fiabilité modérée. MAE entre 4.6 et 6.9 μg/m³."},
        "Low":    {"en":"Lower reliability. City has episodic burning or dust "
                        "events not captured by weather features. MAE > 6.9 μg/m³.",
                   "fr":"Fiabilité moindre. Brûlage épisodique ou événements de "
                        "poussière non capturés par les données météo."},
    }

    return {
        "city":   city,
        "region": region,
        "tier":   tier,
        "mae":    mae,
        "description_en": TIER_DESC[tier]["en"],
        "description_fr": TIER_DESC[tier]["fr"],
        "color":  {"High": "#22c55e", "Medium": "#f59e0b", "Low": "#f97316"}[tier],
    }


@app.get("/alert-prob/{city}", tags=["Innovations"])
def alert_probability(city: str):
    """
    Platt-scaled alert probability (Innovation #5).
    P(PM2.5 > WHO 24h limit) derived from logistic regression on test predictions.
    """
    lat, lon, region = lookup_city(city)
    stats  = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25   = stats["mean_pm25"]
    platt  = STATE["platt"] or {"coef": 0.2221, "intercept": -3.0372}
    prob   = get_alert_prob(pm25)

    # Calibration curve (5 example PM2.5 values)
    curve  = [
        {"pm25": v, "prob_pct": round(get_alert_prob(v) * 100, 1)}
        for v in [5, 10, 15, 25, 40, 60]
    ]

    return {
        "city":            city,
        "region":          region,
        "current_pm25":    pm25,
        "alert_prob_pct":  round(prob * 100, 1),
        "formula":         f"P = sigmoid({platt['coef']:.4f} × PM2.5 + {platt['intercept']:.4f})",
        "who_threshold":   WHO_24H,
        "calibration_curve": curve,
        "interpretation": ("High risk — alert likely" if prob > 0.7 else
                           "Moderate risk — monitor closely" if prob > 0.35 else
                           "Low risk — within safe range"),
    }


@app.get("/harmattan/{city}", tags=["Innovations"])
def harmattan_warning(city: str, lang: str = Query("en")):
    """
    Harmattan early warning system (Innovation #6).
    0–100 risk score based on wind direction, season, humidity and region.
    """
    lat, lon, region = lookup_city(city)
    month  = datetime.now().month
    wind   = 12.0 if region in NORTHERN and month in [11,12,1,2] else 6.0
    wdir   = 30.0 if region in NORTHERN else 180.0
    hum    = 25.0 if region in NORTHERN and month in [11,12,1,2] else 65.0
    stats  = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25   = stats["mean_pm25"]

    risk = harmattan_risk_score(pm25, wind, wdir, hum, region, month)
    if   risk >= 70: status, color = ("ACTIVE",      "#ef4444")
    elif risk >= 40: status, color = ("APPROACHING", "#f97316")
    elif risk >= 20: status, color = ("WATCH",       "#f59e0b")
    else:            status, color = ("CLEAR",       "#22c55e")

    is_season = month in [11, 12, 1, 2]
    msg = {
        "en": {
            "ACTIVE":      "Harmattan dust transport active. Restrict outdoor activities. "
                           "Health advisories for vulnerable groups.",
            "APPROACHING": "Harmattan conditions developing. Monitor PM2.5. "
                           "Alert sensitive groups.",
            "WATCH":       "Seasonal watch — Harmattan possible within 2 weeks. "
                           "Prepare health advisories.",
            "CLEAR":       "No Harmattan threat. Normal outdoor activities permitted.",
        },
        "fr": {
            "ACTIVE":      "Transport de poussière Harmattan actif. Limitez les activités extérieures.",
            "APPROACHING": "Conditions Harmattan en développement. Surveillez le PM2.5.",
            "WATCH":       "Surveillance saisonnière — Harmattan possible dans 2 semaines.",
            "CLEAR":       "Aucune menace Harmattan. Activités extérieures normales.",
        },
    }

    return {
        "city":                city,
        "region":              region,
        "risk_score":          risk,
        "status":              status,
        "color":               color,
        "is_harmattan_season": is_season,
        "month":               month,
        "message":             msg.get(lang, msg["en"])[status],
        "primary_driver":      "northern_wind_season" if is_season and region in NORTHERN
                               else "non_harmattan",
    }


@app.get("/school-advisory/{city}", tags=["Innovations"])
def school_advisory(city: str, lang: str = Query("en")):
    """
    School outdoor advisory (Innovation #7).
    4 action levels based on PM2.5 + estimated O₃.
    """
    lat, lon, region = lookup_city(city)
    stats  = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25   = stats["mean_pm25"]
    temp   = 28.0
    o3_est = max(0, 30 + (temp - 25) * 2.8)

    if pm25 <= 15 and o3_est <= 60:
        level, col = 1, "#22c55e"
        en = "SAFE — All outdoor activities permitted including physical education"
        fr = "SÛR — Toutes les activités extérieures autorisées"
    elif pm25 <= 35 and o3_est <= 80:
        level, col = 2, "#f59e0b"
        en = "CAUTION — Limit vigorous outdoor activity. Shorten PE sessions."
        fr = "PRÉCAUTION — Limitez les activités extérieures vigoureuses"
    elif pm25 <= 55 or o3_est > 100:
        level, col = 3, "#f97316"
        en = "RESTRICTED — No PE outdoors. Short breaks only (10 min max)."
        fr = "RESTREINT — Pas d'EPS dehors. Pauses courtes seulement (10 min max)"
    else:
        level, col = 4, "#ef4444"
        en = "CLOSE OUTDOOR AREAS — All outdoor activities cancelled. Stay indoors."
        fr = "FERMER LES ESPACES EXTÉRIEURS — Toutes activités annulées"

    return {
        "city":           city,
        "region":         region,
        "action_level":   level,
        "color":          col,
        "message":        fr if lang == "fr" else en,
        "pm25":           pm25,
        "o3_estimate":    round(o3_est, 1),
        "who_pm25_limit": WHO_24H,
        "vulnerable_groups": {
            "en": ["Children under 12 most at risk",
                   "Those with asthma should carry inhaler"],
            "fr": ["Enfants de moins de 12 ans les plus à risque",
                   "Les asthmatiques doivent avoir leur inhalateur"],
        }.get(lang, "en"),
    }


@app.get("/agri-advisory/{city}", tags=["Innovations"])
def agricultural_advisory(city: str, lang: str = Query("en")):
    """
    Agricultural advisory (Innovation #8).
    Dust/drought alerts for the Far North, North, Adamawa cattle corridor.
    """
    lat, lon, region = lookup_city(city)
    stats  = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25   = stats["mean_pm25"]

    is_cattle = region in NORTHERN
    month     = datetime.now().month

    if not is_cattle:
        return {
            "city": city, "region": region,
            "is_cattle_corridor": False,
            "advisory": {"en": "No agricultural dust advisory for this region.",
                         "fr": "Aucune alerte poussière agricole pour cette région."}[lang],
        }

    if pm25 > 80 or (pm25 > 50 and month in [11, 12, 1, 2]):
        alert_lv, color = "DUST STORM ALERT", "#ef4444"
        en = "Severe dust event. Shelter livestock immediately. Delay crop spraying."
        fr = "Événement de poussière sévère. Mettez le bétail à l'abri immédiatement."
    elif pm25 > 35:
        alert_lv, color = "DUST WARNING", "#f97316"
        en = "Elevated dust. Cover water sources. Protect young livestock. Reduce grazing."
        fr = "Poussière élevée. Couvrez les points d'eau. Réduisez le pâturage."
    elif month in [3, 4, 5] and region == "Far North":
        alert_lv, color = "DROUGHT WATCH", "#f59e0b"
        en = "Pre-monsoon drought risk. Conserve water. Prepare livestock watering."
        fr = "Risque de sécheresse pré-mousson. Conservez l'eau."
    else:
        alert_lv, color = "NORMAL", "#22c55e"
        en = "Normal conditions. Standard agricultural practices."
        fr = "Conditions normales. Pratiques agricoles standards."

    return {
        "city":                city,
        "region":              region,
        "is_cattle_corridor":  True,
        "alert_level":         alert_lv,
        "color":               color,
        "advisory":            fr if lang == "fr" else en,
        "pm25":                pm25,
        "month":               month,
        "is_harmattan_season": month in [11, 12, 1, 2],
    }


@app.get("/sms-preview/{city}", tags=["Innovations"])
def sms_preview(city: str, lang: str = Query("en")):
    """
    Bilingual SMS alert preview (Innovation #9).
    Ministry of Public Health format, triggered when RL threshold exceeded.
    """
    lat, lon, region = lookup_city(city)
    stats    = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25     = stats["mean_pm25"]
    rl_thr   = get_rl_threshold(city)
    level    = get_aqi_level(pm25)
    level_en = AQI_LEVELS[level]["en"]
    now      = datetime.now().strftime("%H:%M")
    date_str = datetime.now().strftime("%d/%m/%Y")

    sms_en = (
        f"AIRSENSE-CM ALERT: {city} — PM2.5 = {pm25:.1f} μg/m³ "
        f"[{level_en.upper()}]. "
        f"RL threshold {rl_thr:.0f} μg/m³. "
        f"Vulnerable groups: avoid prolonged outdoor exposure. "
        f"Wear mask if needed. {date_str} {now}. "
        f"Info: airsense-cm.org"
    )
    sms_fr = (
        f"ALERTE AIRSENSE-CM: {city} — PM2.5 = {pm25:.1f} μg/m³ "
        f"[{AQI_LEVELS[level]['fr'].upper()}]. "
        f"Seuil RL {rl_thr:.0f} μg/m³. "
        f"Groupes vulnérables: évitez l'exposition extérieure prolongée. "
        f"Portez un masque si nécessaire. {date_str} {now}. "
        f"Info: airsense-cm.org"
    )

    return {
        "city":          city,
        "region":        region,
        "pm25":          pm25,
        "rl_threshold":  rl_thr,
        "alert_triggered": pm25 > rl_thr,
        "sms_en":        sms_en,
        "sms_fr":        sms_fr,
        "sms_active":    sms_en if lang == "en" else sms_fr,
        "char_count_en": len(sms_en),
        "char_count_fr": len(sms_fr),
        "sender":        "AIRSENSE-CM",
        "generated_at":  datetime.utcnow().isoformat() + "Z",
    }


@app.get("/explain/{city}", tags=["Innovations"])
def explain(city: str, lang: str = Query("en")):
    """
    Region-specific SHAP fingerprint (Innovation #11).
    Top-7 climate drivers for the city's region.
    """
    lat, lon, region = lookup_city(city)
    shap_data   = STATE["region_shap"] or REGION_SHAP_FALLBACK
    region_data = shap_data.get(region, REGION_SHAP_FALLBACK.get(region, []))

    SHAP_DESC = {
        "year":             {"en":"Multi-year pollution trend (2020–2025)",
                             "fr":"Tendance pluriannuelle (2020–2025)"},
        "precipitation":    {"en":"Rainfall — primary natural particle removal mechanism",
                             "fr":"Précipitations — mécanisme naturel d'élimination des particules"},
        "humidity":         {"en":"Humidity — particle growth and atmospheric trapping",
                             "fr":"Humidité — croissance des particules et piégeage atmosphérique"},
        "daylight_duration":{"en":"Daylight hours — proxy for wet season and convective mixing",
                             "fr":"Heures de clarté — saison humide et mélange convectif"},
        "latitude":         {"en":"Latitude — North–South pollution gradient",
                             "fr":"Latitude — gradient de pollution Nord–Sud"},
        "is_dust_event":    {"en":"Dust storm flag — Harmattan extreme events",
                             "fr":"Indicateur de tempête de poussière — événements extrêmes Harmattan"},
        "is_dry_season":    {"en":"Dry season — no rainfall to wash particles",
                             "fr":"Saison sèche — pas de pluie pour laver les particules"},
        "region_enc":       {"en":"Region encoding — burning activity not in weather data",
                             "fr":"Encodage région — activité de brûlage non capturée par météo"},
        "longitude":        {"en":"Longitude — coastal/inland contrast (especially South West)",
                             "fr":"Longitude — contraste côtier/intérieur (surtout Sud-Ouest)"},
        "surface_pressure": {"en":"Surface pressure — stability and particle trapping inversions",
                             "fr":"Pression de surface — inversions de température et piégeage"},
        "is_harmattan":     {"en":"Harmattan season flag (Nov–Feb, northern regions)",
                             "fr":"Indicateur saison Harmattan (Nov–Fév, régions nord)"},
    }

    drivers = []
    for feat, val in region_data:
        drivers.append({
            "feature":     feat,
            "mean_abs_shap": val,
            "description": SHAP_DESC.get(feat, {}).get(lang, feat),
            "rank":        len(drivers) + 1,
        })

    top_feat = drivers[0]["feature"] if drivers else "unknown"
    INSIGHT_EN = {
        "year":           "Multi-year trend dominates — annual retraining required for reliable deployment.",
        "precipitation":  "Rainfall is the primary PM2.5 control — every 10 mm/day reduces PM2.5 by ~3.5 μg/m³.",
        "latitude":       "Geographic position outweighs all meteorological signals — South stays clean due to distance from Saharan sources.",
        "region_enc":     "Region label outranks weather variables — highland burning activity is not captured by meteorological data alone.",
        "is_dust_event":  "Dust storm events are the single largest positive PM2.5 driver — Harmattan transport from Bodélé Depression.",
        "precipitation_hours": "Precipitation frequency matters more than total amount in this region.",
    }
    insight = INSIGHT_EN.get(top_feat,
              f"'{top_feat}' is the primary driver of PM2.5 variability in {region}.")

    return {
        "city":          city,
        "region":        region,
        "top_drivers":   drivers,
        "key_insight":   insight,
        "methodology":   "XGBoost pred_contribs=True (native SHAP), "
                         "separate explainer per region on test subset.",
        "n_features":    44,
    }


@app.get("/climate/{city}", tags=["Innovations"])
def climate_projection(
    city:     str,
    scenario: str  = Query("SSP2-4.5 (Intermediate)", description="SSP scenario name"),
    year:     int  = Query(2050, ge=2026, le=2100),
    lang:     str  = Query("en"),
):
    """
    CMIP6 PM2.5 climate projections (Innovation #12).
    Returns full 2025–2100 trajectory + projected value at target year.
    """
    lat, lon, region = lookup_city(city)
    stats    = CITY_STATS.get(city, {"mean_pm25": 15.0})
    base_pm  = stats["mean_pm25"]

    # Try pre-computed projections first
    if STATE["climate"] and "cities" in STATE["climate"]:
        city_proj = STATE["climate"]["cities"].get(city)
        if city_proj and scenario in city_proj:
            years_list = STATE["climate"].get("years", list(range(2025, 2101)))
            pm25_vals  = city_proj[scenario]
            try:
                yr_idx  = years_list.index(year)
                proj_pm = pm25_vals[yr_idx]
            except (ValueError, IndexError):
                proj_pm = project_pm25(base_pm, region, year,
                                       SSP_RATES.get(scenario, 0.22))
            return _build_climate_response(city, region, base_pm, scenario,
                                           year, proj_pm, years_list,
                                           pm25_vals, lang)

    # Compute inline (fallback)
    rate      = SSP_RATES.get(scenario, 0.22)
    years_l   = list(range(2025, 2101))
    pm25_vals = [round(project_pm25(base_pm, region, y, rate), 2) for y in years_l]
    yr_idx    = years_l.index(year)
    proj_pm   = pm25_vals[yr_idx]
    return _build_climate_response(city, region, base_pm, scenario,
                                   year, proj_pm, years_l, pm25_vals, lang)


def _build_climate_response(city, region, base_pm, scenario, year,
                             proj_pm, years_list, pm25_vals, lang):
    delta     = round(proj_pm - base_pm, 2)
    who_now   = base_pm > WHO_24H
    who_proj  = proj_pm > WHO_24H
    rate      = SSP_RATES.get(scenario, 0.22)
    dT        = rate * (year - 2025) / 10.0 * REGION_WARM.get(region, 1.0)

    return {
        "city":             city,
        "region":           region,
        "scenario":         scenario,
        "target_year":      year,
        "baseline_pm25":    round(base_pm, 2),
        "projected_pm25":   round(proj_pm, 2),
        "delta_pm25":       delta,
        "delta_temperature":round(dT, 2),
        "who_exceeded_now":  who_now,
        "who_exceeded_2050": who_proj,
        "trajectory":       [{"year": y, "pm25": v}
                             for y, v in zip(years_list, pm25_vals)],
        "methodology":      "IPCC AR6 warming rates × empirical PM2.5/temperature "
                            "sensitivity × regional amplification. Indicative — not a "
                            "certified climate model output.",
        "interpretation": {
            "en": (f"{city} is projected to reach {proj_pm:.1f} μg/m³ by {year} "
                   f"under {scenario}, a {'+' if delta>=0 else ''}{delta:.1f} μg/m³ "
                   f"change from today's {base_pm:.1f} μg/m³. "
                   + ("WHO 24h limit will be exceeded." if who_proj and not who_now
                      else "Already exceeds WHO 24h limit under all scenarios." if who_now
                      else "Remains below WHO 24h limit under this scenario.")),
            "fr": (f"{city} devrait atteindre {proj_pm:.1f} μg/m³ d'ici {year} "
                   f"sous {scenario}."),
        }[lang],
    }


@app.get("/health-impact/{city}", tags=["Innovations"])
def health_impact_endpoint(city: str, lang: str = Query("en")):
    """
    WHO concentration-response health impact (Innovation in app.py health page).
    Excess respiratory cases, hospital risk, lost workdays per 10,000 people.
    """
    lat, lon, region = lookup_city(city)
    stats = CITY_STATS.get(city, {"mean_pm25": 15.0})
    pm25  = stats["mean_pm25"]
    er, hr, ld = health_impact(pm25)
    alert_p    = get_alert_prob(pm25)

    advisories_en = {
        "good":      ["No restrictions for any group."],
        "moderate":  ["Sensitive groups: reduce prolonged outdoor exertion."],
        "poor":      ["Children: reduce outdoor play.",
                      "Elderly: limit strenuous activities.",
                      "Asthmatics: carry inhaler outdoors."],
        "very_poor": ["Children: no outdoor sports.",
                      "Pregnant women: stay indoors.",
                      "Outdoor workers: wear N95 mask, take breaks."],
        "hazardous": ["Everyone: stay indoors.",
                      "Seek medical advice if experiencing symptoms.",
                      "Use air purifiers where available."],
    }

    level = get_aqi_level(pm25)
    return {
        "city":    city,
        "region":  region,
        "pm25":    pm25,
        "aqi_level": level,
        "per_10000_people": {
            "excess_respiratory_cases": er,
            "hospital_admission_risk_pct": hr,
            "lost_workdays": ld,
        },
        "alert_probability_pct": round(alert_p * 100, 1),
        "platt_formula": (
            f"P(exceed WHO) = sigmoid({(STATE['platt'] or {}).get('coef', 0.2221):.4f}"
            f" × PM2.5 + {(STATE['platt'] or {}).get('intercept', -3.0372):.4f})"
        ),
        "group_advisories": advisories_en.get(level, []),
        "method": "WHO Global Air Quality Guidelines 2021 concentration-response functions.",
        "note":   "Estimates only — not a substitute for clinical assessment.",
    }


@app.get("/africa-benchmark", tags=["Innovations"])
def africa_benchmark(lang: str = Query("en")):
    """
    Cameroon vs 12 African cities PM2.5 benchmark (Innovation #10).
    Matches the Africa Benchmark tab on the analytics page.
    """
    out = []
    for city_name, pm25_val, is_cameroon in AFRICA_BENCHMARK:
        level = get_aqi_level(pm25_val)
        out.append({
            "city":         city_name,
            "pm25":         pm25_val,
            "is_cameroon":  is_cameroon,
            "aqi_level":    level,
            "label":        AQI_LEVELS[level][lang] if lang in ("en","fr") else AQI_LEVELS[level]["en"],
            "color":        AQI_LEVELS[level]["color"],
            "who_exceeded": pm25_val > WHO_24H,
            "who_ratio":    round(pm25_val / WHO_24H, 2),
        })

    worst    = max(out, key=lambda x: x["pm25"])
    best     = min(out, key=lambda x: x["pm25"])
    cm_cities= [c for c in out if c["is_cameroon"]]

    return {
        "benchmark":      out,
        "who_24h_limit":  WHO_24H,
        "worst_city":     worst["city"],
        "best_city":      best["city"],
        "cameroon_cities": [c["city"] for c in cm_cities],
        "cameroon_vs_nairobi_ratio": round(
            next(c["pm25"] for c in cm_cities if "Maroua" in c["city"]) / 16, 1
        ),
        "note": {
            "en": "Maroua (Far North) records PM2.5 nearly 5× higher than Nairobi. "
                  "Cameroon's internal North–South gradient is larger than "
                  "the gap between Africa's cleanest and most polluted capitals.",
            "fr": "Maroua (Extrême-Nord) enregistre un PM2.5 presque 5× supérieur "
                  "à Nairobi. Le gradient Nord–Sud interne au Cameroun est plus "
                  "large que l'écart entre les capitales africaines les plus propres "
                  "et les plus polluées.",
        }[lang],
    }


@app.get("/compare", tags=["Innovations"])
def compare_cities(
    city_a: str = Query(..., example="Douala"),
    city_b: str = Query(..., example="Maroua"),
    lang:   str = Query("en"),
):
    """
    Side-by-side seasonal profile comparison (Innovation #15).
    Matches the City Compare page.
    """
    la, lona, ra = lookup_city(city_a)
    lb, lonb, rb = lookup_city(city_b)
    sa = CITY_STATS.get(city_a, {"mean_pm25": 15.0})
    sb = CITY_STATS.get(city_b, {"mean_pm25": 15.0})
    months = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    sea_a  = seasonal_profile(ra, sa["mean_pm25"])
    sea_b  = seasonal_profile(rb, sb["mean_pm25"])

    diff   = sa["mean_pm25"] - sb["mean_pm25"]
    worse  = city_a if diff > 0 else city_b

    return {
        "city_a": {
            "name":            city_a,
            "region":          ra,
            "mean_pm25":       sa["mean_pm25"],
            "who_exc_pct":     sa.get("who_exc", 0),
            "tier":            sa.get("tier", "Medium"),
            "rl_threshold":    get_rl_threshold(city_a),
            "seasonal_pm25":   [{"month": m, "pm25": v}
                                for m, v in zip(months, sea_a)],
        },
        "city_b": {
            "name":            city_b,
            "region":          rb,
            "mean_pm25":       sb["mean_pm25"],
            "who_exc_pct":     sb.get("who_exc", 0),
            "tier":            sb.get("tier", "Medium"),
            "rl_threshold":    get_rl_threshold(city_b),
            "seasonal_pm25":   [{"month": m, "pm25": v}
                                for m, v in zip(months, sea_b)],
        },
        "comparison": {
            "pm25_difference":  round(abs(diff), 2),
            "worse_city":       worse,
            "better_city":      city_b if diff > 0 else city_a,
            "summary": {
                "en": f"{worse} has {abs(diff):.1f} μg/m³ higher annual mean PM2.5.",
                "fr": f"{worse} a {abs(diff):.1f} μg/m³ de PM2.5 annuel moyen de plus.",
            }[lang],
        },
    }


# ── IoT ───────────────────────────────────────────────────────────────────────

@app.post("/ingest", tags=["IoT"])
def ingest(payload: ESP32Payload):
    """
    ESP32 IoT sensor ingestion endpoint.
    Classifies PM2.5 on arrival using RL threshold for the city.
    """
    entry  = {**payload.dict(), "received_at": datetime.utcnow().isoformat() + "Z"}
    sensor_buffer.append(entry)
    if len(sensor_buffer) > 1000:
        sensor_buffer.pop(0)

    alert_triggered = False
    alert_prob      = None
    rl_threshold    = None

    if payload.pm25 is not None:
        rl_threshold    = get_rl_threshold(payload.city)
        alert_triggered = payload.pm25 > rl_threshold
        alert_prob      = round(get_alert_prob(payload.pm25) * 100, 1)
        level           = get_aqi_level(payload.pm25)
    else:
        level = "moderate"

    return {
        "status":          "received",
        "device_id":       payload.device_id,
        "city":            payload.city,
        "pm25":            payload.pm25,
        "aqi_level":       level,
        "rl_threshold":    rl_threshold,
        "alert_triggered": alert_triggered,
        "alert_prob_pct":  alert_prob,
        "buffer_size":     len(sensor_buffer),
    }


@app.get("/sensor-feed", tags=["IoT"])
def sensor_feed(
    city:  Optional[str] = None,
    limit: int           = Query(20, le=100),
):
    """Recent ESP32 sensor readings from the in-memory ring buffer."""
    feed = sensor_buffer[-limit:]
    if city:
        feed = [r for r in feed if r.get("city", "").lower() == city.lower()]
    return {
        "readings":   list(reversed(feed)),
        "count":      len(feed),
        "total_seen": len(sensor_buffer),
    }