"""
Manual weather trading script.

This script helps you execute weather trades based on your edge calculations.
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

print("=" * 70)
print("MANUAL WEATHER TRADING")
print("=" * 70)
print()

# Connect to Kalshi
api_key_id = os.getenv('KALSHI_API_KEY_ID')
key_file = project_root / "kalshi_private_key.pem"

if not key_file.exists():
    print("[X] Private key file not found")
    exit(1)

with open(key_file, 'r') as f:
    private_key = f.read()

config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
config.api_key_id = api_key_id
config.private_key_pem = private_key
client = KalshiClient(config)

# Get balance
balance_info = client.get_balance()
balance = balance_info.balance / 100.0

print(f"Account Balance: ${balance:.2f}")
print()

# Search for weather markets
print("Searching for active weather markets...")
print()

markets_instance = markets_api.MarketsApi(client)

weather_series = ['KXHIGHNY', 'KXHIGHCHI', 'KXHIGHMIA', 'KXHIGHHOU', 'KXHIGHAUS']

found_markets = []

for series_ticker in weather_series:
    try:
        response = markets_instance.get_markets(series_ticker=series_ticker, limit=10)
        markets = response.markets if hasattr(response, 'markets') else []
        
        for market in markets:
            status = getattr(market, 'status', 'unknown')
            if status in ['active', 'open']:
                found_markets.append(market)
                
    except Exception as e:
        continue

if not found_markets:
    print("[!] No active weather markets found")
    print()
    print("Markets might not be launched yet. Try:")
    print("1. Check again at 10 AM EST")
    print("2. Run: python scripts/deep_market_search.py")
    print("3. Visit: https://kalshi.com/?category=climate")
    exit(0)

print(f"[OK] Found {len(found_markets)} active weather markets!")
print()

# Display markets
for i, market in enumerate(found_markets[:20], 1):
    ticker = market.ticker
    title = getattr(market, 'title', 'N/A')
    yes_bid = getattr(market, 'yes_bid', None)
    yes_ask = getattr(market, 'yes_ask', None)
    
    print(f"{i}. {ticker}")
    print(f"   {title[:65]}")
    if yes_bid and yes_ask:
        print(f"   Bid/Ask: {yes_bid/100:.2f} / {yes_ask/100:.2f}")
    print()

print("=" * 70)
print()
print("MANUAL TRADING WORKFLOW:")
print()
print("1. Compare these markets to your forecasts")
print("   Run: python scripts/get_todays_forecast.py")
print()
print("2. Calculate your edge:")
print("   - Your forecast: 72F for NYC")
print("   - Kalshi 70-72F bracket: 30 cents")
print("   - True probability: ~45% (based on forecast)")
print("   - Implied probability: 30%")
print("   - Edge: 15 percentage points")
print()
print("3. Size your position (Kelly criterion):")
print("   - Edge = 0.15")
print("   - Win probability = 0.45")
print("   - Kelly fraction = edge / odds")
print("   - With fractional Kelly (0.25), bet ~2-3% of bankroll")
print()
print("4. Execute trade:")
print("   - Use Kalshi website or API")
print("   - Buy the bracket with edge")
print("   - Record your trade for tracking")
print()
print("5. Wait for settlement (next day):")
print("   - Markets settle based on NWS data")
print("   - If you win: Get $1.00 per contract - 7% fee")
print("   - If you lose: Lose your purchase price")
print()
print(f"Your balance: ${balance:.2f}")
print(f"Recommended max trade: ${balance * 0.05:.2f} (5% per market)")
print()
print("=" * 70)

# Example calculation
print()
print("EXAMPLE CALCULATION:")
print()
print("Scenario: NYC high temp tomorrow")
print("  Your forecast: 72F")
print("  Kalshi bracket: 70-72F at 30 cents")
print("  Your win probability: 45%")
print()
print("Position sizing:")
print(f"  Bankroll: ${balance:.2f}")
print(f"  Kelly bet: 2.5% = ${balance * 0.025:.2f}")
print(f"  Contracts: {int(balance * 0.025 / 0.30)} contracts @ 30 cents")
print(f"  Total cost: ${int(balance * 0.025 / 0.30) * 0.30:.2f}")
print()
print("Expected outcome:")
print(f"  If win (45% chance): +${int(balance * 0.025 / 0.30) * (1.00 - 0.07) - int(balance * 0.025 / 0.30) * 0.30:.2f}")
print(f"  If lose (55% chance): -${int(balance * 0.025 / 0.30) * 0.30:.2f}")
print(f"  Expected value: +${int(balance * 0.025 / 0.30) * (0.45 * 0.70 - 0.55 * 0.30):.2f}")
print()
print("Trade on Kalshi.com or use API to execute")

