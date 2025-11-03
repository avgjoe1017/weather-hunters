"""
Complete morning routine for weather trading.

Run this script every morning at 10 AM EST to:
1. Check for active weather markets
2. Get today's forecasts
3. Calculate edge
4. Show trading recommendations
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient
from kalshi_python.api import markets_api
from src.features.weather_data_collector import HistoricalWeatherCollector
from datetime import datetime, timedelta

load_dotenv()

print("=" * 70)
print("WEATHER TRADING MORNING ROUTINE")
print("=" * 70)
print()

# Connect to Kalshi
api_key_id = os.getenv('KALSHI_API_KEY_ID')
key_file = project_root / "kalshi_private_key.pem"

with open(key_file, 'r') as f:
    private_key = f.read()

config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
config.api_key_id = api_key_id
config.private_key_pem = private_key
client = KalshiClient(config)

# Get balance
balance_info = client.get_balance()
balance = balance_info.balance / 100.0

print(f"[1/4] Account Balance: ${balance:.2f}")
print()

# Get forecasts
print("[2/4] Getting weather forecasts...")
print()

collector = HistoricalWeatherCollector()
tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

cities = {
    'NYC': ('New York', 'KXHIGHNY'),
    'CHI': ('Chicago', 'KXHIGHCHI'),
    'MIA': ('Miami', 'KXHIGHMIA'),
    'HOU': ('Houston', 'KXHIGHHOU'),
    'AUS': ('Austin', 'KXHIGHAUS')
}

forecasts = {}

for code, (name, series) in cities.items():
    try:
        forecast = collector.collect_current_forecast(tomorrow, code)
        forecasts[code] = {
            'name': name,
            'series': series,
            'temp': forecast.get('forecast_high_temp'),
            'lower_bracket': int(forecast.get('forecast_high_temp') // 2) * 2,
        }
        forecasts[code]['upper_bracket'] = forecasts[code]['lower_bracket'] + 2
        
        print(f"  {name}: {forecasts[code]['temp']:.1f}F (bracket: {forecasts[code]['lower_bracket']}-{forecasts[code]['upper_bracket']})")
    except:
        print(f"  {name}: Forecast unavailable")

print()

# Check for active markets
print("[3/4] Searching for active markets...")
print()

markets_instance = markets_api.MarketsApi(client)
active_markets = {}

for code, data in forecasts.items():
    try:
        response = markets_instance.get_markets(series_ticker=data['series'], limit=10)
        markets = response.markets if hasattr(response, 'markets') else []
        
        for market in markets:
            status = getattr(market, 'status', 'unknown')
            if status in ['active', 'open']:
                if code not in active_markets:
                    active_markets[code] = []
                active_markets[code].append(market)
    except:
        continue

if not active_markets:
    print("[!] No active markets found")
    print("Weather markets might not be launched yet.")
    print("Try again later or check https://kalshi.com/?category=climate")
    exit(0)

print(f"[OK] Found active markets for {len(active_markets)} cities")
print()

# Calculate edge and recommendations
print("[4/4] Calculating edge and recommendations...")
print()
print("=" * 70)

trades = []

for code, markets in active_markets.items():
    data = forecasts[code]
    print(f"\n{data['name']} - Forecast: {data['temp']:.1f}F")
    print("-" * 70)
    
    for market in markets[:6]:  # Show top 6 brackets
        ticker = market.ticker
        title = getattr(market, 'title', '')
        yes_ask = getattr(market, 'yes_ask', None)
        
        if yes_ask:
            # Extract bracket from title (rough parsing)
            implied_prob = yes_ask / 100.0
            
            # Calculate edge (simplified - assumes forecast is in the bracket)
            # In reality, you'd calculate probability based on forecast distribution
            edge = 0.0
            if str(data['lower_bracket']) in title and str(data['upper_bracket']) in title:
                # This is our target bracket
                edge = 0.45 - implied_prob  # Assume 45% true probability for center bracket
                win_prob = 0.45
            elif str(data['lower_bracket'] - 2) in title or str(data['upper_bracket'] + 2) in title:
                # Adjacent bracket
                edge = 0.25 - implied_prob
                win_prob = 0.25
            else:
                # Other bracket
                edge = 0.10 - implied_prob
                win_prob = 0.10
            
            if edge > 0.10:  # Good edge
                kelly_fraction = 0.25
                bet_size = balance * kelly_fraction * edge
                contracts = int(bet_size / implied_prob)
                
                print(f"\n  [GOOD TRADE] {ticker}")
                print(f"    {title[:60]}")
                print(f"    Price: ${yes_ask/100:.2f}")
                print(f"    Edge: {edge*100:.1f}%")
                print(f"    Recommended: {contracts} contracts (${contracts * yes_ask/100:.2f})")
                
                trades.append({
                    'city': data['name'],
                    'ticker': ticker,
                    'price': yes_ask/100,
                    'edge': edge,
                    'contracts': contracts,
                    'cost': contracts * yes_ask/100
                })

print()
print("=" * 70)
print()

if trades:
    print(f"[OK] {len(trades)} GOOD TRADES IDENTIFIED!")
    print()
    print("EXECUTION PLAN:")
    print()
    
    total_cost = sum(t['cost'] for t in trades)
    
    for i, trade in enumerate(trades, 1):
        print(f"{i}. {trade['city']} - {trade['ticker']}")
        print(f"   Buy {trade['contracts']} contracts @ ${trade['price']:.2f}")
        print(f"   Cost: ${trade['cost']:.2f}")
        print(f"   Edge: {trade['edge']*100:.1f}%")
        print()
    
    print(f"Total capital needed: ${total_cost:.2f}")
    print(f"Your balance: ${balance:.2f}")
    
    if total_cost <= balance:
        print("[OK] Sufficient funds for all trades")
    else:
        print("[!] Insufficient funds - prioritize highest edge trades")
    
    print()
    print("Execute these trades on:")
    print("  https://kalshi.com")
    print("  or use the API")
    
else:
    print("[!] No trades with sufficient edge found")
    print("Market prices might be efficient today.")
    print("Check again later or wait for tomorrow.")

print()
print("=" * 70)

