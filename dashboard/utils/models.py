try:
    from dotenv import load_dotenv; load_dotenv()
except ImportError:
    pass
"""utils/models.py — Model loading and prediction."""
import numpy as np
import json
import pickle
import logging
from pathlib import Path
import streamlit as st

# ── Handle imports from both root and dashboard-relative contexts ──────────────
try:
    from config import CITIES, NORTHERN
except ImportError:
    from ..config import CITIES, NORTHERN

logger = logging.getLogger("airsense")




@st.cache_resource
def load_models():
    try:
        import xgboost as xgb
        base  = Path(__file__).parent.parent.parent / "models"
        model = xgb.XGBRegressor(random_state=42, seed=42)
        model.load_model(str(base / "xgb_pm25.json"))
        with open(base / "label_encoders.pkl", "rb") as f: enc = pickle.load(f)
        with open(base / "features.json")            as f: fi  = json.load(f)
        return model, enc, fi
    except Exception as e:
        logger.warning("load_models: %s", e)
        return None, None, None


@st.cache_resource
def load_artefacts():
    base = Path(__file__).parent.parent.parent / "models"
    out  = {}
    for k, fn in [
        ("conformal",  "conformal_intervals.json"),
        ("city_conf",  "city_confidence_tiers.json"),  # Fixed: was "city_confidence.json"
        ("platt",      "platt_alert_calibration.json"),
        ("region_shap","region_shap.pkl"),
        ("climate",    "climate_projections.json"),
    ]:
        try:
            fp = base / fn
            if fn.endswith(".pkl"):
                with open(fp, "rb") as f: out[k] = pickle.load(f)
            else:
                with open(fp)        as f: out[k] = json.load(f)
        except Exception as e:
            logger.debug("load_artefacts: %s not found or unreadable: %s", fn, e)
            out[k] = None
    return out


def get_conf_interval(region, art):
    if art and art.get("conformal"):
        c = art["conformal"]
        # Handle both 'global_q_hat' (Cell 31) and 'q_hat' (Cell 99 simplified save)
        global_q = c.get("global_q_hat") or c.get("q_hat", 30.8)
        return c.get("region_intervals", {}).get(region, global_q)
    fallback = {
        "South":14.1,"East":17.3,"Centre":19.2,"South West":22.4,
        "Littoral":23.6,"Adamawa":26.2,"West":30.9,"North West":41.4,
        "North":48.8,"Far North":56.6,
    }
    return fallback.get(region, 30.8)


def get_alert_prob(pm25, art):
    if art and art.get("platt"):
        p    = art["platt"]
        coef = p.get("coef", 0.2221)
        intc = p.get("intercept", -3.0372)
    else:
        coef, intc = 0.2221, -3.0372
    import math
    z = coef * pm25 + intc
    return 1 / (1 + math.exp(-z))


def infer_region_from_lat(lat):
    if lat > 10.0: return "Far North"
    if lat > 8.5:  return "North"
    if lat > 6.5:  return "Adamawa"
    if lat > 5.8:  return "West"
    if lat > 5.2:  return "North West"
    if lat > 4.5:  return "Centre"
    if lat > 3.5:  return "Littoral"
    if lat > 2.5:  return "South"
    return "South"


def nearest_known_city_enc(lat, lon, enc):
    le_c = enc["city"]; le_r = enc["region"]
    best_city, best_dist = list(le_c.classes_)[0], float("inf")
    for reg, clist in CITIES.items():
        for cname, clat, clon in clist:
            d = (clat - lat) ** 2 + (clon - lon) ** 2
            if d < best_dist:
                best_dist = d
                best_city = cname
    best_region = infer_region_from_lat(lat)
    try:    ce = list(le_c.classes_).index(best_city)
    except: ce = 0
    try:    re = list(le_r.classes_).index(best_region)
    except: re = 0
    return ce, re, best_region


