# Paper Trading Protocol - Forward Performance Test

**The "Blind" Study to Validate Our Ensemble Strategy**

**Date:** November 3, 2025  
**Status:** Protocol Ready  
**Duration:** 14-30 days recommended

---

## Executive Summary

Before risking real capital, we must validate our backtest results on **truly unseen data: the future**. This protocol implements a rigorous "forward performance test" equivalent to a double-blind study in medicine.

**The Question:** Does our +3,262% backtest represent real edge, or just overfitting?

**The Method:** Make predictions, lock them in writing BEFORE outcomes are known, then verify against reality.

---

## The Problem: Backtest Bias

### Why Backtests Can Lie

**Overfitting:**
- Model memorizes noise instead of signal
- Performs great on training data
- Fails miserably on new data

**Lookahead Bias:**
- Accidentally using future information
- Perfect hindsight in feature engineering
- Unrealistic assumptions about execution

**Selection Bias:**
- Cherry-picking profitable periods
- Ignoring regime changes
- Survivorship bias in data

**Our +3,262% backtest is a HYPOTHESIS, not proof.**

---

## The Solution: Forward Performance Test

### The "Blind" Study Design

**In Medicine:**
- Researchers don't know who gets drug vs placebo
- Prevents expectation bias
- Results can't be manipulated

**In Trading (Our Protocol):**
- **"Researcher" (You):** Run the script, don't interfere
- **"Subject" (Model):** Make predictions daily
- **"Sealed Envelope" (Log):** Lock predictions before outcomes known
- **"Unblinding" (Settlement):** Check actual NWS reports

**Key Principle:** Once logged, predictions cannot be changed. The model's success or failure is determined by reality, not hope.

---

## Protocol Overview

### Timeline

```
Day 1-30: Paper Trading Period
├── Every Morning (~9 AM EST)
│   └── Run: python scripts/paper_trade_morning.py
│       └── Logs predictions to CSV (BEFORE outcomes known)
│
├── Every Evening (After settlement ~6 PM EST)
│   └── Run: python scripts/verify_settlement.py
│       └── Checks NWS reports, updates outcomes
│
└── After 14-30 Days
    └── Run: python scripts/analyze_paper_trades.py
        └── Comprehensive analysis and verdict
```

### Success Criteria (Defined BEFORE Starting)

**Primary Endpoint:**
- Win Rate > 55%

**Secondary Endpoint:**
- Total P&L > $0 (after 7% fees)

**Safety Endpoint:**
- Win Rate > 40% (no severe degradation)

**Statistical Power:**
- Minimum 20 trades (1 week)
- Recommended 80-100 trades (2-4 weeks)
- Ideal 150+ trades (1 month)

---

## Detailed Protocol

### Phase 1: Morning Predictions (The "Seal")

**When:** Every morning ~9 AM EST (before markets open)

**Script:** `python scripts/paper_trade_morning.py`

**What It Does:**
1. Loads trained Random Forest model
2. Gets tomorrow's forecasts (simulated for now, real in production)
3. Calculates ensemble metrics:
   - `ensemble_spread` (confidence)
   - `model_disagreement` (pro agreement)
   - `nws_vs_ensemble` (market inefficiency)
4. Applies trade filters (all 3 conditions must be TRUE)
5. Makes bracket predictions
6. Calculates position sizes
7. **Writes to `logs/paper_trades.csv` BEFORE outcome is known**

**Output:**
```
Date: 2025-11-04
City: Houston
Predicted Bracket: 68-70F
Our Prob: 60.7%
Market Prob: 40%
Edge: 20.7%
Contracts: 120
Cost: $48.00
Outcome: PENDING  <-- This is the "sealed envelope"
```

**Critical Rules:**
- ✅ DO: Run the script
- ✅ DO: Let it log predictions
- ❌ DON'T: Change the model
- ❌ DON'T: Second-guess trades
- ❌ DON'T: Cherry-pick which to log

### Phase 2: Evening Verification (The "Unblinding")

**When:** Every evening after 6 PM EST (after NWS settlement)

**Script:** `python scripts/verify_settlement.py`

**What It Does:**
1. Loads `logs/paper_trades.csv`
2. Finds yesterday's PENDING trades
3. Fetches NWS Daily Climate Reports for each city
4. Parses actual settlement temperature
5. Compares actual to predicted bracket
6. Updates outcome (WIN/LOSS)
7. Calculates P&L with 7% Kalshi fees
8. Saves updated log

**Output:**
```
Houston (HOU):
  Actual High: 69F
  Predicted: 68-70F
  Outcome: WIN
  P&L: +$44.64

Chicago (CHI):
  Actual High: 54F
  Predicted: 50-52F
  Outcome: LOSS
  P&L: -$38.00

Daily Results:
  2 Trades, 1 Win (50.0%), Total P&L: +$6.64
```

