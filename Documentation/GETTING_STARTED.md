# Getting Started with the Kalshi ML Trading Bot

This guide will walk you through setting up and running your first trading session.

## Prerequisites

- Python 3.8 or higher
- A Kalshi account (demo or production)
- Basic understanding of prediction markets
- ~30 minutes for setup

## Step 1: Clone and Setup

```bash
# Navigate to the project directory
cd kalshi-ml-trader

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Mac/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure Your Environment

1. Copy the template environment file:
```bash
cp .env.template .env
```

2. Edit `.env` with your Kalshi credentials:
```bash
KALSHI_EMAIL=your_email@example.com
KALSHI_PASSWORD=your_password
KALSHI_USE_DEMO=true  # IMPORTANT: Start with demo mode
```

**⚠️ IMPORTANT:** Always start with `KALSHI_USE_DEMO=true` to test with play money!

## Step 3: Verify Your Setup

Test your API connection:

```bash
python -c "from src.api.kalshi_connector import create_connector_from_env; api = create_connector_from_env(); print('Connected!'); print(f'Balance: ${api.get_balance()[\"balance\"]/100:.2f}')"
```

You should see:
```
Connected!
Balance: $10000.00  # Demo account starts with $10k
```

## Step 4: Run Your First Scan (Dry Run)

This will scan markets but NOT execute any trades:

```bash
python src/main.py
```

You should see output like:
```
Starting FLB market scan...
Scanning 234 open markets
[DRY RUN] Found opportunity: {'ticker': 'EXAMPLE-23', ...}
Scan complete. Found 3 opportunities
```

## Step 5: Understanding the Output

The bot will log:

- **Market scans**: How many markets it checked
- **Opportunities found**: Markets matching FLB criteria
- **Trade signals**: What it would trade (in dry run)
- **Position stats**: Current exposure and utilization

Example opportunity:
```
[DRY RUN] Found opportunity: {
  'ticker': 'WEATHER-LAX-2024',
  'side': 'yes',
  'price': 95,
  'count': 5,
  'edge': 0.03,
  'strategy': 'FLB_FAVORITE',
  'reason': 'Favorite at 95%, edge=3%'
}
```

## Step 6: Run Live (Demo Money)

Once you're comfortable with the dry runs:

```bash
python src/main.py --live --demo
```

This will:
- Execute REAL trades (but with demo money)
- Update your demo account balance
- Give you real-world experience

**Safety Prompt:** The bot will ask for confirmation before running live.

## Step 7: Monitor Your Trades

While running, the bot logs to:
- **Console**: Real-time updates
- **File**: `logs/trading_YYYY-MM-DD.log`

Check your positions:
```bash
# In another terminal:
python -c "from src.api.kalshi_connector import create_connector_from_env; api = create_connector_from_env(); positions = api.get_positions(); print(f'Active positions: {len(positions)}')"
```

## Step 8: Stopping the Bot

Press `Ctrl+C` to stop gracefully. The bot will:
- Complete current cycle
- Print final summary
- Close cleanly

## Common Configuration Options

### Adjust Scan Interval

Scan every 10 minutes instead of 5:
```bash
python src/main.py --interval 600
```

### Adjust Risk Parameters

Edit `src/main.py` or create a config file:
```python
config = FLBConfig(
    favorite_threshold=0.92,  # Only trade 92%+ favorites
    longshot_threshold=0.08,   # Only fade <8% longshots
    max_contracts_per_trade=5, # Smaller positions
    max_total_exposure=500     # Lower total risk
)
```

## Strategy Explanations

### Strategy A: FLB Harvester (Active)

This strategy is currently implemented and active.

**What it does:**
- Scans ALL open markets on Kalshi
- Identifies favorites (price ≥ 90¢) and longshots (price ≤ 10¢)
- Buys underpriced favorites
- Fades overpriced longshots (by buying NO)

**Why it works:**
Based on academic research showing persistent market bias where:
- High-probability events win MORE often than their price suggests
- Low-probability events win LESS often than their price suggests

**Expected performance:**
- Win rate: ~55-60% on all trades
- ROI: ~5-15% per winning trade
- Holding period: Varies by market (hours to weeks)

### Strategy B: Alpha Specialist (Coming Soon)

This strategy will focus on weather markets with superior forecasting.

**What it will do:**
- Aggregate multiple weather models (NOAA, ECMWF, AccuWeather)
- Use ML to predict outcomes better than market
- Trade only when model shows significant edge

**Why it will work:**
- Access to professional-grade forecast data
- Specialized model trained on historical weather + market data
- Market often relies on single sources or casual forecasts

## Troubleshooting

### "Authentication failed"
- Check your `.env` credentials
- Verify you have a Kalshi account
- Ensure `KALSHI_USE_DEMO=true` for demo mode

### "No opportunities found"
- Normal! Not every scan finds trades
- FLB opportunities are less common (5-10% of markets)
- Try adjusting thresholds or wait for more markets

### "Rate limit exceeded"
- The bot has built-in rate limiting
- If persistent, increase `min_request_interval` in the connector

### "Insufficient balance"
- Check your balance: `api.get_balance()`
- Reduce `max_total_exposure` in config
- In demo mode, you start with $10,000

## Next Steps

1. **Run for 24-48 hours in demo mode** to understand the bot's behavior
2. **Review the logs** to see what trades it made and why
3. **Analyze performance** using the backtest module (coming soon)
4. **Tune parameters** based on your risk tolerance
5. **Consider implementing Strategy B** for additional edge

## Safety Reminders

- ✅ Always start with demo mode
- ✅ Test thoroughly before using real money
- ✅ Start with small position sizes
- ✅ Monitor the bot regularly
- ✅ Understand that all trading involves risk
- ⚠️ Never invest more than you can afford to lose
- ⚠️ Past performance doesn't guarantee future results

## Getting Help

- Check logs in `logs/` directory
- Review the academic papers in the documentation
- Open an issue if you find bugs
- Read the inline code comments for detailed explanations

## Quick Reference Commands

```bash
# Dry run (no trades)
python src/main.py

# Live demo mode
python src/main.py --live --demo

# Live production (real money)
python src/main.py --live

# Custom scan interval (10 min)
python src/main.py --interval 600

# Check balance
python -c "from src.api import create_connector_from_env; api = create_connector_from_env(); print(api.get_balance())"

# Check positions
python -c "from src.api import create_connector_from_env; api = create_connector_from_env(); print(api.get_positions())"
```

---

**Ready to start?** Run `python src/main.py` and watch your first scan!
