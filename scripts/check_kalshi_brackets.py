"""
Check actual Kalshi weather market bracket sizes.

This will tell us if our 2°F granularity matches reality.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient

load_dotenv()

print("=" * 70)
print("KALSHI WEATHER BRACKET ANALYSIS")
print("=" * 70)
print()

# Connect to Kalshi
config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
config.api_key_id = os.getenv('KALSHI_API_KEY_ID')

with open(os.getenv('KALSHI_PRIVATE_KEY_FILE'), 'r') as f:
    config.private_key_pem = f.read()

client = KalshiClient(config)

# Search for weather markets
print("[1/2] Searching for weather/climate markets...")
print()

from kalshi_python.api import series_api
s_api = series_api.SeriesApi(client)

# Get a weather series
try:
    series_response = s_api.get_series(category="climate", limit=10)
    
    if series_response.series:
        print(f"[OK] Found {len(series_response.series)} climate series")
        print()
        
        # Pick first series with "HIGH" in ticker (temperature high markets)
        for series in series_response.series:
            if 'HIGH' in series.ticker:
                print(f"Analyzing: {series.title}")
                print(f"Ticker: {series.ticker}")
                print()
                
                # Get markets for this series
                from kalshi_python.api import market_api
                m_api = market_api.MarketApi(client)
                
                try:
                    markets_response = m_api.get_markets(series_ticker=series.ticker, limit=20, status="finalized")
                    
                    if markets_response.markets:
                        print(f"[2/2] Analyzing {len(markets_response.markets)} markets...")
                        print()
                        
                        # Extract bracket information from market tickers
                        brackets = []
                        for market in markets_response.markets[:10]:
                            print(f"Market: {market.ticker}")
                            print(f"  Title: {market.subtitle}")
                            print(f"  Question: What temperature range?")
                            print()
                            
                            # Try to extract temperature range from subtitle
                            # Typical format: "Will NYC high be 70-75°F?"
                            import re
                            temp_match = re.search(r'(\d+)-(\d+)', market.subtitle)
                            if temp_match:
                                low = int(temp_match.group(1))
                                high = int(temp_match.group(2))
                                bracket_size = high - low
                                brackets.append(bracket_size)
                                print(f"    -> Bracket: {low}-{high}°F (size: {bracket_size}°F)")
                                print()
                        
                        if brackets:
                            avg_bracket = sum(brackets) / len(brackets)
                            print("=" * 70)
                            print("ANALYSIS")
                            print("=" * 70)
                            print()
                            print(f"Kalshi bracket sizes: {set(brackets)}")
                            print(f"Average bracket size: {avg_bracket:.1f}°F")
                            print()
                            print("Our model granularity: 2°F")
                            print()
                            
                            if avg_bracket >= 4:
                                print(f"[OK] GOOD NEWS! Kalshi uses {avg_bracket:.0f}°F brackets")
                                print(f"    Our 82% (±2°F) accuracy means we'll hit the right")
                                print(f"    {avg_bracket:.0f}°F bracket much more often!")
                                print()
                                print("    Estimated exact bracket accuracy:")
                                # If brackets are 5°F and we're accurate to ±2°F, we hit exact bracket ~90% of time
                                estimated = 82 + (avg_bracket - 2) * 3  # Rough estimate
                                estimated = min(estimated, 95)
                                print(f"    ~{estimated:.0f}% (from 82% ±2°F accuracy)")
                            elif avg_bracket == 2:
                                print(f"[~] Kalshi uses 2°F brackets (same as our model)")
                                print(f"    Our exact accuracy: 7.7% (too low)")
                                print(f"    Need to improve model or use multi-bracket strategy")
                            else:
                                print(f"[!] Kalshi uses {avg_bracket:.0f}°F brackets")
                                print(f"    Need to retrain model with {avg_bracket:.0f}°F granularity")
                        
                        break  # Only analyze first HIGH series
                    else:
                        print("No finalized markets found")
                except Exception as e:
                    print(f"Error fetching markets: {e}")
                
                break  # Only check first series
        
    else:
        print("[X] No climate series found")
        
except Exception as e:
    print(f"[X] Error: {e}")

print()
print("=" * 70)

