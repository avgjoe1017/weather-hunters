"""
Train models on REAL ensemble data with confidence filtering.

This is the professional approach:
1. Train on ensemble features (ECMWF, GFS, GDPS, etc.)
2. Use ensemble_spread for confidence
3. Use model_disagreement for signal quality
4. Use nws_vs_ensemble for market inefficiency

Expected result: 65-75% accuracy on TRADES (filtered)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("ENSEMBLE MODEL TRAINING - OFFICIAL NOAA GROUND TRUTH")
print("=" * 70)
print()
print("Training on 100% OFFICIAL NOAA data (not proxy)")
print()

# Load ensemble training data (OFFICIAL NOAA ground truth)
data_file = project_root / "data" / "weather" / "ensemble_training_OFFICIAL_2020-2024.csv"

if not data_file.exists():
    print(f"[X] Ensemble data not found: {data_file}")
    print("    Run: python scripts/build_ensemble_training_data.py")
    sys.exit(1)

print("[1/6] Loading ensemble training data...")
df = pd.read_csv(data_file)
df['date'] = pd.to_datetime(df['date'])

print(f"[OK] Loaded {len(df)} observations")
print(f"    Date range: {df['date'].min()} to {df['date'].max()}")
print(f"    Cities: {df['city'].nunique()}")
print()

# Feature engineering
print("[2/6] Engineering features...")
df['day_of_year'] = df['date'].dt.dayofyear
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year

# Lagged features
df = df.sort_values(['city', 'date'])
df['prev_high'] = df.groupby('city')['actual_high_temp'].shift(1)
df['prev_7day_avg'] = df.groupby('city')['actual_high_temp'].rolling(7, min_periods=1).mean().reset_index(0, drop=True)

df = df.dropna()

# Target (2°F brackets)
df['bracket'] = (df['actual_high_temp'] // 2).astype(int)

print(f"[OK] Features ready")
print()

# Feature list - now includes ENSEMBLE features
feature_cols = [
    # Time features
    'day_of_year', 'month',
    
    # Historical temps
    'prev_high', 'prev_7day_avg',
    
    # PROFESSIONAL MODEL FORECASTS (NEW)
    'ecmwf_forecast',  # Best single model
    'gfs_forecast',
    'gdps_forecast',
    'ensemble_mean',   # Best overall forecast
    
    # ALPHA FEATURES (NEW - THE EDGE)
    'ensemble_spread',      # Confidence measure
    'model_disagreement',   # Pro agreement
    'nws_vs_ensemble',      # Market inefficiency
    
    # Supporting atmospheric
    'pressure_msl',
    'wind_speed',
    'humidity',
]

# Check which features exist
available_features = [f for f in feature_cols if f in df.columns]
print(f"Using {len(available_features)} features")
print()

# Train/test split
train_df = df[df['year'] < 2024].copy()
test_df = df[df['year'] == 2024].copy()

print(f"Train set: {len(train_df)} samples (2020-2023)")
print(f"Test set: {len(test_df)} samples (2024)")
print()

X_train = train_df[available_features].values
y_train = train_df['bracket'].values

X_test = test_df[available_features].values
y_test = test_df['bracket'].values

# Train models
print("[3/6] Training ensemble models...")
print()

models = {
    'gradient_boost': GradientBoostingClassifier(n_estimators=150, max_depth=6, learning_rate=0.1, random_state=42),
    'random_forest': RandomForestClassifier(n_estimators=150, max_depth=12, random_state=42, n_jobs=-1),
    'logistic': LogisticRegression(max_iter=1000, multi_class='multinomial', random_state=42)
}

results = {}

for name, model in models.items():
    print(f"  Training {name}...")
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    exact_acc = (y_pred == y_test).mean()
    close_acc = (np.abs(y_pred - y_test) <= 1).mean()
    
    results[name] = {
        'model': model,
        'exact_accuracy': exact_acc,
        'close_accuracy': close_acc,
        'predictions': y_pred,
        'probabilities': y_proba
    }
    
    print(f"    Exact: {exact_acc:.1%}  Close: {close_acc:.1%}")

print()
print("[OK] Models trained")
print()

# Cross-validation
print("[4/6] Cross-validating...")
tscv = TimeSeriesSplit(n_splits=5)
cv_scores = {name: [] for name in models.keys()}

for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
    X_fold_train, X_fold_val = X_train[train_idx], X_train[val_idx]
    y_fold_train, y_fold_val = y_train[train_idx], y_train[val_idx]
    
    for name, res in results.items():
        model = res['model']
        model.fit(X_fold_train, y_fold_train)
        y_fold_pred = model.predict(X_fold_val)
        acc = (np.abs(y_fold_pred - y_fold_val) <= 1).mean()
        cv_scores[name].append(acc)

print("Cross-validation scores (close accuracy):")
for name, scores in cv_scores.items():
    print(f"  {name:20s} {np.mean(scores):.1%} +/- {np.std(scores):.1%}")

print()

# Save models
print("[5/6] Saving models...")
models_dir = project_root / "models"
models_dir.mkdir(exist_ok=True)

for name, res in results.items():
    model_file = models_dir / f"ensemble_{name}.joblib"
    joblib.dump(res['model'], model_file)
    print(f"  Saved: {model_file}")

# Save metadata
metadata = {
    'features': available_features,
    'train_date_range': (train_df['date'].min().strftime('%Y-%m-%d'), train_df['date'].max().strftime('%Y-%m-%d')),
    'test_date_range': (test_df['date'].min().strftime('%Y-%m-%d'), test_df['date'].max().strftime('%Y-%m-%d')),
}
joblib.dump(metadata, models_dir / "ensemble_metadata.joblib")

print()

# Performance summary
print("[6/6] Performance analysis...")
print()

print("=" * 70)
print("MODEL PERFORMANCE (ALL DAYS)")
print("=" * 70)
print()

for name, res in sorted(results.items(), key=lambda x: x[1]['close_accuracy'], reverse=True):
    print(f"{name.upper()}:")
    print(f"  Exact Bracket: {res['exact_accuracy']:.1%}")
    print(f"  Within ±2°F:   {res['close_accuracy']:.1%}")
    print()

print("=" * 70)
print()

# Now analyze with CONFIDENCE FILTERING
print("=" * 70)
print("PERFORMANCE WITH CONFIDENCE FILTERING")
print("=" * 70)
print()

# Get ensemble predictions
best_model_name = max(results.items(), key=lambda x: x[1]['close_accuracy'])[0]
best_model = results[best_model_name]['model']
best_preds = results[best_model_name]['predictions']

# Add predictions to test dataframe
test_df_with_preds = test_df.copy()
test_df_with_preds['prediction'] = best_preds
test_df_with_preds['correct'] = (best_preds == y_test).astype(int)

# Filter by confidence levels
print(f"Using best model: {best_model_name}")
print()

# High confidence (ensemble_spread < 1.5°F)
high_conf = test_df_with_preds[test_df_with_preds['ensemble_spread'] < 1.5]
if len(high_conf) > 0:
    acc = high_conf['correct'].mean()
    print(f"High Confidence (spread <1.5°F): {len(high_conf)} days ({len(high_conf)/len(test_df)*100:.1f}%)")
    print(f"  Accuracy: {acc:.1%}")
    print()

# Pro agreement (model_disagreement < 1.0°F)
pro_agree = test_df_with_preds[test_df_with_preds['model_disagreement'] < 1.0]
if len(pro_agree) > 0:
    acc = pro_agree['correct'].mean()
    print(f"Pro Agreement (disagreement <1.0°F): {len(pro_agree)} days ({len(pro_agree)/len(test_df)*100:.1f}%)")
    print(f"  Accuracy: {acc:.1%}")
    print()

# Market inefficiency (nws_vs_ensemble > 2.0°F)
market_ineff = test_df_with_preds[test_df_with_preds['nws_vs_ensemble'] > 2.0]
if len(market_ineff) > 0:
    acc = market_ineff['correct'].mean()
    print(f"Market Inefficiency (>2°F): {len(market_ineff)} days ({len(market_ineff)/len(test_df)*100:.1f}%)")
    print(f"  Accuracy: {acc:.1%}")
    print()

# OPTIMAL TRADES (all conditions)
optimal = test_df_with_preds[
    (test_df_with_preds['ensemble_spread'] < 1.5) &
    (test_df_with_preds['model_disagreement'] < 1.0) &
    (test_df_with_preds['nws_vs_ensemble'] > 1.5)
]

if len(optimal) > 0:
    acc = optimal['correct'].mean()
    print("=" * 70)
    print(f"OPTIMAL TRADES (all conditions): {len(optimal)} days ({len(optimal)/len(test_df)*100:.1f}%)")
    print(f"  Accuracy: {acc:.1%}")
    print("=" * 70)
    print()
    
    if acc > 0.60:
        print("[OK] EXCELLENT! Accuracy >60% on selective trades!")
        print("     This should be HIGHLY PROFITABLE")
    elif acc > 0.55:
        print("[OK] GOOD! Accuracy >55% on selective trades")
        print("     Should be profitable")
    else:
        print("[~] Accuracy {:.1%} on selective trades".format(acc))
        print("    May be marginally profitable")
else:
    print("[!] No optimal trades in test set (conditions too strict?)")

print()
print("=" * 70)
print()
print("[OK] ENSEMBLE TRAINING COMPLETE!")
print()
print("Next step:")
print("  Run: python scripts/backtest_ensemble_strategy.py")
print("  (Backtest with confidence-filtered trades)")
print()
print("=" * 70)

