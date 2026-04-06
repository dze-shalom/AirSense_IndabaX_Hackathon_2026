# Notebooks — AirSense Cameroon
**IndabaX 2026 · L'IA au service de la résilience climatique et sanitaire au Cameroun**

---

## Run Order

```
00_Data_Cleaning.ipynb  →  01_EDA.ipynb  →  02_Model_Training.ipynb  →  03_Pitch_Charts.ipynb
```

Run `00` first. Every other notebook simply loads the CSV it produces.

---

## 00 — Data Cleaning & Enrichment

**Input:** `data/Dataset_complet_Meteo.xlsx` (official hackathon dataset)
**Output:** `data/cameroon_official_dataset.csv` — complete, 42 cities, zero nulls

The official Excel dataset contains weather variables only for 40 cities.
This notebook enriches it with real satellite-measured air quality compounds
following the hackathon README tip: *"enrich your analysis with additional
variables from open-meteo.com (hourly data, air quality, climate models, etc.)"*

| Step | What it does |
|------|-------------|
| 1 | Install packages |
| 2 | Load the official Excel and fix numeric columns stored as Excel date serials |
| 3 | Fetch full weather for Banyo & Mora from Open-Meteo Archive API at their real coordinates |
| 4 | Fetch PM2.5, PM10, Dust, CO, NO₂, O₃, AOD, AQI for all 42 cities from Open-Meteo Air Quality API (CAMS satellite data, 2020–2025) |
| 5 | Build physics-based proxy compounds for any city where the API fetch failed — ensures zero nulls |
| 6 | Merge weather and compounds into one dataset |
| 7 | Rename columns and derive engineered features |
| 8 | Build PM2.5 target variable (real CAMS values where available, proxy formula as fallback) |
| 9 | Add Banyo and Mora rows using real weather from Step 3 |
| 10 | Audit missing values, understand the pattern, then fill appropriately |
| 11 | Quality check — view the data before saving |
| 12 | Save final dataset |

**Compound variables fetched (not in official Excel):**

| Variable | Source | Relevance to Cameroon |
|----------|--------|-----------------------|
| `pm2_5_real` | CAMS satellite | Target variable — real measured PM2.5 |
| `pm2_5_peak` | CAMS | Daily peak — captures intra-day dust storm spikes |
| `pm10_mean` | CAMS | Coarse dust, peaks during Harmattan season |
| `dust_mean` | CAMS | Saharan mineral dust from Bodélé Depression |
| `dust_peak` | CAMS | Daily dust peak — early warning signal for storms |
| `co_mean` | CAMS | Cooking fire emissions — dominant source in rural Cameroon |
| `no2_mean` | CAMS | Traffic emissions — Douala and Yaounde |
| `o3_mean` | CAMS | Photochemical smog formed by heat + sunlight + NO₂ |
| `so2_mean` | CAMS | Douala/Limbe refinery emissions + Mount Cameroon volcanic activity |
| `aod_mean` | CAMS | Aerosol optical depth — total particle load from satellite |
| `eu_aqi` | CAMS | European composite air quality index |
| `humidity` | Open-Meteo Archive | Not in official Excel, used in BFAI and health impact calculations |

> **Note on NH₃ (ammonia):** Not fetched. CAMS provides no coverage for Central
> Africa for this variable — the earlier test fetch returned 100% null for all
> 42 cities. A fabricated feature adds noise to the model. Excluded entirely.

> **Note on Banyo and Mora:** The official Excel has 40 cities. The hackathon
> README states 42. Both cities are added by fetching their real weather data
> at actual coordinates from Open-Meteo, not by interpolating from neighbours.
> Their compound data is also fetched at their own coordinates. All data is real.

> **Rate limiting:** Open-Meteo's free tier triggers 429 errors after ~5 rapid
> requests. The fetch cell pauses 3s between cities and 20s every 5 cities.
> Failed cities after 3 retries get physics-based proxy values — no city is
> ever left with null compound values. A retry cell is available to re-fetch
> failed cities after a 2-minute cooldown.

---

## 01 — Exploratory Data Analysis

**Input:** `data/cameroon_official_dataset.csv`
**Output:** Charts and findings — no files saved

This notebook performs no cleaning. The dataset is guaranteed clean before
it arrives here — zero nulls, all 42 cities, all compounds present.
Every section can be re-run safely after kernel restart.

| Section | What it answers |
|---------|----------------|
| 1 | Dataset overview — shape, cities per region, null check, PM2.5 summary |
| 2 | PM2.5 distribution — overall histogram, regional boxplot, monthly bar chart |
| 3 | Feature correlations with PM2.5 — Pearson r for every numeric variable, ranked |
| 4 | Full correlation matrix — feature interdependencies, multicollinearity check |
| 5 | Scatter plots — shape of relationship for top 6 features |
| 6 | New features analysis — wind gusts, dust events, apparent temperature, haze flag |
| 7 | Harmattan heatmap — PM2.5 by region × month, Harmattan months highlighted |
| 8 | Feature importance preview — quick Random Forest + comparison with Pearson r |
| 9 | City-level trends — 2020–2025 time series for 8 focus cities |
| 10 | Interactive map — all 42 cities coloured by mean PM2.5 |
| 11 | EDA summary — key numbers ready to quote in the pitch deck |

