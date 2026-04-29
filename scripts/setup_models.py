"""
scripts/setup_models.py
=======================
Rebuilds all .pkl model artefacts that are tracked via Git LFS.

Run this once after cloning (or when git-lfs is unavailable) to produce
functional stub files from the data already embedded in the codebase:

    python scripts/setup_models.py

What it rebuilds
----------------
label_encoders.pkl      — sklearn LabelEncoders for city + region, fitted on
                          the 40-city / 10-region catalogue in api/main.py
region_shap.pkl         — dict of per-region top-7 SHAP values (hardcoded fallback)
platt_calibrator.pkl    — LogisticRegression reproducing platt_alert_calibration.json
scaler.pkl              — StandardScaler identity stub (mean=0, std=1)
model_ridge.pkl         — DummyRegressor(mean PM2.5) safe fallback
model_harmattan.pkl     — same
model_non_harmattan.pkl — same
model_harm_detector.pkl — DummyClassifier always predicting 0 (non-harmattan)
model_pm25_lag.pkl      — DummyRegressor fallback
model_lgb.pkl           — DummyRegressor fallback
models_multi.pkl        — dict of per-compound DummyRegressors
city_calibrators.pkl    — dict of per-city DummyRegressors (identity)
xgb_pm25.pkl            — DummyRegressor (xgb_pm25.json is the real model)
xgb_pm25_cams_only.pkl  — same
xgb_pm25_mixed.pkl      — same

NOTE: xgb_pm25.json is not LFS-tracked and is the real prediction model used
at runtime. These stubs allow the dashboard to import without crashing when
the optional pkl-based models are missing.
"""

import json
import pickle
import sys
from pathlib import Path

import numpy as np

ROOT   = Path(__file__).parent.parent
MODELS = ROOT / "models"

