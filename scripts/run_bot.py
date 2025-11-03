"""
Run the Kalshi trading bot using the official SDK for authentication.

This script uses the verified working authentication and runs the FLB Harvester strategy.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient
from loguru import logger

# Load environment
load_dotenv()

print("=" * 70)
print("KALSHI TRADING BOT - FLB HARVESTER")
print("=" * 70)
print()

# Configuration
api_key_id = os.getenv('KALSHI_API_KEY_ID')
key_file = project_root / "kalshi_private_key.pem"

if not key_file.exists():
    print("[X] Private key file not found: kalshi_private_key.pem")
    print("Run: python scripts/save_key_to_file.py")
    exit(1)

# Load key
with open(key_file, 'r') as f:
    private_key = f.read()

# Create Kalshi client
print("[1/5] Connecting to Kalshi API...")
config = Configuration(host="https://api.elections.kalshi.com/trade-api/v2")
config.api_key_id = api_key_id
config.private_key_pem = private_key
client = KalshiClient(config)

# Get balance
try:
    balance_info = client.get_balance()
    balance = balance_info.balance / 100.0
    print(f"[OK] Connected! Account Balance: ${balance:.2f}")
    print()
except Exception as e:
    print(f"[X] Connection failed: {e}")
    exit(1)

# Initialize components
print("[2/5] Initializing trading components...")

from src.risk.risk_manager import RiskManager, RiskLimits
from src.monitoring.metrics_collector import MetricsCollector
from src.strategies.flb_harvester import FLBHarvester

# Risk Manager - use defaults (conservative settings)
risk_mgr = RiskManager(
    initial_capital=balance * 100  # Convert to cents
)

# Metrics Collector
metrics = MetricsCollector(output_dir=str(project_root / "metrics"))

# FLB Harvester Strategy
strategy = FLBHarvester(risk_manager=risk_mgr)

print(f"[OK] Risk Manager initialized (${balance:.2f} capital)")
print(f"[OK] Metrics Collector initialized")
print(f"[OK] FLB Harvester strategy loaded")
print()

# Scan markets
print("[3/5] Scanning markets for FLB opportunities...")
print()

try:
    # Get all open markets
    from kalshi_python.api import markets_api
    markets_instance = markets_api.MarketsApi(client)
    
    markets_response = markets_instance.get_markets(
        limit=200,
        status="open"
    )
    
    markets = markets_response.markets if hasattr(markets_response, 'markets') else []
    
    print(f"[OK] Found {len(markets)} open markets")
    print()
    
    if not markets:
        print("[!] No open markets found. Try again later.")
        exit(0)
    
    # Scan for opportunities
    print("[4/5] Analyzing markets...")
    opportunities = []
    
    for i, market in enumerate(markets[:50]):  # Scan first 50 for demo
        ticker = market.ticker
        
        # Get market details
        try:
            # Simple check - more detailed analysis would go here
            if hasattr(market, 'yes_bid') and hasattr(market, 'no_bid'):
                yes_price = market.yes_bid
                no_price = market.no_bid
                
                # Check for favorite-longshot opportunities
                if yes_price and yes_price >= 90:  # Favorite
                    edge = strategy._calculate_edge(yes_price / 100.0, is_favorite=True)
                    if edge > strategy.min_edge:
                        opportunities.append({
                            'ticker': ticker,
                            'type': 'favorite',
                            'price': yes_price,
                            'edge': edge
                        })
                elif yes_price and yes_price <= 10:  # Longshot
                    edge = strategy._calculate_edge(yes_price / 100.0, is_favorite=False)
                    if edge > strategy.min_edge:
                        opportunities.append({
                            'ticker': ticker,
                            'type': 'longshot',
                            'price': yes_price,
                            'edge': edge
                        })
        except Exception as e:
            continue
    
    print()
    print("[5/5] Analysis complete!")
    print()
    print("=" * 70)
    print("SCAN RESULTS")
    print("=" * 70)
    print()
    
    if opportunities:
        print(f"[OK] Found {len(opportunities)} FLB opportunities:")
        print()
        for opp in opportunities[:10]:  # Show top 10
            print(f"  • {opp['ticker']}")
            print(f"    Type: {opp['type'].title()}")
            print(f"    Price: ${opp['price']/100:.2f}")
            print(f"    Edge: {opp['edge']*100:.1f}%")
            print()
        
        print("=" * 70)
        print()
        print("🎯 NEXT STEPS:")
        print()
        print("1. Review opportunities above")
        print("2. Check risk calculations match your tolerance")
        print("3. To enable live trading:")
        print("   - Review Documentation/NEXT_STEPS.md")
        print("   - Modify this script to execute trades")
        print("   - Start with small positions")
        print()
        print(f"Current Balance: ${balance:.2f}")
        print(f"Max Position Size: ${balance * 0.05:.2f} (5%)")
        print(f"Daily Loss Limit: ${balance * 0.05:.2f} (5%)")
        
    else:
        print("[!] No FLB opportunities found in current scan")
        print()
        print("This is normal - opportunities appear periodically.")
        print("The bot can run continuously to catch them.")
        print()
        print(f"Markets scanned: {min(50, len(markets))}")
        print(f"Account balance: ${balance:.2f}")
    
except Exception as e:
    print(f"[X] Error during market scan: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print()
print("=" * 70)
print("Bot scan complete. No trades executed (observation mode).")
print("=" * 70)

