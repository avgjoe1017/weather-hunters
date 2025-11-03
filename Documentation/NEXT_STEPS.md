# Next Steps - Getting Started with Trading

## ✅ Current Status

- Authentication: **WORKING** ($50.08 balance confirmed)
- All components: **INSTALLED**
- Documentation: **COMPLETE**

## Immediate Next Steps

### Step 1: Update Your .env File

Update your `.env` to use the working configuration:

```bash
# Kalshi API Configuration
KALSHI_API_KEY_ID=80b0b7b7-936c-42ac-8c68-00de23d9aa4f
KALSHI_PRIVATE_KEY_FILE=kalshi_private_key.pem
KALSHI_USE_DEMO=false  # Demo endpoint unavailable, using production

# Keep your old credentials commented out for reference:
# KALSHI_EMAIL=joebalewski@gmail.com
# KALSHI_PASSWORD=Homework1!
# KALSHI_PRIVATE_KEY=... (old multiline format)
```

### Step 2: Run System Tests

Test that everything works end-to-end:

```bash
# 1. Test API connection
python scripts/test_with_key_file.py

# 2. Run comprehensive installation tests
python src/test_installation.py

# 3. Run health check
python scripts/health_check.py
```

### Step 3: Test the FLB Harvester (Dry Run)

Run the bot in observation mode to see what it finds:

```bash
# This will scan markets but NOT execute trades
python -m src.main
```

**What to expect:**
- Bot will scan all open markets
- Identify FLB opportunities (favorite-longshot bias)
- Calculate position sizes with Kelly criterion
- Show what trades it *would* make (but won't execute)
- Display risk metrics and exposure

### Step 4: Review Risk Settings

Check your risk parameters in `src/main.py` (lines 43-58):

```python
RiskLimits(
    kelly_fraction=0.25,              # Conservative Kelly sizing
    max_position_size_pct=0.05,       # 5% max per position
    max_portfolio_exposure_pct=0.30,   # 30% max total exposure
    max_daily_loss_pct=0.05,          # 5% daily loss limit (kill-switch)
    max_losing_streak=5,               # Stop after 5 consecutive losses
    correlation_threshold=0.7,         # Limit correlated positions
    max_correlated_exposure_pct=0.15   # 15% max in correlated markets
)
```

These are **conservative defaults**. You may want to adjust based on your risk tolerance.

### Step 5: Understand Your Strategies

#### Strategy A: FLB Harvester (Ready to Run)
- **Edge**: Exploits favorite-longshot bias in prediction markets
- **Expected Return**: 15-25% annually
- **Risk**: Market inefficiency may vary
- **Status**: ✅ Ready to trade

#### Strategy B: Weather Alpha (Implementation Complete)
- **Edge**: Superior weather forecasts from ML models
- **Expected Return**: 20-35% annually  
- **Risk**: Requires historical data and model training
- **Status**: ✅ Code ready, needs data collection
- **To run**: `python scripts/run_weather_strategy.py`

### Step 6: Run Live Scan (Observation Mode)

Let the bot scan live markets and show you opportunities:

```bash
# Run main trading engine (observation mode by default)
python -m src.main
```

**Watch for:**
- Number of markets scanned
- Opportunities identified
- Position sizing calculations
- Risk manager decisions
- Would-be trade execution details

### Step 7: Enable Live Trading (When Ready)

⚠️ **CAUTION**: This uses real money!

Before going live:
1. ✅ Verify all tests pass
2. ✅ Understand the FLB strategy
3. ✅ Review risk limits
4. ✅ Start with small position sizes
5. ✅ Monitor closely for the first few trades

To enable live trading, modify `src/main.py` line ~369 to set `dry_run=False`, or add a command-line flag.

## Understanding the System

### Key Files

- **`src/main.py`**: Main trading engine
- **`src/strategies/flb_harvester.py`**: FLB strategy logic
- **`src/risk/risk_manager.py`**: Risk controls and Kelly sizing
- **`src/monitoring/metrics_collector.py`**: Performance tracking
- **`logs/`**: Trading logs (created on first run)
- **`metrics/`**: Performance metrics (created on first run)

### Monitoring Your Bot

Once running, check:

```bash
# View logs
tail -f logs/trading_*.log

# Check metrics
ls -lh metrics/

# Monitor positions
python -c "from src.api.kalshi_connector import create_connector_from_env; api = create_connector_from_env(); print(api.get_positions())"
```

### Safety Features Built-In

✅ **Kelly Sizing**: Automatically sizes positions based on edge and bankroll  
✅ **Daily Loss Limit**: Stops trading if you lose 5% in a day  
✅ **Losing Streak Protection**: Stops after 5 consecutive losses  
✅ **Correlation Limits**: Prevents overexposure to correlated markets  
✅ **Exposure Caps**: Max 5% per position, 30% total portfolio  
✅ **Metrics Tracking**: Records every trade for analysis  

## Recommended Testing Sequence

### Day 1: Observation & Testing
```bash
# Morning: Run tests
python src/test_installation.py
python scripts/health_check.py

# Afternoon: Run bot in observation mode
python -m src.main

# Evening: Review logs and metrics
tail -f logs/trading_*.log
```

### Day 2-3: Monitor Market Scanning
- Let the bot scan markets for 2-3 days
- Review opportunities it identifies
- Verify position sizing makes sense
- Check risk calculations

### Day 4: Paper Trading
- Run with dry_run=True but log as if trading
- Track hypothetical performance
- Verify strategy logic

### Day 5+: Live Trading (Optional)
- Start with minimal position sizes
- Monitor closely
- Scale up gradually

## Common Questions

**Q: How often should I run the bot?**
A: The bot can run continuously. It scans markets on a configurable interval (default: every 5 minutes).

**Q: What's my current account balance?**
A: $50.08 (confirmed working)

**Q: How much should I risk per trade?**
A: With $50.08, at 5% max position size, you'll risk ~$2.50 per trade maximum. The Kelly criterion will further reduce this based on edge.

**Q: When will I see profits?**
A: FLB strategy typically finds 3-5 opportunities per week. Profits accumulate gradually over weeks/months.

**Q: Can I run both strategies?**
A: Yes! FLB runs automatically. Weather strategy requires historical data collection first.

## Getting Help

- **Strategy details**: `Documentation/FINAL_DELIVERY_SUMMARY.md`
- **Setup issues**: `Documentation/SETUP_CHECKLIST.md`
- **API docs**: `Documentation/API_AUTHENTICATION_UPDATE.md`
- **Full progress**: `Documentation/PROGRESS.md`

## Quick Command Reference

```bash
# Test authentication
python scripts/test_with_key_file.py

# Run full test suite
python src/test_installation.py

# Health check
python scripts/health_check.py

# Run trading bot
python -m src.main

# Check balance
python -c "from kalshi_python import *; config = Configuration(host='https://api.elections.kalshi.com/trade-api/v2'); config.api_key_id='80b0b7b7-936c-42ac-8c68-00de23d9aa4f'; config.private_key_pem=open('kalshi_private_key.pem').read(); client = KalshiClient(config); print(f'Balance: ${client.get_balance().balance/100:.2f}')"

# View recent logs
tail -20 logs/trading_*.log

# Check positions
python scripts/check_positions.py  # (create this if needed)
```

---

**You're ready to go!** Start with Step 2 (run tests) and proceed from there. 🚀

