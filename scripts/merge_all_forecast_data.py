"""
Merge All Forecast Data Sources

This combines:
1. NOAA ground truth (Y variable) - 100% REAL
2. Kalshi internal forecasts (X variable) - 100% REAL
3. Open-Meteo forecasts (X variable) - 100% REAL (if available)

Output: A single dataset for the "Real Data" backtest
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 70)
print("MERGE ALL FORECAST DATA")
print("=" * 70)
print()

# Load NOAA ground truth (Y)
noaa_file = PROJECT_ROOT / "data" / "weather" / "nws_settlement_ground_truth_OFFICIAL.csv"

if not noaa_file.exists():
    print("[X] NOAA ground truth not found.")
    sys.exit(1)

df_noaa = pd.read_csv(noaa_file)
df_noaa['date'] = pd.to_datetime(df_noaa['date'])

print(f"[1/4] Loaded NOAA ground truth: {len(df_noaa)} records")

# Load Kalshi forecasts (X)
kalshi_file = PROJECT_ROOT / "data" / "weather" / "kalshi_forecast_history.csv"

if kalshi_file.exists():
    df_kalshi = pd.read_csv(kalshi_file)
    df_kalshi['date'] = pd.to_datetime(df_kalshi['date'])
    print(f"[2/4] Loaded Kalshi forecasts: {len(df_kalshi)} records")
else:
    print(f"[2/4] Kalshi forecasts not found - skipping")
    df_kalshi = None

# Load Open-Meteo forecasts (X)
open_meteo_file = PROJECT_ROOT / "data" / "weather" / "open_meteo_historical_forecasts.csv"

if open_meteo_file.exists():
    df_open_meteo = pd.read_csv(open_meteo_file)
    df_open_meteo['date'] = pd.to_datetime(df_open_meteo['date'])
    print(f"[3/4] Loaded Open-Meteo forecasts: {len(df_open_meteo)} records")
else:
    print(f"[3/4] Open-Meteo forecasts not found - skipping")
    df_open_meteo = None

# Merge
print()
print("[4/4] Merging datasets...")
print()

merged = df_noaa.copy()

# Merge Kalshi
if df_kalshi is not None:
    merged = merged.merge(
        df_kalshi[['date', 'city', 'kalshi_forecast_temp']],
        on=['date', 'city'],
        how='left'
    )
    print(f"      After Kalshi merge: {len(merged)} rows, {merged['kalshi_forecast_temp'].notna().sum()} with Kalshi data")

# Merge Open-Meteo
if df_open_meteo is not None:
    merged = merged.merge(
        df_open_meteo[['date', 'city', 'open_meteo_forecast_temp']],
        on=['date', 'city'],
        how='left'
    )
    print(f"      After Open-Meteo merge: {len(merged)} rows, {merged['open_meteo_forecast_temp'].notna().sum()} with Open-Meteo data")

print()

# Calculate alpha features
print("Calculating alpha features...")
print()

# If we have both Kalshi and Open-Meteo, calculate disagreement
if 'kalshi_forecast_temp' in merged.columns and 'open_meteo_forecast_temp' in merged.columns:
    merged['model_disagreement'] = abs(merged['kalshi_forecast_temp'] - merged['open_meteo_forecast_temp'])
    print("  [OK] model_disagreement (abs difference between Kalshi and Open-Meteo)")

# If we have Kalshi, calculate error vs. actual
if 'kalshi_forecast_temp' in merged.columns:
    merged['kalshi_error'] = abs(merged['kalshi_forecast_temp'] - merged['nws_settlement_temp'])
    print("  [OK] kalshi_error (Kalshi forecast error)")

# If we have Open-Meteo, calculate error vs. actual
if 'open_meteo_forecast_temp' in merged.columns:
    merged['open_meteo_error'] = abs(merged['open_meteo_forecast_temp'] - merged['nws_settlement_temp'])
    print("  [OK] open_meteo_error (Open-Meteo forecast error)")

# Determine bracket (Kalshi uses 2F brackets)
merged['actual_bracket_low'] = (merged['nws_settlement_temp'] // 2) * 2
merged['actual_bracket_high'] = merged['actual_bracket_low'] + 2

if 'kalshi_forecast_temp' in merged.columns:
    merged['kalshi_predicted_bracket_low'] = (merged['kalshi_forecast_temp'] // 2) * 2
    merged['kalshi_correct'] = (merged['kalshi_predicted_bracket_low'] == merged['actual_bracket_low']).astype(int)
    print("  [OK] kalshi_correct (1 if Kalshi predicted correct bracket)")

if 'open_meteo_forecast_temp' in merged.columns:
    merged['open_meteo_predicted_bracket_low'] = (merged['open_meteo_forecast_temp'] // 2) * 2
    merged['open_meteo_correct'] = (merged['open_meteo_predicted_bracket_low'] == merged['actual_bracket_low']).astype(int)
    print("  [OK] open_meteo_correct (1 if Open-Meteo predicted correct bracket)")

print()

# Save merged dataset
output_file = PROJECT_ROOT / "data" / "weather" / "merged_real_forecast_data.csv"
merged.to_csv(output_file, index=False)

print(f"Saved to: {output_file}")
print()

# Summary statistics
print("=" * 70)
print("MERGED DATASET SUMMARY")
print("=" * 70)
print()
print(f"Total records: {len(merged)}")
print(f"Date range: {merged['date'].min()} to {merged['date'].max()}")
print(f"Cities: {merged['city'].nunique()}")
print()

print("Data completeness:")
print(f"  NOAA ground truth: {len(merged)} (100%)")

if 'kalshi_forecast_temp' in merged.columns:
    kalshi_pct = merged['kalshi_forecast_temp'].notna().sum() / len(merged) * 100
    print(f"  Kalshi forecasts: {merged['kalshi_forecast_temp'].notna().sum()} ({kalshi_pct:.1f}%)")

if 'open_meteo_forecast_temp' in merged.columns:
    om_pct = merged['open_meteo_forecast_temp'].notna().sum() / len(merged) * 100
    print(f"  Open-Meteo forecasts: {merged['open_meteo_forecast_temp'].notna().sum()} ({om_pct:.1f}%)")

print()

# Model performance comparison (if we have both)
if 'kalshi_correct' in merged.columns and 'open_meteo_correct' in merged.columns:
    print("Model accuracy comparison (exact bracket):")
    print()
    
    kalshi_acc = merged['kalshi_correct'].mean() * 100
    om_acc = merged['open_meteo_correct'].mean() * 100
    
    print(f"  Kalshi:       {kalshi_acc:.1f}%")
    print(f"  Open-Meteo:   {om_acc:.1f}%")
    print()
    
    # Where do they disagree?
    disagreement = merged[merged['model_disagreement'] > 2.0]
    if len(disagreement) > 0:
        print(f"High disagreement (>2F): {len(disagreement)} cases")
        kalshi_wins = disagreement['kalshi_correct'].sum()
        om_wins = disagreement['open_meteo_correct'].sum()
        print(f"  Kalshi correct: {kalshi_wins} ({kalshi_wins/len(disagreement)*100:.1f}%)")
        print(f"  Open-Meteo correct: {om_wins} ({om_wins/len(disagreement)*100:.1f}%)")
        print()
        print("  -> This is the ALPHA: Trade when models disagree and we can identify the winner")

elif 'kalshi_correct' in merged.columns:
    print("Kalshi forecast accuracy (exact bracket):")
    kalshi_acc = merged['kalshi_correct'].mean() * 100
    print(f"  {kalshi_acc:.1f}%")
    print()
    print("  -> Alpha opportunity: Can WE beat Kalshi's model?")

elif 'open_meteo_correct' in merged.columns:
    print("Open-Meteo forecast accuracy (exact bracket):")
    om_acc = merged['open_meteo_correct'].mean() * 100
    print(f"  {om_acc:.1f}%")

print()
print("=" * 70)
print("NEXT STEPS")
print("=" * 70)
print()
print("1. Analyze model disagreement patterns")
print("2. Train ML model to predict WHO will be right (Kalshi or Open-Meteo)")
print("3. Re-run backtest with REAL forecast data")
print("4. Compare to simulated backtest (+3,050%)")
print()
print("The new backtest will be 90% REAL data (only market prices simulated)")
print("=" * 70)