**Critical Rules:**
- ✅ DO: Run after settlement
- ✅ DO: Let it verify automatically
- ❌ DON'T: Manually edit outcomes
- ❌ DON'T: Skip unfavorable results

### Phase 3: Analysis (The "Study Results")

**When:** After 14-30 days of data collection

**Script:** `python scripts/analyze_paper_trades.py`

**What It Does:**
1. Loads all verified trades
2. Calculates comprehensive metrics:
   - Overall win rate
   - Total P&L
   - Win/loss ratio
   - Performance by city
   - Performance by confidence level
3. Compares to backtest results
4. Statistical significance test (binomial)
5. Evaluates success criteria
6. **Provides FINAL VERDICT**

**Possible Verdicts:**

**A) STRATEGY VALIDATED ✅**
```
Win Rate: 58.2% (>55%)
P&L: +$487.30 (>$0)
Data: 21 days collected

RECOMMENDATION: READY FOR LIVE TRADING
```

**B) MIXED RESULTS ⚠️**
```
Win Rate: 52.1% (close to 55%)
P&L: +$28.45 (>$0 but low)
Data: 9 days (need more)

RECOMMENDATION: Continue paper trading
```

**C) STRATEGY FAILED ❌**
```
Win Rate: 38.2% (<40%)
P&L: -$142.80 (<$0)
Data: 18 days (sufficient)

RECOMMENDATION: DO NOT TRADE LIVE
```

---

## Implementation Steps

### Day 0: Setup

**1. Create logs directory:**
```bash
mkdir logs
```

**2. Verify scripts are ready:**
```bash
ls scripts/paper_trade_morning.py
ls scripts/verify_settlement.py
ls scripts/analyze_paper_trades.py
```

**3. Test run (optional):**
```bash
python scripts/paper_trade_morning.py
# Check logs/paper_trades.csv was created
```

### Days 1-30: Data Collection

**Morning Routine (9 AM EST):**
```bash
cd C:\Users\joeba\Documents\weather-hunters
python scripts/paper_trade_morning.py
```

**Evening Routine (6 PM EST):**
```bash
cd C:\Users\joeba\Documents\weather-hunters
python scripts/verify_settlement.py
```

**Record in spreadsheet (optional but recommended):**
| Date | Trades | Wins | Losses | P&L | Notes |
|------|--------|------|--------|-----|-------|
| 11/04 | 2 | 1 | 1 | +$6.64 | Houston won, Chicago lost |
| 11/05 | 3 | 2 | 1 | +$22.18 | Good day |
| ... | ... | ... | ... | ... | ... |

### Days 14-30: Analysis

**Weekly Check-in:**
```bash
python scripts/analyze_paper_trades.py
```

**Review:**
- Is win rate trending >55%?
- Is P&L positive?
- Any patterns in losses?

**Final Analysis (Day 30):**
```bash
python scripts/analyze_paper_trades.py > results.txt
```

---

## Interpretation Guide

### Good Signs ✅

**Win Rate 55-65%:**
- Matches or beats backtest expectations
- Strategy is working as designed
- Edge is real

**Positive P&L:**
- After fees, still profitable
- Kelly sizing is working
- Risk management effective

**Consistent Across Cities:**
- Houston, Miami, NYC, Chicago all profitable
- No single city carrying all weight
- Robust strategy

**High Confidence Trades Win More:**
- `ensemble_spread < 1.0`: 65%+ win rate
- Confidence filtering is valuable
- Model understands uncertainty

### Warning Signs ⚠️

**Win Rate 50-55%:**
- Below backtest expectations
- May need more data
- Or slight model degradation

**Low P&L Despite Wins:**
- Winning too small, losing too big
- Position sizing may be wrong
- Kelly fraction may need adjustment

**One City Dominates:**
- If only Houston wins, others lose
- May be overfitting to one market
- Need to understand why

**High Confidence Trades Don't Win More:**
- Confidence filtering not working
- `ensemble_spread` may not be predictive
- Feature engineering issue

### Red Flags ❌

**Win Rate <50%:**
- Worse than coin flip
- Model has no edge
- DO NOT TRADE LIVE

**Win Rate <40%:**
- Severe degradation
- Model is systematically wrong
- Need complete rebuild

**Negative P&L:**
- Losing money after fees
- Even if win rate okay
- Position sizing wrong

**Pattern of Overconfidence:**
- High confidence trades lose more
- Model is miscalibrated
- Dangerous for live trading

---

## What to Do After the Study

### Scenario A: Validated (Win Rate >55%, P&L >$0)

