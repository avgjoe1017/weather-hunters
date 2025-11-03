"""
Collect 4 years of historical weather data for backtesting.

Downloads data from Open-Meteo (free, no API key) for all Kalshi cities.
This will take 5-10 minutes but only needs to be run once.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
import pandas as pd
import time
from datetime import datetime

print("=" * 70)
print("HISTORICAL WEATHER DATA COLLECTION")
print("=" * 70)
print()

# Kalshi cities and their official coordinates
CITIES = {
    'NYC': {
        'name': 'New York (Central Park)',
        'lat': 40.7829,
        'lon': -73.9654
    },
    'CHI': {
        'name': 'Chicago (Midway)',
        'lat': 41.7754,
        'lon': -87.7512
    },
    'MIA': {
        'name': 'Miami (Intl Airport)',
        'lat': 25.7959,
        'lon': -80.2871
    },
    'HOU': {
        'name': 'Houston (Hobby)',
        'lat': 29.6455,
        'lon': -95.2789
    },
    'AUS': {
        'name': 'Austin (Bergstrom)',
        'lat': 30.1944,
        'lon': -97.6700
    }
}

# Date range: 4 years for backtesting
START_DATE = "2020-01-01"
END_DATE = "2024-10-31"

print(f"Collecting data from {START_DATE} to {END_DATE}")
print(f"Cities: {len(CITIES)}")
print()

# Create data directory
data_dir = project_root / "data" / "weather"
data_dir.mkdir(parents=True, exist_ok=True)

all_data = []

for city_code, city_info in CITIES.items():
    print(f"[{list(CITIES.keys()).index(city_code)+1}/{len(CITIES)}] Downloading {city_info['name']}...")
    
    try:
        # Open-Meteo Archive API
        url = "https://archive-api.open-meteo.com/v1/archive"
        params = {
            "latitude": city_info['lat'],
            "longitude": city_info['lon'],
            "start_date": START_DATE,
            "end_date": END_DATE,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "temperature_2m_mean",
                "precipitation_sum",
                "windspeed_10m_max",
                "relative_humidity_2m_mean"
            ],
            "temperature_unit": "fahrenheit",
            "windspeed_unit": "mph",
            "precipitation_unit": "inch",
            "timezone": "America/New_York"
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        # Parse response
        daily = data['daily']
        dates = daily['time']
        
        for i in range(len(dates)):
            all_data.append({
                'date': dates[i],
                'city': city_code,
                'city_name': city_info['name'],
                'actual_high_temp': daily['temperature_2m_max'][i],
                'actual_low_temp': daily['temperature_2m_min'][i],
                'actual_mean_temp': daily['temperature_2m_mean'][i],
                'precipitation': daily['precipitation_sum'][i],
                'wind_speed': daily['windspeed_10m_max'][i],
                'humidity': daily['relative_humidity_2m_mean'][i]
            })
        
        print(f"    [OK] {len(dates)} days collected")
        
        # Be nice to the API
        time.sleep(0.5)
        
    except Exception as e:
        print(f"    [X] Error: {e}")
        continue

print()
print(f"[OK] Total: {len(all_data)} observations collected")
print()

# Save to CSV
if all_data:
    df = pd.DataFrame(all_data)
    
    # Save individual city files
    print("Saving data files...")
    for city_code in CITIES.keys():
        city_df = df[df['city'] == city_code]
        filename = data_dir / f"{city_code}_2020-2024.csv"
        city_df.to_csv(filename, index=False)
        print(f"  Saved: {filename} ({len(city_df)} days)")
    
    # Save combined file
    combined_file = data_dir / "all_cities_2020-2024.csv"
    df.to_csv(combined_file, index=False)
    print(f"  Saved: {combined_file} ({len(df)} total)")
    print()
    
    # Statistics
    print("=" * 70)
    print("DATA SUMMARY")
    print("=" * 70)
    print()
    
    print(f"Date Range: {df['date'].min()} to {df['date'].max()}")
    print(f"Total Days: {len(df['date'].unique())}")
    print(f"Total Observations: {len(df)}")
    print()
    
    print("Average Temperatures by City:")
    for city_code in CITIES.keys():
        city_df = df[df['city'] == city_code]
        avg_high = city_df['actual_high_temp'].mean()
        std_high = city_df['actual_high_temp'].std()
        print(f"  {city_code}: {avg_high:.1f}F ± {std_high:.1f}F")
    
    print()
    print("=" * 70)
    print()
    print("[OK] DATA COLLECTION COMPLETE!")
    print()
    print("Next steps:")
    print("  1. Run: python scripts/train_weather_models.py")
    print("     (Train ML models on this real data)")
    print()
    print("  2. Run: python scripts/backtest_weather_models.py")
    print("     (Backtest with real historical data)")
    print()
    print("  3. Review results to decide if strategy is profitable")
    print()
    print("Expected time: 10-15 minutes total")
    print()
    
else:
    print("[X] No data collected. Check errors above.")
    print()

