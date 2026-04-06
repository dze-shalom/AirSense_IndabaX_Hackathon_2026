# AirSense Cameroon — IndabaX 2026

> AI for Climate and Health Resilience in Cameroon

Predicts PM2.5 across 85+ cities in all 10 regions using 6 years of CAMS + Open-Meteo data.

## Structure

```
dashboard/
├── app.py              # Entry point — routing only (56 lines)
├── config.py           # All constants: colours, cities, translations, nav
├── components/
│   ├── sidebar.py      # Navigation, CSS, layout shell
│   ├── ui.py           # card(), sec(), info_box(), SVG gauges
│   └── charts.py       # PLO() Plotly layout defaults
├── pages/
│   ├── overview.py     # National map, rankings, heatmap
│   ├── explorer.py     # Forecast + Analytics + Compare (tabbed)
│   ├── alerts.py       # Alert centre + Health calculator (tabbed)
│   ├── science.py      # SHAP analysis + Climate 2050 (tabbed)
│   ├── ai_assistant.py # Claude-powered health Q&A
│   └── about.py        # Model card, innovations, team
└── utils/
    ├── helpers.py      # aqi(), bfai(), classify_source(), city_profile()
    ├── models.py       # load_models(), predict_7day(), get_alert_prob()
    └── api.py          # fetch_forecast(), geocode_city(), call_claude()
```

## Run

```bash
pip install -r requirements.txt
streamlit run dashboard/app.py
```

## Configuration

Create `.streamlit/secrets.toml`:
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
```

## Models

Place trained model artefacts in `models/`:
- `xgb_pm25.json`
- `label_encoders.pkl`
- `features.json`
- `conformal_intervals.json`
- `platt_alert_calibration.json`
- `region_shap.pkl`