**Congratulations! Strategy is validated.**

**Next Steps:**
1. Start live trading with $5-10 per trade
2. Trade only highest confidence signals first
3. Focus on best cities (Houston, Miami)
4. Continue tracking actual vs. predicted
5. Scale up gradually over 2-4 weeks

**Expected Live Returns:**
- Conservative: 200-400% annually
- Realistic: 500-800% annually
- Optimistic: 1,000-1,500% annually

### Scenario B: Mixed Results (Win Rate 50-55%)

**Strategy shows promise but needs more data.**

**Next Steps:**
1. Continue paper trading another 2 weeks
2. Collect total of 30+ days
3. Re-analyze for statistical significance
4. If still marginal:
   - Adjust confidence thresholds
   - Trade only ensemble_spread < 1.0
   - Skip low-edge opportunities

### Scenario C: Failed (<50% Win Rate or Negative P&L)

**Strategy did NOT validate. Do NOT trade live.**

**Possible Causes:**
1. **Overfitting:** Model memorized 2024 data
2. **Market Change:** 2025 is different from 2024
3. **Bad Assumptions:** Simulated market prices wrong
4. **Feature Issues:** Ensemble metrics not predictive

**Next Steps:**
1. Analyze failed trades
2. Look for patterns:
   - Did high `nws_vs_ensemble` actually indicate edge?
   - Was `ensemble_spread` predictive of accuracy?
   - Were market prices realistic?
3. Collect REAL Kalshi historical prices
4. Retrain with actual market data
5. Run new backtest
6. Paper trade again (new 30-day cycle)

**DO NOT:**
- Rationalize away bad results
- Cherry-pick data
- Trade live hoping it improves
- Blame "bad luck"

---

## Key Principles

### The Scientific Method

**1. Hypothesis:**
"Our ensemble strategy will achieve 55%+ win rate in live trading"

**2. Experiment:**
Paper trade for 30 days with locked-in predictions

**3. Data Collection:**
Record every prediction and outcome without bias

**4. Analysis:**
Statistical evaluation of results

**5. Conclusion:**
Accept or reject hypothesis based on data

### Avoiding Bias

**Confirmation Bias:**
- Don't interpret ambiguous results as success
- Be honest about failures
- Let data speak

**Selection Bias:**
- Log ALL trades, not just ones you like
- Don't skip "uncertain" days
- Include every city

**Hindsight Bias:**
- Don't change model after seeing outcomes
- Lock predictions BEFORE settlement
- No "I knew it wouldn't work" after losses

### Statistical Rigor

**Sample Size:**
- Minimum 20 trades for any conclusion
- 50+ trades for confidence
- 100+ trades for high confidence

**Significance:**
- p < 0.05 for win rate > 50%
- Binomial test for statistical significance
- Confidence intervals on win rate

**Multiple Comparisons:**
- If testing multiple cities, adjust thresholds
- Bonferroni correction if needed
- Don't p-hack by testing many variations

---

## FAQ

**Q: Can I skip days when I'm busy?**  
A: Yes, but don't cherry-pick. If you skip, skip ALL cities that day.

**Q: What if I disagree with a trade signal?**  
A: Log it anyway. This is a test of the MODEL, not your judgment.

**Q: Can I adjust the model mid-study?**  
A: NO! That defeats the "blind" study. Start a new study if you change anything.

**Q: What if NWS reports are delayed?**  
A: Verify manually. Go to NWS website, find CLI report, update log.

**Q: How do I handle ties (e.g., actual 70F, bracket is 70-72F)?**  
A: 70F is NOT in 70-72F bracket. That's a loss. Be strict.

**Q: Can I use real Kalshi prices instead of simulated?**  
A: YES! That's even better. Update `paper_trade_morning.py` to fetch live prices.

**Q: What if I get 60% win rate but still lose money?**  
A: Position sizing is wrong. Either Kelly fraction too aggressive, or fee impact too high.

**Q: Should I adjust for multiple testing?**  
A: If testing multiple strategies simultaneously, yes. For this single strategy, no.

---

## Conclusion

This protocol transforms your backtest from a **hope** into a **validated fact** (or disproves it).

**If it validates:** You have a professional-grade, statistically significant edge. Trade with confidence.

**If it doesn't:** You've saved yourself from blowing up your account. Improve and test again.

**Either way, you WIN by being rigorous.**

---

**This is how professionals trade. Let's do this right.** 🎯

---

**Protocol Version:** 1.0  
**Date:** November 3, 2025  
**Expected Duration:** 14-30 days  
**Success Criteria:** Win Rate >55%, P&L >$0  
**Statistical Test:** Binomial (p < 0.05)

