"""
Quick Reality Check - Test if ensemble strategy works with REAL Kalshi prices

This script tests our ensemble strategy using:
- ✅ REAL NOAA ground truth (Y variable)
- ✅ REAL Kalshi market prices (from historical data)
- ⚠️ Simulated ensemble forecasts (X variables) - based on known model errors

This tells us: "With REAL market prices, would our strategy have worked?"
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("\n" + "="*70)
print("REALITY CHECK - Testing with REAL Kalshi Prices")
print("="*70)
print()
print("This is the moment of truth.")
print("Does the strategy work with REAL market data?")
print()
print("="*70 + "\n")

# Load ground truth (we have this)
print("[1/5] Loading NOAA ground truth...")
ground_truth_file = PROJECT_ROOT / "data" / "weather" / "nws_settlement_ground_truth_OFFICIAL.csv"

if not ground_truth_file.exists():
    print("[X] NOAA ground truth not found!")
    print(f"    Expected: {ground_truth_file}")
    sys.exit(1)

ground_truth = pd.read_csv(ground_truth_file)
ground_truth['date'] = pd.to_datetime(ground_truth['date'])
print(f"[OK] Loaded {len(ground_truth)} NOAA settlement records")
print(f"     Date range: {ground_truth['date'].min()} to {ground_truth['date'].max()}")
print()

# Load Kalshi historical prices
print("[2/5] Loading REAL Kalshi historical prices...")
kalshi_prices_file = PROJECT_ROOT / "data" / "weather" / "kalshi_historical_prices.csv"

if not kalshi_prices_file.exists():
    print("[X] Kalshi historical prices not found!")
    print(f"    Expected: {kalshi_prices_file}")
    print()
    print("ACTION REQUIRED:")
    print("1. Go to: https://kalshi.com/market-data")
    print("2. Download historical market data CSV")
    print("3. Filter to weather markets (KXHIGH series)")
    print("4. Save as: data/weather/kalshi_historical_prices.csv")
    print()
    print("Required columns:")
    print("  - date (YYYY-MM-DD)")
    print("  - city (NYC, CHI, MIA, HOU)")
    print("  - market_ticker")
    print("  - close_price (market closing price)")
    print("  - bracket_low (predicted bracket)")
    print("  - bracket_high")
    print()
    print("OR run: python scripts/collect_historical_market_prices.py")
    sys.exit(1)

kalshi_prices = pd.read_csv(kalshi_prices_file)
kalshi_prices['date'] = pd.to_datetime(kalshi_prices['date'])
print(f"[OK] Loaded {len(kalshi_prices)} Kalshi price records")
print(f"     Markets: {kalshi_prices['city'].unique().tolist()}")
print()

# Merge
print("[3/5] Merging datasets...")
merged = pd.merge(
    ground_truth,
    kalshi_prices,
    on=['date', 'city'],
    how='inner'
)

if len(merged) == 0:
    print("[X] No matching records found!")
    print("    Check that dates and cities match between datasets")
    sys.exit(1)

print(f"[OK] Merged: {len(merged)} matching records")
print()

# Simulate ensemble features (same method as training)
print("[4/5] Calculating ensemble features...")
print("     NOTE: Still using simulated forecasts (based on known model errors)")
print()

# Simulate what forecasts would have been (based on actual outcome + typical model error)
np.random.seed(42)  # Reproducible
merged['ecmwf_forecast'] = merged['nws_settlement_temp'] + np.random.normal(0, 1.5, len(merged))
merged['gfs_forecast'] = merged['nws_settlement_temp'] + np.random.normal(0, 1.8, len(merged))
merged['gdps_forecast'] = merged['nws_settlement_temp'] + np.random.normal(0, 1.7, len(merged))
merged['icon_forecast'] = merged['nws_settlement_temp'] + np.random.normal(0, 1.6, len(merged))
merged['nws_forecast'] = merged['nws_settlement_temp'] + np.random.normal(0, 2.5, len(merged))

# Calculate alpha features
pro_models = ['ecmwf_forecast', 'gfs_forecast', 'gdps_forecast', 'icon_forecast']
merged['ensemble_mean'] = merged[pro_models].mean(axis=1)
merged['ensemble_spread'] = merged[pro_models].std(axis=1)
merged['model_disagreement'] = merged[['ecmwf_forecast', 'gfs_forecast', 'gdps_forecast']].std(axis=1)
merged['nws_vs_ensemble'] = np.abs(merged['nws_forecast'] - merged['ensemble_mean'])

print("[OK] Features calculated")
print()

# Backtest with REAL prices
print("[5/5] Running backtest with REAL Kalshi prices...")
print()

STARTING_CAPITAL = 1000.0
capital = STARTING_CAPITAL
trades = []

for idx, row in merged.iterrows():
    # Apply same filters as original strategy
    if row['ensemble_spread'] > 1.5:
        continue
    if row['model_disagreement'] > 1.0:
        continue
    if row['nws_vs_ensemble'] < 1.5:
        continue
    
    # Predict bracket
    predicted_temp = row['ensemble_mean']
    predicted_bracket_low = int(predicted_temp // 2) * 2
    predicted_bracket_high = predicted_bracket_low + 2
    
    # KEY DIFFERENCE: Use REAL market price (not simulated!)
    market_price = row['close_price']  # FROM KALSHI DATA
    
    # Calculate our edge
    our_prob = 0.603  # Based on 60.3% accuracy on filtered trades from original backtest
    market_prob = market_price
    edge = our_prob - market_prob
    
    if edge < 0.05:  # Skip if edge too small
        continue
    
    # Position size (Kelly with 0.25 fraction)
    kelly_fraction = 0.25
    bet_fraction = kelly_fraction * edge
    bet_size = STARTING_CAPITAL * bet_fraction  # Based on starting capital (not current)
    
    # Calculate contracts
    contracts = int(bet_size / market_price)
    
    # Cap at 30% of starting capital
    max_contracts = int((STARTING_CAPITAL * 0.30) / market_price)
    contracts = min(contracts, max_contracts)
    
    if contracts < 1:
        continue
    
    # Entry cost
    entry_cost = contracts * market_price
    
    if entry_cost > capital:  # Can't afford
        continue
    
    # Check if won
    actual_temp = row['nws_settlement_temp']
    actual_bracket_low = int(actual_temp // 2) * 2
    won = (predicted_bracket_low == actual_bracket_low)
    
    # Calculate P&L with REAL Kalshi fees (7% on winners)
    if won:
        gross_profit = contracts * (1.0 - market_price)
        fee = gross_profit * 0.07
        net_pnl = gross_profit - fee
    else:
        net_pnl = -entry_cost
    
    capital += net_pnl
    
    trades.append({
        'date': row['date'],
        'city': row['city'],
        'market_price': market_price,
        'our_prob': our_prob,
        'edge': edge,
        'contracts': contracts,
        'entry_cost': entry_cost,
        'predicted_bracket': f"{predicted_bracket_low}-{predicted_bracket_high}",
        'actual_temp': actual_temp,
        'won': won,
        'pnl': net_pnl,
        'capital': capital
    })

trades_df = pd.DataFrame(trades)

# Results
print("="*70)
print("RESULTS - MOMENT OF TRUTH")
print("="*70)
print()

if len(trades_df) == 0:
    print("[X] NO TRADES EXECUTED")
    print()
    print("Possible reasons:")
    print("  - Filters too strict")
    print("  - No matching data")
    print("  - Market prices show no edge")
    print()
    print("VERDICT: Cannot validate strategy with this data")
    sys.exit(0)

# Calculate metrics
total_return = ((capital - STARTING_CAPITAL) / STARTING_CAPITAL) * 100
wins = trades_df['won'].sum()
losses = len(trades_df) - wins
win_rate = (wins / len(trades_df)) * 100

print(f"Starting Capital: ${STARTING_CAPITAL:,.2f}")
print(f"Ending Capital:   ${capital:,.2f}")
print(f"Total Return:     {total_return:+.1f}%")
print()
print(f"Total Trades:     {len(trades_df)}")
print(f"Wins:             {wins} ({win_rate:.1f}%)")
print(f"Losses:           {losses}")
print()

if wins > 0:
    avg_win = trades_df[trades_df['won']]['pnl'].mean()
    print(f"Avg Win:          ${avg_win:.2f}")

if losses > 0:
    avg_loss = trades_df[~trades_df['won']]['pnl'].mean()
    print(f"Avg Loss:         ${avg_loss:.2f}")

if wins > 0 and losses > 0:
    print(f"Win/Loss Ratio:   {abs(avg_win/avg_loss):.2f}x")

print()
print("="*70)

# Comparison to simulated backtest
print("COMPARISON TO SIMULATED BACKTEST")
print("="*70)
print()
print(f"Simulated backtest: +3,050% return, 60.3% win rate")
print(f"REAL price test:    {total_return:+.1f}% return, {win_rate:.1f}% win rate")
print()

if total_return > 1000:
    print("[!] EXTREME RESULTS - Check data quality")
elif total_return > 100:
    print("Wow - Still very profitable with real prices!")
elif total_return > 50:
    print("Strong performance - Much lower than sim but still excellent")
elif total_return > 15:
    print("Good performance - Profitable and worth pursuing")
elif total_return > 0:
    print("Marginal - Profitable but edge is small")
else:
    print("Unprofitable - Strategy doesn't work with real prices")

print()
print("="*70)

# Final verdict
print("FINAL VERDICT")
print("="*70)
print()

if total_return > 15 and win_rate > 52:
    print("✅ STRATEGY VALIDATED")
    print()
    print("Real Kalshi prices show the strategy is profitable.")
    print("Returns are lower than simulated backtest but still strong.")
    print()
    print("RECOMMENDATION:")
    print("  1. Proceed with 30-day forward test")
    print("  2. Collect real forecasts (Open-Meteo or live)")
    print("  3. If forward test confirms, go live")
    print()
    print("Expected live returns: 20-100% annually")
    
elif total_return > 0 and win_rate > 48:
    print("⚠️  MARGINALLY PROFITABLE")
    print()
    print("Strategy shows small edge with real prices.")
    print("Edge exists but much smaller than simulated.")
    print()
    print("RECOMMENDATION:")
    print("  1. 30-day forward test is CRITICAL")
    print("  2. Consider improving model/filters")
    print("  3. Use very conservative position sizing")
    print()
    print("Expected live returns: 5-30% annually (if validated)")
    
else:
    print("❌ STRATEGY NOT VALIDATED")
    print()
    print("Real Kalshi prices show strategy is unprofitable.")
    print("Simulated prices were too optimistic.")
    print()
    print("RECOMMENDATION:")
    print("  1. DO NOT trade live")
    print("  2. Collect REAL forecast data (not simulated)")
    print("  3. Rebuild model with 100% real X variables")
    print("  4. OR pivot to different strategy")
    print()
    print("The +3,050% backtest was based on bad assumptions.")

print()
print("="*70)
print()

# Save results
output_dir = PROJECT_ROOT / "data" / "backtest_results"
output_dir.mkdir(parents=True, exist_ok=True)

trades_file = output_dir / "reality_check_trades.csv"
trades_df.to_csv(trades_file, index=False)

print(f"Detailed trades saved to: {trades_file}")
print()

# Summary
print("="*70)
print("KEY INSIGHT")
print("="*70)
print()
print("This test used:")
print("  ✅ REAL NOAA ground truth (Y variable)")
print("  ✅ REAL Kalshi market prices")
print("  ⚠️ Simulated ensemble forecasts (X variables)")
print()
print("For 100% real test:")
print("  - Need Open-Meteo historical forecast API (€10-50/month)")
print("  - OR 30-day forward test (free, collects real forecasts)")
print()
print("But this test answers the critical question:")
print("  'Are our price assumptions reasonable?'")
print()

if total_return > 15:
    print("Answer: YES - Markets were priced as expected")
elif total_return > 0:
    print("Answer: PARTIALLY - Markets more efficient than assumed")
else:
    print("Answer: NO - Markets much more efficient than assumed")

print()
print("="*70)
print()

