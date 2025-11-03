"""
Collect Historical Market Prices from Kalshi

Uses the get-market-candlesticks endpoint to collect REAL historical
market prices (OHLC) for all weather markets.

This ELIMINATES simulated prices from the backtest.

Endpoint: GET /trade-api/v2/markets/{ticker}/candlesticks
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd
import time
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Custom connector since SDK doesn't have candlesticks endpoint
from src.api.kalshi_connector import create_connector_from_env

load_dotenv(PROJECT_ROOT / ".env")

print("=" * 70)
print("HISTORICAL MARKET PRICES COLLECTOR")
print("=" * 70)
print()
print("Collecting REAL historical market prices from Kalshi")
print("This eliminates simulated prices from the backtest")
print()

# Load official NOAA data to know what events to query
noaa_file = PROJECT_ROOT / "data" / "weather" / "nws_settlement_ground_truth_OFFICIAL.csv"

if not noaa_file.exists():
    print("[X] NOAA ground truth not found. Run collect_noaa_ground_truth.py first.")
    sys.exit(1)

df = pd.read_csv(noaa_file)
df['date'] = pd.to_datetime(df['date'])

print(f"[1/5] Loaded {len(df)} NOAA settlement records")
print(f"      Date range: {df['date'].min()} to {df['date'].max()}")
print()

# Connect to Kalshi
connector = create_connector_from_env()

print("[2/5] Connected to Kalshi API")
print()

# Series ticker mapping
SERIES_MAP = {
    'NYC': 'KXHIGHNY',
    'CHI': 'KXHIGHCHI',
    'MIA': 'KXHIGHMIA',
    'HOU': 'KXHIGHHOU',
}

print("[3/5] Fetching historical market candlestick data...")
print()
print("NOTE: This collects daily OHLC (Open/High/Low/Close) prices")
print("      This is REAL market data, not simulated")
print()

price_data = []
errors = []

for idx, row in df.iterrows():
    city = row['city']
    date = row['date']
    
    series_ticker = SERIES_MAP.get(city)
    if not series_ticker:
        continue
    
    # Construct market ticker (we need the full ticker including bracket)
    # For now, we'll use the event ticker format
    date_str = date.strftime('%y-%m-%d')
    event_ticker = f"{series_ticker}-{date_str}"
    
    # We need to find all markets for this event
    # The actual market ticker includes the bracket (e.g., KXHIGHNY-25-11-03-T70)
    
    # For this initial version, let's just demonstrate with the event-level data
    # In production, we'd iterate through all brackets
    
    print(f"[{idx+1}/{len(df)}] {event_ticker} ({city}, {date.strftime('%Y-%m-%d')})")
    
    try:
        # Get markets for this series and date
        # We'll use the markets endpoint to find all markets for this event
        markets_response = connector.get_markets(
            series_ticker=series_ticker,
            status='settled'  # We only want settled markets for backtest
        )
        
        if not markets_response or 'markets' not in markets_response:
            print(f"      No markets found")
            continue
        
        # Find markets for this specific date
        date_markets = [
            m for m in markets_response['markets']
            if date_str in m['ticker']
        ]
        
        if not date_markets:
            print(f"      No markets for this date")
            continue
        
        print(f"      Found {len(date_markets)} bracket markets")
        
        # For each bracket market, get candlesticks
        for market in date_markets:
            ticker = market['ticker']
            
            # Get daily candlestick data
            # We want the closing price on the day the market was open
            start_ts = int((date - timedelta(days=2)).timestamp() * 1000)
            end_ts = int((date + timedelta(days=1)).timestamp() * 1000)
            
            # Make direct API call (SDK doesn't support candlesticks yet)
            url = f"{connector.base_url}/markets/{ticker}/candlesticks"
            params = {
                'start_ts': start_ts,
                'end_ts': end_ts,
                'period_interval': 1440  # Daily
            }
            
            headers = connector._get_headers()  # Assuming we can get auth headers
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                candlestick_data = response.json()
                
                if 'candlesticks' in candlestick_data and candlestick_data['candlesticks']:
                    # Get the last candlestick (closing price before settlement)
                    last_candle = candlestick_data['candlesticks'][-1]
                    
                    close_price = last_candle['close']
                    volume = last_candle['volume']
                    
                    price_data.append({
                        'date': date.strftime('%Y-%m-%d'),
                        'city': city,
                        'event_ticker': event_ticker,
                        'market_ticker': ticker,
                        'close_price': close_price / 100.0,  # Convert cents to dollars
                        'open_price': last_candle['open'] / 100.0,
                        'high_price': last_candle['high'] / 100.0,
                        'low_price': last_candle['low'] / 100.0,
                        'volume': volume,
                        'source': 'kalshi_candlesticks_api'
                    })
                    
                    print(f"        {ticker}: Close=${close_price/100:.2f}, Vol={volume}")
            else:
                print(f"        {ticker}: API error {response.status_code}")
            
            time.sleep(0.2)  # Rate limiting
        
    except Exception as e:
        print(f"      ERROR: {e}")
        errors.append({
            'event_ticker': event_ticker,
            'reason': str(e)
        })
        continue

print()
print(f"[4/5] Collection complete")
print(f"      Collected: {len(price_data)} market prices")
print(f"      Errors: {len(errors)} events")
print()

if len(price_data) == 0:
    print("[!] No price data collected.")
    print()
    print("Possible reasons:")
    print("  - Markets may not have candlestick history")
    print("  - Need to authenticate properly")
    print("  - Try downloading from kalshi.com/market-data instead")
    print()
    print("Alternative: Download CSV from https://kalshi.com/market-data")
    sys.exit(0)

# Save to CSV
output_file = PROJECT_ROOT / "data" / "weather" / "kalshi_historical_prices.csv"
output_file.parent.mkdir(parents=True, exist_ok=True)

df_prices = pd.DataFrame(price_data)
df_prices.to_csv(output_file, index=False)

print(f"[5/5] Saved to {output_file}")
print()

# Summary
print("=" * 70)
print("HISTORICAL MARKET PRICES SUMMARY")
print("=" * 70)
print()
print(f"Total events checked: {len(df)}")
print(f"Prices collected: {len(price_data)}")
print()

if len(price_data) > 0:
    print("Sample prices:")
    print(df_prices.head(10).to_string(index=False))
    print()
    
    print("Next steps:")
    print("  1. Merge with NOAA ground truth")
    print("  2. Merge with forecast data")
    print("  3. Run 100% REAL DATA backtest")
    print("  4. Compare to simulated backtest (+3,050%)")
else:
    print("No prices collected.")
    print()
    print("RECOMMENDED: Download historical data from:")
    print("  https://kalshi.com/market-data")
    print()
    print("This provides bulk OHLC data for all markets as CSV")

print()
print("=" * 70)

