"""
Automated Settlement Source Collector

Uses the get-market endpoint's settlement_sources field to AUTOMATICALLY
discover where Kalshi gets its ground truth.

This eliminates hard-coded NWS URLs and makes the system infinitely scalable.

Field: market.settlement_sources (from GET /trade-api/v2/markets/{ticker})
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient
import pandas as pd
from bs4 import BeautifulSoup
import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

print("=" * 70)
print("AUTOMATED SETTLEMENT SOURCE COLLECTOR")
print("=" * 70)
print()
print("Discovering settlement sources DIRECTLY from Kalshi API")
print("This makes the system infinitely scalable")
print()

# Setup Kalshi client
private_key_file = PROJECT_ROOT / os.environ["KALSHI_PRIVATE_KEY_FILE"]

config = Configuration(
    host="https://api.elections.kalshi.com/trade-api/v2"
)
config.api_key_id = os.environ["KALSHI_API_KEY_ID"]
config.private_key_pem = private_key_file.read_text()

client = KalshiClient(config)

print("[1/5] Connected to Kalshi API")
print()

# Load official NOAA data to know what events to query
noaa_file = PROJECT_ROOT / "data" / "weather" / "nws_settlement_ground_truth_OFFICIAL.csv"

if noaa_file.exists():
    df = pd.read_csv(noaa_file)
    df['date'] = pd.to_datetime(df['date'])
    print(f"[2/5] Loaded {len(df)} NOAA records for reference")
else:
    df = None
    print(f"[2/5] No NOAA data found (will discover settlement sources)")

print()

# Find recent settled weather markets
print("[3/5] Finding recently settled weather markets...")
print()

from kalshi_python.markets_api import MarketsApi
markets_api = MarketsApi(client)

weather_series = ['KXHIGHNY', 'KXHIGHCHI', 'KXHIGHMIA', 'KXHIGHHOU']
settled_markets = []

for series in weather_series:
    try:
        response = markets_api.get_markets(
            series_ticker=series,
            status='settled',
            limit=10
        )
        
        if response and response.markets:
            settled_markets.extend(response.markets)
            print(f"  {series}: {len(response.markets)} settled markets")
    except Exception as e:
        print(f"  {series}: ERROR - {e}")

print()
print(f"Found {len(settled_markets)} total settled markets")
print()

if len(settled_markets) == 0:
    print("[!] No settled markets found")
    print("    Try with a different status or series")
    sys.exit(0)

# Extract settlement sources
print("[4/5] Extracting settlement sources...")
print()

settlement_data = []

for market in settled_markets[:10]:  # Analyze first 10
    ticker = market.ticker
    
    print(f"--- {ticker} ---")
    
    try:
        # Get full market details
        market_details = markets_api.get_market(ticker=ticker)
        
        if not market_details:
            print("  No market details")
            continue
        
        # Check if settlement_sources field exists
        if hasattr(market_details, 'settlement_sources'):
            sources = market_details.settlement_sources
            
            if sources:
                for source in sources:
                    url = source.url if hasattr(source, 'url') else str(source)
                    print(f"  Settlement Source: {url}")
                    
                    settlement_data.append({
                        'ticker': ticker,
                        'series': market.series_ticker,
                        'settlement_url': url,
                        'settlement_value': market.result if hasattr(market, 'result') else None
                    })
            else:
                print("  No settlement sources listed")
        else:
            print("  settlement_sources field not found")
            print(f"  Available fields: {dir(market_details)}")
        
        print()
        
    except Exception as e:
        print(f"  ERROR: {e}")
        print()

# Save settlement source mapping
print(f"[5/5] Collected {len(settlement_data)} settlement sources")
print()

if len(settlement_data) > 0:
    output_file = PROJECT_ROOT / "data" / "weather" / "settlement_source_mapping.csv"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    df_sources = pd.DataFrame(settlement_data)
    df_sources.to_csv(output_file, index=False)
    
    print(f"Saved to: {output_file}")
    print()
    
    # Summary
    print("=" * 70)
    print("SETTLEMENT SOURCE SUMMARY")
    print("=" * 70)
    print()
    print(df_sources.to_string(index=False))
    print()
    
    # Demonstrate auto-scraping
    print("=" * 70)
    print("AUTO-SCRAPER DEMONSTRATION")
    print("=" * 70)
    print()
    
    if len(df_sources) > 0:
        first_source = df_sources.iloc[0]
        url = first_source['settlement_url']
        
        print(f"Attempting to scrape: {url}")
        print()
        
        try:
            headers = {'User-Agent': '(WeatherTrading, contact@example.com)'}
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try to find temperature data
            text = soup.get_text()
            
            # Look for "MAXIMUM TEMPERATURE" pattern
            for line in text.split('\n'):
                if 'MAXIMUM' in line.upper() or 'HIGH TEMPERATURE' in line.upper():
                    print(f"Found: {line.strip()}")
            
            print()
            print("[OK] Auto-scraper successfully retrieved settlement page")
            print()
            print("KEY INSIGHT:")
            print("  Our bot can now trade ANY weather market without hard-coding URLs")
            print("  1. Get market from Kalshi API")
            print("  2. Extract settlement_sources.url")
            print("  3. Scrape that URL for ground truth")
            print("  4. Verify our prediction was correct")
            print()
            print("This is INFINITELY SCALABLE.")
            
        except Exception as e:
            print(f"[!] Auto-scrape failed: {e}")
            print()
            print("But the settlement_sources field is still a goldmine.")
            print("We now know exactly where Kalshi gets its data.")
    
else:
    print("[!] No settlement sources collected")
    print()
    print("Possible reasons:")
    print("  - Field name may be different")
    print("  - Settlement sources may not be exposed via API")
    print("  - Need to check different market types")
    print()
    print("Alternative: Continue with manual NWS URL mapping")

print()
print("=" * 70)

