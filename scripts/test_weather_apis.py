"""
Test weather API connections.

Tests both Open-Meteo and Weather.gov to ensure they work.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import requests
from datetime import datetime, timedelta

print("=" * 70)
print("WEATHER API CONNECTION TEST")
print("=" * 70)
print()

# Test 1: Open-Meteo (Historical Data)
print("[1/3] Testing Open-Meteo (historical data)...")
print()

try:
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "start_date": "2024-10-01",
        "end_date": "2024-10-07",
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York"
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if 'daily' in data and 'temperature_2m_max' in data['daily']:
        temps = data['daily']['temperature_2m_max']
        print(f"[OK] Open-Meteo working!")
        print(f"     Retrieved {len(temps)} days of data")
        print(f"     Sample: Oct 1, 2024 = {temps[0]:.1f}F")
        print()
    else:
        print("[X] Open-Meteo returned unexpected data")
        print(f"    Response: {data}")
        print()
        
except Exception as e:
    print(f"[X] Open-Meteo failed: {e}")
    print("    This is the primary data source!")
    print()

# Test 2: Open-Meteo (Forecast)
print("[2/3] Testing Open-Meteo (forecasts)...")
print()

try:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": 40.7128,
        "longitude": -74.0060,
        "daily": "temperature_2m_max,temperature_2m_min",
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York",
        "forecast_days": 3
    }
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    
    if 'daily' in data and 'temperature_2m_max' in data['daily']:
        temps = data['daily']['temperature_2m_max']
        dates = data['daily']['time']
        print(f"[OK] Open-Meteo forecast working!")
        print(f"     Retrieved {len(temps)} days forecast")
        print(f"     {dates[1]}: {temps[1]:.1f}F (tomorrow)")
        print()
    else:
        print("[X] Open-Meteo forecast returned unexpected data")
        print()
        
except Exception as e:
    print(f"[X] Open-Meteo forecast failed: {e}")
    print()

# Test 3: Weather.gov (Official Kalshi Source)
print("[3/3] Testing Weather.gov (official data)...")
print()

try:
    # Central Park coordinates (what Kalshi uses)
    lat, lon = 40.7829, -73.9654
    
    # Step 1: Get grid coordinates
    points_url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(points_url, timeout=10, headers={'User-Agent': 'WeatherTrader/1.0'})
    response.raise_for_status()
    grid_data = response.json()
    
    # Step 2: Get forecast
    forecast_url = grid_data['properties']['forecast']
    forecast_response = requests.get(forecast_url, timeout=10, headers={'User-Agent': 'WeatherTrader/1.0'})
    forecast_response.raise_for_status()
    forecast = forecast_response.json()
    
    if 'properties' in forecast and 'periods' in forecast['properties']:
        periods = forecast['properties']['periods']
        tomorrow = periods[2] if len(periods) > 2 else periods[0]  # Usually period 2 is tomorrow day
        
        print(f"[OK] Weather.gov working!")
        print(f"     Retrieved {len(periods)} forecast periods")
        print(f"     {tomorrow['name']}: {tomorrow['temperature']}F")
        print()
    else:
        print("[X] Weather.gov returned unexpected data")
        print()
        
except Exception as e:
    print(f"[X] Weather.gov failed: {e}")
    print("    This is what Kalshi uses for settlement!")
    print()

# Summary
print("=" * 70)
print("SUMMARY")
print("=" * 70)
print()
print("API Status:")
print("  Open-Meteo Historical:  [TEST ABOVE]")
print("  Open-Meteo Forecast:    [TEST ABOVE]")
print("  Weather.gov:            [TEST ABOVE]")
print()
print("If all passed:")
print("  -> Run: python scripts/collect_historical_weather.py")
print("  -> This will download 4 years of data (~5-10 minutes)")
print()
print("If any failed:")
print("  -> Check internet connection")
print("  -> APIs might be temporarily down")
print("  -> Try again in a few minutes")
print()
print("=" * 70)

