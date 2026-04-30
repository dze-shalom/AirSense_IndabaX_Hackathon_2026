# AirSense Cameroon — IndabaX 2026

> **AI for Climate and Health Resilience in Cameroon**
> Real-time PM2.5 monitoring, 7-day forecasting, and health advisory across 85+ cities in all 10 regions.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Data Pipeline](#data-pipeline)
5. [Model Training](#model-training)
6. [Public API](#public-api)
7. [Dashboard Pages](#dashboard-pages)
8. [Configuration](#configuration)
9. [Deployment](#deployment)
10. [Innovations](#innovations)
11. [Team](#team)

---

## Overview

AirSense Cameroon predicts PM2.5 air quality across Cameroon using 6 years of satellite reanalysis (CAMS) combined with meteorological data (Open-Meteo). The system:

- **Predicts** daily PM2.5 concentrations for 85+ cities across all 10 regions
- **Forecasts** 7 days ahead using XGBoost + live Open-Meteo weather data
- **Alerts** with Platt-calibrated exceedance probability (F1 = 0.82 at P=0.50)
- **Explains** predictions via region-specific SHAP feature attributions
- **Projects** future air quality under CMIP6 SSP2-4.5 and SSP5-8.5 climate scenarios
- **Advises** schools, farms, and vulnerable groups in English and French

---

## Architecture

```
AirSense_IndabaX_Hackathon_2026/
│
├── dashboard/                      # Streamlit web application
│   ├── app.py                      # Entry point — routing only (56 lines)
│   ├── config.py                   # Constants: colours, cities, translations, nav
│   ├── manifest.json               # PWA manifest for mobile install
│   ├── components/
│   │   ├── sidebar.py              # Navigation, CSS injection, light/dark theme
│   │   ├── ui.py                   # card(), sec(), info_box(), SVG gauges
│   │   └── charts.py               # PLO() — theme-aware Plotly layout defaults
│   ├── pages/
│   │   ├── overview.py             # National choropleth map + city rankings
│   │   ├── explorer.py             # Forecast + Analytics + Compare (tabbed)
│   │   ├── alerts.py               # Alert centre + Health calculator (tabbed)
│   │   ├── science.py              # SHAP analysis + Climate 2050 projections
│   │   ├── ai_assistant.py         # Claude-powered bilingual health Q&A
│   │   └── about.py                # Model card, innovations, team
│   └── utils/
│       ├── helpers.py              # aqi(), bfai(), classify_source(), city_profile()
│       ├── live_data.py            # get_live_stats(), compute_live_shap()
│       ├── models.py               # load_models(), predict_7day(), get_alert_prob()
│       └── api.py                  # fetch_forecast(), geocode_city(), call_claude()
│
├── api/
│   └── main.py                     # FastAPI backend — 20+ REST endpoints
│
├── models/                         # Trained model artefacts (Git LFS)
│   ├── xgb_pm25.json               # Main XGBoost model (CAMS features)
│   ├── xgb_pm25_mixed.pkl          # Mixed CAMS+meteo variant
│   ├── label_encoders.pkl          # City + region LabelEncoders
│   ├── features.json               # Ordered feature list for inference
│   ├── conformal_intervals.json    # Per-city 90% conformal prediction intervals
│   ├── platt_alert_calibration.json# Platt scaling: sigmoid(0.222·PM − 3.037)
│   ├── region_shap.pkl             # Per-region top-7 SHAP feature weights
│   └── ...                         # Additional pkl stubs (see setup_models.py)
│
├── scripts/
│   └── setup_models.py             # Rebuild all artefacts from scratch (run after clone)
│
├── notebooks/                      # Training & analysis notebooks
├── deployment/
│   └── render.yaml                 # Render.com deployment config (API + dashboard)
└── requirements.txt
```

**Data flow:**

```
Open-Meteo API ──┐
CAMS Reanalysis ──┤──► Feature Engineering ──► XGBoost ──► PM2.5 Prediction
City/Region enc ──┘          │                     │
                        SHAP Explainer        Conformal CI
                             │                     │
                        Alert Probability ◄── Platt Calibration
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- (Optional) Anthropic API key for the AI Assistant page

### 1. Clone and install

```bash
git clone https://github.com/dze-shalom/airsense_indabax_hackathon_2026
cd airsense_indabax_hackathon_2026
pip install -r requirements.txt
```

### 2. Rebuild model artefacts

If the `.pkl` files are not present (Git LFS unavailable), generate stubs:

```bash
python scripts/setup_models.py
```

This takes ~5 seconds and produces functional fallback models for all artefacts. The main prediction model (`xgb_pm25.json`) is tracked in Git directly and does not require LFS.

### 3. Configure secrets (optional)

Create `.streamlit/secrets.toml` for the AI Assistant:

```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

### 4. Run the dashboard

```bash
streamlit run dashboard/app.py
```

Open http://localhost:8501 in your browser.

### 5. Run the API (optional)

```bash
uvicorn api.main:app --reload --port 8000
```

Swagger UI: http://localhost:8000/docs

---

## Data Pipeline

### Training data

| Source | Period | Resolution | Variables |
|--------|--------|------------|-----------|
| CAMS Reanalysis | 2018–2024 | Daily, city-level | PM2.5, PM10, dust, CO, NO₂, O₃, AOD |
| Open-Meteo ERA5 | 2018–2024 | Daily, city-level | Temp, humidity, wind, precipitation, solar |

City coordinates for 85+ cities across all 10 regions are embedded in `config.py` and `scripts/setup_models.py`.

### Feature engineering

Key engineered features:

| Feature | Description |
|---------|-------------|
| `is_harmattan` | Nov–Feb AND northern region AND NE wind bearing |
| `is_dry_season` | Month in {11,12,1,2,3} |
| `is_dust_event` | CAMS dust PM2.5 > 20 µg/m³ |
| `month_sin`, `month_cos` | Cyclical month encoding |
| `day_of_year` | Seasonal signal (1–365) |
| `daylight_duration` | Solar hours (proxy for photochemistry) |
| `city_enc`, `region_enc` | Label-encoded spatial identifiers |

### Live inference

At runtime the dashboard fetches 7-day weather forecasts from Open-Meteo for any selected city, applies the same feature transformations, and runs them through `xgb_pm25.json`.

```python
# utils/models.py
def predict_7day(city, lat, lon):
    fd = fetch_forecast(lat, lon)          # Open-Meteo 7-day
    rows = build_feature_rows(fd, city)    # same pipeline as training
    model = xgb.XGBRegressor()
    model.load_model("models/xgb_pm25.json")
    return model.predict(rows)
```

---

## Model Training

### Retrain from scratch

```bash
# 1. Collect CAMS + Open-Meteo data for all cities
python notebooks/01_data_collection.ipynb  # or equivalent script

# 2. Feature engineering
python notebooks/02_feature_engineering.ipynb

# 3. Train XGBoost
python notebooks/03_train_xgb.ipynb

# 4. Calibrate alerts (Platt scaling)
python notebooks/04_calibration.ipynb

# 5. Compute SHAP per region
python notebooks/05_shap_analysis.ipynb

# 6. Package artefacts
python scripts/setup_models.py   # adds any stubs not produced above
```

### Model performance

| Model | MAE (µg/m³) | R² | Notes |
|-------|-------------|-----|-------|
| XGBoost (CAMS) | 3.1 | 0.91 | Primary — used for forecast |
| XGBoost (mixed) | 3.4 | 0.89 | Open-Meteo features only |
| Ridge (baseline) | 6.2 | 0.72 | Fallback stub |

Alert threshold classifier (Platt-calibrated logistic):
- **F1 = 0.82** at P(exceed) = 0.50
- Formula: `P = sigmoid(0.222 × PM2.5 − 3.037)`

Conformal prediction intervals provide city-specific 90% coverage bounds without distributional assumptions.

---

## Public API

The FastAPI backend at `api/main.py` exposes 20+ endpoints.

### Base URL

```
http://localhost:8000        (local)
https://airsense-cm.onrender.com  (deployed)
```

### Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check + artefact status |
| `GET` | `/regions` | All regions, cities, coordinates |
| `GET` | `/predict` | Predict PM2.5 for a city on a date |
| `GET` | `/forecast/{city}` | 7-day XGBoost + Open-Meteo forecast |
| `GET` | `/alert-status/{city}` | Current AQI level + threshold alert |
| `GET` | `/alert-prob/{city}` | Platt-scaled P(exceed WHO 24h) |
| `GET` | `/leaderboard` | Top-N most polluted cities |
| `GET` | `/bfai/{city}` | Breath of Fresh Air Index (0–100) |
| `GET` | `/source/{city}` | Pollution source attribution (5 sources) |
| `GET` | `/conformal/{city}` | 90% prediction interval (calibrated) |
| `GET` | `/harmattan/{city}` | Harmattan early-warning risk score |
| `GET` | `/school-advisory/{city}` | School outdoor action level (1–4) |
| `GET` | `/agri-advisory/{city}` | Agricultural dust/drought alert |
| `GET` | `/sms-preview/{city}` | Bilingual SMS alert text (EN/FR) |
| `GET` | `/explain/{city}` | Region-specific SHAP fingerprint |
| `GET` | `/climate/{city}` | CMIP6 2050 projections (SSP2/SSP5) |
| `GET` | `/health-impact/{city}` | WHO concentration-response estimates |
| `GET` | `/africa-benchmark` | Cameroon vs 12 African cities |
| `GET` | `/compare` | Side-by-side seasonal profiles of 2 cities |
| `POST` | `/ingest` | ESP32 IoT sensor data ingestion |
| `GET` | `/sensor-feed` | Recent sensor readings buffer |

### Example request

```bash
curl "http://localhost:8000/forecast/Douala"
```

```json
{
  "city": "Douala",
  "region": "Littoral",
  "forecast": [
    {"date": "2026-05-01", "pm25": 18.4, "aqi": "moderate", "ci_low": 14.1, "ci_high": 22.7},
    {"date": "2026-05-02", "pm25": 16.9, "aqi": "moderate", "ci_low": 12.8, "ci_high": 21.0},
    ...
  ],
  "alert_prob": 0.43,
  "source_attribution": {"Dust": 0.08, "Traffic": 0.50, "Biomass": 0.12, "Industry": 0.15, "Secondary": 0.10, "Other": 0.05}
}
```

### Interactive docs

Navigate to `http://localhost:8000/docs` for the full Swagger UI with request schemas, response models, and a Try It Out interface.

---

## Dashboard Pages

| Page | Key features |
|------|-------------|
| **Overview** | National choropleth map (Plotly Mapbox), city rankings, seasonal heatmap, WHO exceedance stats |
| **Explorer** | 7-day PM2.5 forecast with confidence intervals, source attribution donut, BFAI gauge, multi-city compare |
| **Alerts & Health** | Alert centre with calibrated exceedance probabilities, school/agricultural advisories, health impact calculator, seasonal advisory calendar |
| **Science** | SHAP feature importance per region, climate 2050 projections (CMIP6 SSP2/SSP5), model comparison table, Africa benchmark |
| **AI Assistant** | Claude-powered bilingual (EN/FR) health Q&A with city-specific context |
| **About** | Model card, technical innovations, team |

### PM2.5 threshold standards

The dashboard supports configurable reference standards selectable from the sidebar:

| Standard | 24h limit |
|----------|-----------|
| WHO 2021 | 15 µg/m³ |
| EU 2024 | 25 µg/m³ |
| US EPA | 35 µg/m³ |
| ECOWAS | 50 µg/m³ |
| Custom | User-defined |

All AQI colour bands, alert counts, and charts update dynamically when the standard is changed.

---

## Configuration

### Threshold standard

Change in the sidebar under "PM2.5 Standard". Persists in Streamlit session state.

### Language

Toggle EN ↔ FR in the sidebar. All UI strings, advisories, form labels, and chart annotations update immediately.

### Theme

Switch Light ↔ Dark in the sidebar top bar. Particle background, chart palettes, map tiles, and all surfaces update.

### Secrets (`/.streamlit/secrets.toml`)

```toml
ANTHROPIC_API_KEY = "sk-ant-..."   # Required for AI Assistant page
```

---

## Deployment

### Render.com (recommended)

`deployment/render.yaml` defines two services — dashboard and API:

```bash
# Deploy both services with one push
git push origin main
```

Render auto-detects `render.yaml` and deploys both services. Environment variable `ANTHROPIC_API_KEY` must be set in the Render dashboard.

### Docker (manual)

```bash
# Dashboard
docker build -t airsense-dashboard -f docker/Dockerfile.dashboard .
docker run -p 8501:8501 airsense-dashboard

# API
docker build -t airsense-api -f docker/Dockerfile.api .
docker run -p 8000:8000 airsense-api
```

### Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Optional | Powers the AI Assistant page |
| `PORT` | Auto (Render) | Port for the web service |

---

## Innovations

1. **Breath of Fresh Air Index (BFAI)** — Composite 0–100 score combining PM2.5 (50%), wind speed (25%), and humidity (25%) for intuitive air quality communication beyond raw µg/m³.

2. **Harmattan Early-Warning System** — Detects Saharan dust intrusions from NE wind bearing + dry-season indicator + PM2.5 spike. Triggers 48h advance advisories in northern regions.

3. **Conformal Prediction Intervals** — Distribution-free 90% confidence bounds per city, enabling honest uncertainty quantification without Gaussian assumptions.

4. **Platt-Calibrated Alert Classifier** — Logistic regression maps XGBoost PM2.5 output to exceedance probability (F1 = 0.82). Per-city recalibration corrects regional distribution shift.

5. **Dynamic Source Attribution** — Five-source decomposition (Dust, Biomass Burning, Traffic, Industry, Secondary Aerosol) computed from live meteorological conditions + SHAP weights.

6. **CMIP6 Climate Projections** — SSP2-4.5 and SSP5-8.5 scenarios projected to 2050 with bias correction from historical CAMS baseline.

7. **Bilingual Advisory System** — All alerts, advisories, and health guidance in English and French. School outdoor action levels and agricultural dust/drought alerts tailored per region.

8. **Configurable Reference Standards** — WHO 2021, EU 2024, US EPA, ECOWAS, or custom threshold. All visualisations and alert counts update dynamically.

---

## Team

**Dze-Kum Shalom Chow** — Lead developer, ML modelling, dashboard design
IndabaX Cameroon 2026

---

*Data sources: CAMS Reanalysis (Copernicus/ECMWF), Open-Meteo ERA5, WHO Global Air Quality Guidelines 2021*
