"""
Market Liquidity Analyzer

Uses get-market-orderbook to analyze REAL-TIME liquidity for weather markets.

This is the professional-grade filter that separates good trades from bad trades.

Endpoint: GET /trade-api/v2/markets/{ticker}/orderbook
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

print("=" * 70)
print("MARKET LIQUIDITY ANALYZER")
print("=" * 70)
print()
print("Analyzing REAL-TIME order book depth for weather markets")
print()

# Setup Kalshi client
private_key_file = PROJECT_ROOT / os.environ["KALSHI_PRIVATE_KEY_FILE"]

config = Configuration(
    host="https://api.elections.kalshi.com/trade-api/v2"
)
config.api_key_id = os.environ["KALSHI_API_KEY_ID"]
config.private_key_pem = private_key_file.read_text()

client = KalshiClient(config)

print("[1/4] Connected to Kalshi API")
print()

# Find active weather markets
print("[2/4] Finding active weather markets...")
print()

from kalshi_python.markets_api import MarketsApi
markets_api = MarketsApi(client)

# Get active weather markets
weather_series = ['KXHIGHNY', 'KXHIGHCHI', 'KXHIGHMIA', 'KXHIGHHOU']
active_markets = []

for series in weather_series:
    try:
        response = markets_api.get_markets(
            series_ticker=series,
            status='open',
            limit=50
        )
        
        if response and response.markets:
            active_markets.extend(response.markets)
            print(f"  {series}: {len(response.markets)} active markets")
    except Exception as e:
        print(f"  {series}: ERROR - {e}")

print()
print(f"[3/4] Found {len(active_markets)} total active weather markets")
print()

if len(active_markets) == 0:
    print("[!] No active markets found")
    print("    Weather markets may not be open right now")
    print("    Try again during market hours (typically 10 AM - 8 PM EST)")
    sys.exit(0)

# Analyze order book for each market
print("[4/4] Analyzing order book depth...")
print()

liquidity_analysis = []

for market in active_markets[:10]:  # Analyze first 10 markets
    ticker = market.ticker
    
    print(f"--- {ticker} ---")
    
    try:
        # Get order book
        orderbook = markets_api.get_market_orderbook(ticker=ticker)
        
        if not orderbook:
            print("  No order book data")
            continue
        
        # Extract best bid and ask
        yes_bids = orderbook.yes if hasattr(orderbook, 'yes') else []
        no_bids = orderbook.no if hasattr(orderbook, 'no') else []
        
        # Calculate spread
        if yes_bids:
            best_bid = max([bid[0] for bid in yes_bids]) / 100.0
            best_bid_size = [bid[1] for bid in yes_bids if bid[0] == best_bid * 100][0]
        else:
            best_bid = 0
            best_bid_size = 0
        
        if yes_bids:
            # Ask is inverse - sellers of YES
            best_ask = min([bid[0] for bid in yes_bids if bid[0] > best_bid * 100]) / 100.0 if len(yes_bids) > 1 else 1.0
            best_ask_size = [bid[1] for bid in yes_bids if bid[0] == best_ask * 100][0] if len(yes_bids) > 1 else 0
        else:
            best_ask = 1.0
            best_ask_size = 0
        
        # Calculate metrics
        spread = best_ask - best_bid
        spread_pct = (spread / best_bid * 100) if best_bid > 0 else 999
        
        # Liquidity score (0-10)
        # High score = tight spread + deep book
        spread_score = max(0, 5 - spread * 100)  # Penalize wide spreads
        depth_score = min(5, (best_bid_size + best_ask_size) / 20)  # Reward depth
        liquidity_score = spread_score + depth_score
        
        # Trade decision
        if spread > 0.05:
            decision = "SKIP - Wide spread"
        elif best_bid_size < 10 and best_ask_size < 10:
            decision = "SKIP - Thin book"
        elif liquidity_score < 3:
            decision = "SKIP - Poor liquidity"
        else:
            decision = "TRADEABLE"
        
        print(f"  Best Bid: ${best_bid:.2f} ({best_bid_size} contracts)")
        print(f"  Best Ask: ${best_ask:.2f} ({best_ask_size} contracts)")
        print(f"  Spread: ${spread:.3f} ({spread_pct:.1f}%)")
        print(f"  Liquidity Score: {liquidity_score:.1f}/10")
        print(f"  Decision: {decision}")
        print()
        
        liquidity_analysis.append({
            'ticker': ticker,
            'best_bid': best_bid,
            'best_ask': best_ask,
            'spread': spread,
            'spread_pct': spread_pct,
            'bid_size': best_bid_size,
            'ask_size': best_ask_size,
            'liquidity_score': liquidity_score,
            'decision': decision
        })
        
    except Exception as e:
        print(f"  ERROR: {e}")
        print()

# Summary
print("=" * 70)
print("LIQUIDITY ANALYSIS SUMMARY")
print("=" * 70)
print()

if liquidity_analysis:
    import pandas as pd
    df = pd.DataFrame(liquidity_analysis)
    
    tradeable = df[df['decision'] == 'TRADEABLE']
    
    print(f"Total markets analyzed: {len(df)}")
    print(f"Tradeable markets: {len(tradeable)}")
    print(f"Skipped (poor liquidity): {len(df) - len(tradeable)}")
    print()
    
    if len(tradeable) > 0:
        print("TRADEABLE MARKETS:")
        print(tradeable[['ticker', 'best_bid', 'best_ask', 'spread', 'liquidity_score']].to_string(index=False))
        print()
        print("These markets have:")
        print("  - Tight spreads (< 5¢)")
        print("  - Sufficient depth (>= 10 contracts)")
        print("  - Good liquidity score (>= 3/10)")
        print()
        print("These are SAFE to trade.")
    else:
        print("[!] NO TRADEABLE MARKETS")
        print()
        print("All markets have either:")
        print("  - Wide spreads (> 5¢)")
        print("  - Thin order books (< 10 contracts)")
        print("  - Poor overall liquidity")
        print()
        print("RECOMMENDATION: Wait for better market conditions")
    
    print()
    print("=" * 70)
    print("KEY INSIGHT")
    print("=" * 70)
    print()
    print("This analysis is what separates professionals from amateurs.")
    print()
    print("A 'good' model with 'poor' liquidity = LOSSES from slippage.")
    print("A 'mediocre' model with 'excellent' liquidity = PROFITS.")
    print()
    print("Our bot will ONLY trade when liquidity score >= 3.")
    print("=" * 70)

else:
    print("No liquidity data collected")

print()

