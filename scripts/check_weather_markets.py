"""
Check if Kalshi has weather markets available.

This is CRITICAL - the weather strategy only works if Kalshi actually
has daily temperature markets for NYC, Chicago, Miami, Austin.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient
from kalshi_python.api import markets_api

load_dotenv()

print("=" * 70)
print("WEATHER MARKET AVAILABILITY CHECK")
print("=" * 70)
print()

# Setup
api_key_id = os.getenv('KALSHI_API_KEY_ID')
key_file = project_root / "kalshi_private_key.pem"

if not key_file.exists():
    print("[X] Private key file not found")
    exit(1)

with open(key_file, 'r') as f:
    private_key = f.read()

# Connect
print("[1/3] Connecting to Kalshi...")
config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
config.api_key_id = api_key_id
config.private_key_pem = private_key
client = KalshiClient(config)

balance_info = client.get_balance()
balance = balance_info.balance / 100.0
print(f"[OK] Connected! Balance: ${balance:.2f}")
print()

# Search for weather markets
print("[2/3] Searching for weather markets...")
markets_instance = markets_api.MarketsApi(client)

try:
    # Get all open markets
    response = markets_instance.get_markets(
        limit=200,
        status="open"
    )
    
    all_markets = response.markets if hasattr(response, 'markets') else []
    print(f"[OK] Retrieved {len(all_markets)} total open markets")
    print()
    
except Exception as e:
    print(f"[X] Error: {e}")
    exit(1)

# Filter for weather-related markets
print("[3/3] Analyzing for weather markets...")
print()

weather_keywords = ['HIGH', 'TEMP', 'RAIN', 'SNOW', 'WEATHER', 'NYC', 'CHICAGO', 'MIAMI', 'AUSTIN']

weather_markets = []
for market in all_markets:
    ticker = market.ticker.upper()
    title = getattr(market, 'title', '').upper()
    
    # Check if any weather keyword is in ticker or title
    if any(keyword in ticker or keyword in title for keyword in weather_keywords):
        weather_markets.append({
            'ticker': market.ticker,
            'title': getattr(market, 'title', 'N/A'),
            'yes_bid': getattr(market, 'yes_bid', None),
            'yes_ask': getattr(market, 'yes_ask', None),
            'volume': getattr(market, 'volume', 0),
            'close_time': getattr(market, 'close_time', 'N/A')
        })

print("=" * 70)
print("RESULTS")
print("=" * 70)
print()

if weather_markets:
    print(f"[OK] Found {len(weather_markets)} weather-related markets!")
    print()
    print("=" * 70)
    
    # Categorize by type
    temp_markets = [m for m in weather_markets if 'HIGH' in m['ticker'] or 'TEMP' in m['ticker']]
    rain_markets = [m for m in weather_markets if 'RAIN' in m['ticker']]
    other_markets = [m for m in weather_markets if m not in temp_markets and m not in rain_markets]
    
    # Temperature markets
    if temp_markets:
        print()
        print("TEMPERATURE MARKETS:")
        print("-" * 70)
        for m in temp_markets[:10]:
            print(f"\n{m['ticker']}")
            print(f"  Title: {m['title'][:60]}")
            if m['yes_bid'] and m['yes_ask']:
                print(f"  Price: {m['yes_bid']}-{m['yes_ask']} cents")
            print(f"  Volume: {m['volume']}")
            print(f"  Closes: {m['close_time']}")
    
    # Rain markets
    if rain_markets:
        print()
        print("RAIN/PRECIPITATION MARKETS:")
        print("-" * 70)
        for m in rain_markets[:10]:
            print(f"\n{m['ticker']}")
            print(f"  Title: {m['title'][:60]}")
            if m['yes_bid'] and m['yes_ask']:
                print(f"  Price: {m['yes_bid']}-{m['yes_ask']} cents")
            print(f"  Volume: {m['volume']}")
    
    # Other weather markets
    if other_markets:
        print()
        print("OTHER WEATHER MARKETS:")
        print("-" * 70)
        for m in other_markets[:10]:
            print(f"\n{m['ticker']}")
            print(f"  Title: {m['title'][:60]}")
    
    print()
    print("=" * 70)
    print()
    
    # Analysis
    print("WEATHER STRATEGY VIABILITY:")
    print()
    
    if temp_markets:
        print(f"[OK] Temperature markets found: {len(temp_markets)}")
        
        # Check for daily markets
        daily_temp = [m for m in temp_markets if 'DAILY' in m['title'].upper() or 'TOMORROW' in m['title'].upper()]
        
        if daily_temp:
            print(f"[OK] Daily temperature markets: {len(daily_temp)}")
            print()
            print(">>> WEATHER STRATEGY IS VIABLE! <<<")
            print()
            print("Next steps:")
            print("1. Run backtest: python scripts/run_weather_strategy.py")
            print("2. Set up forecast collection")
            print("3. Start trading weather markets daily")
        else:
            print(f"[!] No daily temperature markets found")
            print(f"[!] Markets might be monthly/seasonal only")
            print()
            print("Weather strategy needs daily temperature brackets.")
            print("Check back later or trade FLB strategy instead.")
    else:
        print("[X] No temperature markets found")
        print()
        print("Weather strategy NOT viable at this time.")
        print("Kalshi may not have launched temperature markets yet.")
        print()
        print("RECOMMENDATION: Use FLB strategy until weather markets available.")
        print("Run: python scripts/scan_markets.py")

else:
    print("[!] No weather-related markets found")
    print()
    print("This could mean:")
    print("1. Kalshi hasn't launched weather markets yet")
    print("2. Weather markets are seasonal (not available now)")
    print("3. Search keywords need adjustment")
    print()
    print("=" * 70)
    print()
    print("RECOMMENDATION:")
    print("- Use FLB strategy for now: python scripts/scan_markets.py")
    print("- Check back for weather markets periodically")
    print("- Weather strategy is ready when markets launch")

print()
print("=" * 70)
print(f"Total markets scanned: {len(all_markets)}")
print(f"Weather markets found: {len(weather_markets)}")
print(f"Your balance: ${balance:.2f}")
print("=" * 70)

