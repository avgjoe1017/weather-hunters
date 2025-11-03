# Battle of the Models - The Real Alpha Strategy

**Date:** November 3, 2025  
**Discovery:** Kalshi Forecast Percentile History API  
**Status:** Game-changing breakthrough

---

## 🚀 **The Breakthrough Discovery**

### **What We Found:**

Kalshi has a live API endpoint that provides their **internal forecast history**:

```
GET /series/{series_ticker}/events/{ticker}/forecast_percentile_history
```

**What this is:**
- Kalshi's own data science team's probabilistic forecasts
- Historical predictions for past events
- Available at various percentiles (we use 50th = median)

**What this is NOT:**
- Not market prices (bid/ask spread)
- Not raw ensemble data (ECMWF/GFS individual models)
- Not settlement data

**Why it matters:**
- We can now compare OUR model vs. THEIR model
- We can identify when WE are right and THEY are wrong
- **That's the alpha**

---

## 💡 **The New Strategy: Model Arbitrage**

### **Old Approach (Simulated):**

**Problem:**
- We simulated ALL forecasts based on assumptions
- We simulated market prices based on assumptions
- Result: +3,050% was a hypothesis with too many unknowns

### **New Approach (Real Data):**

**Solution:**
- Y (Ground Truth): ✅ 100% REAL (NOAA GHCND data)
- X1 (Our Forecasts): ✅ REAL (Open-Meteo Historical API)
- X2 (Kalshi Forecasts): ✅ REAL (Kalshi Forecast History API)
- Market Prices: ⚠️ Smart simulation (based on X2)

**Result:**
- 90% real data (only prices simulated)
- Much more reliable backtest
- Can validate "battle of the models" hypothesis

---

## 🎯 **How It Works**

### **Step 1: Collect the Data**

**Three data sources:**

1. **NOAA Ground Truth** (already have this)
   - Script: Already collected
   - File: `data/weather/nws_settlement_ground_truth_OFFICIAL.csv`
   - Status: ✅ Complete

2. **Kalshi Internal Forecasts** (NEW)
   - Script: `scripts/collect_kalshi_forecast_history.py`
   - API: `GET /series/{ticker}/events/{event}/forecast_percentile_history`
   - Output: `data/weather/kalshi_forecast_history.csv`
   - Data: What KALSHI predicted before outcome

3. **Open-Meteo Historical Forecasts** (PAID)
   - Script: `scripts/collect_open_meteo_historical_forecasts.py`
   - API: Open-Meteo Historical Forecast Archive
   - Output: `data/weather/open_meteo_historical_forecasts.csv`
   - Data: What ECMWF/GFS/GDPS predicted before outcome
   - Cost: ~€10-50/month

### **Step 2: Merge & Analyze**

**Script:** `scripts/merge_all_forecast_data.py`

**What it does:**
- Merges all three sources on date + city
- Calculates model disagreement
- Identifies when models were correct
- Shows where alpha exists

**Key Metric:**
```
model_disagreement = |kalshi_forecast - open_meteo_forecast|
```

**The Alpha:**
- When `model_disagreement > 2°F` → Models strongly disagree
- Check historical accuracy: WHO was usually right?
- Trade AGAINST the less accurate model

### **Step 3: Train "Meta-Model"**

**Objective:** Predict which model will be correct

**Features:**
- `kalshi_forecast_temp` - Kalshi's prediction
- `open_meteo_forecast_temp` - Our ensemble prediction
- `model_disagreement` - How much they disagree
- Historical accuracy - Who was right more often in similar situations

**Output:**
- Confidence score: "Trade this" or "Skip this"
- Predicted winner: "Trust Kalshi" or "Fade Kalshi"

---

## 📊 **The Alpha Sources**

### **Source 1: Kalshi Overconfidence**

**Hypothesis:** Kalshi's model may be overconfident in certain conditions

**Example:**
- Kalshi predicts: 75°F
- Open-Meteo ensemble: 70°F
- Actual: 71°F
- **Winner:** Open-Meteo

**When to trade:**
- Large disagreement (>2°F)
- Historical pattern shows Open-Meteo more accurate
- Market price reflects Kalshi's forecast

### **Source 2: Ensemble Advantage**

**Hypothesis:** Multi-model ensemble (ECMWF+GFS+GDPS) beats single model

**Why it works:**
- Diversification reduces model risk
- Captures different strengths (ECMWF for Europe influence, GFS for US)
- Ensemble spread = confidence measure

**When to trade:**
- Our ensemble_spread is low (high confidence)
- Kalshi disagrees with our ensemble
- Historical shows ensemble wins in this regime

### **Source 3: Update Lag**

**Hypothesis:** Kalshi's model may update slower than live weather models

**Opportunity:**
- Rapid weather changes
- New data available (satellite, radar)
- Kalshi hasn't updated, we have

**When to trade:**
- High volatility days
- Recent forecast shifts
- Kalshi forecast is stale

---

## 🔬 **Testing the Hypothesis**

