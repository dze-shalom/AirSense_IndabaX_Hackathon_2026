# Notebooks — AirSense Cameroon
**IndabaX 2026 · L'IA au service de la résilience climatique et sanitaire au Cameroun**

---

## Run Order

```
00_Data_Cleaning_v3.ipynb  →  01_EDA_v3.ipynb  →  02_Modelling_v4.ipynb  →  03_Pitch_Charts.ipynb
```

Run `00` first. Every subsequent notebook reads the parquet file it produces.

---

## 00 — Data Cleaning & Preparation

**Input:** `data/Dataset_complet_Meteo.csv` (official hackathon dataset, converted from Excel)
**Output:** `data/airsense_eda_ready.parquet` — 87,240 rows × 80 columns, 0 nulls

> **Why CSV and not Excel directly?** Excel silently auto-formats integers as dates.
> Save the official `.xlsx` as CSV UTF-8 before running this notebook.

The official dataset contains weather variables only. This notebook enriches it
with real satellite-measured air quality compounds following the hackathon README tip:
*"enrich your analysis with additional variables from open-meteo.com."*

| Step | What it does |
|------|-------------|
| 1 | Install packages and confirm library versions |
| 2 | Load the official CSV — 87,240 rows × 26 columns, 0 nulls |
| 3 | Inspect date range, city/region coverage, column types |
| 4 | Variable audit — justify every keep/drop decision before touching the data |
| 5 | Clean and rename — standardise to snake_case, regions to English |
| 6 | Duplicate and coverage check — confirm 0 gaps and 0 duplicates |
| 7 | Missing value assessment — quantify before deciding how to handle |
| 8 | Feature engineering — cyclic time, wind components, season flags, nh3_proxy |
| 9 | Weather code check and intermediate save |
| 10 | Scientific justification for each additional variable to fetch |
| 11 | Fetch 12 weather variables from Open-Meteo Archive API (humidity, VPD, BLH, etc.) |
| 12 | Scientific justification for each air quality compound |
| 13 | Fetch 8 CAMS compounds from Open-Meteo Air Quality API (PM2.5, PM10, dust, CO, NO₂, O₃, SO₂, AOD) |
| 13d | Fetch Boundary Layer Height (hourly → daily min + mean aggregation) |
| 14 | Build proxy targets for the 2020–2022 pre-CAMS period |
| 15 | Validate all proxy formulas against real CAMS data before applying them |
| 16 | Data provenance heatmap — visualise real vs proxy coverage per city |
| 17 | Extreme value check and final save |
| 18 | Citable provenance summary report |
| 18b | Post-load fixes (sample_weight, eu_aqi fill) and final null-free export |

**Why the 2020–2022 period uses proxy targets:**
CAMS satellite data for Central Africa is only available from 2022-08-04 onwards.
For the 37,840 earlier rows (43.4% of total), we build scientifically justified proxies
per compound — then validate each proxy against the CAMS overlap period before applying it.
The starter formula outperformed our custom formula for PM2.5 (MAE 8.36 vs 9.00 μg/m³),
so we use it. Dust and O₃ proxies produced negative R² — replaced with city-month medians
from real data. All decisions are documented and traceable.

**Final dataset:**

| Property | Value |
|----------|-------|
| Rows | 87,240 |
| Columns | 80 |
| Cities / Regions | 40 / 10 |
| Date range | 2020-01-01 → 2025-12-20 |
| Real CAMS rows | 49,400 (56.6%) |
| Proxy rows | 37,840 (43.4%) |
| Nulls | 0 |

---

## 01 — Exploratory Data Analysis

**Input:** `data/airsense_eda_ready.parquet`
**Output:** Charts and findings — no files saved (outputs embedded in notebook)

Answers two mission questions before any modelling begins:
1. **What does the target look like?** — distributions, skewness, WHO exceedance rates
2. **What drives it?** — which climate factors correlate with PM2.5 by region and season

Each section ends with an explicit modelling decision that connects directly to `02_Modelling`.