def build_features(row, ce, re, lat, lon, reg_classes):
    import numpy as np
    from datetime import datetime
    month = datetime.strptime(row["date"], "%Y-%m-%d").month
    doy   = datetime.strptime(row["date"], "%Y-%m-%d").timetuple().tm_yday
    year  = datetime.strptime(row["date"], "%Y-%m-%d").year
    rad   = np.deg2rad(row.get("wind_direction_10m_dominant", 180))
    ws    = row.get("wind_speed_10m_max", 10)
    tdm   = row.get("temperature_2m_mean", 25)
    # dew_point_2m_mean is hourly-only in Open-Meteo; estimate from humidity+temp
    _hum  = row.get("relative_humidity_2m_mean", 60)
    _tdm  = row.get("temperature_2m_mean", 25)
    dp    = row.get("dew_point_2m_mean",
               _tdm - ((100 - _hum) / 5.0))  # Magnus approximation
    sh    = row.get("sunshine_duration", 30000)
    dl    = row.get("daylight_duration", 43000)
    prec  = row.get("precipitation_sum", 0)
    rname = reg_classes[re] if re < len(reg_classes) else "Centre"
    north = rname in NORTHERN

    def tet(T): return 0.6108 * np.exp((17.27 * T) / (T + 237.3))
    vpd = max(0, tet(tdm) - tet(dp))

    # Derived values
    is_harm    = int(month in [11,12,1,2] and north)
    is_dry     = int(month in [11,12,1,2,3])
    is_no_rain = int(prec == 0)
    is_no_wind = int(ws < 2)
    temp_range = row.get("temperature_2m_max", 30) - row.get("temperature_2m_min", 18)
    wg         = row.get("wind_gusts_10m_max", ws * 1.5)      # wind gust estimate

    return {
        # ── Location & encoding ─────────────────────────────────────────────
        "latitude": lat, "longitude": lon, "region_enc": re, "city_enc": ce,
        # ── Date features ───────────────────────────────────────────────────
        "month": month, "day_of_year": doy, "year": year,
        # 1st Fourier harmonics
        "month_sin":   np.sin(2*np.pi*month/12),
        "month_cos":   np.cos(2*np.pi*month/12),
        "doy_sin":     np.sin(2*np.pi*doy/365),
        "doy_cos":     np.cos(2*np.pi*doy/365),
        # 2nd Fourier harmonics (notebook Cell 6)
        "month_sin_2": np.sin(4*np.pi*month/12),
        "month_cos_2": np.cos(4*np.pi*month/12),
        "doy_sin_2":   np.sin(4*np.pi*doy/365),
        "doy_cos_2":   np.cos(4*np.pi*doy/365),
        # 3rd Fourier harmonics
        "doy_sin_3":   np.sin(6*np.pi*doy/365),
        "doy_cos_3":   np.cos(6*np.pi*doy/365),
        # ── Temperature ─────────────────────────────────────────────────────
        "temp_max":  row.get("temperature_2m_max", 30),
        "temp_min":  row.get("temperature_2m_min", 18),
        "temp_mean": tdm, "apparent_temp_mean": tdm,
        "temp_range": temp_range,
        # ── Precipitation / humidity ─────────────────────────────────────────
        "precipitation":       prec,
        "precipitation_hours": row.get("precipitation_hours", 0),
        "humidity":        row.get("relative_humidity_2m_mean", 60),
        "dew_point":       dp,
        "wet_bulb_temp":   row.get("wet_bulb_temperature_2m_mean", row.get("wet_bulb_temp", 20)),
        "vpd":             round(vpd, 4),
        "vpd_max":         row.get("vapour_pressure_deficit_max", 2.0),
        # ── Wind ─────────────────────────────────────────────────────────────
        "wind_speed":    ws,
        "wind_direction":row.get("wind_direction_10m_dominant", 180),
        "wind_u":        -ws*np.sin(rad),
        "wind_v":        -ws*np.cos(rad),
        "wind_100m":     row.get("wind_speed_100m_max", 20),
        "wind_gust":     wg,
        # ── Radiation / solar ────────────────────────────────────────────────
        "solar_radiation":    row.get("shortwave_radiation_sum", 18),
        "evapotranspiration": row.get("et0_fao_evapotranspiration", 5),
        "daylight_duration":  dl,
        "sunshine_ratio":     min(sh / max(dl, 1), 1.0),
        # ── Pressure / cloud ─────────────────────────────────────────────────
        "surface_pressure": row.get("surface_pressure_mean", row.get("surface_pressure", 950)),
        "cloud_cover":      row.get("cloud_cover_mean", 50),
        "weather_code_cat": min(row.get("weather_code", 3), 9),
        # ── Soil ─────────────────────────────────────────────────────────────
        "soil_moisture": row.get("soil_moisture_0_to_7cm_mean", 0.2),
        "soil_temp":     row.get("soil_temperature_0_to_7cm_mean", 25),
        # ── Season / event flags ─────────────────────────────────────────────
        "is_harmattan":   is_harm,
        "is_dry_season":  is_dry,
        "is_no_rain":     is_no_rain,
        "is_no_wind":     is_no_wind,
        "is_heat_stress": int(tdm > 40),
        "is_dust_event":  0,
        "is_haze_fog":    int(row.get("weather_code", 3) in [45, 48]),
        "is_real_measurement": 1,   # live forecast → treat as real
        # ── Interaction features (notebook Cell 6) ───────────────────────────
        "harm_x_wind":           is_harm * ws,
        "harm_x_gust":           is_harm * wg,
        "harm_x_soil":           is_harm * row.get("soil_moisture_0_to_7cm_mean", 0.2),
        "harm_x_lat":            is_harm * lat,
        "harm_x_vpd":            is_harm * round(vpd, 4),
        "stagnation":            is_no_wind * is_no_rain,
        "city_x_month":          ce * month,
        "vpd_x_dry_season":      round(vpd, 4) * is_dry,
        "temp_range_x_humidity": temp_range * row.get("relative_humidity_2m_mean", 60),
        # ── Extra features from features.json ────────────────────────────────
        "weather_code":          row.get("weather_code", 3),
        "weather_code_enc":      min(int(row.get("weather_code", 3)), 9),
        "boundary_layer_height": 1500.0,
        "blh_min":               500.0,
        "nh3_proxy":             0.5,
        "pm25_is_real":          1,
        "region_x_dry_season":   re * is_dry,
        "sample_weight":         1.0,
    }


