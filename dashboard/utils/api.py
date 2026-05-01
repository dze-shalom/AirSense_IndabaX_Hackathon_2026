"""utils/api.py — External API calls (Open-Meteo, Anthropic, AirSense FastAPI)."""
import os, logging, requests, streamlit as st
from config import NORTHERN

logger = logging.getLogger("airsense")

# ── AirSense FastAPI backend URL ──────────────────────────────────────────────
def _api_base() -> str:
    try:
        url = st.secrets.get("AIRSENSE_API_URL", "")
    except Exception:
        url = ""
    return url or os.environ.get("AIRSENSE_API_URL", "http://localhost:8000").rstrip("/")


@st.cache_data(ttl=60, show_spinner=False)
def api_health_check() -> bool:
    """Returns True if the FastAPI backend is reachable."""
    try:
        r = requests.get(f"{_api_base()}/health", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_airsense_forecast(city: str, lang: str = "en"):
    """GET /forecast/{city} — 7-day XGBoost forecast from the API backend.
    Returns the full response dict or None on failure.
    """
    try:
        r = requests.get(
            f"{_api_base()}/forecast/{city}",
            params={"lang": lang},
            timeout=20,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("fetch_airsense_forecast %s: %s", city, e)
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_airsense_explain(city: str, lang: str = "en"):
    """GET /explain/{city} — region SHAP fingerprint from the API backend."""
    try:
        r = requests.get(
            f"{_api_base()}/explain/{city}",
            params={"lang": lang},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("fetch_airsense_explain %s: %s", city, e)
        return None


@st.cache_data(ttl=3600, show_spinner=False)
def fetch_airsense_alert_status(city: str, lang: str = "en"):
    """GET /alert-status/{city} from the API backend."""
    try:
        r = requests.get(
            f"{_api_base()}/alert-status/{city}",
            params={"lang": lang},
            timeout=10,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("fetch_airsense_alert_status %s: %s", city, e)
        return None


def _map_api_forecast_to_preds(api_data: dict) -> list:
    """Convert /forecast/{city} response to the list format used by predict_7day()."""
    out = []
    for p in api_data.get("forecast", []):
        w = p.get("weather") or {}
        out.append({
            "date":     p["date"],
            "pm25":     p["pm25"],
            "wmo_code": w.get("wmo_code", 3),
            "temp_max": w.get("temp_max", 28),
            "temp_min": w.get("temp_min", 18),
            "precip":   w.get("precip_mm", 0),
            "humidity": w.get("humidity", 60),
            "wind":     w.get("wind_kmh", 10),
        })
    return out or None


@st.cache_data(ttl=3600)
def fetch_forecast(lat, lon):
    try:
        r = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat, "longitude": lon, "timezone": "Africa/Douala",
                "forecast_days": 7,
                "daily": ",".join([
                    "temperature_2m_max","temperature_2m_min","temperature_2m_mean",
                    "precipitation_sum","precipitation_hours",
                    "wind_speed_10m_max","wind_gusts_10m_max","wind_direction_10m_dominant",
                    "wind_speed_100m_max","shortwave_radiation_sum",
                    "et0_fao_evapotranspiration","weather_code",
                    "relative_humidity_2m_mean","cloud_cover_mean",
                    "vapour_pressure_deficit_max","daylight_duration","sunshine_duration",
                    "soil_moisture_0_to_7cm_mean","soil_temperature_0_to_7cm_mean",
                ]),
            },
            timeout=15,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("fetch_forecast failed: %s", e)
        return None


@st.cache_data(ttl=86400)
def geocode_city(query):
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": query, "format": "json", "limit": 5, "accept-language": "en"},
            headers={"User-Agent": "AirSense-Cameroon/1.0"},
            timeout=8,
        )
        results = r.json()
        if not results: return None
        for res in results:
            if res.get("address", {}).get("country_code", "") == "cm":
                return float(res["lat"]), float(res["lon"]), res["display_name"], "cm"
        res = results[0]
        return float(res["lat"]), float(res["lon"]), res["display_name"], res.get("address", {}).get("country_code", "??")
    except Exception as e:
        logger.warning("geocode: %s", e)
        return None


@st.cache_data(ttl=86400)
def fetch_historical(lat, lon, start, end):
    try:
        r = requests.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": lat, "longitude": lon,
                "start_date": start, "end_date": end,
                "timezone": "Africa/Douala",
                "daily": ",".join([
                    "temperature_2m_max","temperature_2m_min","temperature_2m_mean",
                    "precipitation_sum","wind_speed_10m_max","wind_direction_10m_dominant",
                    "shortwave_radiation_sum","relative_humidity_2m_mean",
                    "cloud_cover_mean","et0_fao_evapotranspiration",
                ]),
            },
            timeout=20,
        )
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.warning("fetch_historical: %s", e)
        return None


def wmo_icon(code):
    if code == 0:            return "Clear"
    if code in (1, 2):       return "P.Cloudy"
    if code == 3:             return "Cloudy"
    if code in (45, 48):     return "Fog"
    if code in (51,53,55):   return "Drizzle"
    if code in (61,63,65):   return "Rain"
    if code in (80,81,82):   return "Showers"
    if code in (95,96,99):   return "Thunder"
    return "—"


def call_claude(msg, city, region, pm25, lang):
    try:
        api_key = st.secrets.get("ANTHROPIC_API_KEY", "") or ""
    except Exception:
        api_key = ""
    api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return "API key not configured." if lang == "en" else "Clé API non configurée."
    try:
        system = (
            f"You are AirSense, an air quality health assistant for Cameroon. "
            f"Current context: {city} ({region}), PM2.5 = {pm25:.1f} µg/m³ "
            f"({'above' if pm25 > 15 else 'below'} WHO 24h limit of 15 µg/m³). "
            f"Be concise and practical. Respond in {'French' if lang == 'fr' else 'English'}."
        )
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-sonnet-4-5-20251001", "max_tokens": 400,
                  "system": system, "messages": [{"role": "user", "content": msg}]},
            timeout=30,
        )
        r.raise_for_status()
        return "".join(b.get("text","") for b in r.json().get("content",[]) if b.get("type")=="text")
    except Exception as e:
        logger.error("Claude: %s", e)
        return f"Error: {e}"
