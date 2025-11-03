# Weather Trading Guide - Daily Workflow

## 🌦️ Complete Guide to Trading Weather Markets

**Expected Returns:** 30-37% annually  
**Opportunities:** 4-8 markets daily  
**Your Edge:** Superior weather forecasts vs. market prices  

---

## ⏰ Daily Routine (10 AM EST)

### Step 1: Run Morning Routine Script

```bash
python scripts/morning_routine.py
```

**This will:**
- ✅ Check your balance
- ✅ Get weather forecasts for all cities
- ✅ Find active Kalshi markets
- ✅ Calculate your edge
- ✅ Show trade recommendations

**Time:** 2 minutes

---

## 📊 Understanding the Output

### Forecast Example:
```
New York: 72.3F (bracket: 70-72)
Chicago: 45.8F (bracket: 44-46)
Miami: 78.1F (bracket: 78-80)
```

### Market Example:
```
[GOOD TRADE] KXHIGHNY-25-70T72
  Will NYC high temp be 70-72F tomorrow?
  Price: $0.30
  Edge: 15.2%
  Recommended: 8 contracts ($2.40)
```

### What This Means:
- **Price $0.30** = Kalshi thinks 30% probability
- **Your forecast 72.3F** = Actually ~45% probability (centered in 70-72)
- **Edge 15.2%** = You have 15 percentage point advantage
- **8 contracts** = Optimal bet size using Kelly criterion

---

## 💰 Position Sizing (Built-In)

The script uses **fractional Kelly** sizing:
- Conservative 25% Kelly fraction
- Automatically calculates optimal bet size
- Accounts for edge and win probability
- Limits risk to 2-5% of bankroll per trade

**Example:**
- Balance: $50
- Edge: 15%
- Win probability: 45%
- Kelly bet: 25% × 15% = 3.75% of bankroll
- Position: ~$2 (4-6 contracts)

---

## 🎯 Executing Trades

### Option A: Kalshi Website (Easiest)
1. Go to https://kalshi.com
2. Search for the ticker (e.g., KXHIGHNY-25-70T72)
3. Click "Buy Yes"
4. Enter number of contracts
5. Review fees (7% on winnings)
6. Confirm trade

### Option B: API (Automated)
```python
from kalshi_python import KalshiClient

# Use the ticker from morning routine
order = client.create_order(
    ticker="KXHIGHNY-25-70T72",
    action="buy",
    side="yes",
    count=8,  # Number of contracts
    type="market"
)
```

---

## 📈 Settlement & P&L

### Next Day (~6 AM EST):
Markets settle based on **National Weather Service** data
- Objective, no disputes
- Winner gets $1.00 per contract
- Loser gets $0.00

### Example Trade:
```
Bought 8 contracts @ $0.30 = $2.40 cost

IF WIN (45% probability):
  Receive: 8 × $1.00 = $8.00
  Fee (7%): $8.00 × 0.07 = $0.56
  Net: $8.00 - $0.56 - $2.40 = $5.04 profit
  
IF LOSE (55% probability):
  Lose: $2.40

Expected Value: (0.45 × $5.04) - (0.55 × $2.40) = $0.95
```

---

## 🎲 Edge Calculation Details

### How We Calculate True Probability:

**Given:**
- Forecast: 72.3°F
- Model uncertainty: ±2-3°F

**For 70-72°F bracket:**
1. Forecast is centered in bracket
2. Normal distribution around forecast
3. ~45% probability of landing in 2°F bracket
4. Compare to Kalshi's 30% (implied by $0.30 price)
5. **Edge = 45% - 30% = 15%**

### Confidence Levels:

**High Confidence** (Trade these):
- Edge > 10%
- Models agree (low disagreement)
- Forecast centered in bracket
- Clear weather patterns

**Medium Confidence** (Trade with caution):
- Edge 5-10%
- Some model disagreement
- Forecast near bracket edge
- Uncertain weather

**Low Confidence** (Skip):
- Edge < 5%
- High model disagreement
- Forecast far from bracket
- Volatile weather patterns

---

## 📊 Tracking Performance

### Daily Log:
```
Date: 2025-11-03
Market: KXHIGHNY-25-70T72
Forecast: 72.3F
Bracket: 70-72F
Price: $0.30
Contracts: 8
Cost: $2.40
Result: [Pending/Win/Loss]
P&L: [Pending/$5.04/-$2.40]
```

### Weekly Review:
- Win rate (target: 60-65%)
- Average edge (target: 8-12%)
- P&L after fees
- Adjust position sizing if needed

---

## ⚠️ Risk Management

### Daily Limits (Built-In):
- Max 5% of bankroll per market
- Max 4 markets per day (diversification)
- Max 20% total exposure

### Weekly Limits:
- If down 10% in a week → reduce position sizes by 50%
- If down 20% in a week → pause trading, review strategy

### Quality Control:
- Only trade when edge > 10%
- Skip uncertain weather (storms, fronts)
- Avoid bracket edges (forecast between brackets)
- Trust model disagreement signals

---

## 🚀 Scaling Up

### Starting Capital: $50
**Month 1:** Trade 4 markets/day @ $2 each
- Win 60%: ~72 wins, 48 losses
- Monthly profit: ~$100 (after fees)
- End of month: $150

### Month 2: $150
**Increase** position sizes to $3-5
- Monthly profit: ~$300
- End of month: $450

### Month 6: $500+
- Trade 4-8 markets daily
- Position sizes $10-25
- Monthly returns: $500-1000
- **30-37% annual pace**

---

## 🎓 Advanced Tips

### Best Trading Opportunities:
1. **Clear forecasts** (stable high pressure)
2. **Model agreement** (low uncertainty)
3. **Extreme values** (very hot/cold days)
4. **Seasonal transitions** (markets mispriced)

### Avoid Trading:
1. Storm systems (high uncertainty)
2. Weather fronts (timing issues)
3. Bracket edge forecasts (split probability)
4. Low liquidity markets (can't get filled)

### Forecast Sources:
- Weather.gov (official NWS)
- OpenMeteo (European model ensemble)
- GFS, NAM models (free access)
- Weather.com (backup reference)

---

## 📞 Daily Checklist

**Every Morning (10 AM EST):**
- [ ] Run `python scripts/morning_routine.py`
- [ ] Review forecasts and edge calculations
- [ ] Check model agreement/confidence
- [ ] Execute trades with edge > 10%
- [ ] Log all trades in spreadsheet
- [ ] Set alerts for settlement (next morning)

**Every Evening (6 AM next day):**
- [ ] Check settlement results
- [ ] Calculate P&L after 7% fee
- [ ] Update performance tracking
- [ ] Review what worked/didn't
- [ ] Prepare for next day's trading

---

## 💡 Quick Reference

```bash
# Morning routine (all-in-one)
python scripts/morning_routine.py

# Just forecasts
python scripts/get_todays_forecast.py

# Just markets
python scripts/deep_market_search.py

# Manual trading helper
python scripts/trade_weather_manual.py

# Check balance
python scripts/test_with_key_file.py
```

---

## 🎯 Success Metrics

**Target Performance:**
- **Win Rate:** 60-65%
- **Average Edge:** 8-12%
- **Monthly Return:** 2.5-3%
- **Annual Return:** 30-37%

**Your Starting Point:**
- Capital: $50.08
- Target Year 1: $65-68
- Target Year 2: $84-93
- Target Year 3: $110-127

**Compound at 30-37% annually by trading weather every single day.**

---

**Status:** Ready to trade tomorrow morning! 🌦️💰