def _local_7day(fd, city, region, lat, lon, model, enc, fi):
    """Run local XGBoost model for all 7 days. Returns list of dicts or None."""
    if model is None or fd is None or enc is None or fi is None:
        return None
    try:
        le_c = enc["city"]; le_r = enc["region"]
        try:    ce = list(le_c.classes_).index(city);  re = list(le_r.classes_).index(region)
        except: ce, re, region = nearest_known_city_enc(lat, lon, enc) if enc else (0, 0, region)
        daily = fd.get("daily", {}); dates = daily.get("time", [])
        fl    = fi.get("features", [])
        if not fl or not dates:
            return None
        _train_year_max = 2024
        preds = []
        for i, date in enumerate(dates):
            row   = {k: (v[i] if isinstance(v, list) and i < len(v) else 0)
                     for k, v in daily.items() if k != "time"}
            row["date"] = date
            feats = build_features(row, ce, re, lat, lon, list(le_r.classes_))
            feats["year"] = min(feats.get("year", _train_year_max), _train_year_max)
            fa    = np.array([[feats.get(f, 0) for f in fl]])
            try:
                pred = float(np.expm1(model.predict(fa)[0]))
            except Exception as e:
                logger.error("_local_7day inference error: %s", e)
                return None
            preds.append({
                "date":     date,
                "pm25":     max(0.5, pred),
                "wmo_code": daily.get("weather_code",  [3]*7)[i] if i < 7 else 3,
                "temp_max": daily.get("temperature_2m_max", [28]*7)[i] if i < 7 else 28,
                "temp_min": daily.get("temperature_2m_min", [18]*7)[i] if i < 7 else 18,
                "precip":   daily.get("precipitation_sum",  [0]*7)[i]  if i < 7 else 0,
                "humidity": daily.get("relative_humidity_2m_mean", [60]*7)[i] if i < 7 else 60,
                "wind":     daily.get("wind_speed_10m_max", [10]*7)[i] if i < 7 else 10,
                "source":   "local",
            })
        return preds
    except Exception as e:
        logger.error("_local_7day: %s", e, exc_info=True)
        return None


