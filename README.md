# AirSense Cameroon — IndabaX 2026

> **AI for Climate and Health Resilience in Cameroon**
> Real-time PM2.5 monitoring, 7-day forecasting, and health advisory across 85+ cities in all 10 regions.

**[Live Dashboard →](https://airsensecameroon.streamlit.app/)** | **[API Docs →](https://airsense-cm.onrender.com/docs)**

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Progressive Web App (PWA)](#progressive-web-app-pwa)
5. [Data Pipeline](#data-pipeline)
6. [Model Training](#model-training)
7. [Public API](#public-api)
8. [Dashboard Pages](#dashboard-pages)
9. [Configuration](#configuration)
10. [Deployment](#deployment)
11. [Innovations](#innovations)
12. [Team](#team)

---

## Overview

AirSense Cameroon predicts PM2.5 air quality across Cameroon using 6 years of satellite reanalysis (CAMS) combined with meteorological data (Open-Meteo). The system:

- **Predicts** daily PM2.5 concentrations for 85+ cities across all 10 regions
- **Forecasts** 7 days ahead using XGBoost + live Open-Meteo weather data
- **Alerts** with Platt-calibrated exceedance probability (F1 = 0.847 at P=0.50)
- **Explains** predictions via region-specific SHAP feature attributions
- **Projects** future air quality under CMIP6 SSP2-4.5 and SSP5-8.5 climate scenarios
- **Advises** schools, farms, and vulnerable groups in English and French
- **Reports** downloadable PDF air quality reports per city
- **Chats** via a conversational AI assistant powered by Groq (Llama 3.1, free tier)

---

## Architecture

```
AirSense_IndabaX_Hackathon_2026/
│
├── dashboard/                      # Streamlit web application
│   ├── app.py                      # Entry point — routing only
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
│   │   ├── science.py              # SHAP + Climate 2050 + Policy brief + PDF report
│   │   ├── ai_assistant.py         # Groq-powered conversational health assistant
│   │   └── about.py                # Model card, innovations, team
│   └── utils/
│       ├── helpers.py              # aqi(), bfai(), live_source_attribution()
│       ├── live_data.py            # get_live_stats(), compute_live_shap()
│       ├── models.py               # load_models(), predict_7day(), get_alert_prob()
│       ├── api.py                  # fetch_forecast(), stream_groq(), call_groq()
│       └── pdf_report.py           # generate_pdf_report() — ReportLab PDF export
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
│   └── region_shap.pkl             # Per-region top-7 SHAP feature weights
│
├── scripts/
│   └── setup_models.py             # Rebuild all artefacts from scratch
│
├── notebooks/                      # Training & analysis notebooks
├── deployment/
│   └── render.yaml                 # Render.com deployment config
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
                             │
                      Groq LLM (free) ──► Conversational AI + Policy Brief
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Git
- (Optional) Free [Groq API key](https://console.groq.com) for the AI Assistant and policy briefs

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

This takes ~5 seconds and produces functional fallback models. The main prediction model (`xgb_pm25.json`) is tracked in Git directly and does not require LFS.

### 3. Configure secrets (optional but recommended)

Create `.streamlit/secrets.toml` (this file is gitignored — never commit it):

```toml
GROQ_API_KEY = "gsk_..."         # Free at console.groq.com — enables AI assistant + policy briefs
AIRSENSE_API_URL = "http://localhost:8000"  # Optional: point to your running API backend
```

**Getting a free Groq key:**
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up (Google or GitHub)
3. Click **API Keys → Create API Key**
4. Copy the key (starts with `gsk_...`)

Without the key, the dashboard still works fully — the AI assistant falls back to rule-based responses and policy briefs use data-driven templates.

### 4. Run the dashboard

```bash
cd dashboard
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser, or use the [live hosted dashboard](https://airsensecameroon.streamlit.app/).

### 5. Run the API (optional)

The dashboard works without the API (uses local models as fallback). To enable API-first mode:

```bash
uvicorn api.main:app --reload --port 8000
```

Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Progressive Web App (PWA)

AirSense Cameroon ships as a **Progressive Web App** — it can be installed directly on your phone or desktop and works offline with cached data, without going through an app store.

### What the PWA provides

| Feature | Detail |
|---------|--------|
| **Installable** | Adds to your home screen / taskbar like a native app |
| **Standalone mode** | Runs without browser chrome (no address bar) |
| **Offline support** | Service worker caches the app shell; last-known data is shown when offline |
| **Theme integration** | Matches system theme colour (`#4a6fa5` / `#1a3c5e`) |
| **Bilingual** | Full EN/FR experience carries over to the installed app |

The PWA is powered by two files:

- `dashboard/manifest.json` — declares the app name, icons, colours, and display mode  
- `dashboard/sw.js` — service worker that caches the app shell on install and uses a network-first strategy for navigation, cache-first for static assets

---

### How to install AirSense on your device

#### Android (Chrome / Edge / Samsung Internet)

1. Open **[https://airsensecameroon.streamlit.app](https://airsensecameroon.streamlit.app)** in **Chrome** (or any Chromium-based browser).
2. Tap the **three-dot menu** (⋮) in the top-right corner.
3. Tap **"Add to Home screen"** or **"Install app"**.
4. Confirm by tapping **"Add"** in the prompt.
5. The AirSense icon appears on your home screen — tap it to launch in standalone mode.

> **Tip:** Some Android browsers show an automatic install banner at the bottom of the screen after a few seconds. Tap **"Install"** there to skip the menu steps.

---

#### iPhone / iPad (Safari — iOS 16.4+)

> PWA install is only available through **Safari** on iOS. Chrome/Firefox on iOS cannot install PWAs.

1. Open **[https://airsensecameroon.streamlit.app](https://airsensecameroon.streamlit.app)** in **Safari**.
2. Tap the **Share** button (box with an arrow pointing up) in the bottom toolbar.
3. Scroll down in the share sheet and tap **"Add to Home Screen"**.
4. Edit the name if desired, then tap **"Add"** in the top-right corner.
5. The AirSense icon appears on your home screen.

> On iOS 16.4+, the installed app runs in standalone mode (no Safari UI) and the service worker caches the app shell for basic offline use.

---

#### Desktop — Chrome / Edge (Windows, macOS, Linux)

1. Open **[https://airsensecameroon.streamlit.app](https://airsensecameroon.streamlit.app)** in **Chrome** or **Edge**.
2. Look for the **install icon** (monitor with a down-arrow) in the address bar on the right side.  
   - In Chrome it looks like **⊕** or a small desktop icon.  
   - In Edge it looks like a **+** inside a box.
3. Click it and select **"Install"** in the confirmation dialog.
4. AirSense opens in its own window and is pinned to your taskbar / Applications folder / dock.

Alternatively:
- **Chrome:** Menu (⋮) → **"Cast, save, and share"** → **"Install page as app…"**
- **Edge:** Menu (…) → **"Apps"** → **"Install this site as an app"**

---

#### Verify the PWA is active (developer check)

Open DevTools → **Application** tab → **Service Workers**. You should see `sw.js` listed as `activated and running`. Under **Manifest** you should see the AirSense app name, icons, and `display: standalone`.

---

### Running the PWA locally

The service worker registers automatically when the Streamlit dashboard is served. For local testing, the dashboard must be served over **HTTPS** or **localhost** (both satisfy the secure-context requirement for service workers).

```bash
cd dashboard
streamlit run app.py
# Then open http://localhost:8501 — the service worker registers immediately
```

To test the offline fallback, open DevTools → **Network** tab → tick **"Offline"**, then reload the page. The cached shell should load.

---

## Data Pipeline

### Training data

| Source | Period | Resolution | Variables |
|--------|--------|------------|-----------|
| CAMS Reanalysis | 2018–2024 | Daily, city-level | PM2.5, PM10, dust, CO, NO₂, O₃, AOD |
| Open-Meteo ERA5 | 2018–2024 | Daily, city-level | Temp, humidity, wind, precipitation, solar |

City coordinates for 85+ cities across all 10 regions are embedded in `config.py`.

### Feature engineering

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

```python
# utils/models.py — API-first with local fallback
def predict_7day(city, lat, lon):
    if api_health_check():
        return fetch_airsense_forecast(city)   # FastAPI backend
    fd = fetch_forecast(lat, lon)              # Open-Meteo direct
    rows = build_feature_rows(fd, city)
    model = xgb.XGBRegressor()
    model.load_model("models/xgb_pm25.json")
    return model.predict(rows)
```

---

## Model Training

### Retrain from scratch

Run the notebooks **in order** using Jupyter:

```bash
# 1. Clean raw data, engineer features, fetch CAMS + ERA5, build proxy targets
jupyter nbconvert --to notebook --execute notebooks/00_Data_Cleaning.ipynb

# 2. Exploratory data analysis — distributions, correlations, Harmattan seasonality
jupyter nbconvert --to notebook --execute notebooks/01_EDA.ipynb

# 3. Train all models (XGBoost + Optuna, ensemble, GNN, Transformer),
#    calibrate alerts, compute SHAP, save all artefacts to models/
jupyter nbconvert --to notebook --execute notebooks/02_Modelling.ipynb

# 4. Generate publication-ready pitch charts to outputs/
jupyter nbconvert --to notebook --execute notebooks/03_Pitch_Charts.ipynb

# Optional: rebuild stub artefacts without re-training (if models/ is missing)
python scripts/setup_models.py
```

### Model performance

| Model | MAE (µg/m³) | R² | Notes |
|-------|-------------|-----|-------|
| XGBoost (CAMS-only) | 6.35 | 0.60 | Primary — real measurements only |
| XGBoost (mixed) | 6.27 | 0.60 | Includes proxy data |
| Ridge (baseline) | 7.52 | 0.45 | City-month average fallback |

Alert classifier (Platt-calibrated logistic):
- **F1 = 0.847** at P(exceed) = 0.50
- Formula: `P = sigmoid(0.2221 × PM2.5 − 3.0372)`

---

## Public API

### Base URL

```
http://localhost:8000        (local)
https://airsense-cm.onrender.com  (deployed)
```

### Key endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Service health check |
| `GET` | `/regions` | All regions, cities, coordinates |
| `GET` | `/forecast/{city}` | 7-day XGBoost + Open-Meteo forecast |
| `GET` | `/alert-status/{city}` | Current AQI level + alert |
| `GET` | `/alert-prob/{city}` | Platt-scaled P(exceed WHO 24h) |
| `GET` | `/explain/{city}` | Region SHAP fingerprint |
| `GET` | `/source/{city}` | 5-source pollution attribution |
| `GET` | `/health-impact/{city}` | WHO concentration-response estimates |
| `GET` | `/school-advisory/{city}` | School outdoor action level (1–4) |
| `GET` | `/bfai/{city}` | Breath of Fresh Air Index (0–100) |
| `GET` | `/climate/{city}` | CMIP6 2050 projections |
| `GET` | `/leaderboard` | Top-N most polluted cities |
| `GET` | `/africa-benchmark` | Cameroon vs 12 African cities |
| `POST` | `/ingest` | ESP32 IoT sensor data ingestion |

```bash
# Example
curl "http://localhost:8000/forecast/Douala"
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Dashboard Pages

| Page | Key features |
|------|-------------|
| **Overview** | National map (city PM2.5 bubbles, filter by region/AQI), AQI distribution donut, city rankings, seasonal heatmap, Harmattan animation |
| **Explorer** | 7-day PM2.5 forecast with confidence intervals, source attribution donut, BFAI gauge, multi-city seasonal compare |
| **Alerts & Health** | Alert centre (calibrated probabilities), school/agricultural advisories, health impact calculator, seasonal calendar |
| **Science** | SHAP feature importance per region, climate 2050 projections (SSP2/SSP5), model comparison, policy simulator, AI policy brief, **PDF report download** |
| **AI Assistant** | Conversational health assistant (Groq Llama 3.1, streaming) with live PM2.5 context for all cities; rule-based fallback when no key |
| **About** | Model card, technical innovations, team |

### PM2.5 threshold standards

| Standard | 24h limit |
|----------|-----------|
| WHO 2021 | 15 µg/m³ |
| EU 2024 | 25 µg/m³ |
| US EPA | 35 µg/m³ |
| ECOWAS | 50 µg/m³ |
| Custom | User-defined |

---

## Configuration

### Secrets (`.streamlit/secrets.toml`)

```toml
GROQ_API_KEY    = "gsk_..."                    # Free — AI assistant + policy briefs
AIRSENSE_API_URL = "https://your-api.onrender.com"  # Optional FastAPI backend
```

### Language
Toggle **EN ↔ FR** in the sidebar. All UI text, advisories, charts, policy briefs, and PDF reports switch language immediately.

### Theme
Switch **Light ↔ Dark** in the top bar. Chart palettes, map tiles, and all surfaces update.

### PM2.5 Standard
Select in the sidebar (**WHO / EU / EPA / ECOWAS / Custom**). All alert counts, AQI bands, and charts update dynamically.

---

## Deployment

### Render.com (recommended)

`deployment/render.yaml` defines two services:

```bash
git push origin main   # Render auto-deploys both dashboard + API
```

Set these environment variables in the Render dashboard:

| Variable | Required | Description |
|----------|----------|-------------|
| `GROQ_API_KEY` | Optional | Enables AI assistant and policy brief generation |
| `AIRSENSE_API_URL` | Optional | URL of the deployed API service |

### Local with Docker

```bash
# Dashboard
docker build -t airsense-dashboard -f docker/Dockerfile.dashboard .
docker run -p 8501:8501 -e GROQ_API_KEY=gsk_... airsense-dashboard

# API
docker build -t airsense-api -f docker/Dockerfile.api .
docker run -p 8000:8000 airsense-api
```

---

## Innovations

1. **Breath of Fresh Air Index (BFAI)** — Composite 0–100 score combining PM2.5 (50%), wind speed (25%), and humidity (25%) for intuitive air quality communication beyond raw µg/m³.

2. **Harmattan Early-Warning System** — Detects Saharan dust intrusions from NE wind bearing + dry-season indicator + PM2.5 spike. Triggers advance advisories in northern regions with animated dust-transport map.

3. **Conformal Prediction Intervals** — Distribution-free 90% confidence bounds per city without Gaussian assumptions.

4. **Platt-Calibrated Alert Classifier** — Logistic regression maps XGBoost PM2.5 output to exceedance probability (F1 = 0.847). Per-city recalibration corrects regional distribution shift.

5. **Dynamic Source Attribution** — Five-source decomposition (Dust, Biomass Burning, Traffic, Industry, Secondary Aerosol) computed from live meteorological conditions + SHAP weights. Updates per month and city.

6. **CMIP6 Climate Projections** — SSP2-4.5 and SSP5-8.5 scenarios projected to 2050 with bias correction from historical CAMS baseline.

7. **Conversational AI Assistant** — Groq Llama 3.1 8B (free tier, 14k req/day) with live PM2.5 context, 7-day forecasts, SHAP data, and full chart guide injected into the system prompt. Streaming responses. Bilingual EN/FR. Rule-based fallback requires no API key.

8. **PDF Report Export** — One-click downloadable PDF per city: current status, 7-day forecast table, source attribution, health impact, and recommendations. Fully bilingual.

9. **API-First Architecture** — Dashboard routes all predictions through the FastAPI backend when available, with silent fallback to local XGBoost models. No user-visible difference.

10. **Configurable Reference Standards** — WHO 2021, EU 2024, US EPA, ECOWAS, or custom threshold. All visualisations and alert counts update dynamically.

11. **Progressive Web App (PWA)** — Full PWA with Web App Manifest and offline-capable service worker. Installable on Android, iOS, and desktop without an app store. App shell is cached on first load; network-first navigation with cache fallback ensures the dashboard remains usable on intermittent connectivity common in Cameroon.

---

## Team

**Dze-Kum Shalom Chow** — Lead developer, ML modelling, dashboard design
**Ayanda Blessing Khumalo** — Statistical Lead, Statistical validation and hypothesis testing
**MALLA NDASSI Marie Ange** — Domain Expert, Atmospheric physics insights
**Mih Ndum Lizette** — Data pipeline & ETL engineering
IndabaX Cameroon 2026

---

*Data sources: CAMS Reanalysis (Copernicus/ECMWF), Open-Meteo ERA5, WHO Global Air Quality Guidelines 2021*
