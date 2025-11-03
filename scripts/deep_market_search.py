"""
Deep search for climate/weather markets.
The user is RIGHT - they exist on the website. Let's find them in the API.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient
from kalshi_python.api import markets_api, series_api

load_dotenv()

# Connect
api_key_id = os.getenv('KALSHI_API_KEY_ID')
with open(project_root / "kalshi_private_key.pem", 'r') as f:
    private_key = f.read()

config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
config.api_key_id = api_key_id
config.private_key_pem = private_key
client = KalshiClient(config)

print("=" * 70)
print("DEEP SEARCH FOR WEATHER/CLIMATE MARKETS")
print("=" * 70)
print()

# Try 1: Get all series first
print("[1/4] Checking available series...")
try:
    s_api = series_api.SeriesApi(client)
    series_resp = s_api.get_series()
    all_series = series_resp.series if hasattr(series_resp, 'series') else []
    
    print(f"Found {len(all_series)} series total")
    
    # Look for weather-related series
    weather_series = []
    for s in all_series:
        ticker = s.ticker.upper()
        title = getattr(s, 'title', '').upper()
        
        if any(kw in ticker or kw in title for kw in [
            'WEATHER', 'CLIMATE', 'TEMP', 'HIGH', 'LOW', 'DEGREE',
            'RAIN', 'SNOW', 'FROST', 'HEAT'
        ]):
            weather_series.append(s)
            print(f"  Found: {s.ticker} - {getattr(s, 'title', 'N/A')}")
    
    print(f"\nWeather-related series: {len(weather_series)}")
    
except Exception as e:
    print(f"Error getting series: {e}")
    weather_series = []

print()

# Try 2: Get markets with higher limit
print("[2/4] Fetching more markets (limit=1000)...")
try:
    m_api = markets_api.MarketsApi(client)
    resp = m_api.get_markets(limit=1000)
    all_markets = resp.markets if hasattr(resp, 'markets') else []
    
    print(f"Retrieved {len(all_markets)} markets")
    
except Exception as e:
    print(f"Error: {e}")
    all_markets = []

print()

# Try 3: Search through ALL markets for weather keywords
print("[3/4] Searching all markets for weather keywords...")

weather_keywords = [
    'NY', 'NYC', 'NEWYORK', 
    'CHI', 'CHICAGO',
    'MIA', 'MIAMI',
    'ATX', 'AUSTIN',
    'HIGH', 'LOW', 'TEMP', 'DEGREE',
    'RAIN', 'SNOW', 'WEATHER', 'CLIMATE'
]

found_markets = []
for market in all_markets:
    ticker = market.ticker.upper()
    title = getattr(market, 'title', '').upper()
    
    # Check if ANY weather keyword is in ticker or title
    for kw in weather_keywords:
        if kw in ticker or kw in title:
            found_markets.append(market)
            break

print(f"Found {len(found_markets)} potentially weather-related markets")
print()

# Try 4: If we found weather series, get markets for those series
print("[4/4] Getting markets from weather series...")
series_markets = []

for series in weather_series[:5]:  # Check first 5 series
    try:
        resp = m_api.get_markets(series_ticker=series.ticker, limit=100)
        markets = resp.markets if hasattr(resp, 'markets') else []
        series_markets.extend(markets)
        print(f"  {series.ticker}: {len(markets)} markets")
    except Exception as e:
        print(f"  {series.ticker}: Error - {e}")

print()
print("=" * 70)
print("RESULTS")
print("=" * 70)
print()

# Show all found markets
all_found = list(set(found_markets + series_markets))

if all_found:
    print(f"[OK] FOUND {len(all_found)} WEATHER/CLIMATE MARKETS!")
    print()
    
    for m in all_found[:20]:  # Show first 20
        print(f"\n{m.ticker}")
        print(f"  {getattr(m, 'title', 'N/A')[:65]}")
        
        yes_bid = getattr(m, 'yes_bid', None)
        yes_ask = getattr(m, 'yes_ask', None)
        if yes_bid and yes_ask:
            print(f"  Price: {yes_bid}-{yes_ask} cents")
        
        status = getattr(m, 'status', 'unknown')
        print(f"  Status: {status}")
        
        volume = getattr(m, 'volume', 0)
        print(f"  Volume: {volume}")
    
    if len(all_found) > 20:
        print(f"\n... and {len(all_found) - 20} more")
    
    print()
    print("=" * 70)
    print("WEATHER STRATEGY IS VIABLE!")
    print("Run: python scripts/run_weather_strategy.py")
    
else:
    print("[!] Still no weather markets found")
    print()
    print("Possible reasons:")
    print("1. Markets are seasonal (not active in November)")
    print("2. Markets closed and new ones not launched yet")
    print("3. Need different API parameters")
    print()
    print("Check the Kalshi website directly:")
    print("https://kalshi.com/?category=climate")