def predict_7day(fd, city, region, lat, lon, model, enc, fi):
    # ── 1. CAMS / Open-Meteo Air Quality API (most accurate) ─────────────────
    try:
        from utils.api import fetch_cams_forecast, fetch_forecast as _fetch_wx
        cams = fetch_cams_forecast(lat, lon)
        if cams and len(cams) >= 3:
            wx    = fd or _fetch_wx(lat, lon) or {}
            daily = wx.get("daily", {})
            preds = []
            for i, day in enumerate(cams[:7]):
                preds.append({
                    "date":     day["date"],
                    "pm25":     max(0.5, day["pm25"]),
                    "wmo_code": daily.get("weather_code",  [3]*7)[i] if i < len(daily.get("weather_code", [])) else 3,
                    "temp_max": daily.get("temperature_2m_max", [28]*7)[i] if i < len(daily.get("temperature_2m_max", [])) else 28,
                    "temp_min": daily.get("temperature_2m_min", [18]*7)[i] if i < len(daily.get("temperature_2m_min", [])) else 18,
                    "precip":   daily.get("precipitation_sum",  [0]*7)[i]  if i < len(daily.get("precipitation_sum", [])) else 0,
                    "humidity": daily.get("relative_humidity_2m_mean", [60]*7)[i] if i < len(daily.get("relative_humidity_2m_mean", [])) else 60,
                    "wind":     daily.get("wind_speed_10m_max", [10]*7)[i] if i < len(daily.get("wind_speed_10m_max", [])) else 10,
                    "source":   "cams",
                })
            # If CAMS returned fewer than 7 days, pad with local model
            if len(preds) < 7 and model is not None and fd is not None:
                local = _local_7day(fd, city, region, lat, lon, model, enc, fi) or []
                cams_dates = {p["date"] for p in preds}
                for lp in local:
                    if lp["date"] not in cams_dates and len(preds) < 7:
                        lp["source"] = "local"
                        preds.append(lp)
                preds.sort(key=lambda x: x["date"])
            logger.debug("predict_7day(%s): CAMS %d days", city, len(preds))
            return preds
    except Exception as e:
        logger.warning("predict_7day CAMS path failed for %s: %s", city, e)

    # ── 2. AirSense FastAPI backend ───────────────────────────────────────────
    try:
        from utils.api import api_health_check, fetch_airsense_forecast, _map_api_forecast_to_preds
        if api_health_check():
            data = fetch_airsense_forecast(city)
            if data and data.get("forecast"):
                preds = _map_api_forecast_to_preds(data)
                if preds:
                    logger.debug("predict_7day(%s): using AirSense API", city)
                    return preds
    except Exception as e:
        logger.warning("predict_7day API path failed for %s: %s", city, e)

    # ── 3. Local XGBoost model fallback ───────────────────────────────────────
    return _local_7day(fd, city, region, lat, lon, model, enc, fi)


# ── Multi-compound models ─────────────────────────────────────────────────────

@st.cache_resource
def load_multi_models():
    """Load 8-compound XGBoost models from models_multi.pkl."""
    try:
        base = Path(__file__).parent.parent.parent / "models"
        with open(base / "models_multi.pkl", "rb") as f:
            return pickle.load(f)
    except Exception as e:
        logger.warning("load_multi_models: %s", e)
        return None


