"""utils/live_data.py — Live model predictions for all cities.

Replaces static CITY_STATS with real-time XGBoost predictions driven by
Open-Meteo weather forecasts.  Results are cached for 1 hour so the ~40
API calls only happen once per session refresh.

Usage in any page:
    from utils.live_data import get_live_stats, live_pm25

    stats = get_live_stats()          # dict matching CITY_STATS schema
    pm25  = live_pm25(city, region)   # float — live or static fallback
"""
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import streamlit as st

from config import CITIES, CITY_STATS, WHO_24H
from utils.api import fetch_forecast
from utils.models import load_models, predict_7day

logger = logging.getLogger("airsense")

# ── helpers ───────────────────────────────────────────────────────────────────

def _predict_city(city_name, region, lat, lon, model, enc, fi):
    """Fetch forecast + run model for one city.  Returns (city_name, result_dict) or None."""
    try:
        fd = fetch_forecast(lat, lon)
        if fd is None:
            return None
        preds = predict_7day(fd, city_name, region, lat, lon, model, enc, fi)
        if not preds:
            return None

        today_pm25 = preds[0]["pm25"]
        # % of the 7-day window above WHO 24h guideline
        who_exc = sum(1 for p in preds if p["pm25"] > WHO_24H) / len(preds) * 100

        # Carry over tier from static config (model confidence label)
        tier = CITY_STATS.get(city_name, {}).get("tier", "Medium")

        return city_name, {
            "mean_pm25": round(today_pm25, 2),
            "who_exc":   round(who_exc, 1),
            "region":    region,
            "tier":      tier,
            "forecasts": preds,          # full 7-day list — extra vs CITY_STATS
            "live":      True,           # flag so pages can show "live" badge
        }
    except Exception as e:
        logger.warning("live_data._predict_city %s: %s", city_name, e)
        return None


# ── main cached function ──────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def get_live_stats():
    """Return a dict of {city_name: stats} with live PM2.5 predictions.

    On first call this fetches ~40 forecasts and runs XGBoost inference —
    expect 15–30 s depending on network.  Subsequent calls within the hour
    return instantly from Streamlit's cache.

    Falls back to an empty dict (so callers can fall through to CITY_STATS)
    if the model artefacts are not found.
    """
    model, enc, fi = load_models()
    if model is None:
        logger.warning("get_live_stats: model not loaded — returning empty dict")
        return {}

    results = {}

    # Build flat task list: (city_name, region, lat, lon)
    tasks = [
        (city_name, region, lat, lon)
        for region, city_list in CITIES.items()
        for city_name, lat, lon in city_list
    ]

    # Parallel fetch — I/O bound, safe to thread
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures = {
            pool.submit(_predict_city, name, reg, lat, lon, model, enc, fi): name
            for name, reg, lat, lon in tasks
        }
        for future in as_completed(futures):
            out = future.result()
            if out:
                city_name, data = out
                results[city_name] = data

    logger.info("get_live_stats: %d/%d cities predicted", len(results), len(tasks))
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
    """Compute per-region SHAP feature importance from live Open-Meteo data.

    For each region, fetches today's weather for the first city, builds the
    feature vector, and runs SHAP TreeExplainer.  Returns
    {region: [(feature, mean_abs_shap), ...]} or None if model not available.
    Falls back to REGION_SHAP_FALLBACK when called from pages.
    """
    try:
        import shap as _shap
        import numpy as np
    except ImportError:
        logger.warning("compute_live_shap: shap not installed")
        return None

    from utils.models import build_features, nearest_known_city_enc

    model, enc, fi = load_models()
    if model is None:
        return None

    feature_list = fi.get("features", [])
    if not feature_list:
        return None

    results = {}

    for region, city_list in CITIES.items():
        city_name, lat, lon = city_list[0]          # representative city per region
        fd = fetch_forecast(lat, lon)
        if fd is None:
            continue

        daily = fd.get("daily", {})
        dates = daily.get("time", [])
        if not dates:
            continue

        le_c = enc["city"]
        le_r = enc["region"]
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
            shap_vals = explainer.shap_values(X)          # (n_days, n_features)
            mean_abs  = np.abs(shap_vals).mean(axis=0)
            top_idx   = mean_abs.argsort()[::-1][:7]
            results[region] = [(feature_list[i], float(mean_abs[i])) for i in top_idx]
        except Exception as e:
            logger.warning("compute_live_shap %s: %s", region, e)

    logger.info("compute_live_shap: %d regions computed", len(results))
    return results if results else None


def live_all() -> dict:
    """Merge live predictions over static CITY_STATS.  Always returns full city set."""
    merged = dict(CITY_STATS)          # start with static baseline
    merged.update(get_live_stats())    # overwrite with live where available
    return merged
