"""
Collect Open-Meteo Historical Forecasts

This uses Open-Meteo's Archive API to get historical weather forecasts
(what models predicted BEFORE the day happened).

This is different from historical weather data (what actually happened).

API: https://open-meteo.com/en/docs/historical-forecast-api
"""

import sys
from pathlib import Path
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 70)
print("OPEN-METEO HISTORICAL FORECAST COLLECTOR")
print("=" * 70)
print()
print("Collecting historical weather MODEL FORECASTS (REAL DATA)")
print()

# Load official NOAA data
noaa_file = PROJECT_ROOT / "data" / "weather" / "nws_settlement_ground_truth_OFFICIAL.csv"

if not noaa_file.exists():
    print("[X] NOAA ground truth not found. Run collect_noaa_ground_truth.py first.")
    sys.exit(1)

df = pd.read_csv(noaa_file)
df['date'] = pd.to_datetime(df['date'])

print(f"[1/4] Loaded {len(df)} NOAA settlement records")
print(f"      Date range: {df['date'].min()} to {df['date'].max()}")
print()

# City coordinates
CITIES = {
    'NYC': {'lat': 40.7789, 'lon': -73.9692},
    'CHI': {'lat': 41.9742, 'lon': -87.9073},
    'MIA': {'lat': 25.7959, 'lon': -80.2870},
    'HOU': {'lat': 29.9902, 'lon': -95.3368},
}

print("[2/4] Fetching historical forecasts from Open-Meteo...")
print()
print("NOTE: Open-Meteo's Archive API provides historical model forecasts")
print("      This is what ECMWF/GFS/GDPS predicted BEFORE each day")
print()

# Check if Open-Meteo Historical Forecast API is available
# Note: This is a PAID feature on Open-Meteo
# The free tier does NOT include historical forecasts

print("[!] IMPORTANT: Open-Meteo Historical Forecast API")
print("    - This is a PAID feature (not available on free tier)")
print("    - Cost: ~€10-50/month depending on usage")
print("    - Alternative: Use forward test to collect going forward")
print()

response = input("Do you have an Open-Meteo API key? (y/n): ")

if response.lower() != 'y':
    print()
    print("[!] Historical forecast collection SKIPPED")
    print()
    print("Options:")
    print("  1. Sign up for Open-Meteo API: https://open-meteo.com/en/pricing")
    print("  2. Use forward test to collect real data going forward")
    print("  3. Continue with Kalshi forecast history only")
    print()
    print("For now, we'll proceed with Kalshi data and forward test.")
    sys.exit(0)

# If user has API key, proceed
api_key = input("Enter your Open-Meteo API key: ")

forecast_data = []

# Group by city for efficient API calls
for city, coords in CITIES.items():
    city_dates = df[df['city'] == city]['date'].unique()
    
    print(f"\n--- {city} ({len(city_dates)} dates) ---")
    
    for date in city_dates:
        # We want the forecast from the day BEFORE
        target_date = pd.to_datetime(date)
        forecast_date = target_date - timedelta(days=1)
        
        print(f"  {target_date.strftime('%Y-%m-%d')} (forecast from {forecast_date.strftime('%Y-%m-%d')})", end='')
        
        try:
            # Open-Meteo Historical Forecast API
            url = "https://customer-api.open-meteo.com/v1/forecast-archive"
            
            params = {
                'apikey': api_key,
                'latitude': coords['lat'],
                'longitude': coords['lon'],
                'start_date': forecast_date.strftime('%Y-%m-%d'),
                'end_date': forecast_date.strftime('%Y-%m-%d'),
                'daily': 'temperature_2m_max',
                'temperature_unit': 'fahrenheit',
                'timezone': 'America/New_York',
                'forecast_days': 1  # Next day forecast
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Extract forecast
            if 'daily' in data and 'temperature_2m_max' in data['daily']:
                temps = data['daily']['temperature_2m_max']
                if temps and len(temps) > 0:
                    forecast_temp = temps[0]
                    
                    forecast_data.append({
                        'date': target_date.strftime('%Y-%m-%d'),
                        'city': city,
                        'forecast_date': forecast_date.strftime('%Y-%m-%d'),
                        'open_meteo_forecast_temp': forecast_temp,
                        'source': 'open_meteo_archive_api'
                    })
                    
                    print(f" -> {forecast_temp}F")
                else:
                    print(" -> No data")
            else:
                print(" -> No data")
            
            time.sleep(0.1)  # Rate limiting
            
        except Exception as e:
            print(f" -> ERROR: {e}")
            continue

print()
print(f"[3/4] Collection complete: {len(forecast_data)} forecasts")
print()

if len(forecast_data) == 0:
    print("[!] No forecasts collected")
    print("    Check API key and pricing tier")
    sys.exit(0)

# Save
output_file = PROJECT_ROOT / "data" / "weather" / "open_meteo_historical_forecasts.csv"
output_file.parent.mkdir(parents=True, exist_ok=True)

df_forecasts = pd.DataFrame(forecast_data)
df_forecasts.to_csv(output_file, index=False)

print(f"[4/4] Saved to {output_file}")
print()

print("=" * 70)
print("HISTORICAL FORECAST SUMMARY")
print("=" * 70)
print()
print(f"Forecasts collected: {len(forecast_data)}")
print()
print("Sample:")
print(df_forecasts.head(10).to_string(index=False))
print()
print("Next step:")
print("  Run: python scripts/merge_all_forecast_data.py")
print("=" * 70)

