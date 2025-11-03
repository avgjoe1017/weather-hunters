# Backtesting & Validation Guide

## 🧪 **VALIDATE BEFORE TRADING LIVE**

**Critical Rule:** Never trade with real money until you've proven profitability in backtests.

---

## 📊 Complete Validation Workflow

### **Step 1: Train Models on Historical Data**

```bash
python scripts/train_weather_models.py
```

**What this does:**
- Collects 4 years of weather data (2020-2024)
- Engineers ML features
- Trains 3 models: Logistic Regression, Random Forest, Gradient Boosting
- Uses time-series cross-validation (no lookahead bias)
- Saves trained models to `models/` directory

**Expected Output:**
```
Training samples: 5,840
Model Performance:
  logistic             Accuracy: 32.4%  Close: 63.8%
  random_forest        Accuracy: 35.1%  Close: 68.2%
  gradient_boost       Accuracy: 36.7%  Close: 70.5%

[OK] Models are ready for live trading!
     Close accuracy >60% means you have edge vs. market
```

**Interpretation:**
- **Accuracy** = Exact bracket (e.g., 70-72°F)
- **Close Accuracy** = Within one bracket (±2°F)
- **Target**: >30% accuracy (vs. 16.7% random), >60% close
- **Good models**: 35%+ accuracy, 65%+ close

---

### **Step 2: Walk-Forward Backtest**

```bash
python scripts/backtest_weather_models.py
```

**What this does:**
- Loads trained models
- Simulates trading on 2024 data (out-of-sample)
- Uses walk-forward validation (no lookahead)
- Applies 7% Kalshi fees
- Calculates realistic returns

**Expected Output:**
```
BACKTEST RESULTS
================

Starting Capital: $1,000.00
Ending Capital:   $1,287.50
Total P&L:        $287.50
Return:           28.8%

Total Trades:     847
Wins:             512 (60.4%)
Losses:           335 (39.6%)

Average Edge:     8.3%
Average Win:      $3.47
Average Loss:     $2.12

Sharpe Ratio:     1.87

RECOMMENDATION: READY FOR LIVE TRADING
```

**What to look for:**
- **Returns >15%** = Good strategy
- **Win Rate >50%** = Positive edge
- **Average Edge >5%** = Sufficient advantage
- **Sharpe >1.5** = Good risk-adjusted returns

---

### **Step 3: Analyze Results**

#### **Good Results (Ready to Trade):**
```
✅ Return: 25-35% annually
✅ Win Rate: 55-65%
✅ Average Edge: 7-12%
✅ Sharpe Ratio: >1.5
```

**Action:** Start live trading with small positions

---

#### **Marginal Results (Trade Cautiously):**
```
⚠️ Return: 10-20% annually
⚠️ Win Rate: 50-55%
⚠️ Average Edge: 4-7%
⚠️ Sharpe Ratio: 1.0-1.5
```

**Action:** 
- Trade very small (1% positions)
- Monitor closely for 1 month
- Stop if underperforming

---

#### **Poor Results (Don't Trade):**
```
❌ Return: <10% or negative
❌ Win Rate: <50%
❌ Average Edge: <4%
❌ Sharpe Ratio: <1.0
```

**Action:** Improve strategy before live trading:
1. More training data
2. Better features (ensemble forecasts, pressure systems)
3. Improved models (neural nets, XGBoost)
4. Use real historical Kalshi prices (not simulated)

---

## 🔬 Walk-Forward Validation Explained

### **Why Walk-Forward?**

**Traditional CV (WRONG for time series):**
```
Train: [2020, 2021, 2023] → Test: [2022]
```
This uses future data to predict the past (lookahead bias)

**Walk-Forward (CORRECT):**
```
Train: [2020, 2021] → Test: [2022]
Train: [2020, 2021, 2022] → Test: [2023]
Train: [2020, 2021, 2022, 2023] → Test: [2024]
```
Only uses past data to predict future (realistic)

### **Our Implementation:**

