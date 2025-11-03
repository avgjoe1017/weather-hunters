"""
Verify Settlement - "Unblinding" the Results

Run this AFTER settlement (evening) to check actual NWS temperatures
and update the paper trade log with outcomes.

This completes the "blind" study by revealing the truth.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
from datetime import datetime, timedelta
import requests
import re

print("=" * 70)
print("SETTLEMENT VERIFICATION - UNBLINDING RESULTS")
print("=" * 70)
print()

# Load paper trade log
logs_dir = project_root / "logs"
paper_trade_log = logs_dir / "paper_trades.csv"

if not paper_trade_log.exists():
    print("[X] No paper trade log found!")
    print(f"    Expected: {paper_trade_log}")
    print("    Run: python scripts/paper_trade_morning.py first")
    sys.exit(1)

df = pd.read_csv(paper_trade_log)

# Find pending trades (yesterday's predictions)
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
pending = df[(df['date'] == yesterday) & (df['outcome'] == 'PENDING')].copy()

if len(pending) == 0:
    print(f"[!] No pending trades for {yesterday}")
    print("    Either:")
    print("    1. No trades were made yesterday")
    print("    2. Settlements already verified")
    print("    3. Check if date is correct")
    sys.exit(0)

print(f"[1/3] Found {len(pending)} pending trades for {yesterday}")
print()

# NWS CLI report URLs by city
NWS_URLS = {
    'NYC': 'https://forecast.weather.gov/product.php?site=OKX&product=CLI&issuedby=NYC',
    'CHI': 'https://forecast.weather.gov/product.php?site=LOT&product=CLI&issuedby=ORD',
    'MIA': 'https://forecast.weather.gov/product.php?site=MFL&product=CLI&issuedby=MIA',
    'HOU': 'https://forecast.weather.gov/product.php?site=HGX&product=CLI&issuedby=IAH',
}

print("[2/3] Fetching NWS Daily Climate Reports...")
print()

KALSHI_FEE = 0.07

for idx, row in pending.iterrows():
    city = row['city']
    city_name = row['city_name']
    
    print(f"Checking {city_name} ({city})...")
    
    if city not in NWS_URLS:
        print(f"  [!] No NWS URL configured for {city}")
        continue
    
    try:
        # Fetch NWS CLI report
        response = requests.get(NWS_URLS[city], timeout=10)
        response.raise_for_status()
        
        # Parse temperature (look for "MAXIMUM" in temperature section)
        # Format: "  MAXIMUM         84   2:39 PM"
        match = re.search(r'MAXIMUM\s+(\d+)', response.text)
        
        if match:
            actual_temp = int(match.group(1))
            print(f"  Actual High: {actual_temp}F")
            
            # Check if prediction was correct
            predicted_low = row['predicted_bracket_low']
            predicted_high = row['predicted_bracket_high']
            
            correct = predicted_low <= actual_temp < predicted_high
            outcome = 'WIN' if correct else 'LOSS'
            
            # Calculate P&L
            num_contracts = row['num_contracts']
            cost = row['cost']
            
            if correct:
                gross_payout = num_contracts * 1.00
                fee = gross_payout * KALSHI_FEE
                net_payout = gross_payout - fee
                pnl = net_payout - cost
            else:
                pnl = -cost
            
            print(f"  Predicted: {predicted_low}-{predicted_high}F")
            print(f"  Outcome: {outcome}")
            print(f"  P&L: ${pnl:+.2f}")
            
            # Update dataframe
            df.loc[idx, 'actual_temp'] = actual_temp
            df.loc[idx, 'outcome'] = outcome
            df.loc[idx, 'pnl'] = pnl
            
        else:
            print(f"  [!] Could not parse temperature from NWS report")
            print(f"      Check manually: {NWS_URLS[city]}")
    
    except requests.RequestException as e:
        print(f"  [X] Error fetching NWS report: {e}")
        print(f"      Check manually: {NWS_URLS[city]}")
    
    print()

# Save updated log
df.to_csv(paper_trade_log, index=False)
print(f"[3/3] Updated paper trade log: {paper_trade_log}")
print()

# Show summary
verified = df[(df['date'] == yesterday) & (df['outcome'] != 'PENDING')]

if len(verified) > 0:
    wins = (verified['outcome'] == 'WIN').sum()
    losses = (verified['outcome'] == 'LOSS').sum()
    win_rate = wins / len(verified)
    total_pnl = verified['pnl'].sum()
    
    print("=" * 70)
    print(f"SETTLEMENT RESULTS - {yesterday}")
    print("=" * 70)
    print()
    print(f"Total Trades: {len(verified)}")
    print(f"Wins:         {wins} ({win_rate*100:.1f}%)")
    print(f"Losses:       {losses} ({(1-win_rate)*100:.1f}%)")
    print(f"Total P&L:    ${total_pnl:+.2f}")
    print()
    
    if win_rate >= 0.55:
        print("[OK] Win rate >= 55% (meets success criteria!)")
    else:
        print("[!] Win rate < 55% (below target)")
    
    if total_pnl > 0:
        print("[OK] Profitable day")
    else:
        print("[!] Unprofitable day")
    
    print()
    print("=" * 70)
else:
    print("[!] No trades were successfully verified")
    print("    Check NWS reports manually if needed")