CITIES = {
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

REGION_SHAP_FALLBACK = {
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

COMPOUND_KEYS = [
    "pm2_5_target", "pm10_target", "dust_target", "aod_target",
    "co_target", "no2_target", "o3_target", "so2_target",
]
COMPOUND_DEFAULTS = {
    "pm2_5_target": 15.0, "pm10_target": 25.0, "dust_target": 5.0,
    "aod_target":    0.3,  "co_target": 200.0, "no2_target":  8.0,
    "o3_target":    40.0,  "so2_target":  4.0,
}


def save(name: str, obj) -> None:
    path = MODELS / name
    with open(path, "wb") as f:
        pickle.dump(obj, f, protocol=4)
    print(f"  ✓  {name}  ({path.stat().st_size} bytes)")


def dummy_regressor(constant: float):
    """DummyRegressor pre-fitted to return a constant value."""
    from sklearn.dummy import DummyRegressor
    m = DummyRegressor(strategy="constant", constant=constant)
    m.fit([[0]], [constant])
    return m


def dummy_classifier():
    """DummyClassifier pre-fitted to always predict class 0."""
    from sklearn.dummy import DummyClassifier
    m = DummyClassifier(strategy="constant", constant=0)
    m.fit([[0], [0]], [0, 1])
    return m


def main():
    print(f"\nAirSense — setup_models.py\nWriting stubs to: {MODELS}\n")

    try:
        import sklearn  # noqa: F401
    except ImportError:
        print("ERROR: scikit-learn not found.  Run:  pip install scikit-learn")
        sys.exit(1)

    # ── 1. label_encoders.pkl ──────────────────────────────────────────────────
    print("Building label_encoders.pkl …")
    from sklearn.preprocessing import LabelEncoder
    all_cities  = sorted(c for cities in CITIES.values() for c, *_ in cities)
    all_regions = sorted(CITIES.keys())
    enc = {
        "city":   LabelEncoder().fit(all_cities),
        "region": LabelEncoder().fit(all_regions),
    }
    print(f"  cities ({len(enc['city'].classes_)}): {list(enc['city'].classes_)[:5]} …")
    print(f"  regions ({len(enc['region'].classes_)}): {list(enc['region'].classes_)}")
    save("label_encoders.pkl", enc)

    # ── 2. region_shap.pkl ─────────────────────────────────────────────────────
    print("Building region_shap.pkl …")
    save("region_shap.pkl", REGION_SHAP_FALLBACK)

    # ── 3. platt_calibrator.pkl ────────────────────────────────────────────────
    # Use LogisticRegression with coefficients set from platt_alert_calibration.json
    print("Building platt_calibrator.pkl …")
    from sklearn.linear_model import LogisticRegression
    platt_json = json.loads((MODELS / "platt_alert_calibration.json").read_text())
    lr = LogisticRegression()
    lr.fit([[0], [100]], [0, 1])            # minimal fit to initialise internals
    lr.coef_      = np.array([[platt_json["coef"]]])
    lr.intercept_ = np.array([platt_json["intercept"]])
    lr.classes_   = np.array([0, 1])
    save("platt_calibrator.pkl", lr)

    # ── 4. scaler.pkl (identity) ───────────────────────────────────────────────
    print("Building scaler.pkl …")
    from sklearn.preprocessing import StandardScaler
    n = 68
    sc = StandardScaler()
    sc.mean_              = np.zeros(n)
    sc.scale_             = np.ones(n)
    sc.var_               = np.ones(n)
    sc.n_features_in_     = n
    sc.n_samples_seen_    = 1000
    save("scaler.pkl", sc)

    # ── 5. Regression stubs (log1p-space, matching predict_7day expectation) ───
    log_default = float(np.log1p(15.0))
    print("Building model_ridge / harmattan / lag / lgb stubs …")
    save("model_ridge.pkl",          dummy_regressor(log_default))
    save("model_harmattan.pkl",      dummy_regressor(log_default))
    save("model_non_harmattan.pkl",  dummy_regressor(log_default))
    save("model_pm25_lag.pkl",       dummy_regressor(log_default))
    save("model_lgb.pkl",            dummy_regressor(log_default))

    # ── 6. model_harm_detector.pkl ────────────────────────────────────────────
    print("Building model_harm_detector.pkl …")
    save("model_harm_detector.pkl", dummy_classifier())

    # ── 7. models_multi.pkl ────────────────────────────────────────────────────
    print("Building models_multi.pkl …")
    multi = {}
    for key in COMPOUND_KEYS:
        default = COMPOUND_DEFAULTS[key]
        # PM compounds use log1p transform; gas-phase compounds are raw
        val = (float(np.log1p(default))
               if key in ("pm2_5_target","pm10_target","dust_target","aod_target")
               else default)
        multi[key] = dummy_regressor(val)
    save("models_multi.pkl", multi)

    # ── 8. city_calibrators.pkl ───────────────────────────────────────────────
    print("Building city_calibrators.pkl …")
    all_city_names = [c for cities in CITIES.values() for c, *_ in cities]
    # Use DummyRegressor that returns log1p(mean) as a pass-through stub
    save("city_calibrators.pkl", {c: dummy_regressor(log_default) for c in all_city_names})

    # ── 9. xgb_*.pkl stubs (json is the real model) ───────────────────────────
    print("Building xgb pkl stubs …")
    save("xgb_pm25.pkl",           dummy_regressor(log_default))
    save("xgb_pm25_cams_only.pkl", dummy_regressor(log_default))
    save("xgb_pm25_mixed.pkl",     dummy_regressor(log_default))

    print("\nDone. Quick sanity check:")
    enc2 = pickle.load(open(MODELS / "label_encoders.pkl", "rb"))
    print(f"  label_encoders: {len(enc2['city'].classes_)} cities, {len(enc2['region'].classes_)} regions")
    shap2 = pickle.load(open(MODELS / "region_shap.pkl", "rb"))
    print(f"  region_shap: {len(shap2)} regions")
    multi2 = pickle.load(open(MODELS / "models_multi.pkl", "rb"))
    print(f"  models_multi keys: {list(multi2.keys())}")
    import math
    lr2 = pickle.load(open(MODELS / "platt_calibrator.pkl", "rb"))
    prob = lr2.predict_proba([[20]])[0][1]
    print(f"  platt P(exceed|PM2.5=20): {prob:.3f}")
    print("\nAll artefacts OK.")


if __name__ == "__main__":
    main()