def predict_compounds_today(fd, city, region, lat, lon, enc, fi):
    """Return dict of {compound_key: predicted_value} for today using models_multi.pkl.
    Falls back to None if models not available.
    """
    from config import COMPOUND_KEYS
    models_multi = load_multi_models()
    if models_multi is None or fd is None or enc is None:
        return None
    try:
        le_c = enc["city"]; le_r = enc["region"]
        try:    ce = list(le_c.classes_).index(city); re = list(le_r.classes_).index(region)
        except: ce, re, region = nearest_known_city_enc(lat, lon, enc)
        daily = fd.get("daily", {}); dates = daily.get("time", [])
        if not dates: return None
        row = {k: (v[0] if isinstance(v, list) and v else 0) for k, v in daily.items() if k != "time"}
        row["date"] = dates[0]
        fl   = fi.get("features", [])
        feats = build_features(row, ce, re, lat, lon, list(le_r.classes_))
        X = np.array([[feats.get(f, 0) for f in fl]])
        results = {}
        for key in COMPOUND_KEYS:
            m = models_multi.get(key)
            if m is None: continue
            try:
                raw = float(m.predict(X)[0])
                # PM compounds use log1p transform; CO/NO2/O3/SO2 are raw
                if key in ("pm2_5_target","pm10_target","dust_target","aod_target"):
                    results[key] = max(0.0, float(np.expm1(raw)))
                else:
                    results[key] = max(0.0, raw)
            except Exception:
                pass
        return results if results else None
    except Exception as e:
        logger.error("predict_compounds_today: %s", e)
        return None


# ── Two-stage Harmattan model ─────────────────────────────────────────────────

@st.cache_resource
def load_harmattan_models():
    """Load two-stage Harmattan model artefacts."""
    try:
        base = Path(__file__).parent.parent.parent / "models"
        with open(base / "model_harm_detector.pkl",  "rb") as f: detector   = pickle.load(f)
        with open(base / "model_harmattan.pkl",      "rb") as f: harm_mdl   = pickle.load(f)
        with open(base / "model_non_harmattan.pkl",  "rb") as f: non_harm   = pickle.load(f)
        return detector, harm_mdl, non_harm
    except Exception as e:
        logger.warning("load_harmattan_models: %s", e)
        return None, None, None


def predict_7day_smart(fd, city, region, lat, lon, model, enc, fi):
    """Route to two-stage Harmattan model when artefacts available and season matches,
    otherwise fall back to standard predict_7day().
    """
    from datetime import datetime as _dt
    try:
        from config import NORTHERN, HIGHLAND
    except ImportError:
        from ..config import NORTHERN, HIGHLAND
    detector, harm_mdl, non_harm = load_harmattan_models()
    month = _dt.now().month
    in_harmattan = month in (11, 12, 1, 2) and region in (NORTHERN | HIGHLAND)

    if detector is None or harm_mdl is None or not in_harmattan:
        return predict_7day(fd, city, region, lat, lon, model, enc, fi)

    try:
        le_c = enc["city"]; le_r = enc["region"]
        try:    ce = list(le_c.classes_).index(city); re = list(le_r.classes_).index(region)
        except: ce, re, region = nearest_known_city_enc(lat, lon, enc)
        daily = fd.get("daily", {}); dates = daily.get("time", [])
        fl    = fi.get("features", [])
        preds = []
        for i, date in enumerate(dates):
            row = {k: (v[i] if isinstance(v, list) and i < len(v) else 0)
                   for k, v in daily.items() if k != "time"}
            row["date"] = date
            feats = build_features(row, ce, re, lat, lon, list(le_r.classes_))
            X = np.array([[feats.get(f, 0) for f in fl]])
            try:
                is_harm = int(detector.predict(X)[0])
                mdl     = harm_mdl if is_harm else (non_harm or model)
                pred    = float(np.expm1(mdl.predict(X)[0]))
            except Exception:
                pred = float(np.expm1(model.predict(X)[0]))
            preds.append({
                "date":     date,
                "pm25":     max(0.5, pred),
                "wmo_code": daily.get("weather_code",  [3]*7)[i] if i < 7 else 3,
                "temp_max": daily.get("temperature_2m_max", [28]*7)[i] if i < 7 else 28,
                "temp_min": daily.get("temperature_2m_min", [18]*7)[i] if i < 7 else 18,
                "precip":   daily.get("precipitation_sum",  [0]*7)[i]  if i < 7 else 0,
                "humidity": daily.get("relative_humidity_2m_mean", [60]*7)[i] if i < 7 else 60,
                "wind":     daily.get("wind_speed_10m_max", [10]*7)[i] if i < 7 else 10,
            })
        return preds
    except Exception as e:
        logger.error("predict_7day_smart: %s", e, exc_info=True)
        return predict_7day(fd, city, region, lat, lon, model, enc, fi)