| Section | Question answered |
|---------|------------------|
| 1 | Setup and load confirmation |
| 2 | Dataset overview — compound stats, WHO exceedance rates, provenance split |
| 3 | Target distributions — skewness 2.37 → log-transform decision |
| 3b | NH3 proxy validation — r=0.572 with PM2.5, seasonal pattern confirmed |
| 4 | Pollution by region — north-south gradient, two-regime discovery |
| 5 | Seasonality — Harmattan peak, wet season trough, West anomaly |
| 5b | Harmattan deep dive — 9.8% of days, 1.7× PM2.5 multiplier, all compounds |
| 6 | Weather–PM2.5 correlations — humidity r=−0.551, full ranked table |
| 6b | Weather code analysis — clear sky = highest PM2.5 (counter-intuitive finding) |
| 7 | Compound interactions — dust cluster, two-regime confirmation |
| 8 | City-level rankings — worst and best cities identified |
| 8b | Year-over-year trend — 2024 worst year on record, +35% since 2020 |
| 9 | Proxy vs real data validation — proxy compressed (std 5.24 vs CAMS 15.71) |
| 9b | CAMS-only correlation validation — feature rankings stable, no proxy distortion |
| 10 | v2 feature validation — vpd r=+0.484, wind_gust r=+0.186, blh_min r=−0.099 |
| 10b | BLH min vs mean + VPD regime analysis |
| 11 | Full feature correlation ranking — nh3_proxy tops at r=+0.572 |
| 12 | EDA summary and modelling decisions table |

**Key findings:**
- **51.9% of all city-days exceed the WHO 24h PM2.5 limit** — a genuine public health crisis
- Two pollution regimes: northern Sahel (Saharan dust, Harmattan-driven) and highlands (West/North West, biomass burning year-round)
- **2024 was the worst year on record** — national mean rose 35% from 2020 to 2024
- Atmospheric dryness dominates: humidity, VPD, is_no_rain, evapotranspiration all in top 8 features
- `nh3_proxy` (engineered burning index) outperforms every raw meteorological variable at r=+0.572

---

## 02 — Model Training & Evaluation

**Input:** `data/airsense_eda_ready.parquet`
**Output:** 20 model artefacts saved to `models/`

Builds a complete air quality prediction and alert system. Starts from the competition
baselines and systematically explores every architectural approach — documenting what
was tried, what won, and why.

| Step | Model / Analysis | Test MAE | Test R² | Decision |
|------|-----------------|----------|---------|----------|
| 4 | Baseline: starter formula | 9.047 | 0.208 | Benchmark |
| 4 | Baseline: city-month mean | 7.521 | 0.454 | Benchmark |
| 3b | Proxy data audit | — | — | CAMS-only = PRIMARY |
| 5 | XGBoost CAMS-only | 6.274 | 0.609 | No circularity |
| 5b | Regularised + Optuna (FINAL) | **5.936** | **0.660** | ★ Deployment model |
| 5c | Conformal prediction intervals | ±17.34 μg/m³ | 97.7% coverage | Uncertainty for health tool |
| 6 | Multi-output: all 8 compounds | 5.93–39.1 | −0.17–0.70 | 8 compound models |
| 6b | Two-stage Harmattan model | 6.118 | 0.646 | ✗ Single XGB wins |
| 6c | LightGBM + XGBoost ensemble | 5.969 | 0.651 | ✗ No gain over single |
| 6d | GraphSAGE GNN (spatial) | 8.186 | 0.291 | Spatial propagation role |
| 6e | Transformer (Day+1 / Day+3) | 7.048 / 7.260 | 0.597 / 0.569 | 72h early warning |
| 7 | Calibrated alert system | AUC=0.921, F1=0.857 | — | Temperature scaling selected |
| 7b | Rule-based threshold baseline | F1=0.905 | — | Calibrated catches more dangerous days |
| 7c | XGBoost + lag features | **0.685** | **0.992** | Best for operational deployment |
| 8 | SHAP global + per-region | — | — | vpd_x_dry_season is #1 driver |
| 9–9e | Regional error + spatial gen. | L1 R²=0.52–0.68 | — | Deploy to any Cameroonian city |
| 10 | CMIP6 2050 projections | — | — | −15% Maroua by 2050 (partial API data) |
| 11 | Master comparison table | — | — | Full summary for judges |
| 12 | Production inference function | — | — | Deployment-ready API wrapper |
| 13 | Save all artefacts | — | — | 20 files to `models/` |

