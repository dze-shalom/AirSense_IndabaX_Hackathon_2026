"""utils/models.py — Model loading and prediction."""
import numpy as np
import json
import pickle
import logging
from pathlib import Path
import streamlit as st
from config import CITIES, NORTHERN

logger = logging.getLogger("airsense")


@st.cache_resource
def load_models():
    try:
        import xgboost as xgb
        base  = Path(__file__).parent.parent.parent / "models"
        model = xgb.XGBRegressor()
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
        ("city_conf",  "city_confidence.json"),
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
        except Exception:
            out[k] = None
    return out


def get_conf_interval(region, art):
    if art and art.get("conformal"):
        return art["conformal"].get("region_intervals", {}).get(
            region, art["conformal"].get("global_q_hat", 30.8))
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
    dp    = row.get("dew_point_2m_mean", 15)
    sh    = row.get("sunshine_duration", 30000)
    dl    = row.get("daylight_duration", 43000)
    prec  = row.get("precipitation_sum", 0)
    rname = reg_classes[re] if re < len(reg_classes) else "Centre"
    north = rname in NORTHERN

    def tet(T): return 0.6108 * np.exp((17.27 * T) / (T + 237.3))
    vpd = max(0, tet(tdm) - tet(dp))

    return {
        "latitude": lat, "longitude": lon, "region_enc": re, "city_enc": ce,
        "month": month, "day_of_year": doy, "year": year,
        "month_sin": np.sin(2*np.pi*month/12), "month_cos": np.cos(2*np.pi*month/12),
        "doy_sin":   np.sin(2*np.pi*doy/365),  "doy_cos":   np.cos(2*np.pi*doy/365),
        "temp_max":  row.get("temperature_2m_max", 30),
        "temp_min":  row.get("temperature_2m_min", 18),
        "temp_mean": tdm, "apparent_temp_mean": tdm,
        "precipitation": prec, "precipitation_hours": row.get("precipitation_hours", 0),
        "wind_speed": ws, "wind_direction": row.get("wind_direction_10m_dominant", 180),
        "wind_u": -ws*np.sin(rad), "wind_v": -ws*np.cos(rad),
        "solar_radiation":    row.get("shortwave_radiation_sum", 18),
        "evapotranspiration": row.get("et0_fao_evapotranspiration", 5),
        "daylight_duration":  dl,
        "weather_code_cat":   min(row.get("weather_code", 3), 9),
        "humidity":        row.get("relative_humidity_2m_mean", 60),
        "dew_point":       dp,
        "surface_pressure":row.get("surface_pressure_mean", 950),
        "cloud_cover":     row.get("cloud_cover_mean", 50),
        "wind_100m":       row.get("wind_speed_100m_max", 20),
        "soil_moisture":   row.get("soil_moisture_0_to_7cm_mean", 0.2),
        "soil_temp":       row.get("soil_temperature_0_to_7cm_mean", 25),
        "wet_bulb_temp":   row.get("wet_bulb_temperature_2m_mean", 20),
        "vpd_max":         row.get("vapour_pressure_deficit_max", 2.0),
        "vpd":             round(vpd, 4),
        "temp_range":      row.get("temperature_2m_max", 30) - row.get("temperature_2m_min", 18),
        "sunshine_ratio":  min(sh / max(dl, 1), 1.0),
        "is_harmattan":    int(month in [11,12,1,2] and north),
        "is_dry_season":   int(month in [11,12,1,2,3]),
        "is_no_rain":      int(prec == 0),
        "is_no_wind":      int(ws < 2),
        "is_heat_stress":  int(tdm > 40),
        "is_dust_event":   0,
        "is_haze_fog":     int(row.get("weather_code", 3) in [45, 48]),
    }


def predict_7day(fd, city, region, lat, lon, model, enc, fi):
    if model is None or fd is None:
        return None
    try:
        le_c = enc["city"]; le_r = enc["region"]
        try:    ce = list(le_c.classes_).index(city);  re = list(le_r.classes_).index(region)
        except: ce, re, region = nearest_known_city_enc(lat, lon, enc) if enc else (0, 0, region)
        daily = fd.get("daily", {}); dates = daily.get("time", [])
        fl    = fi.get("features", [])
        preds = []
        for i, date in enumerate(dates):
            row   = {k: (v[i] if isinstance(v, list) and i < len(v) else 0)
                     for k, v in daily.items() if k != "time"}
            row["date"] = date
            feats = build_features(row, ce, re, lat, lon, list(le_r.classes_))
            fa    = np.array([[feats.get(f, 0) for f in fl]])
            pred  = float(np.expm1(model.predict(fa)[0]))
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
        logger.error("predict_7day: %s", e, exc_info=True)
        return None


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
    from config import NORTHERN, HIGHLAND
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
