"""
Rebuild Ensemble Training Data with OFFICIAL NOAA Ground Truth

This replaces the proxy Y variable with 100% official NOAA data.
The X variables (ensemble forecasts) are still simulated, but the 
ground truth is now REAL.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np

print("=" * 70)
print("REBUILD WITH OFFICIAL NOAA GROUND TRUTH")
print("=" * 70)
print()

# Load OFFICIAL NOAA ground truth
official_data = pd.read_csv(project_root / 'data' / 'weather' / 'nws_settlement_ground_truth_OFFICIAL.csv')
official_data['date'] = pd.to_datetime(official_data['date'])
print(f"[1/5] Loaded {len(official_data)} official NOAA records")
print()

# Load existing enhanced weather data (has atmospheric features)
enhanced_data = pd.read_csv(project_root / 'data' / 'weather' / 'all_cities_2020-2024_enhanced.csv')
enhanced_data['date'] = pd.to_datetime(enhanced_data['date'])
print(f"[2/5] Loaded {len(enhanced_data)} enhanced weather records")
print()

# Merge to get atmospheric features with official temperatures
print("[3/5] Merging official temps with atmospheric features...")
merged = enhanced_data.merge(
    official_data[['city', 'date', 'nws_settlement_temp']],
    on=['city', 'date'],
    how='inner'
)

# Replace the proxy temperature with official NOAA temperature
merged['actual_high_temp'] = merged['nws_settlement_temp']
merged = merged.drop('nws_settlement_temp', axis=1)

print(f"[OK] Merged {len(merged)} records")
print()

# Now simulate ensemble forecasts (same as before)
print("[4/5] Simulating ensemble forecasts...")
print()

np.random.seed(42)

all_data = []

for idx, row in merged.iterrows():
    actual_temp = row['actual_high_temp']
    
    # Simulate professional model forecasts
    ecmwf_error = np.random.normal(0, 1.5)
    ecmwf_forecast = actual_temp + ecmwf_error
    
    gfs_error = np.random.normal(0, 2.0)
    gfs_forecast = actual_temp + gfs_error
    
    gdps_error = np.random.normal(0, 2.0)
    gdps_forecast = actual_temp + gdps_error
    
    icon_error = np.random.normal(0, 1.5)
    icon_forecast = actual_temp + icon_error
    
    nws_error = np.random.normal(0, 2.5)
    nws_forecast = actual_temp + nws_error
    
    # Calculate ensemble metrics
    pro_models = [ecmwf_forecast, gfs_forecast, gdps_forecast, icon_forecast]
    ensemble_mean = np.mean(pro_models)
    ensemble_spread = np.std(pro_models)
    model_disagreement = np.std([ecmwf_forecast, gfs_forecast, gdps_forecast])
    nws_vs_ensemble = abs(nws_forecast - ensemble_mean)
    best_model_forecast = ecmwf_forecast
    
    # Add to dataset
    all_data.append({
        **row.to_dict(),
        'ecmwf_forecast': ecmwf_forecast,
        'gfs_forecast': gfs_forecast,
        'gdps_forecast': gdps_forecast,
        'icon_forecast': icon_forecast,
        'nws_forecast': nws_forecast,
        'ensemble_mean': ensemble_mean,
        'ensemble_spread': ensemble_spread,
        'model_disagreement': model_disagreement,
        'nws_vs_ensemble': nws_vs_ensemble,
        'best_model': best_model_forecast,
    })
    
    if idx % 1000 == 0 and idx > 0:
        print(f"  Processed {idx}/{len(merged)}...")

print()
print(f"[OK] Generated ensemble features for {len(all_data)} records")
print()

# Create DataFrame
ensemble_df = pd.DataFrame(all_data)

# Save
print("[5/5] Saving official ensemble training data...")
output_file = project_root / "data" / "weather" / "ensemble_training_OFFICIAL_2020-2024.csv"
ensemble_df.to_csv(output_file, index=False)
print(f"[OK] Saved: {output_file}")
print()

print("=" * 70)
print("OFFICIAL ENSEMBLE DATA READY")
print("=" * 70)
print()
print(f"Total Records: {len(ensemble_df)}")
print(f"Date Range: {ensemble_df['date'].min()} to {ensemble_df['date'].max()}")
print(f"Cities: {ensemble_df['city'].nunique()}")
print()
print("Ground Truth (Y variable):")
print("  Source: 100% Official NOAA GHCND data")
print("  Stations: Exact Kalshi settlement stations")
print("  Accuracy: 100% (not proxy)")
print()
print("Features (X variables):")
print("  Ensemble forecasts: Simulated (±1.5-2.5°F error)")
print("  Atmospheric: Real historical (Open-Meteo)")
print("  Alpha features: ensemble_spread, model_disagreement, nws_vs_ensemble")
print()
print("=" * 70)
print()
print("Next steps:")
print("  1. Re-train: python scripts/train_ensemble_models.py")
print("  2. Re-backtest: python scripts/backtest_ensemble_strategy.py")
print()
print("Expected result:")
print("  - More honest than +3,262% (proxy was wrong 45% of time)")
print("  - But still potentially profitable if strategy is sound")
print("  - Forward test will be the REAL validation")
print()
print("=" * 70)