**Three complementary architectures deployed:**

| Model | Role | Test MAE |
|-------|------|---------|
| XGBoost Optuna (CAMS-only) | Same-day nowcasting | 5.936 μg/m³ |
| XGBoost + lag features | Operational (when real data available) | 0.685 μg/m³ |
| Transformer (Day+1/2/3) | 72-hour early warning | 7.05–7.26 μg/m³ |
| GraphSAGE GNN | Spatial interpolation to ungauged cities | 8.186 μg/m³ |

**Why we use real CAMS PM2.5 instead of the starter proxy:**
The starter notebook explicitly invites this: *"Improve this with real data from
the Open-Meteo Air Quality API."* Teams predicting the synthetic proxy formula
train models that invert that formula — not models that learn atmospheric physics.
Our model achieves R²=0.660 on real CAMS satellite measurements, a genuinely
harder and more meaningful benchmark. Beating both baselines (R²=0.208 and 0.454)
with real PM2.5 is a stronger result than achieving R²=0.99 on a synthetic target.

**Saved artefacts (`models/`):**

| File | Description |
|------|-------------|
| `xgb_pm25.json` / `.pkl` | Primary XGBoost PM2.5 model (Optuna-tuned, CAMS-only) |
| `model_pm25_lag.pkl` | XGBoost with lag features (operational) |
| `models_multi.pkl` | All 8 compound models |
| `label_encoders.pkl` | Region and city encoders |
| `features.json` | Final 68-feature list |
| `conformal_intervals.json` | q_hat = ±17.34 μg/m³, 97.7% coverage |
| `platt_alert_calibration.json` | Alert calibration coefficients (JSON) |
| `platt_calibrator.pkl` | Alert calibration Python object |
| `city_confidence_tiers.json` | High/Medium/Low reliability per city |
| `region_shap.pkl` | Per-region SHAP values for dashboard Science tab |
| `transformer_pm25.pt` | Transformer state dict (3-day ahead) |
| `gnn_graphsage.pt` | GNN state dict (spatial propagation) |
| `cmip6_projections_2050.csv` | PM2.5 projections to 2050 |
| `spatial_generalization_results.csv` | Unseen city validation results |

---

## 03 — Pitch Charts

**Input:** `data/airsense_eda_ready.parquet` + `models/` artefacts
**Output:** PNG charts saved to `outputs/` — ready for pitch deck and demo video

Generates publication-ready visualisations covering the full project narrative.

| Chart | File | What it shows |
|-------|------|--------------|
| 1 | `pitch_01_problem.png` | PM2.5 exceedance rates across all 40 cities |
| 2 | `pitch_02_two_regimes.png` | Northern dust vs highland burning — two pollution regimes |
| 3 | `pitch_03_trend.png` | Year-over-year worsening 2020–2025 |
| 4 | `pitch_04_who_calendar.png` | WHO exceedance % by city × month heatmap |
| 5 | `pitch_05_model_journey.png` | MAE improvement from baseline to final model |
| 6 | `pitch_06_shap.png` | Top 10 SHAP drivers — global feature importance |
| 7 | `pitch_07_alert_calibration.png` | Alert calibration curve — probability vs actual exceedance |
| 8 | `pitch_08_spatial_gen.png` | Spatial generalisation — model on unseen cities |
| 9 | `pitch_09_projections.png` | CMIP6 2050 projections under SSP2-4.5 and SSP5-8.5 |

---

## starter_notebook_EN.ipynb

The official starter notebook provided by IndabaX. Kept as reference only.
Do not modify. Our notebooks follow its section structure and extend every
model suggestion in its *Going Further* section.

---

## Configuration

Create `.streamlit/secrets.toml` before running the dashboard:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

Required model artefacts in `models/` for the dashboard to run:
- `xgb_pm25.json`
- `label_encoders.pkl`
- `features.json`
- `conformal_intervals.json`
- `platt_alert_calibration.json`
- `region_shap.pkl`
- `city_confidence_tiers.json`