### **Backtest Validation:**

**Old backtest (simulated):**
- +3,050% return
- 60.3% win rate
- **Status:** Hypothesis

**New backtest (real data):**
- Uses real Kalshi forecasts
- Uses real Open-Meteo forecasts
- Only market prices simulated
- **Status:** Much more reliable

**Questions to answer:**
1. How often do Kalshi and Open-Meteo disagree?
2. When they disagree, who is usually right?
3. Can we predict the winner?
4. Is there exploitable alpha?

### **Forward Test Validation:**

**30-day live collection (still required):**
- Validates market price assumptions
- Confirms alpha persists in live trading
- Tests execution reality

---

## 💻 **Implementation Steps**

### **Phase 1: Data Collection (Today)**

```bash
# Step 1: Collect Kalshi forecast history
python scripts/collect_kalshi_forecast_history.py
```

**What to expect:**
- May find limited historical data (Kalshi may only have recent events)
- Will show what date ranges are available
- If no data: Forward test becomes primary method

```bash
# Step 2: (Optional) Collect Open-Meteo historical
python scripts/collect_open_meteo_historical_forecasts.py
```

**Note:** Requires paid API key (~€10-50/month)

```bash
# Step 3: Merge all data
python scripts/merge_all_forecast_data.py
```

**Output:** Single dataset with all forecasts + ground truth

---

### **Phase 2: Analysis (Today)**

After merging, analyze:

**Key Questions:**
1. What % of dates have Kalshi forecast data?
2. What % have Open-Meteo forecast data?
3. How often do they disagree (>2°F)?
4. When they disagree, who wins?

**Expected Findings:**
- If Kalshi has limited history → Forward test more important
- If disagreement is rare → Less alpha than expected
- If one model dominates → Use the winner, ignore loser
- If it's context-dependent → Build meta-model

---

### **Phase 3: Rebuild Backtest (Tomorrow)**

**New backtest script:**
```python
# scripts/backtest_real_forecast_strategy.py

# Load merged data (100% real forecasts)
df = pd.load_csv('data/weather/merged_real_forecast_data.csv')

# Filter to high-disagreement days
trades = df[df['model_disagreement'] > 2.0]

# Predict winner (meta-model or simple rule)
trades['predicted_winner'] = predict_winner(trades)

# Simulate trading
# - Use Kalshi forecast to estimate market price
# - Take position based on our prediction
# - Check against actual outcome

# Calculate P&L with 7% fees
```

---

## 📈 **Expected Outcomes**

### **Scenario 1: Historical Data is Available**

**If we get 2-3 years of Kalshi + Open-Meteo forecasts:**
- Build robust "battle of models" backtest
- Calculate real alpha from model disagreement
- Get realistic win rate estimate
- **Decision:** If profitable → Forward test → Go live

### **Scenario 2: Limited Historical Data**

**If Kalshi only has 3-6 months of history:**
- Smaller sample size
- Less reliable backtest
- **Decision:** Forward test becomes primary validation

### **Scenario 3: No Historical Data**

**If Kalshi doesn't provide historical forecasts:**
- Can't backtest model arbitrage
- **Decision:** Forward test is mandatory
- Still valuable: Can collect Kalshi forecasts going forward

---

## 🎯 **The Bottom Line**

### **What Changed:**

**Before (Simulated):**
- Y: Real
- X: Simulated
- Prices: Simulated
- **Confidence:** Low

**After (User's Discovery):**
- Y: Real (NOAA)
- X1: Real (Open-Meteo historical)
- X2: Real (Kalshi forecast history)
- Prices: Smart simulation (based on X2)
- **Confidence:** Much higher

### **The New Alpha:**

**Old hypothesis:**
```
Our edge = Better weather forecasts than the market
```

**New hypothesis:**
```
Our edge = Identifying when Kalshi's model is wrong
```

**Why this is better:**
- Kalshi's forecast is observable (via API)
- We can backtest this hypothesis (with real data)
- We can measure disagreement quantitatively
- The alpha is more specific and testable

### **Next Actions:**

1. ✅ Created `scripts/collect_kalshi_forecast_history.py`
2. ✅ Created `scripts/collect_open_meteo_historical_forecasts.py`
3. ✅ Created `scripts/merge_all_forecast_data.py`
4. ⏳ Run collection scripts (check data availability)
5. ⏳ Analyze model disagreement patterns
6. ⏳ Rebuild backtest with real forecasts
7. ⏳ Compare to simulated backtest (+3,050%)
8. ⏳ Forward test (still required for market prices)

---

## 🔗 **References**

- **Kalshi Forecast API:** https://docs.kalshi.com/api-reference/events/get-event-forecast-percentile-history
- **Open-Meteo Historical:** https://open-meteo.com/en/docs/historical-forecast-api
- **NOAA GHCND:** https://www.ncei.noaa.gov/products/land-based-station/global-historical-climatology-network-daily

---

**This is the breakthrough we needed. Now let's see what the data tells us.** 🚀📊

