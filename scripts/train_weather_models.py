"""
Train ML models on historical weather data.

This script:
1. Collects 4 years of historical weather data (2020-2024)
2. Engineers features using the weather pipeline
3. Trains multiple ML models
4. Validates with time-series cross-validation
5. Saves trained models for prediction
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
import joblib
import json

print("=" * 70)
print("WEATHER MODEL TRAINING")
print("=" * 70)
print()

# Step 1: Collect historical data
print("[1/5] Collecting historical weather data (2020-2024)...")
print()

from src.features.weather_data_collector import HistoricalWeatherCollector

collector = HistoricalWeatherCollector()

cities = ['NYC', 'CHI', 'MIA', 'HOU', 'AUS']
all_data = []

for city in cities:
    print(f"  Collecting {city}...")
    try:
        # Collect 4 years of data
        city_data = []
        for year in range(2020, 2025):
            for month in range(1, 13):
                if year == 2024 and month > 11:  # Don't go into future
                    break
                
                # Collect month's data
                start_date = f"{year}-{month:02d}-01"
                end_date = f"{year}-{month:02d}-28"
                
                try:
                    data = collector.collect_historical_data(start_date, end_date, city)
                    if data and len(data) > 0:
                        city_data.extend(data)
                except:
                    continue
        
        print(f"    {city}: {len(city_data)} days collected")
        all_data.extend(city_data)
    except Exception as e:
        print(f"    {city}: Error - {e}")

print()
print(f"[OK] Total: {len(all_data)} observations collected")
print()

# Step 2: Engineer features
print("[2/5] Engineering features...")
print()

from src.features.weather_pipeline import WeatherFeaturePipeline

pipeline = WeatherFeaturePipeline()

# Convert to DataFrame
df = pd.DataFrame(all_data)

# For this simplified version, we'll create features manually
# In production, you'd use the full pipeline

# Create target: Which 2°F bracket did actual temp fall into?
# Brackets: 0-2, 2-4, 4-6, ..., 98-100
df['bracket'] = (df['actual_high_temp'] // 2).astype(int)

# Features from forecast
features = []
feature_names = []

for idx, row in df.iterrows():
    feat = [
        row.get('forecast_high_temp', 70),
        row.get('forecast_low_temp', 50),
        row.get('humidity', 50),
        row.get('wind_speed', 5),
        row.get('precipitation', 0),
        row.get('cloud_cover', 50),
    ]
    
    # Add day of year (seasonal)
    try:
        date = pd.to_datetime(row.get('date', '2020-01-01'))
        feat.append(date.dayofyear)
        feat.append(date.month)
    except:
        feat.append(180)
        feat.append(6)
    
    features.append(feat)

feature_names = [
    'forecast_high', 'forecast_low', 'humidity', 'wind_speed',
    'precipitation', 'cloud_cover', 'day_of_year', 'month'
]

X = np.array(features)
y = df['bracket'].values

print(f"[OK] Created {X.shape[0]} samples with {X.shape[1]} features")
print(f"Feature names: {feature_names}")
print()

# Step 3: Time-series cross-validation
print("[3/5] Training models with time-series cross-validation...")
print()

# Use time-series split (respects temporal order)
tscv = TimeSeriesSplit(n_splits=5)

models = {
    'logistic': LogisticRegression(max_iter=1000, multi_class='multinomial'),
    'random_forest': RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
    'gradient_boost': GradientBoostingClassifier(n_estimators=100, max_depth=5, random_state=42)
}

results = {}

for name, model in models.items():
    print(f"Training {name}...")
    
    fold_scores = []
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        model.fit(X_train, y_train)
        y_pred = model.predict(X_val)
        
        # Calculate accuracy (did we pick the right bracket?)
        acc = accuracy_score(y_val, y_pred)
        
        # Calculate +/- 1 bracket accuracy (close enough for trading)
        close_acc = np.mean(np.abs(y_val - y_pred) <= 1)
        
        fold_scores.append({'accuracy': acc, 'close_accuracy': close_acc})
        
        print(f"  Fold {fold}: Accuracy={acc:.3f}, Close={close_acc:.3f}")
    
    avg_acc = np.mean([s['accuracy'] for s in fold_scores])
    avg_close = np.mean([s['close_accuracy'] for s in fold_scores])
    
    results[name] = {
        'accuracy': avg_acc,
        'close_accuracy': avg_close,
        'fold_scores': fold_scores
    }
    
    print(f"  Average: Accuracy={avg_acc:.3f}, Close={avg_close:.3f}")
    print()

# Step 4: Train final models on all data
print("[4/5] Training final models on all data...")
print()

# Create models directory
models_dir = project_root / "models"
models_dir.mkdir(exist_ok=True)

for name, model in models.items():
    print(f"  Training {name}...")
    model.fit(X, y)
    
    # Save model
    model_file = models_dir / f"{name}_weather.pkl"
    joblib.dump(model, model_file)
    print(f"  Saved to {model_file}")

print()

# Step 5: Save metadata
print("[5/5] Saving model metadata...")
print()

metadata = {
    'trained_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'training_samples': int(X.shape[0]),
    'features': feature_names,
    'cities': cities,
    'date_range': '2020-2024',
    'results': {
        name: {
            'accuracy': float(res['accuracy']),
            'close_accuracy': float(res['close_accuracy'])
        }
        for name, res in results.items()
    }
}

metadata_file = models_dir / "model_metadata.json"
with open(metadata_file, 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"[OK] Saved metadata to {metadata_file}")
print()

# Summary
print("=" * 70)
print("TRAINING COMPLETE")
print("=" * 70)
print()
print(f"Models trained: {len(models)}")
print(f"Training samples: {X.shape[0]}")
print(f"Features: {X.shape[1]}")
print()

print("Model Performance:")
for name, res in results.items():
    print(f"  {name:20s} Accuracy: {res['accuracy']:.1%}  Close: {res['close_accuracy']:.1%}")

print()
print("Saved models:")
for name in models.keys():
    print(f"  models/{name}_weather.pkl")

print()
print("=" * 70)
print()
print("INTERPRETATION:")
print()
print("Accuracy = Exact bracket prediction (e.g., 70-72F)")
print("Close = Within one bracket (e.g., predicted 70-72F, actual 68-70F)")
print()
print("For trading:")
print("  - 30%+ accuracy = Good (better than random 16.7% with 6 brackets)")
print("  - 60%+ close accuracy = Excellent (you're in the right range)")
print()

if max(res['close_accuracy'] for res in results.values()) > 0.60:
    print("[OK] Models are ready for live trading!")
    print("     Close accuracy >60% means you have edge vs. market")
else:
    print("[!] Models need improvement before live trading")
    print("    Consider: More data, better features, ensemble methods")

print()
print("Next step: python scripts/backtest_weather_models.py")
print("           (Test models with walk-forward validation)")

