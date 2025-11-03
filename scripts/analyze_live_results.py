"""
Live Results Analysis

After 30 days of collection, this analyzes:
1. Actual win rate vs predicted (60.3%)
2. Actual P&L vs backtest (+3,050%)
3. Did alpha features predict accuracy?
4. Is the strategy validated for live trading?

This is the final verdict on the hypothesis.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

LIVE_VALIDATION_LOG = PROJECT_ROOT / "logs" / "live_validation.csv"

print("=" * 70)
print("LIVE RESULTS ANALYSIS - THE VERDICT")
print("=" * 70)
print()

# Load data
if not LIVE_VALIDATION_LOG.exists():
    print("[X] No validation log found.")
    print("    Run live_data_collector.py daily for 30+ days first.")
    sys.exit(1)

df = pd.read_csv(LIVE_VALIDATION_LOG)

# Filter to settled trades only
settled = df[df['outcome'].isin(['WIN', 'LOSS'])].copy()

if len(settled) == 0:
    print("[!] No settled trades yet.")
    print("    Run settle_live_data.py to update outcomes.")
    sys.exit(0)

print(f"Total predictions logged: {len(df)}")
print(f"Settled trades: {len(settled)}")
print(f"Pending trades: {len(df[df['outcome'] == 'PENDING'])}")
print()

# Convert P&L to numeric
settled['pnl'] = pd.to_numeric(settled['pnl'], errors='coerce')

# Calculate metrics
wins = len(settled[settled['outcome'] == 'WIN'])
losses = len(settled[settled['outcome'] == 'LOSS'])
win_rate = wins / len(settled) if len(settled) > 0 else 0
total_pnl = settled['pnl'].sum()

print("=" * 70)
print("OVERALL PERFORMANCE")
print("=" * 70)
print()
print(f"Win Rate:   {win_rate:.1%}  (Predicted: 60.3%)")
print(f"Wins:       {wins}")
print(f"Losses:     {losses}")
print(f"Total P&L:  ${total_pnl:.2f}")
print()

# Compare to backtest hypothesis
expected_win_rate = 0.603
if abs(win_rate - expected_win_rate) < 0.05:
    print("[OK] Win rate within 5% of backtest prediction")
    win_rate_validated = True
else:
    print(f"[!] Win rate differs by {abs(win_rate - expected_win_rate)*100:.1f}%")
    win_rate_validated = False

print()

# Analyze alpha features
print("=" * 70)
print("ALPHA FEATURE VALIDATION")
print("=" * 70)
print()

# Did ensemble_spread predict confidence?
print("Does ensemble_spread < 1.5 predict higher accuracy?")
print()

high_conf = settled[settled['ensemble_spread'] < 1.5]
low_conf = settled[settled['ensemble_spread'] >= 1.5]

if len(high_conf) > 0:
    high_conf_win_rate = len(high_conf[high_conf['outcome'] == 'WIN']) / len(high_conf)
    print(f"  High confidence (spread <1.5): {len(high_conf)} trades, {high_conf_win_rate:.1%} win rate")
else:
    print(f"  High confidence (spread <1.5): 0 trades")

if len(low_conf) > 0:
    low_conf_win_rate = len(low_conf[low_conf['outcome'] == 'WIN']) / len(low_conf)
    print(f"  Low confidence (spread >=1.5): {len(low_conf)} trades, {low_conf_win_rate:.1%} win rate")
else:
    print(f"  Low confidence (spread >=1.5): 0 trades")

print()

# Did model_disagreement matter?
print("Does model_disagreement < 1.0 predict higher accuracy?")
print()

agree = settled[settled['model_disagreement'] < 1.0]
disagree = settled[settled['model_disagreement'] >= 1.0]

if len(agree) > 0:
    agree_win_rate = len(agree[agree['outcome'] == 'WIN']) / len(agree)
    print(f"  Models agree (<1.0): {len(agree)} trades, {agree_win_rate:.1%} win rate")
else:
    print(f"  Models agree (<1.0): 0 trades")

if len(disagree) > 0:
    disagree_win_rate = len(disagree[disagree['outcome'] == 'WIN']) / len(disagree)
    print(f"  Models disagree (>=1.0): {len(disagree)} trades, {disagree_win_rate:.1%} win rate")
else:
    print(f"  Models disagree (>=1.0): 0 trades")

print()

# Did nws_vs_ensemble predict inefficiency?
print("Does nws_vs_ensemble > 1.5 predict higher edge?")
print()

inefficient = settled[settled['nws_vs_ensemble'] > 1.5]
efficient = settled[settled['nws_vs_ensemble'] <= 1.5]

if len(inefficient) > 0:
    ineff_pnl = inefficient['pnl'].sum()
    ineff_win_rate = len(inefficient[inefficient['outcome'] == 'WIN']) / len(inefficient)
    print(f"  Inefficient (>1.5): {len(inefficient)} trades, {ineff_win_rate:.1%} win rate, ${ineff_pnl:.2f} P&L")
else:
    print(f"  Inefficient (>1.5): 0 trades")

if len(efficient) > 0:
    eff_pnl = efficient['pnl'].sum()
    eff_win_rate = len(efficient[efficient['outcome'] == 'WIN']) / len(efficient)
    print(f"  Efficient (<=1.5): {len(efficient)} trades, {eff_win_rate:.1%} win rate, ${eff_pnl:.2f} P&L")
else:
    print(f"  Efficient (<=1.5): 0 trades")

print()

# Analyze trades that met ALL conditions
print("=" * 70)
print("SELECTIVE TRADES (ALL CONDITIONS MET)")
print("=" * 70)
print()

selective = settled[
    (settled['ensemble_spread'] < 1.5) &
    (settled['model_disagreement'] < 1.0) &
    (settled['nws_vs_ensemble'] > 1.5)
]

if len(selective) > 0:
    selective_wins = len(selective[selective['outcome'] == 'WIN'])
    selective_win_rate = selective_wins / len(selective)
    selective_pnl = selective['pnl'].sum()
    
    print(f"Trades meeting all conditions: {len(selective)}")
    print(f"Win rate: {selective_win_rate:.1%} (Predicted: 60.7%)")
    print(f"Total P&L: ${selective_pnl:.2f}")
    print()
    
    if abs(selective_win_rate - 0.607) < 0.10:
        print("[OK] Selective win rate matches backtest (within 10%)")
        selective_validated = True
    else:
        print(f"[!] Selective win rate differs by {abs(selective_win_rate - 0.607)*100:.1f}%")
        selective_validated = False
else:
    print("No trades met all conditions yet.")
    selective_validated = False

print()

# Statistical significance
print("=" * 70)
print("STATISTICAL SIGNIFICANCE")
print("=" * 70)
print()

# Binomial test: Is win rate significantly different from 50%?
from scipy import stats

if len(settled) >= 20:
    p_value = stats.binom_test(wins, len(settled), 0.5, alternative='greater')
    print(f"Binomial test (H0: win_rate = 50%):")
    print(f"  p-value: {p_value:.4f}")
    
    if p_value < 0.05:
        print(f"  [OK] Win rate is statistically significant (p < 0.05)")
        stat_sig = True
    else:
        print(f"  [!] Win rate not yet statistically significant")
        stat_sig = False
else:
    print(f"Need 20+ trades for statistical test (have {len(settled)})")
    stat_sig = False

print()

# Final verdict
print("=" * 70)
print("FINAL VERDICT")
print("=" * 70)
print()

criteria = {
    'Win rate close to 60.3%': win_rate_validated if len(settled) >= 20 else None,
    'Positive P&L': total_pnl > 0,
    'Selective trades validated': selective_validated if len(selective) >= 10 else None,
    'Statistically significant': stat_sig if len(settled) >= 20 else None,
}

passed = sum(1 for v in criteria.values() if v is True)
total = sum(1 for v in criteria.values() if v is not None)

for criterion, result in criteria.items():
    if result is True:
        print(f"[OK] {criterion}")
    elif result is False:
        print(f"[X] {criterion}")
    else:
        print(f"[?] {criterion} (insufficient data)")

print()

if total == 0:
    print("VERDICT: Insufficient data for validation")
    print(f"  Need at least 20-30 settled trades")
    print(f"  Currently have: {len(settled)}")
    print()
    print(f"  Keep running live_data_collector.py daily")
elif passed / total >= 0.75:
    print("VERDICT: STRATEGY VALIDATED FOR LIVE TRADING")
    print()
    print(f"  {passed}/{total} criteria passed")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  P&L: ${total_pnl:.2f}")
    print()
    print("  The +3,050% backtest hypothesis is SUPPORTED by live data.")
    print("  Proceed to live trading with confidence.")
else:
    print("VERDICT: STRATEGY NOT VALIDATED")
    print()
    print(f"  {passed}/{total} criteria passed")
    print(f"  Win rate: {win_rate:.1%}")
    print(f"  P&L: ${total_pnl:.2f}")
    print()
    print("  The +3,050% backtest hypothesis is NOT supported by live data.")
    print("  DO NOT proceed to live trading.")
    print("  Review model assumptions and feature engineering.")

print()
print("=" * 70)

