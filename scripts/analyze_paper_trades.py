"""
Analyze Paper Trading Results - Complete Study Analysis

Run this after collecting N days of paper trade data to analyze results.

This is your "study analysis" - did the forward test validate the backtest?
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime

print("=" * 70)
print("PAPER TRADING ANALYSIS - FORWARD PERFORMANCE TEST RESULTS")
print("=" * 70)
print()

# Load paper trade log
logs_dir = project_root / "logs"
paper_trade_log = logs_dir / "paper_trades.csv"

if not paper_trade_log.exists():
    print("[X] No paper trade log found!")
    print(f"    Expected: {paper_trade_log}")
    sys.exit(1)

df = pd.read_csv(paper_trade_log)

# Filter to verified trades only
verified = df[df['outcome'] != 'PENDING'].copy()

if len(verified) == 0:
    print("[!] No verified trades yet")
    print("    Run paper trades for a few days first")
    sys.exit(0)

print(f"Analyzing {len(verified)} verified trades")
print()

# Calculate metrics
wins = (verified['outcome'] == 'WIN').sum()
losses = (verified['outcome'] == 'LOSS').sum()
win_rate = wins / len(verified)

total_invested = verified['cost'].sum()
total_pnl = verified['pnl'].sum()
returns = (total_pnl / total_invested) * 100 if total_invested > 0 else 0

avg_edge = verified['edge'].mean()
avg_win = verified[verified['outcome'] == 'WIN']['pnl'].mean() if wins > 0 else 0
avg_loss = verified[verified['outcome'] == 'LOSS']['pnl'].mean() if losses > 0 else 0
win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0

# By city
print("=" * 70)
print("FORWARD PERFORMANCE TEST RESULTS")
print("=" * 70)
print()

print("Overall Performance:")
print(f"  Total Trades:    {len(verified)}")
print(f"  Wins:            {wins} ({win_rate*100:.1f}%)")
print(f"  Losses:          {losses} ({(1-win_rate)*100:.1f}%)")
print()
print(f"  Total Invested:  ${total_invested:.2f}")
print(f"  Total P&L:       ${total_pnl:+.2f}")
print(f"  Return:          {returns:+.1f}%")
print()
print(f"  Average Edge:    {avg_edge*100:.1f}%")
print(f"  Average Win:     ${avg_win:.2f}")
print(f"  Average Loss:    ${avg_loss:.2f}")
print(f"  Win/Loss Ratio:  {win_loss_ratio:.2f}x")
print()

# By city
print("Performance by City:")
for city in sorted(verified['city'].unique()):
    city_df = verified[verified['city'] == city]
    city_wins = (city_df['outcome'] == 'WIN').sum()
    city_wr = city_wins / len(city_df) if len(city_df) > 0 else 0
    city_pnl = city_df['pnl'].sum()
    print(f"  {city}: {len(city_df):3d} trades, {city_wins:3d}/{len(city_df):3d} wins ({city_wr*100:5.1f}%), ${city_pnl:+9.2f}")

print()

# Confidence analysis
print("Performance by Confidence Level:")
high_conf = verified[verified['ensemble_spread'] < 1.0]
med_conf = verified[(verified['ensemble_spread'] >= 1.0) & (verified['ensemble_spread'] < 1.5)]
if len(high_conf) > 0:
    hc_wr = (high_conf['outcome'] == 'WIN').sum() / len(high_conf)
    print(f"  High Confidence (spread <1.0F): {len(high_conf):3d} trades, {hc_wr*100:.1f}% win rate")
if len(med_conf) > 0:
    mc_wr = (med_conf['outcome'] == 'WIN').sum() / len(med_conf)
    print(f"  Med Confidence (spread 1.0-1.5F): {len(med_conf):3d} trades, {mc_wr*100:.1f}% win rate")

print()
print("=" * 70)
print()

# Compare to backtest
print("=" * 70)
print("COMPARISON: BACKTEST vs LIVE")
print("=" * 70)
print()

BACKTEST_WIN_RATE = 0.607
BACKTEST_RETURN = 3261.5
BACKTEST_SHARPE = 10.66

print(f"Backtest (2024 historical):")
print(f"  Win Rate:  {BACKTEST_WIN_RATE*100:.1f}%")
print(f"  Return:    +{BACKTEST_RETURN:.1f}%")
print(f"  Sharpe:    {BACKTEST_SHARPE:.2f}")
print()

print(f"Live Forward Test (paper trades):")
print(f"  Win Rate:  {win_rate*100:.1f}%")
print(f"  Return:    {returns:+.1f}%")
print()

# Statistical significance
from scipy import stats

# Binomial test - is win rate significantly > 50%?
if len(verified) >= 10:
    p_value = stats.binom_test(wins, len(verified), p=0.5, alternative='greater')
    print(f"Statistical Test (Win Rate > 50%):")
    print(f"  p-value: {p_value:.4f}")
    if p_value < 0.05:
        print(f"  Result: SIGNIFICANT (p < 0.05)")
        print(f"         Win rate is statistically significant!")
    else:
        print(f"  Result: Not significant yet (need more data)")
    print()

print("=" * 70)
print()

# Success criteria
print("=" * 70)
print("SUCCESS CRITERIA EVALUATION")
print("=" * 70)
print()

criteria_met = []

print("Primary Endpoint: Win Rate > 55%")
if win_rate > 0.55:
    print(f"  [OK] PASS - Win rate is {win_rate*100:.1f}%")
    criteria_met.append(True)
else:
    print(f"  [X] FAIL - Win rate is {win_rate*100:.1f}% (need >55%)")
    criteria_met.append(False)
print()

print("Secondary Endpoint: Positive P&L")
if total_pnl > 0:
    print(f"  [OK] PASS - Total P&L is ${total_pnl:+.2f}")
    criteria_met.append(True)
else:
    print(f"  [X] FAIL - Total P&L is ${total_pnl:+.2f}")
    criteria_met.append(False)
print()

print("Safety Endpoint: Win Rate > 40%")
if win_rate > 0.40:
    print(f"  [OK] PASS - No severe degradation")
    criteria_met.append(True)
else:
    print(f"  [X] FAIL - Severe model degradation detected!")
    criteria_met.append(False)
print()

# Days of data
unique_dates = verified['date'].nunique()
print(f"Data Collection Period: {unique_dates} days")
if unique_dates < 7:
    print("  [!] NOTE: Less than 1 week of data")
    print("      Recommend collecting at least 2-4 weeks for confidence")
elif unique_dates < 14:
    print("  [~] CAUTION: Less than 2 weeks of data")
    print("      Results are preliminary")
else:
    print("  [OK] Sufficient data collected (2+ weeks)")

print()
print("=" * 70)
print()

# Final verdict
if all(criteria_met) and unique_dates >= 7:
    print("=" * 70)
    print("FINAL VERDICT: STRATEGY VALIDATED")
    print("=" * 70)
    print()
    print("[OK] The forward performance test CONFIRMS the backtest results!")
    print()
    print("All success criteria met:")
    print(f"  - Win rate: {win_rate*100:.1f}% (>55%)")
    print(f"  - P&L: ${total_pnl:+.2f} (>$0)")
    print(f"  - Data: {unique_dates} days collected")
    print()
    print("RECOMMENDATION: READY FOR LIVE TRADING")
    print()
    print("Start with:")
    print("  - $5-10 per trade")
    print("  - Best performing cities")
    print("  - Continue monitoring daily")
    print()
    
elif any(criteria_met):
    print("=" * 70)
    print("FINAL VERDICT: MIXED RESULTS")
    print("=" * 70)
    print()
    print("[~] Some criteria met, but not all")
    print()
    if unique_dates < 14:
        print("RECOMMENDATION: Continue paper trading")
        print("  - Collect more data (target: 2-4 weeks)")
        print("  - Re-evaluate after more trades")
    else:
        print("RECOMMENDATION: Strategy needs improvement")
        print("  - Review trades that lost")
        print("  - Consider adjusting confidence thresholds")
        print("  - May need to refine model")
    print()
    
else:
    print("=" * 70)
    print("FINAL VERDICT: STRATEGY FAILED VALIDATION")
    print("=" * 70)
    print()
    print("[X] Forward test does NOT confirm backtest")
    print()
    print("CRITICAL: Do NOT trade live")
    print()
    print("Possible causes:")
    print("  - Backtest overfit to historical data")
    print("  - Market conditions changed")
    print("  - Model assumptions incorrect")
    print()
    print("Next steps:")
    print("  - Review why model failed")
    print("  - Analyze incorrect predictions")
    print("  - Rebuild with different approach")
    print()

print("=" * 70)

