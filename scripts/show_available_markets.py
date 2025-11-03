"""Show what markets are actually available on Kalshi right now."""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient
from kalshi_python.api import markets_api
from collections import defaultdict

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
print("AVAILABLE KALSHI MARKETS")
print("=" * 70)
print()

# Get markets
markets_instance = markets_api.MarketsApi(client)
response = markets_instance.get_markets(limit=200, status="open")
markets = response.markets if hasattr(response, 'markets') else []

print(f"Total open markets: {len(markets)}")
print()

# Categorize by topic
categories = defaultdict(list)

for market in markets:
    ticker = market.ticker
    title = getattr(market, 'title', 'N/A')
    
    # Categorize based on ticker prefix or keywords
    if any(x in ticker for x in ['PRES', 'POTUS', 'ELECT']):
        categories['Elections'].append((ticker, title))
    elif any(x in ticker for x in ['ECON', 'GDP', 'INFL', 'FED', 'RATE']):
        categories['Economics'].append((ticker, title))
    elif any(x in ticker for x in ['SPORT', 'NFL', 'NBA', 'MLB', 'NHL']):
        categories['Sports'].append((ticker, title))
    elif any(x in ticker for x in ['POP', 'CELEB', 'AWARD', 'MOVIE']):
        categories['Pop Culture'].append((ticker, title))
    elif any(x in ticker for x in ['HIGH', 'TEMP', 'RAIN', 'WEATHER']):
        categories['Weather'].append((ticker, title))
    else:
        categories['Other'].append((ticker, title))

# Show categories
for category, items in sorted(categories.items()):
    if items:
        print(f"{category.upper()} ({len(items)} markets)")
        print("-" * 70)
        for ticker, title in items[:5]:  # Show first 5
            print(f"  {ticker}: {title[:55]}")
        if len(items) > 5:
            print(f"  ... and {len(items) - 5} more")
        print()

print("=" * 70)
print()
print("TRADING OPPORTUNITIES:")
print()

# Check FLB opportunities
from scripts.scan_markets import *  # Reuse the logic
print("Run: python scripts/scan_markets.py")
print("  to find FLB opportunities in these markets")