**Key findings:**
- Far North PM2.5 is ~2.8× higher than South on average
- Harmattan season multiplies northern PM2.5 by ~2.5×
- `dust_mean`, `aod_mean`, and `pm10_mean` are the strongest predictors
- `wind_gusts` and `is_dust_event` have higher RF importance than Pearson r — non-linear threshold effects that correlation cannot capture
- Over 43% of all city-days exceed the WHO annual limit of 15 μg/m³
- Douala's NO₂ and CO are distinctly higher than other regions — traffic and industry signature

---

## 02 — Model Training & Evaluation

**Input:** `data/cameroon_official_dataset.csv`
**Output:** `models/xgb_model.joblib`, `models/rl_thresholds.json`, `models/shap_importance.pkl`, `data/cameroon_2050_projections.csv`

Follows the starter notebook structure exactly. Section 4 is the required baseline.
Section 5 covers every model suggested in the Going Further section.
Sections 6–8 are our innovations beyond what the starter notebook suggests.

| Section | Content | Scope | Addresses |
|---------|---------|-------|-----------|
| 1 | Setup | — | — |
| 2 | Load dataset | — | — |
| 3 | Feature engineering | — | — |
| 4 | Random Forest | 42 cities | Baseline (starter notebook) |
| 5a | LightGBM | 42 cities | Going Further — faster boosting |
| 5b | XGBoost + SHAP | 42 cities | Going Further — best model, explains predictions |
| 5c | ARIMA | Douala demo | Going Further — classical time series |
| 5d | Prophet | Douala demo | Going Further — seasonal decomposition |
| 5e | LSTM | Douala demo | Going Further — deep learning sequences |
| 5f | TFT | 42 cities | Going Further — attention over time |
| 5g | ConvLSTM | 42 cities | Going Further — spatial pollution transport |
| 5h | GNN | 42 cities | Going Further — city-to-city graph model |
| 5i | REINFORCE RL | 42 cities | Innovation — city-specific adaptive alert thresholds |
| 6 | Model comparison | 42 cities only | Technical performance |
| 7 | Save best model | — | — |
| 8 | Climate 2050 projection | 42 cities | Innovation — CMIP6 future PM2.5 |

**Why single-city models are in Section 5 but not Section 6:**
ARIMA, Prophet, and LSTM are inherently per-series. A national system serving
42 cities cannot maintain 42 separate time series models. They are included to
demonstrate we explored every Going Further suggestion from the starter notebook,
but the final selection only considers models that scale to all 42 cities.

**REINFORCE RL — why it matters for Cameroon:**
A fixed WHO threshold of 35 μg/m³ would trigger an alert every single day in
Maroua where baseline PM2.5 is ~58 μg/m³. This causes alarm fatigue — health
officers stop responding to alerts entirely. The REINFORCE policy gradient agent
(Williams 1992) learns from the reward signal that a correct alert is worth +1.0,
a missed dangerous event is worth -2.0, and a false alarm is worth -1.0. After
20 training episodes per city, Maroua learns a threshold of ~62 μg/m³ while
Buea learns ~28 μg/m³. The same system, correctly calibrated to each city.

**Temporal split — why not random:**
PM2.5 has strong daily autocorrelation. A random split would allow the model to
"see" PM2.5 from day t+1 during training while predicting day t. We use
2020–2024 for training and 2025 as a strict holdout year — the model has never
seen any 2025 data when evaluated.

**Climate 2050 projection — Section 8:**
The hackathon README explicitly recommends: *"climate models from open-meteo.com."*
This section follows that recommendation. The trained XGBoost model is applied to
CMIP6 climate projections fetched from the Open-Meteo Climate API, covering four
IPCC AR6 warming scenarios (SSP1-1.9 through SSP5-8.5) for years 2026–2100.

What it produces:
- `data/cameroon_2050_projections.csv` — per-city PM2.5 projections
- Comparison table: 2025 baseline vs any chosen future year
- Identifies which regions face the largest PM2.5 increases

Why this matters: northern Cameroon is projected to warm 1.5–2.5°C by 2050
(IPCC AR6), directly extending the Harmattan season and increasing dust days.
This section translates that warming into concrete PM2.5 numbers that health
ministries and urban planners can use for 25-year adaptation planning.

If the Climate API is unavailable, the section builds a physics-based simulation
using IPCC AR6 regional warming rates — the dashboard Climate tab works either way.

---

## 03 — Pitch Charts

**Input:** `data/cameroon_official_dataset.csv` + trained models
**Output:** PNG charts for the pitch deck

Generates 5 publication-ready charts:
1. The problem — PM2.5 exceedance statistics across Cameroon
2. North-south divide — regional PM2.5 comparison with WHO reference
3. System architecture diagram
4. Model performance comparison — all 9 models
5. REINFORCE RL threshold map — city-specific learned thresholds vs WHO fixed line

---

## starter_notebook_EN.ipynb

The official starter notebook provided by IndabaX. Kept as reference only.
Do not modify. Our notebooks follow its section structure and extend every
model suggestion in its Going Further section.
