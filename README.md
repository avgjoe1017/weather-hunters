# Kalshi ML Trading Program: "Alpha & Bias"

A hybrid machine learning trading system that exploits documented inefficiencies in Kalshi prediction markets through a dual-strategy approach.

## Project Overview

This trading bot combines two proven strategies:

1. **Strategy A: FLB Harvester** - Exploits the Favorite-Longshot Bias (structural market inefficiency)
2. **Strategy B: Alpha Specialist** - Generates superior probability predictions using specialized ML models

## Key Advantages Over Existing Bots

- ✅ **100% Backtestable** - No black-box LLMs
- ✅ **Data-driven** - Built on academic research and statistical proof
- ✅ **Feature-based ML** - Transparent, debuggable models
- ✅ **Dual-edge approach** - Structural + informational advantages

## Project Structure

```
weather-hunters/
├── src/
│   ├── api/              # Kalshi API connector
│   ├── strategies/       # Strategy A (FLB Harvester)
│   ├── features/         # Weather data & ML features ⭐
│   ├── backtest/         # Backtesting engines
│   ├── risk/             # Risk management system
│   ├── monitoring/       # Metrics and monitoring
│   └── main.py           # Main trading engine
├── scripts/              # Utility scripts (weather strategy) ⭐
├── notebooks/            # Analysis notebooks
├── logs/                 # Application logs (auto-created)
├── metrics/              # Metrics output (auto-created)
├── Documentation/        # Complete documentation
├── data/                 # Historical data (weather, backtest results)
└── config/               # Configuration files (optional)
```

## Setup Instructions

### 1. Environment Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. API Configuration

**Option A: Automated Setup (Recommended)**
```bash
python scripts/setup.py
# This will create .env.template, install dependencies, and run tests
```

**Option B: Manual Setup**
```bash
# Create .env file
copy .env.template .env  # Windows
# or
cp .env.template .env    # Mac/Linux

# Edit .env with your credentials:
KALSHI_EMAIL=your_email@example.com
KALSHI_PASSWORD=your_password
KALSHI_USE_DEMO=true  # Start with demo mode
```

### 3. Verify Setup

```bash
# Quick verification
python scripts/verify_setup.py

# Or full installation test
python src/test_installation.py
```

### 4. Running the Bot

```bash
# Dry run (no real trades - default)
python -m src.main

# Live trading (demo environment)
python -m src.main --live --demo

# Live trading (real money - use with caution)
python -m src.main --live
```

## Strategy Details

### Strategy A: FLB Harvester
- Scans all markets 24/7
- Buys favorites (price ≥ 90¢)
- Sells longshots (price ≤ 10¢)
- Based on "Makers and Takers" whitepaper

### Strategy B: Weather Alpha ⭐
- **Fully implemented and ready to run**
- Superior weather forecasts (ECMWF, GFS, ensemble)
- Daily temperature markets on 4 cities (NYC, CHI, MIA, AUS)
- 365 opportunities/year per city = 1,460 total
- **Expected: 30-37% annual returns**
- Run: `python scripts/run_weather_strategy.py`

## Quick Start

### Setup (First Time)
```bash
# Automated setup
python scripts/setup.py --venv

# Verify setup
python scripts/verify_setup.py
```

### Weather Strategy (Recommended First)
```bash
# Run complete weather strategy (collects data, backtests)
python scripts/run_weather_strategy.py
```

### FLB Strategy (Main Trading Engine)
```bash
# Dry run (no real trades)
python -m src.main

# Live trading (demo)
python -m src.main --live --demo
```

### Health Check
```bash
# Check system health
python scripts/health_check.py
```

## What's Complete

✅ **Strategy A: FLB Harvester** - Production ready
✅ **Strategy B: Weather Alpha** - Fully implemented, ready to run
✅ **Production Infrastructure** - Risk management, backtesting, monitoring
✅ **Complete Documentation** - See `Documentation/` folder

## Documentation

- **`Documentation/FINAL_DELIVERY_SUMMARY.md`** - Complete overview
- **`Documentation/QUICK_START.txt`** - Quick start guide
- **`Documentation/WEATHER_STRATEGY_COMPLETE.md`** - Weather strategy guide
- **`Documentation/PRODUCTION_HARDENING.md`** - V2 implementation guide

## Safety Features

- Dry run mode for testing
- Demo environment support
- Position size limits
- Risk management controls
- Comprehensive logging

## References

- "Makers and Takers: The Economics of the Kalshi Prediction Market" (Whelan, et al.)
- "Markets vs. Machines" (DiVA Portal)

## License

MIT License - See LICENSE file for details
