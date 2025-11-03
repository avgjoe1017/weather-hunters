"""
Simple market scanner using Kalshi official SDK.

Shows live markets and identifies potential FLB (Favorite-Longshot Bias) opportunities.
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
print("KALSHI MARKET SCANNER - FLB OPPORTUNITIES")
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

# Get markets
print("[2/3] Fetching open markets...")
markets_instance = markets_api.MarketsApi(client)

try:
    response = markets_instance.get_markets(
        limit=100,
        status="open"
    )
    
    markets = response.markets if hasattr(response, 'markets') else []
    print(f"[OK] Found {len(markets)} open markets")
    print()
    
except Exception as e:
    print(f"[X] Error: {e}")
    exit(1)

# Analyze
print("[3/3] Analyzing for FLB opportunities...")
print()

favorites = []  # Markets with very high YES probability (>90%)
longshots = []  # Markets with very low YES probability (<10%)

for market in markets:
    try:
        ticker = market.ticker
        yes_bid = getattr(market, 'yes_bid', None)
        yes_ask = getattr(market, 'yes_ask', None)
        
        if yes_bid and yes_ask:
            mid_price = (yes_bid + yes_ask) / 2.0 / 100.0  # Convert to decimal
            
            # Favorite: high probability markets tend to be overpriced
            if mid_price >= 0.90:
                favorites.append({
                    'ticker': ticker,
                    'price': mid_price,
                    'bid': yes_bid / 100.0,
                    'ask': yes_ask / 100.0,
                    'title': getattr(market, 'title', 'N/A')[:50]
                })
            
            # Longshot: low probability markets tend to be underpriced
            elif mid_price <= 0.10:
                longshots.append({
                    'ticker': ticker,
                    'price': mid_price,
                    'bid': yes_bid / 100.0,
                    'ask': yes_ask / 100.0,
                    'title': getattr(market, 'title', 'N/A')[:50]
                })
    except:
        continue

# Results
print("=" * 70)
print("SCAN RESULTS")
print("=" * 70)
print()

print(f"FAVORITES (High Probability Markets >=90%)")
print(f"Found: {len(favorites)}")
print()

if favorites:
    for i, m in enumerate(favorites[:5], 1):  # Show top 5
        print(f"{i}. {m['ticker']}")
        print(f"   Title: {m['title']}")
        print(f"   Price: {m['price']*100:.1f}¢ (Bid: {m['bid']*100:.1f}¢, Ask: {m['ask']*100:.1f}¢)")
        print(f"   Note: Favorites often overpriced (FLB opportunity to bet NO)")
        print()

print("-" * 70)
print()

print(f"LONGSHOTS (Low Probability Markets <=10%)")
print(f"Found: {len(longshots)}")
print()

if longshots:
    for i, m in enumerate(longshots[:5], 1):  # Show top 5
        print(f"{i}. {m['ticker']}")
        print(f"   Title: {m['title']}")
        print(f"   Price: {m['price']*100:.1f}¢ (Bid: {m['bid']*100:.1f}¢, Ask: {m['ask']*100:.1f}¢)")
        print(f"   Note: Longshots often underpriced (FLB opportunity to bet YES)")
        print()

print("=" * 70)
print()

# Summary
total_opportunities = len(favorites) + len(longshots)

if total_opportunities > 0:
    print(f"[OK] Found {total_opportunities} potential FLB opportunities!")
    print()
    print("NEXT STEPS:")
    print("1. Review the opportunities above")
    print("2. Research specific markets that interest you")
    print("3. Determine position sizes based on edge estimation")
    print("4. See Documentation/NEXT_STEPS.md for live trading")
else:
    print("No clear FLB opportunities at the moment.")
    print("Markets can change quickly - check back regularly!")

print()
print(f"Your balance: ${balance:.2f}")
print(f"Markets scanned: {len(markets)}")
print("=" * 70)

