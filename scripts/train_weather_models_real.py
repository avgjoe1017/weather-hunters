"""
Train ML models on REAL historical weather data.

Uses the collected data from Open-Meteo to build temperature prediction models.
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
import joblib
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("WEATHER MODEL TRAINING (REAL DATA)")
print("=" * 70)
print()

# Load real historical data
data_file = project_root / "data" / "weather" / "all_cities_2020-2024.csv"

if not data_file.exists():
    print(f"[X] Data file not found: {data_file}")
    print("    Run: python scripts/collect_historical_weather.py")
    sys.exit(1)

print(f"[1/5] Loading historical data...")
print()

df = pd.read_csv(data_file)
df['date'] = pd.to_datetime(df['date'])

print(f"[OK] Loaded {len(df)} observations")
print(f"    Date range: {df['date'].min()} to {df['date'].max()}")
print(f"    Cities: {df['city'].nunique()}")
print()

# Feature engineering
print("[2/5] Engineering features...")
print()

df['day_of_year'] = df['date'].dt.dayofyear
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year

# Create lagged features (yesterday's temp helps predict today)
df = df.sort_values(['city', 'date'])
df['prev_high'] = df.groupby('city')['actual_high_temp'].shift(1)
df['prev_7day_avg'] = df.groupby('city')['actual_high_temp'].rolling(7, min_periods=1).mean().reset_index(0, drop=True)

# Drop rows with NaN (first day has no prev_high)
df = df.dropna()

# Create target: which 2°F bracket?
df['bracket'] = (df['actual_high_temp'] // 2).astype(int)

print(f"[OK] Features created")
print(f"    Features: day_of_year, month, prev_high, prev_7day_avg, humidity, wind_speed")
print(f"    Target: Temperature bracket (2°F intervals)")
print(f"    Samples after cleanup: {len(df)}")
print()

# Split train/test (2020-2023 train, 2024 test)
train_df = df[df['year'] < 2024].copy()
test_df = df[df['year'] == 2024].copy()

print(f"Train set: {len(train_df)} samples (2020-2023)")
print(f"Test set: {len(test_df)} samples (2024)")
print()

# Prepare features
feature_cols = ['day_of_year', 'month', 'prev_high', 'prev_7day_avg', 'humidity', 'wind_speed']

X_train = train_df[feature_cols].values
y_train = train_df['bracket'].values

X_test = test_df[feature_cols].values
y_test = test_df['bracket'].values

print(f"[3/5] Training ML models...")
print()

# Train models with time-series cross-validation
models = {
    'logistic': LogisticRegression(max_iter=1000, multi_class='multinomial', random_state=42),
    'random_forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42, n_jobs=-1),
    'gradient_boost': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
}

results = {}

for name, model in models.items():
    print(f"  Training {name}...")
    
    # Train on full training set
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    # Metrics
    exact_acc = (y_pred == y_test).mean()
    close_acc = (np.abs(y_pred - y_test) <= 1).mean()  # Within ±1 bracket (±2°F)
    very_close = (np.abs(y_pred - y_test) <= 2).mean()  # Within ±2 brackets (±4°F)
    
    # Confidence
    max_proba = y_proba.max(axis=1).mean()
    
    results[name] = {
        'model': model,
        'exact_accuracy': exact_acc,
        'close_accuracy': close_acc,
        'very_close_accuracy': very_close,
        'avg_confidence': max_proba
    }
    
    print(f"    Exact: {exact_acc:.1%}  Close: {close_acc:.1%}  Very Close: {very_close:.1%}  Confidence: {max_proba:.1%}")

print()
print("[OK] Models trained")
print()

# Time series cross-validation
print("[4/5] Cross-validating with time series splits...")
print()

tscv = TimeSeriesSplit(n_splits=5)
cv_scores = {name: [] for name in models.keys()}

for fold, (train_idx, val_idx) in enumerate(tscv.split(X_train)):
    X_fold_train, X_fold_val = X_train[train_idx], X_train[val_idx]
    y_fold_train, y_fold_val = y_train[train_idx], y_train[val_idx]
    
    for name, model_info in results.items():
        model = model_info['model']
        model.fit(X_fold_train, y_fold_train)
        y_fold_pred = model.predict(X_fold_val)
        acc = (y_fold_pred == y_fold_val).mean()
        cv_scores[name].append(acc)

print("Cross-validation scores (5-fold):")
for name, scores in cv_scores.items():
    mean_score = np.mean(scores)
    std_score = np.std(scores)
    print(f"  {name:20s} {mean_score:.1%} ± {std_score:.1%}")

print()
print("[OK] Cross-validation complete")
print()

# Save models
print("[5/5] Saving trained models...")
print()

models_dir = project_root / "models"
models_dir.mkdir(exist_ok=True)

for name, model_info in results.items():
    model_file = models_dir / f"weather_{name}.joblib"
    joblib.dump(model_info['model'], model_file)
    print(f"  Saved: {model_file}")

# Save feature names
feature_info = {
    'feature_names': feature_cols,
    'train_date_range': (train_df['date'].min().strftime('%Y-%m-%d'), train_df['date'].max().strftime('%Y-%m-%d')),
    'test_date_range': (test_df['date'].min().strftime('%Y-%m-%d'), test_df['date'].max().strftime('%Y-%m-%d'))
}
joblib.dump(feature_info, models_dir / "feature_info.joblib")

print()
print("=" * 70)
print("MODEL PERFORMANCE SUMMARY")
print("=" * 70)
print()

for name, model_info in results.items():
    print(f"{name.upper()}:")
    print(f"  Exact Bracket: {model_info['exact_accuracy']:.1%}")
    print(f"  Within ±2°F:   {model_info['close_accuracy']:.1%}")
    print(f"  Within ±4°F:   {model_info['very_close_accuracy']:.1%}")
    print(f"  Confidence:    {model_info['avg_confidence']:.1%}")
    print()

print("=" * 70)
print()

# Interpretation
best_model = max(results.items(), key=lambda x: x[1]['close_accuracy'])
best_name = best_model[0]
best_acc = best_model[1]['close_accuracy']

print(f"[OK] TRAINING COMPLETE!")
print()
print(f"Best model: {best_name}")
print(f"Accuracy (±2°F): {best_acc:.1%}")
print()

if best_acc > 0.70:
    print("[OK] EXCELLENT! Model is highly accurate (>70%)")
    print("     This should translate to strong profitability")
elif best_acc > 0.60:
    print("[OK] GOOD! Model is accurate (60-70%)")
    print("     Should be profitable with proper position sizing")
elif best_acc > 0.50:
    print("[~] FAIR. Model is somewhat accurate (50-60%)")
    print("    May be marginally profitable")
else:
    print("[X] POOR. Model accuracy too low (<50%)")
    print("    Likely unprofitable")

print()
print("Next step:")
print("  Run: python scripts/backtest_weather_models_real.py")
print("  This will simulate trading on 2024 data with these models")
print()
print("=" * 70)

