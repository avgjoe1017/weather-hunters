"""
Find climate/weather markets on Kalshi.
The user was right - they exist! I just searched with wrong keywords.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient
from kalshi_python.api import markets_api

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
print("CLIMATE/WEATHER MARKETS - PROPER SEARCH")
print("=" * 70)
print()

# Get markets
markets_instance = markets_api.MarketsApi(client)
response = markets_instance.get_markets(limit=200, status="open")
markets = response.markets if hasattr(response, 'markets') else []

print(f"Scanning {len(markets)} markets...")
print()

# Search with broader criteria
climate_keywords = [
    'HIGH', 'LOW', 'TEMP', 'CLIMATE', 'DEGREE', 
    'NYC', 'CHICAGO', 'CHI', 'MIA', 'MIAMI', 
    'AUSTIN', 'ATX', 'SF', 'LA', 'HOUSTON'
]

climate_markets = []
for market in markets:
    ticker = market.ticker.upper()
    title = getattr(market, 'title', '').upper()
    
    # Much broader search
    if any(kw in ticker for kw in climate_keywords):
        climate_markets.append(market)
    elif 'TEMPERATURE' in title or 'CLIMATE' in title or 'WEATHER' in title:
        climate_markets.append(market)

print("=" * 70)
print(f"FOUND {len(climate_markets)} CLIMATE/WEATHER MARKETS")
print("=" * 70)
print()

if climate_markets:
    for m in climate_markets:
        print(f"\n{m.ticker}")
        print(f"  {getattr(m, 'title', 'N/A')}")
        yes_bid = getattr(m, 'yes_bid', None)
        yes_ask = getattr(m, 'yes_ask', None)
        if yes_bid and yes_ask:
            print(f"  Price: {yes_bid}-{yes_ask} cents")
        print(f"  Volume: {getattr(m, 'volume', 0)}")
        print(f"  Closes: {getattr(m, 'close_time', 'N/A')}")
else:
    print("Still no markets found. Need to check the API category filter.")
    print()
    print("The website might have markets that aren't returned by get_markets()")
    print("Let me try with category filter...")
    print()
    
    # Try with category
    try:
        # Try different approaches
        response2 = markets_instance.get_markets(
            limit=200,
            status="open",
            series_ticker="TEMP"  # Try series ticker
        )
        print(f"With series filter: {len(response2.markets)} markets")
    except Exception as e:
        print(f"Series filter failed: {e}")

print()
print("=" * 70)

