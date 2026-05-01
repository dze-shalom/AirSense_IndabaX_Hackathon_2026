"""utils/live_data.py — Live model predictions for all cities.

Primary path: calls the AirSense FastAPI backend (GET /forecast/{city}).
Fallback path: loads models locally and runs XGBoost inference directly.

Usage:
    from utils.live_data import get_live_stats, live_pm25
    stats = get_live_stats()      # dict matching CITY_STATS schema
    pm25  = live_pm25(city)       # float — live or static fallback
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from config import CITIES, CITY_STATS, WHO_24H

logger = logging.getLogger("airsense")


# ── API-first path ────────────────────────────────────────────────────────────

def _fetch_city_via_api(city_name, region, lat, lon):
    """Fetch one city forecast from the FastAPI backend."""
    from utils.api import fetch_airsense_forecast, _map_api_forecast_to_preds
    data = fetch_airsense_forecast(city_name)
    if not data or not data.get("forecast"):
        return None
    preds = _map_api_forecast_to_preds(data)
    if not preds:
        return None
    today_pm25 = preds[0]["pm25"]
    who_exc = sum(1 for p in preds if p["pm25"] > WHO_24H) / len(preds) * 100
    tier = CITY_STATS.get(city_name, {}).get("tier", "Medium")
    return city_name, {
        "mean_pm25": round(today_pm25, 2),
        "who_exc":   round(who_exc, 1),
        "region":    region,
        "tier":      tier,
        "forecasts": preds,
        "live":      True,
        "source":    "api",
    }


# ── Local-model fallback path ─────────────────────────────────────────────────

def _fetch_city_local(city_name, region, lat, lon, model, enc, fi):
    """Fetch forecast + run local XGBoost for one city."""
    from utils.api import fetch_forecast
    from utils.models import predict_7day
    try:
        fd = fetch_forecast(lat, lon)
        if fd is None:
            return None
        preds = predict_7day(fd, city_name, region, lat, lon, model, enc, fi)
        if not preds:
            return None
        today_pm25 = preds[0]["pm25"]
        who_exc = sum(1 for p in preds if p["pm25"] > WHO_24H) / len(preds) * 100
        tier = CITY_STATS.get(city_name, {}).get("tier", "Medium")
        return city_name, {
            "mean_pm25": round(today_pm25, 2),
            "who_exc":   round(who_exc, 1),
            "region":    region,
            "tier":      tier,
            "forecasts": preds,
            "live":      True,
            "source":    "local",
        }
    except Exception as e:
        logger.warning("live_data._fetch_city_local %s: %s", city_name, e)
        return None


# ── main cached function ──────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_live_stats():
    """Return {city_name: stats} with live PM2.5 predictions.

    Tries FastAPI backend first; falls back to local XGBoost if unreachable.
    Subsequent calls within the hour return instantly from Streamlit cache.
    """
    from utils.api import api_health_check

    tasks = [
        (city_name, region, lat, lon)
        for region, city_list in CITIES.items()
        for city_name, lat, lon in city_list
    ]

    use_api = api_health_check()
    results = {}

    if use_api:
        logger.info("get_live_stats: using FastAPI backend")
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {
                pool.submit(_fetch_city_via_api, *task): task[0]
                for task in tasks
            }
            for future in as_completed(futures):
                out = future.result()
                if out:
                    city_name, data = out
                    results[city_name] = data

        if results:
            logger.info("get_live_stats (api): %d/%d cities", len(results), len(tasks))
            return results
        logger.warning("get_live_stats: API returned no results — falling back to local")

    # Fallback: local model
    from utils.models import load_models
    model, enc, fi = load_models()
    if model is None:
        logger.warning("get_live_stats: local model not loaded — returning empty dict")
        return {}

    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {
            pool.submit(_fetch_city_local, *task, model, enc, fi): task[0]
            for task in tasks
        }
        for future in as_completed(futures):
            out = future.result()
            if out:
                city_name, data = out
                results[city_name] = data

    logger.info("get_live_stats (local): %d/%d cities", len(results), len(tasks))
    return results


def live_pm25(city: str, region: str = None) -> float:
    """Return live PM2.5 for a city, falling back to static CITY_STATS then 15.0."""
    stats = get_live_stats()
    if city in stats:
        return stats[city]["mean_pm25"]
    fallback = CITY_STATS.get(city, {})
    return fallback.get("mean_pm25", 15.0)


def live_city(city: str, region: str = None) -> dict:
    """Return full stats dict for a city (live if available, else static)."""
    stats = get_live_stats()
    if city in stats:
        return stats[city]
    return CITY_STATS.get(city, {
        "mean_pm25": 15.0,
        "who_exc":   40.0,
        "region":    region or "Centre",
        "tier":      "Medium",
        "live":      False,
    })


@st.cache_data(ttl=3600, show_spinner=False)
def compute_live_shap():
    """Per-region SHAP feature importance.

    Tries GET /explain/{city} on the FastAPI backend first.
    Falls back to running SHAP TreeExplainer locally if the API is unreachable
    or the shap package is not installed.
    Returns {region: [(feature, mean_abs_shap), ...]} or None.
    """
    from utils.api import api_health_check, fetch_airsense_explain

    if api_health_check():
        results = {}
        for region, city_list in CITIES.items():
            city_name = city_list[0][0]
            data = fetch_airsense_explain(city_name)
            if data and data.get("top_drivers"):
                results[region] = [
                    (d["feature"], d["mean_abs_shap"])
                    for d in data["top_drivers"]
                ]
        if results:
            logger.info("compute_live_shap (api): %d regions", len(results))
            return results
        logger.warning("compute_live_shap: API returned no SHAP data — falling back to local")

    # Local SHAP fallback
    try:
        import shap as _shap
        import numpy as np
    except ImportError:
        logger.warning("compute_live_shap: shap not installed and API unavailable")
        return None

    from utils.api import fetch_forecast
    from utils.models import load_models, build_features, nearest_known_city_enc

    model, enc, fi = load_models()
    if model is None:
        return None

    feature_list = fi.get("features", [])
    if not feature_list:
        return None

    results = {}
    for region, city_list in CITIES.items():
        city_name, lat, lon = city_list[0]
        fd = fetch_forecast(lat, lon)
        if fd is None:
            continue
        daily = fd.get("daily", {})
        dates = daily.get("time", [])
        if not dates:
            continue
        le_c = enc["city"]; le_r = enc["region"]
        try:
            ce = list(le_c.classes_).index(city_name)
            re = list(le_r.classes_).index(region)
        except Exception:
            ce, re, region = nearest_known_city_enc(lat, lon, enc)
        X_rows = []
        for i, date in enumerate(dates):
            row = {k: (v[i] if isinstance(v, list) and i < len(v) else 0)
                   for k, v in daily.items() if k != "time"}
            row["date"] = date
            feats = build_features(row, ce, re, lat, lon, list(le_r.classes_))
            X_rows.append([feats.get(f, 0) for f in feature_list])
        X = np.array(X_rows)
        try:
            explainer = _shap.TreeExplainer(model)
            shap_vals = explainer.shap_values(X)
            mean_abs  = np.abs(shap_vals).mean(axis=0)
            top_idx   = mean_abs.argsort()[::-1][:7]
            results[region] = [(feature_list[i], float(mean_abs[i])) for i in top_idx]
        except Exception as e:
            logger.warning("compute_live_shap local %s: %s", region, e)

    logger.info("compute_live_shap (local): %d regions computed", len(results))
    return results if results else None


def live_all() -> dict:
    """Merge live predictions over static CITY_STATS.  Always returns full city set."""
    merged = dict(CITY_STATS)          # start with static baseline
    merged.update(get_live_stats())    # overwrite with live where available
    return merged