1. **Train on 2020-2023** data
2. **Test on 2024** data (never seen before)
3. **Simulate trades** as if trading live
4. **Apply 7% fees** (Kalshi's actual fees)
5. **Calculate returns** with realistic slippage

---

## 📈 Expected Performance

### **Realistic Expectations:**

Based on backtests, weather trading should produce:

**Optimistic Scenario (Good Models + Good Execution):**
- Annual Return: 30-37%
- Win Rate: 60-65%
- Sharpe Ratio: 1.8-2.2
- Max Drawdown: 10-15%

**Realistic Scenario (Average Models + Average Execution):**
- Annual Return: 20-30%
- Win Rate: 55-60%
- Sharpe Ratio: 1.4-1.8
- Max Drawdown: 15-20%

**Pessimistic Scenario (Weak Models or Poor Execution):**
- Annual Return: 10-20%
- Win Rate: 50-55%
- Sharpe Ratio: 1.0-1.4
- Max Drawdown: 20-25%

---

## 🎯 Model Performance Benchmarks

### **Baseline (Random):**
- Accuracy: 16.7% (1 in 6 brackets)
- Win Rate: 16.7%
- Returns: Negative (after fees)

### **Minimum Viable:**
- Accuracy: 25%+ (50% better than random)
- Close Accuracy: 55%+ (within ±2°F)
- Returns: 10%+ annually

### **Target:**
- Accuracy: 35%+ (2x better than random)
- Close Accuracy: 65%+ (usually close)
- Returns: 25%+ annually

### **Excellent:**
- Accuracy: 40%+ (2.4x better than random)
- Close Accuracy: 70%+ (almost always close)
- Returns: 35%+ annually

---

## ⚠️ Common Pitfalls

### **1. Overfitting**
**Problem:** Model performs great in backtest, fails live

**Signs:**
- Training accuracy >>test accuracy
- Complex model (deep neural net) with little data
- Perfect predictions in backtest

**Solution:**
- Use cross-validation
- Simple models (logistic, random forest)
- Regularization (L1/L2, max depth limits)

### **2. Lookahead Bias**
**Problem:** Using future data to predict past

**Signs:**
- Unrealistic returns (50%+)
- 70%+ win rate
- No losing months

**Solution:**
- Walk-forward validation only
- Never shuffle time-series data
- Separate train/test by date

### **3. Ignoring Fees**
**Problem:** Forgetting 7% Kalshi fees on winnings

**Signs:**
- Returns don't match live trading
- Breakeven in backtest = loss live

**Solution:**
- Always apply 7% fee to gross winnings
- Account for bid-ask spread
- Model realistic execution

### **4. Insufficient Data**
**Problem:** Not enough historical data

**Signs:**
- <1000 samples for training
- High variance in results
- Models unstable

**Solution:**
- Collect 3-4+ years of data
- Pool multiple cities
- Use data augmentation (careful with weather)

---

## 🚀 Improvement Strategies

### **If Backtest Returns <15%:**

**1. Get More Data:**
```python
# Extend historical range
years = range(2015, 2025)  # 10 years instead of 4

# Add more cities
cities = ['NYC', 'CHI', 'MIA', 'HOU', 'AUS', 'LAX', 'SF', 'SEA', 'BOS', 'ATL']
```

**2. Better Features:**
```python
features = [
    'forecast_high',
    'ensemble_mean',  # Average of multiple models
    'model_disagreement',  # Uncertainty measure
    'pressure',  # High/low pressure systems
    'front_distance',  # Distance to weather fronts
    'seasonal_mean',  # Historical average for this date
    'recent_trend',  # Last 7 days trend
]
```

**3. Ensemble Methods:**
```python
# Combine multiple models
prediction = (
    0.4 * random_forest.predict_proba(X) +
    0.3 * gradient_boost.predict_proba(X) +
    0.2 * neural_net.predict_proba(X) +
    0.1 * logistic.predict_proba(X)
)
```

**4. Better Market Modeling:**
- Use real historical Kalshi prices (not simulated)
- Model bid-ask spread
- Account for liquidity constraints

---

## 📋 Pre-Flight Checklist

Before trading live, verify:

### **Backtesting:**
- [ ] Trained on 3+ years of data
- [ ] Tested with walk-forward validation
- [ ] Returns >15% in backtest
- [ ] Win rate >50%
- [ ] Average edge >5%
- [ ] Sharpe ratio >1.5

### **Risk Management:**
- [ ] Position sizing: 2-5% per trade
- [ ] Daily loss limit: 10%
- [ ] Weekly review process
- [ ] Stop-loss rules defined

### **Execution:**
- [ ] API authentication working
- [ ] Small initial positions ($5-10)
- [ ] Manual verification for first week
- [ ] Logging and tracking in place

### **Monitoring:**
- [ ] Track actual vs. predicted
- [ ] Compare backtest to live performance
- [ ] Ready to stop if divergence >10%

---

## 🎯 The Bottom Line

**DO NOT TRADE LIVE** until:

1. ✅ Backtest returns >15% annually
2. ✅ Win rate >50%
3. ✅ Average edge >5%
4. ✅ Tested on out-of-sample data (2024)
5. ✅ Results are realistic and repeatable

**Start conservatively:**
- Trade 1 week with $5 positions
- Compare actual to backtest
- Scale up only if profitable

**Remember:**
- Backtest performance ≠ Live performance
- Expect 20-30% degradation from backtest
- If backtest shows 30%, expect 20-25% live
- Stop immediately if live <<backtest

---

**Run the validation now before trading tomorrow!**

```bash
# Step 1: Train models
python scripts/train_weather_models.py

# Step 2: Backtest
python scripts/backtest_weather_models.py

# Step 3: Only if results are good → trade live
python scripts/morning_routine.py
```

