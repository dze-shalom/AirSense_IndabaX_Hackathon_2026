from dashboard.utils.models import load_models, predict_7day
import json

# Load model
model, enc, fi = load_models()
print('Model loaded successfully')

# Mock forecast data
mock_fd = {
    'daily': {
        'time': ['2026-04-06', '2026-04-07', '2026-04-08'],
        'temperature_2m_max': [32, 31, 33],
        'temperature_2m_min': [22, 21, 23],
        'temperature_2m_mean': [27, 26, 28],
        'precipitation_sum': [0, 0, 0],
        'precipitation_hours': [0, 0, 0],
        'wind_speed_10m_max': [5, 6, 4],
        'wind_direction_10m_dominant': [180, 190, 170],
        'shortwave_radiation_sum': [20, 18, 22],
        'et0_fao_evapotranspiration': [4, 5, 3],
        'weather_code': [1, 2, 3],
        'relative_humidity_2m_mean': [65, 70, 60],
        'dew_point_2m_mean': [20, 19, 21],
        'surface_pressure_mean': [950, 952, 948],
        'cloud_cover_mean': [30, 40, 20],
        'wind_speed_100m_max': [15, 16, 14],
        'soil_moisture_0_to_7cm_mean': [0.15, 0.16, 0.14],
        'soil_temperature_0_to_7cm_mean': [26, 25, 27],
        'wet_bulb_temperature_2m_mean': [23, 22, 24],
        'vapour_pressure_deficit_max': [1.5, 1.6, 1.4],
        'daylight_duration': [43200, 43100, 43300],
        'sunshine_duration': [30000, 28000, 32000]
    }
}

# Test prediction
city = 'Yaounde'
region = 'Centre'
lat, lon = 3.848, 11.502

preds = predict_7day(mock_fd, city, region, lat, lon, model, enc, fi)
if preds:
    print('Prediction successful!')
    for p in preds[:3]:
        print(f'Date: {p["date"]}, PM2.5: {p["pm25"]:.2f}')
else:
    print('Prediction failed')