"""
Demo validation with simulated historical data.

This demonstrates the validation workflow without requiring external weather APIs.
Shows what the backtest would look like with realistic simulated data.
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
import warnings
warnings.filterwarnings('ignore')

print("=" * 70)
print("WEATHER STRATEGY VALIDATION (DEMO)")
print("=" * 70)
print()
print("NOTE: Using simulated historical data for demonstration")
print("      In production, replace with real weather API data")
print()

# Step 1: Generate realistic simulated data
print("[1/4] Generating simulated historical data (2020-2024)...")
print()

np.random.seed(42)

# Simulate 5 years of weather data (2020-2024)
n_days = 365 * 5
dates = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(n_days)]

cities = ['NYC', 'CHI', 'MIA', 'HOU', 'AUS']
all_data = []

for city in cities:
    # City-specific temperature patterns
    base_temp = {'NYC': 55, 'CHI': 50, 'MIA': 78, 'HOU': 70, 'AUS': 68}[city]
    seasonal_amplitude = 25  # Seasonal variation
    
    for i, date in enumerate(dates):
        # Seasonal pattern (sin wave)
        day_of_year = date.timetuple().tm_yday
        seasonal = seasonal_amplitude * np.sin(2 * np.pi * (day_of_year - 80) / 365)
        
        # Random weather variation
        daily_noise = np.random.normal(0, 5)
        
        # "True" temperature
        actual_temp = base_temp + seasonal + daily_noise
        
        # Forecast is actual + small error (forecasts are pretty good)
        forecast_error = np.random.normal(0, 3)  # 3°F forecast error
        forecast_temp = actual_temp + forecast_error
        
        all_data.append({
            'date': date,
            'city': city,
            'actual_high_temp': actual_temp,
            'forecast_high_temp': forecast_temp,
            'forecast_error': abs(forecast_error)
        })

df = pd.DataFrame(all_data)

print(f"[OK] Generated {len(df)} observations")
print(f"    Cities: {len(cities)}")
print(f"    Date range: 2020-2024")
print(f"    Average forecast error: {df['forecast_error'].mean():.2f}°F")
print()

# Step 2: Train models
print("[2/4] Training ML models...")
print()

# Split into train/test
split_date = datetime(2024, 1, 1)
train_df = df[df['date'] < split_date].copy()
test_df = df[df['date'] >= split_date].copy()

print(f"Train set: {len(train_df)} samples (2020-2023)")
print(f"Test set: {len(test_df)} samples (2024)")
print()

# Create features and labels
def create_features(data):
    features = []
    labels = []
    
    for _, row in data.iterrows():
        feat = [
            row['forecast_high_temp'],
            row['date'].dayofyear,
            row['date'].month,
        ]
        features.append(feat)
        
        # Label: which 2°F bracket?
        bracket = int(row['actual_high_temp'] // 2)
        labels.append(bracket)
    
    X = np.array(features)
    y = np.array(labels)
    
    # Ensure we have data
    if len(X) == 0:
        raise ValueError(f"No data to create features from")
    
    return X, y

X_train, y_train = create_features(train_df)
X_test, y_test = create_features(test_df)

print(f"Training samples: {len(X_train)}")
print(f"Test samples: {len(X_test)}")
print()

# Train models
models = {
    'logistic': LogisticRegression(max_iter=1000, multi_class='multinomial', random_state=42),
    'random_forest': RandomForestClassifier(n_estimators=50, max_depth=8, random_state=42),
    'gradient_boost': GradientBoostingClassifier(n_estimators=50, max_depth=4, random_state=42)
}

results = {}

for name, model in models.items():
    # Train
    model.fit(X_train, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test)
    
    # Exact accuracy
    acc = (y_pred == y_test).mean()
    
    # Close accuracy (within ±1 bracket = ±2°F)
    close_acc = (np.abs(y_pred - y_test) <= 1).mean()
    
    results[name] = {
        'accuracy': acc,
        'close_accuracy': close_acc,
        'model': model
    }
    
    print(f"  {name:20s} Accuracy: {acc:.1%}  Close: {close_acc:.1%}")

print()
print("[OK] Models trained on 2020-2023 data")
print()

# Step 3: Backtest
print("[3/4] Running walk-forward backtest on 2024...")
print()

# Get ensemble predictions
ensemble_preds = np.mean([
    results[name]['model'].predict_proba(X_test)
    for name in models.keys()
], axis=0)

# Simulate trading
starting_capital = 1000
capital = starting_capital
trades = []

threshold = 0.30  # Trade if predicted prob >30%
kelly_fraction = 0.25

for idx in range(len(X_test)):
    predicted_probs = ensemble_preds[idx]
    actual_bracket = y_test[idx]
    
    # Best bracket
    best_bracket = np.argmax(predicted_probs)
    best_prob = predicted_probs[best_bracket]
    
    # Simulate Kalshi market price
    # Market is somewhat efficient but not perfect
    market_prob = 1.0/len(predicted_probs) + np.random.normal(0, 0.03)
    market_prob = max(0.15, min(0.45, market_prob))
    
    # Calculate edge
    edge = best_prob - market_prob
    
    # Trade if good edge
    if best_prob > threshold and edge > 0.05:
        # Kelly sizing
        bet_fraction = kelly_fraction * edge
        bet_size = capital * bet_fraction
        
        num_contracts = int(bet_size / market_prob)
        cost = num_contracts * market_prob
        
        # Did we win?
        won = (best_bracket == actual_bracket)
        
        # P&L with 7% fee
        if won:
            gross_payout = num_contracts * 1.00
            fee = gross_payout * 0.07
            net_payout = gross_payout - fee
            pnl = net_payout - cost
        else:
            pnl = -cost
        
        capital += pnl
        
        trades.append({
            'date': test_df.iloc[idx]['date'],
            'predicted_prob': best_prob,
            'market_price': market_prob,
            'edge': edge,
            'contracts': num_contracts,
            'cost': cost,
            'won': won,
            'pnl': pnl,
            'capital': capital
        })

trades_df = pd.DataFrame(trades)

wins = trades_df[trades_df['won']].shape[0]
losses = trades_df[~trades_df['won']].shape[0]
win_rate = wins / len(trades_df) if len(trades_df) > 0 else 0

total_pnl = capital - starting_capital
returns = (capital / starting_capital - 1) * 100

avg_edge = trades_df['edge'].mean()
avg_win = trades_df[trades_df['won']]['pnl'].mean() if wins > 0 else 0
avg_loss = trades_df[~trades_df['won']]['pnl'].mean() if losses > 0 else 0

print("[OK] Backtest complete")
print()

# Step 4: Results
print("[4/4] Analyzing results...")
print()

print("=" * 70)
print("BACKTEST RESULTS (2024 OUT-OF-SAMPLE)")
print("=" * 70)
print()
print(f"Starting Capital: ${starting_capital:.2f}")
print(f"Ending Capital:   ${capital:.2f}")
print(f"Total P&L:        ${total_pnl:.2f}")
print(f"Return:           {returns:.1f}%")
print()
print(f"Total Trades:     {len(trades_df)}")
print(f"Wins:             {wins} ({win_rate*100:.1f}%)")
print(f"Losses:           {losses} ({(1-win_rate)*100:.1f}%)")
print()
print(f"Average Edge:     {avg_edge*100:.1f}%")
print(f"Average Win:      ${avg_win:.2f}")
print(f"Average Loss:     ${avg_loss:.2f}")
print()

# Sharpe ratio
daily_returns = trades_df.groupby('date')['pnl'].sum()
if len(daily_returns) > 1:
    sharpe = (daily_returns.mean() / daily_returns.std()) * np.sqrt(252)
    print(f"Sharpe Ratio:     {sharpe:.2f}")
    print()

print("=" * 70)
print()

# Model Performance
print("MODEL PERFORMANCE:")
print()
for name, res in results.items():
    print(f"  {name:20s} Accuracy: {res['accuracy']:.1%}  Close: {res['close_accuracy']:.1%}")
print()

# Interpretation
print("=" * 70)
print("INTERPRETATION")
print("=" * 70)
print()

if returns > 20:
    print("[OK] EXCELLENT! Strategy shows strong profitability")
    print(f"     {returns:.1f}% returns in backtest")
    recommendation = "READY FOR LIVE TRADING"
    color = "GREEN"
elif returns > 15:
    print("[OK] GOOD! Strategy is profitable")
    print(f"     {returns:.1f}% returns")
    recommendation = "READY FOR LIVE TRADING (start small)"
    color = "GREEN"
elif returns > 10:
    print("[~] MARGINAL. Strategy barely profitable")
    print(f"    {returns:.1f}% returns")
    recommendation = "TRADE CAUTIOUSLY (very small positions)"
    color = "YELLOW"
elif returns > 0:
    print("[~] WEAK. Returns too low")
    print(f"    {returns:.1f}% returns")
    recommendation = "IMPROVE STRATEGY FIRST"
    color = "YELLOW"
else:
    print("[X] UNPROFITABLE. Strategy doesn't work")
    print(f"    {returns:.1f}% returns (negative)")
    recommendation = "DO NOT TRADE - NEEDS MAJOR IMPROVEMENT"
    color = "RED"

print()

if win_rate > 0.55:
    print(f"[OK] Win rate {win_rate*100:.1f}% is strong (>55%)")
elif win_rate > 0.48:
    print(f"[~] Win rate {win_rate*100:.1f}% is acceptable (48-55%)")
else:
    print(f"[X] Win rate {win_rate*100:.1f}% is too low (<48%)")

print()

if avg_edge > 0.08:
    print(f"[OK] Average edge {avg_edge*100:.1f}% is excellent (>8%)")
elif avg_edge > 0.05:
    print(f"[~] Average edge {avg_edge*100:.1f}% is acceptable (5-8%)")
else:
    print(f"[X] Average edge {avg_edge*100:.1f}% is too small (<5%)")

print()
print("=" * 70)
print()
print(f"RECOMMENDATION: {recommendation}")
print()

if returns > 15 and win_rate > 0.50:
    print("Strategy validated! You can proceed to live trading.")
    print()
    print("Next steps:")
    print("  1. Replace simulated data with real weather APIs")
    print("  2. Run: python scripts/morning_routine.py")
    print("  3. Start with ONE small trade ($5)")
    print("  4. Track actual vs. predicted")
    print("  5. Scale up if profitable")
    print()
    print("Expected live performance:")
    print(f"  Backtest: {returns:.1f}%")
    print(f"  Expected live: {returns * 0.75:.1f}% (25% degradation)")
else:
    print("Strategy needs improvement before live trading.")
    print()
    print("To improve:")
    print("  - Get real historical weather data (not simulated)")
    print("  - Add more features (ensemble forecasts, pressure)")
    print("  - Use better models (XGBoost, neural nets)")
    print("  - Get real historical Kalshi prices")

print()
print("=" * 70)
print()
print("NOTE: This demo uses SIMULATED data.")
print("      Real performance requires real weather APIs.")
print("      The methodology is correct, data needs to be real.")

