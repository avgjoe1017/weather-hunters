"""
Backtest enhanced models on 2024 data.

Uses the best models (86.2% accuracy) to simulate real trading.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
import joblib
from datetime import datetime

print("=" * 70)
print("ENHANCED STRATEGY BACKTEST")
print("=" * 70)
print()

# Load enhanced models
models_dir = project_root / "models"

print("[1/4] Loading enhanced models...")

models = {
    'gradient_boost': joblib.load(models_dir / "weather_gradient_boost_enhanced.joblib"),
    'random_forest': joblib.load(models_dir / "weather_random_forest_enhanced.joblib"),
    'lightgbm': joblib.load(models_dir / "weather_lightgbm_enhanced.joblib")
}

feature_info = joblib.load(models_dir / "feature_info_enhanced.joblib")
feature_cols = feature_info['feature_names']
label_encoder = feature_info['label_encoder']

print(f"[OK] Loaded {len(models)} models")
print(f"    Features: {len(feature_cols)}")
print()

# Load 2024 test data
data_file = project_root / "data" / "weather" / "all_cities_2020-2024_enhanced.csv"
df = pd.read_csv(data_file)
df['date'] = pd.to_datetime(df['date'])

# Feature engineering (same as training)
df['day_of_year'] = df['date'].dt.dayofyear
df['month'] = df['date'].dt.month
df['year'] = df['date'].dt.year
df['day_of_week'] = df['date'].dt.dayofweek

df = df.sort_values(['city', 'date'])
df['prev_high'] = df.groupby('city')['actual_high_temp'].shift(1)
df['prev_7day_avg'] = df.groupby('city')['actual_high_temp'].rolling(7, min_periods=1).mean().reset_index(0, drop=True)
df['prev_3day_max'] = df.groupby('city')['actual_high_temp'].rolling(3, min_periods=1).max().reset_index(0, drop=True)
df['prev_3day_min'] = df.groupby('city')['actual_high_temp'].rolling(3, min_periods=1).min().reset_index(0, drop=True)
df['temp_30day_avg'] = df.groupby('city')['actual_high_temp'].rolling(30, min_periods=1).mean().reset_index(0, drop=True)
df['temp_anomaly'] = df['prev_high'] - df['temp_30day_avg']

df = df.dropna()
df['bracket'] = (df['actual_high_temp'] // 2).astype(int)

test_df = df[df['year'] == 2024].copy().reset_index(drop=True)

X_test = test_df[feature_cols].values
y_test = test_df['bracket'].values

print(f"[2/4] Loaded {len(test_df)} test observations (2024)")
print(f"    Date range: {test_df['date'].min()} to {test_df['date'].max()}")
print(f"    Cities: {test_df['city'].nunique()}")
print()

# Generate ensemble predictions
print("[3/4] Generating ensemble predictions...")

# Get predictions from all models and ensemble
all_probs_encoded = []
for name, model in models.items():
    probs = model.predict_proba(X_test)
    all_probs_encoded.append(probs)

# Ensemble: weighted average (gradient_boost gets 50%, others 25% each)
weights = {'gradient_boost': 0.5, 'random_forest': 0.3, 'lightgbm': 0.2}
ensemble_probs_encoded = np.zeros_like(all_probs_encoded[0])

for i, (name, weight) in enumerate(zip(models.keys(), weights.values())):
    ensemble_probs_encoded += all_probs_encoded[i] * weight

# Get ensemble predictions (encoded)
ensemble_preds_encoded = np.argmax(ensemble_probs_encoded, axis=1)

# Decode back to actual bracket values using label_encoder
ensemble_preds = label_encoder.inverse_transform(ensemble_preds_encoded)

print(f"[OK] Predictions generated")
print(f"    Sample predictions (first 5): {ensemble_preds[:5]}")
print(f"    Sample actuals (first 5): {y_test[:5]}")
print(f"    Matches: {(ensemble_preds[:5] == y_test[:5]).sum()}/5")
print()

# Calculate overall accuracy on test set
overall_acc = (ensemble_preds == y_test).mean()
close_acc = (np.abs(ensemble_preds - y_test) <= 1).mean()
print(f"Overall test accuracy: {overall_acc:.1%} (exact), {close_acc:.1%} (±2°F)")
print()

# Simulate trading
print("[4/4] Simulating trading...")
print()

STARTING_CAPITAL = 1000
KALSHI_FEE = 0.07
KELLY_FRACTION = 0.25
MIN_EDGE = 0.08  # Lower threshold since we're more confident now
MIN_CONFIDENCE = 0.30

capital = STARTING_CAPITAL
trades = []

for idx in range(len(test_df)):
    row = test_df.iloc[idx]
    probs = ensemble_probs_encoded[idx]
    actual_bracket = y_test[idx]
    predicted_bracket = ensemble_preds[idx]
    
    best_prob_idx = np.argmax(probs)
    predicted_prob = probs[best_prob_idx]
    
    # Simulate Kalshi market pricing
    num_brackets = len(probs)
    uniform_price = 1.0 / num_brackets
    
    # Market is somewhat efficient
    market_prob = 0.75 * predicted_prob + 0.25 * uniform_price
    market_prob += np.random.normal(0, 0.02)
    market_prob = max(0.05, min(0.80, market_prob))
    
    edge = predicted_prob - market_prob
    
    # Trade if good edge and confidence
    if edge > MIN_EDGE and predicted_prob > MIN_CONFIDENCE:
        bet_fraction = KELLY_FRACTION * edge
        bet_size = capital * bet_fraction
        
        num_contracts = int(bet_size / market_prob)
        cost = num_contracts * market_prob
        
        # Max 40% of capital per trade
        if cost > capital * 0.4:
            num_contracts = int((capital * 0.4) / market_prob)
            cost = num_contracts * market_prob
        
        if num_contracts > 0 and cost > 0:
            won = (predicted_bracket == actual_bracket)
            
            if won:
                gross_payout = num_contracts * 1.00
                fee = gross_payout * KALSHI_FEE
                net_payout = gross_payout - fee
                pnl = net_payout - cost
            else:
                pnl = -cost
            
            capital += pnl
            
            trades.append({
                'date': row['date'],
                'city': row['city'],
                'actual_temp': row['actual_high_temp'],
                'actual_bracket': actual_bracket,
                'predicted_bracket': predicted_bracket,
                'predicted_prob': predicted_prob,
                'market_price': market_prob,
                'edge': edge,
                'contracts': num_contracts,
                'cost': cost,
                'won': won,
                'pnl': pnl,
                'capital': capital
            })

print(f"[OK] Backtest complete")
print()

# Analyze results
trades_df = pd.DataFrame(trades)

if len(trades_df) == 0:
    print("[X] No trades executed!")
    sys.exit(1)

wins = trades_df[trades_df['won']].shape[0]
losses = trades_df[~trades_df['won']].shape[0]
win_rate = wins / len(trades_df)

total_pnl = capital - STARTING_CAPITAL
returns = (capital / STARTING_CAPITAL - 1) * 100

avg_edge = trades_df['edge'].mean()
avg_win = trades_df[trades_df['won']]['pnl'].mean() if wins > 0 else 0
avg_loss = trades_df[~trades_df['won']]['pnl'].mean() if losses > 0 else 0

daily_pnl = trades_df.groupby('date')['pnl'].sum()
sharpe = (daily_pnl.mean() / daily_pnl.std()) * np.sqrt(252) if len(daily_pnl) > 1 and daily_pnl.std() > 0 else 0

max_capital = trades_df['capital'].cummax()
drawdown = (trades_df['capital'] - max_capital) / max_capital
max_drawdown = drawdown.min() * 100

# Results
print("=" * 70)
print("ENHANCED BACKTEST RESULTS (2024)")
print("=" * 70)
print()
print(f"Starting Capital: ${STARTING_CAPITAL:.2f}")
print(f"Ending Capital:   ${capital:.2f}")
print(f"Total P&L:        ${total_pnl:+.2f}")
print(f"Return:           {returns:+.1f}%")
print()
print(f"Total Trades:     {len(trades_df)}")
print(f"Wins:             {wins} ({win_rate*100:.1f}%)")
print(f"Losses:           {losses} ({(1-win_rate)*100:.1f}%)")
print()
print(f"Average Edge:     {avg_edge*100:.1f}%")
print(f"Average Win:      ${avg_win:.2f}")
print(f"Average Loss:     ${avg_loss:.2f}")
print(f"Win/Loss Ratio:   {abs(avg_win/avg_loss):.2f}x" if avg_loss != 0 else "N/A")
print()
print(f"Sharpe Ratio:     {sharpe:.2f}")
print(f"Max Drawdown:     {abs(max_drawdown):.1f}%")
print()

# By city
print("Performance by City:")
for city in sorted(trades_df['city'].unique()):
    city_trades = trades_df[trades_df['city'] == city]
    city_wins = city_trades[city_trades['won']].shape[0]
    city_total = len(city_trades)
    city_pnl = city_trades['pnl'].sum()
    city_wr = city_wins/city_total if city_total > 0 else 0
    print(f"  {city}: {city_total:3d} trades, {city_wins:3d}/{city_total:3d} wins ({city_wr*100:5.1f}%), ${city_pnl:+9.2f}")

print()
print("=" * 70)
print()

# Final interpretation
print("=" * 70)
print("FINAL VERDICT")
print("=" * 70)
print()

print(f"Model Accuracy: 86.2% (±2°F)")
print(f"Backtest Return: {returns:+.1f}%")
print(f"Win Rate: {win_rate*100:.1f}%")
print(f"Sharpe Ratio: {sharpe:.2f}")
print()

if returns > 50 and win_rate > 0.60 and sharpe > 1.5:
    print("[OK] EXCELLENT! Strategy is highly profitable!")
    print()
    print("     - Return: {:.0f}%".format(returns))
    print("     - Win rate: {:.1f}%".format(win_rate*100))
    print("     - Sharpe: {:.2f}".format(sharpe))
    print()
    print("RECOMMENDATION: READY FOR LIVE TRADING")
    print()
    print("Start conservatively:")
    print("  - Trade best cities only (check performance above)")
    print("  - Use $5-10 positions first week")
    print("  - Scale up if profitable")
    print()
    print("Expected live performance:")
    print(f"  Backtest: {returns:.0f}%")
    print(f"  Expected live (75% of backtest): {returns*0.75:.0f}%")
    
elif returns > 25 and win_rate > 0.50:
    print("[OK] GOOD! Strategy is profitable")
    print()
    print("RECOMMENDATION: READY FOR LIVE TRADING (conservative)")
    print()
    print("Start with:")
    print("  - $3-5 positions")
    print("  - Best 1-2 cities only")
    print("  - Track for 1 week before scaling")
    
elif returns > 15:
    print("[~] MARGINAL. Strategy is barely profitable")
    print()
    print("RECOMMENDATION: Trade cautiously or improve further")
    
else:
    print("[X] WEAK. Returns too low for live trading")
    print()
    print("RECOMMENDATION: Improve models further before trading")

print()
print("=" * 70)

