"""
Train advanced ML models with enhanced features.

Models:
- XGBoost (gradient boosting, usually best for tabular data)
- LightGBM (faster gradient boosting)
- Stacking ensemble (combines all models)
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder
import xgboost as xgb
import lightgbm as lgb
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("ADVANCED WEATHER MODEL TRAINING")
print("=" * 70)
print()

# Load enhanced data
data_file = project_root / "data" / "weather" / "all_cities_2020-2024_enhanced.csv"

if not data_file.exists():
    print(f"[X] Enhanced data file not found: {data_file}")
    print("    Run: python scripts/collect_enhanced_weather.py")
    sys.exit(1)

print(f"[1/6] Loading enhanced historical data...")
print()

df = pd.read_csv(data_file)
df['date'] = pd.to_datetime(df['date'])

print(f"[OK] Loaded {len(df)} observations")
print(f"    Date range: {df['date'].min()} to {df['date'].max()}")
print(f"    Cities: {df['city'].nunique()}")
print(f"    Features: {len(df.columns)}")
print()

# Feature engineering
print("[2/6] Engineering features...")
print()

df['day_of_year'] = df['date'].dt.dayofyear
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year
df['day_of_week'] = df['date'].dt.dayofweek

# Lagged features
df = df.sort_values(['city', 'date'])
df['prev_high'] = df.groupby('city')['actual_high_temp'].shift(1)
df['prev_7day_avg'] = df.groupby('city')['actual_high_temp'].rolling(7, min_periods=1).mean().reset_index(0, drop=True)
df['prev_3day_max'] = df.groupby('city')['actual_high_temp'].rolling(3, min_periods=1).max().reset_index(0, drop=True)
df['prev_3day_min'] = df.groupby('city')['actual_high_temp'].rolling(3, min_periods=1).min().reset_index(0, drop=True)

# Temperature anomaly (deviation from rolling 30-day mean)
df['temp_30day_avg'] = df.groupby('city')['actual_high_temp'].rolling(30, min_periods=1).mean().reset_index(0, drop=True)
df['temp_anomaly'] = df['prev_high'] - df['temp_30day_avg']

# Drop rows with NaN
df = df.dropna()

# Create target
df['bracket'] = (df['actual_high_temp'] // 2).astype(int)

print(f"[OK] Features created")
print(f"    Total features: {len(df.columns)}")
print(f"    Samples after cleanup: {len(df)}")
print()

# Feature selection
feature_cols = [
    # Time features
    'day_of_year', 'month', 'day_of_week',
    
    # Historical temperatures
    'prev_high', 'prev_7day_avg', 'prev_3day_max', 'prev_3day_min',
    'temp_anomaly', 'temp_range',
    
    # NEW: Atmospheric
    'pressure_msl', 'pressure_change_24h',
    
    # NEW: Wind
    'wind_speed', 'wind_direction', 'wind_gusts',
    'wind_from_north', 'wind_from_south', 'wind_from_east', 'wind_from_west',
    
    # NEW: Other weather
    'precipitation', 'rain', 'humidity', 'dewpoint',
    'cloudcover', 'sunshine_hours'
]

# Check which features exist
available_features = [f for f in feature_cols if f in df.columns]
print(f"Using {len(available_features)} features:")
for feat in available_features:
    print(f"  - {feat}")
print()

# Split train/test
train_df = df[df['year'] < 2024].copy()
test_df = df[df['year'] == 2024].copy()

print(f"Train set: {len(train_df)} samples (2020-2023)")
print(f"Test set: {len(test_df)} samples (2024)")
print()

X_train = train_df[available_features].values
y_train_raw = train_df['bracket'].values

X_test = test_df[available_features].values
y_test_raw = test_df['bracket'].values

# XGBoost needs consecutive class labels, so use LabelEncoder
# Fit on all brackets (train + test) to avoid unseen labels
label_encoder = LabelEncoder()
all_brackets = np.concatenate([y_train_raw, y_test_raw])
label_encoder.fit(all_brackets)

y_train = label_encoder.transform(y_train_raw)
y_test = label_encoder.transform(y_test_raw)

# Train models
print("[3/6] Training advanced ML models...")
print()

models = {}

# 1. LightGBM (best for tabular data, handles arbitrary labels)
print("  Training LightGBM...")
lgb_model = lgb.LGBMClassifier(
    n_estimators=250,
    max_depth=10,
    learning_rate=0.1,
    subsample=0.8,
    colsample_bytree=0.8,
    random_state=42,
    n_jobs=-1,
    verbose=-1
)
lgb_model.fit(X_train, y_train)
models['lightgbm'] = lgb_model

# 2. Random Forest (baseline comparison)
print("  Training Random Forest...")
rf_model = RandomForestClassifier(
    n_estimators=200,
    max_depth=12,
    random_state=42,
    n_jobs=-1
)
rf_model.fit(X_train, y_train)
models['random_forest'] = rf_model

# 3. Gradient Boosting (sklearn baseline)
print("  Training Gradient Boosting...")
gb_model = GradientBoostingClassifier(
    n_estimators=150,
    max_depth=6,
    learning_rate=0.1,
    random_state=42
)
gb_model.fit(X_train, y_train)
models['gradient_boost'] = gb_model

print()
print("[OK] 3 models trained (LightGBM, Random Forest, Gradient Boosting)")
print()

# Evaluate models
print("[4/6] Evaluating models on 2024 test data...")
print()

results = {}

for name, model in models.items():
    y_pred_encoded = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    # Convert back to actual bracket values for error calculation
    y_pred = label_encoder.inverse_transform(y_pred_encoded)
    
    exact_acc = (y_pred == y_test_raw).mean()
    close_acc = (np.abs(y_pred - y_test_raw) <= 1).mean()
    very_close = (np.abs(y_pred - y_test_raw) <= 2).mean()
    avg_conf = y_proba.max(axis=1).mean()
    
    results[name] = {
        'model': model,
        'exact_accuracy': exact_acc,
        'close_accuracy': close_acc,
        'very_close_accuracy': very_close,
        'avg_confidence': avg_conf,
        'predictions': y_pred,
        'probabilities': y_proba
    }
    
    print(f"  {name:20s} Exact: {exact_acc:.1%}  Close(±2°F): {close_acc:.1%}  VClose(±4°F): {very_close:.1%}  Conf: {avg_conf:.1%}")

print()

# Find best model
best_model_name = max(results.items(), key=lambda x: x[1]['close_accuracy'])[0]
best_acc = results[best_model_name]['close_accuracy']

print(f"[OK] Best model: {best_model_name} ({best_acc:.1%} accuracy)")
print()

# Cross-validation
print("[5/6] Cross-validating with time series splits...")
print()

tscv = TimeSeriesSplit(n_splits=5)
cv_scores = {name: [] for name in models.keys()}

for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
    X_fold_train, X_fold_val = X_train[train_idx], X_train[val_idx]
    y_fold_train, y_fold_val = y_train[train_idx], y_train[val_idx]
    
    for name, res in results.items():
        model = res['model']
        model.fit(X_fold_train, y_fold_train)
        y_fold_pred = model.predict(X_fold_val)
        
        # Use close accuracy for scoring
        acc = (np.abs(y_fold_pred - y_fold_val) <= 1).mean()
        cv_scores[name].append(acc)

print("Cross-validation scores (5-fold, ±2°F):")
for name, scores in cv_scores.items():
    mean_score = np.mean(scores)
    std_score = np.std(scores)
    print(f"  {name:20s} {mean_score:.1%} ± {std_score:.1%}")

print()
print("[OK] Cross-validation complete")
print()

# Save models
print("[6/6] Saving trained models...")
print()

models_dir = project_root / "models"
models_dir.mkdir(exist_ok=True)

for name, res in results.items():
    model_file = models_dir / f"weather_{name}_enhanced.joblib"
    joblib.dump(res['model'], model_file)
    print(f"  Saved: {model_file}")

# Save feature info and label encoder
feature_info = {
    'feature_names': available_features,
    'n_features': len(available_features),
    'train_date_range': (train_df['date'].min().strftime('%Y-%m-%d'), train_df['date'].max().strftime('%Y-%m-%d')),
    'test_date_range': (test_df['date'].min().strftime('%Y-%m-%d'), test_df['date'].max().strftime('%Y-%m-%d')),
    'label_encoder': label_encoder
}
joblib.dump(feature_info, models_dir / "feature_info_enhanced.joblib")

print()
print("=" * 70)
print("MODEL PERFORMANCE SUMMARY")
print("=" * 70)
print()

for name, res in sorted(results.items(), key=lambda x: x[1]['close_accuracy'], reverse=True):
    print(f"{name.upper()}:")
    print(f"  Exact Bracket (±0°F): {res['exact_accuracy']:.1%}")
    print(f"  Close (±2°F):         {res['close_accuracy']:.1%}")
    print(f"  Very Close (±4°F):    {res['very_close_accuracy']:.1%}")
    print(f"  Confidence:           {res['avg_confidence']:.1%}")
    print()

print("=" * 70)
print()

# Comparison with baseline
baseline_acc = 0.568  # From previous basic model
improvement = best_acc - baseline_acc

print(f"[OK] TRAINING COMPLETE!")
print()
print(f"Best model: {best_model_name}")
print(f"Accuracy (±2°F): {best_acc:.1%}")
print(f"Baseline (basic features): {baseline_acc:.1%}")
print(f"Improvement: {improvement:+.1%}")
print()

if best_acc > 0.65:
    print("[OK] EXCELLENT! Accuracy >65% achieved!")
    print("     Ready for profitable trading")
elif best_acc > 0.60:
    print("[OK] GOOD! Accuracy 60-65%")
    print("     Should be profitable")
elif best_acc > 0.55:
    print("[~] MARGINAL. Accuracy 55-60%")
    print("    May be marginally profitable")
else:
    print("[X] WEAK. Accuracy <55%")
    print("    Needs more improvement")

print()
print("Next step:")
print("  Run: python scripts/backtest_enhanced_strategy.py")
print("  This will simulate trading with the best models")
print()
print("=" * 70)

