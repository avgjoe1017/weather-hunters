# 🚀 Setup Checklist

Use this checklist to ensure your trading bot is properly configured before going live.

## Pre-Setup Requirements

- [ ] Python 3.8 or higher installed
- [ ] Kalshi account created (demo or production)
- [ ] Kalshi API credentials obtained (email + password)
- [ ] Basic understanding of prediction markets

---

## Phase 1: Initial Setup

### 1.1 Automated Setup (Recommended)

- [ ] Run setup script: `python scripts/setup.py --venv`
- [ ] Verify all dependencies installed successfully
- [ ] Confirm virtual environment created (if using --venv)
- [ ] Check that .env.template was created

### 1.2 Manual Setup (Alternative)

- [ ] Create virtual environment: `python -m venv venv`
- [ ] Activate virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Create required directories (logs, metrics, data, config)

---

## Phase 2: Configuration

### 2.1 Environment Configuration

- [ ] Create `.env` file from template
  - Windows: `copy .env.template .env`
  - Mac/Linux: `cp .env.template .env`
- [ ] Edit `.env` with your credentials:
  - [ ] `KALSHI_EMAIL` set to your email
  - [ ] `KALSHI_PASSWORD` set to your password
  - [ ] `KALSHI_USE_DEMO=true` for initial testing
- [ ] Verify .env file is not in version control (.gitignore)

### 2.2 Verify Configuration

- [ ] Run quick verification: `python scripts/verify_setup.py`
- [ ] OR run full test: `python src/test_installation.py`
- [ ] All tests should pass

---

## Phase 3: Testing

### 3.1 API Connection Test

- [ ] Test API connection works
- [ ] Verify demo mode is active (if using demo)
- [ ] Check account balance is accessible
- [ ] Confirm market data retrieval works

### 3.2 Strategy Tests

- [ ] Run FLB strategy dry run: `python -m src.main`
- [ ] Verify strategy can scan markets
- [ ] Check that opportunities are identified (if any exist)
- [ ] Review logs for any errors

### 3.3 Risk Manager Test

- [ ] Verify Risk Manager initializes correctly
- [ ] Check that kill-switches are functional
- [ ] Test position sizing calculations
- [ ] Confirm risk limits are set appropriately

### 3.4 Metrics Collector Test

- [ ] Verify Metrics Collector initializes
- [ ] Test that metrics directory exists
- [ ] Check that trade recording works (in dry run)

---

## Phase 4: Pre-Flight (Before Live Trading)

### 4.1 Backtesting (Recommended)

- [ ] Run backtest on historical data (if available)
- [ ] Verify expected returns are positive after fees
- [ ] Check that win rate matches expectations
- [ ] Review backtest results for any anomalies

### 4.2 Risk Limits Configuration

- [ ] Review and adjust risk limits in `src/main.py`
  - [ ] `kelly_fraction` (default: 0.25)
  - [ ] `max_total_exposure_pct` (default: 0.20)
  - [ ] `max_single_position_pct` (default: 0.05)
  - [ ] `max_daily_loss_dollars` (default: 500.0)
  - [ ] `max_consecutive_losses` (default: 5)
- [ ] Verify limits are appropriate for your capital

### 4.3 Demo Trading (Strongly Recommended)

- [ ] Run in demo mode for at least 1 week: `python -m src.main --live --demo`
- [ ] Monitor daily performance
- [ ] Review metrics daily
- [ ] Verify all kill-switches trigger correctly
- [ ] Confirm position sizing works as expected
- [ ] Check that P&L tracking is accurate

### 4.4 Final Checks

- [ ] All logs are being written correctly
- [ ] Metrics are being collected and exported
- [ ] No errors in logs
- [ ] System health monitoring is active
- [ ] Alert system is configured (if applicable)

---

## Phase 5: Production Deployment

### 5.1 Final Verification

- [ ] Run full verification: `python scripts/verify_setup.py`
- [ ] All tests pass
- [ ] Demo trading results match backtest expectations
- [ ] Risk limits tested and confirmed

### 5.2 Production Configuration

- [ ] Switch to production mode: `KALSHI_USE_DEMO=false` in .env
- [ ] Start with minimal capital ($100-500 recommended)
- [ ] Monitor closely for first week
- [ ] Scale gradually if results match expectations

### 5.3 Ongoing Monitoring

- [ ] Review daily metrics
- [ ] Check system health daily
- [ ] Monitor for kill-switch triggers
- [ ] Review logs for errors
- [ ] Track actual vs expected performance

---

## Emergency Procedures

### If Kill-Switch Triggers:

1. [ ] Review kill-switch reason in logs
2. [ ] Check risk manager state
3. [ ] Verify no system errors
4. [ ] Manually reset if appropriate
5. [ ] Review what caused the trigger

### If Errors Occur:

1. [ ] Check logs in `logs/` directory
2. [ ] Review error messages
3. [ ] Check API connection
4. [ ] Verify credentials are valid
5. [ ] Test in demo mode first
6. [ ] Review PROGRESS.md for known issues

---

## Quick Reference Commands

```bash
# Automated setup
python scripts/setup.py --venv

# Quick verification
python scripts/verify_setup.py

# Full installation test
python src/test_installation.py

# Dry run (no trades)
python -m src.main

# Demo trading
python -m src.main --live --demo

# Production (real money - be careful!)
python -m src.main --live
```

---

## Documentation References

- **Getting Started**: `Documentation/GETTING_STARTED.md`
- **Quick Reference**: `Documentation/QUICK_REFERENCE.md`
- **Production Hardening**: `Documentation/PRODUCTION_HARDENING.md`
- **Weather Strategy**: `Documentation/WEATHER_STRATEGY_COMPLETE.md`
- **Progress Log**: `Documentation/PROGRESS.md`

---

**Version:** 3.0  
**Last Updated:** 2025-11-02  
**Status:** Production-Ready Checklist

