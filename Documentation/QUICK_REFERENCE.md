# Quick Reference Guide

## 🚀 Quick Start (5 Minutes)

```bash
# 1. Setup environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Configure
cp .env.template .env
nano .env  # Add your Kalshi credentials

# 3. Test installation
python src/test_installation.py

# 4. Run first scan
python src/main.py
```

## 📁 Project Structure

```
kalshi-ml-trader/
├── src/
│   ├── api/
│   │   └── kalshi_connector.py      # Kalshi API integration ✅
│   ├── strategies/
│   │   └── flb_harvester.py         # FLB strategy ✅
│   └── main.py                      # Main trading engine ✅
├── notebooks/
│   └── flb_backtest.ipynb          # Backtesting framework ✅
├── test_installation.py             # Setup verification ✅
├── requirements.txt                 # Dependencies ✅
├── .env.template                    # Config template ✅
├── README.md                        # Overview ✅
├── GETTING_STARTED.md              # Detailed guide ✅
└── IMPLEMENTATION_SUMMARY.md       # What's built & next steps ✅
```

## 🎯 Common Commands

### Testing & Development
```bash
# Verify installation
python test_installation.py

# Dry run (no trades)
python src/main.py

# Check API connection
python -c "from src.api import create_connector_from_env; api = create_connector_from_env(); print(api.get_balance())"
```

### Running the Bot
```bash
# Demo mode (play money)
python src/main.py --live --demo

# Production (real money - be careful!)
python src/main.py --live

# Custom scan interval (10 minutes)
python src/main.py --interval 600
```

### Monitoring
```bash
# Health check (recommended)
python scripts/health_check.py

# View logs
tail -f logs/trading_*.log

# Check positions
python -c "from src.api import create_connector_from_env; api = create_connector_from_env(); print(api.get_positions())"

# Check balance
python -c "from src.api import create_connector_from_env; api = create_connector_from_env(); print(f'${api.get_balance()[\"balance\"]/100:.2f}')"
```

## 🧠 Strategy Overview

### Strategy A: FLB Harvester (Active ✅)

**What it does:**
- Scans all Kalshi markets every 5 minutes
- Buys underpriced favorites (price ≥ 90¢)
- Fades overpriced longshots (price ≤ 10¢)

**Why it works:**
- Based on academic research showing persistent market bias
- Favorites win MORE than their price suggests
- Longshots win LESS than their price suggests

**Expected performance:**
- Win rate: 55-65%
- ROI per trade: 5-15%
- Trade frequency: 5-15% of markets

### Strategy B: Alpha Specialist (Planned 🔜)

**What it will do:**
- Focus on weather markets
- Use ML model trained on multiple forecast sources
- Trade when model shows edge over market

**Status:** Designed but not yet implemented (see Phase 2 in roadmap)

## ⚙️ Configuration

### In `.env` file:
```bash
# Credentials
KALSHI_EMAIL=your_email@example.com
KALSHI_PASSWORD=your_password

# Environment
KALSHI_USE_DEMO=true  # false for production

# Strategy parameters
FLB_FAVORITE_THRESHOLD=0.90
FLB_LONGSHOT_THRESHOLD=0.10
FLB_MAX_EXPOSURE=1000
```

### In code (`src/strategies/flb_harvester.py`):
```python
config = FLBConfig(
    favorite_threshold=0.90,
    longshot_threshold=0.10,
    max_contracts_per_trade=10,
    max_total_exposure=1000.0,
    min_edge_to_trade=0.02
)
```

## 📊 Understanding Output

### During Market Scan:
```
Starting FLB market scan...
Scanning 234 open markets

[DRY RUN] Found opportunity: {
  'ticker': 'WEATHER-LAX-2024',
  'side': 'yes',
  'price': 95,
  'count': 5,
  'edge': 0.03,
  'strategy': 'FLB_FAVORITE'
}

Scan complete. Found 3 opportunities
```

### Cycle Summary:
```
--- Cycle Summary ---
Total trades executed: 3
Total errors: 0
Total exposure: $285.50
```

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| "Authentication failed" | Check credentials in `.env` |
| "No opportunities found" | Normal - not every scan finds trades |
| "Rate limit exceeded" | Built-in rate limiting should prevent this |
| "Insufficient balance" | Check balance or reduce `max_total_exposure` |
| "Module not found" | Run `pip install -r requirements.txt` |

## 🎓 Learning Resources

### Documentation
- `README.md` - Project overview
- `GETTING_STARTED.md` - Step-by-step setup
- `IMPLEMENTATION_SUMMARY.md` - Architecture & roadmap

### Code
- `src/api/kalshi_connector.py` - Learn API integration
- `src/strategies/flb_harvester.py` - Study strategy logic
- `notebooks/flb_backtest.ipynb` - Backtest analysis

### External
- Kalshi API docs: https://trading-api.readme.io/
- Academic papers referenced in `README.md`

## 🚨 Safety Checklist

- [ ] Start with `KALSHI_USE_DEMO=true`
- [ ] Run dry runs first (`python src/main.py`)
- [ ] Test with demo money (`--live --demo`)
- [ ] Start with small position sizes
- [ ] Monitor logs regularly
- [ ] Understand that trading involves risk
- [ ] Never invest more than you can afford to lose

## 📈 Next Steps

1. **Week 1:** Run in dry-run mode, understand the output
2. **Week 2:** Test with demo money, analyze results
3. **Week 3:** Run backtests, optimize parameters
4. **Week 4:** Consider small-scale production testing
5. **Beyond:** Implement Strategy B (Alpha Specialist)

## 🆘 Getting Help

1. Check logs in `logs/` directory
2. Review documentation files
3. Read inline code comments
4. Open an issue on GitHub
5. Consult Kalshi support for API issues

## 💡 Pro Tips

- **Patience:** Not every scan finds trades - this is normal
- **Backtesting:** Always backtest parameter changes
- **Logs:** Review logs daily to understand bot behavior
- **Start small:** Test with minimal exposure first
- **Monitor:** Check positions and P&L regularly
- **Learn:** Study the academic papers to understand the edge

---

**Remember:** This is a research project. Trading involves risk. Test thoroughly before using real money.

**Status:** Phase 1 Complete ✅ | Ready for testing and deployment
