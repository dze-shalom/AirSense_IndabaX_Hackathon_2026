"""utils/api.py — External API calls: Open-Meteo forecast, Nominatim geocoding, Claude."""
import os
import logging
import requests
import streamlit as st
from config import NORTHERN

logger = logging.getLogger("airsense")


@st.cache_data(ttl=3600)
def fetch_forecast(lat, lon):
    url    = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "daily": ",".join([
            "temperature_2m_max","temperature_2m_min","temperature_2m_mean",
            "precipitation_sum","precipitation_hours","wind_speed_10m_max",
            "wind_direction_10m_dominant","shortwave_radiation_sum",
            "et0_fao_evapotranspiration","weather_code","relative_humidity_2m_mean",
            "dew_point_2m_mean","surface_pressure_mean","cloud_cover_mean",
            "wind_speed_100m_max","soil_moisture_0_to_7cm_mean",
            "soil_temperature_0_to_7cm_mean","wet_bulb_temperature_2m_mean",
            "vapour_pressure_deficit_max","daylight_duration","sunshine_duration",
        ]),
        "timezone": "Africa/Douala",
        "forecast_days": 7,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("fetch_forecast: %s", e)
        return None


@st.cache_data(ttl=86400)
def geocode_city(query: str):
    """Return (lat, lon, display_name, country_code) or None."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 5, "accept-language": "en"},
            headers={"User-Agent": "AirSense-Cameroon-IndabaX2026/1.0"},
            timeout=8,
        )
        results = r.json()
        if not results:
            return None
        for res in results:
            if res.get("address", {}).get("country_code", "") == "cm":
                return float(res["lat"]), float(res["lon"]), res["display_name"], "cm"
        res = results[0]
        return float(res["lat"]), float(res["lon"]), res["display_name"],                res.get("address", {}).get("country_code", "??")
    except Exception as e:
        logger.warning("geocode: %s", e)
        return None


def wmo_icon(code):
    """Return weather icon for WMO code."""
    m = {0:"☀",1:"🌤",2:"🌤",3:"☁",45:"🌫",48:"🌫",
         51:"🌦",53:"🌦",55:"🌦",61:"🌧",63:"🌧",65:"🌧",
         80:"⛈",81:"⛈",82:"⛈",95:"⛈"}
    return m.get(code, "—")


def call_claude(msg, city, region, pm25, lang):
    from config import WHO_24H, T
    from utils.helpers import aqi
    _, _, _, raw = aqi(pm25)
    tip = T[lang].get(f"health_{raw}", T["en"].get(f"health_{raw}", ""))
    sys_p = (
        f"You are AirSense AI, an expert air quality assistant for Cameroon. "
        f"City: {city}, Region: {region}. PM2.5: {pm25:.1f} μg/m³ (WHO 24h limit: {WHO_24H}). "
        f"Advisory: {tip}. Be concise (2-4 sentences), empathetic, actionable. "
        f"Answer in {'French' if lang=='fr' else 'English'}. Do not mention Claude."
    )
    api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return None
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json",
                     "x-api-key": api_key,
                     "anthropic-version": "2023-06-01"},
            json={"model": "claude-sonnet-4-20250514", "max_tokens": 300,
                  "system": sys_p, "messages": [{"role": "user", "content": msg}]},
            timeout=20,
        )
        r.raise_for_status()
        return "".join(b.get("text","") for b in r.json().get("content",[]) if b.get("type")=="text")
    except Exception as e:
        logger.error("Claude: %s", e)
        return None


@st.cache_data(ttl=86400)
def fetch_historical(lat, lon, start_date: str, end_date: str):
    """Fetch real measured weather from Open-Meteo archive API.
    start_date / end_date: 'YYYY-MM-DD' strings.
    Returns same structure as fetch_forecast() for compatibility.
    """
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat, "longitude": lon,
        "start_date": start_date, "end_date": end_date,
        "daily": ",".join([
            "temperature_2m_max","temperature_2m_min","temperature_2m_mean",
            "precipitation_sum","precipitation_hours","wind_speed_10m_max",
            "wind_direction_10m_dominant","shortwave_radiation_sum",
            "et0_fao_evapotranspiration","weather_code","relative_humidity_2m_mean",
            "dew_point_2m_mean","surface_pressure_mean","cloud_cover_mean",
            "wind_speed_100m_max","soil_moisture_0_to_7cm_mean",
            "soil_temperature_0_to_7cm_mean","wet_bulb_temperature_2m_mean",
            "vapour_pressure_deficit_max","daylight_duration","sunshine_duration",
        ]),
        "timezone": "Africa/Douala",
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("fetch_historical: %s", e)
        return None
