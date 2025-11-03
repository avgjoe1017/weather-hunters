# Project Structure

This document describes the organized folder structure of the Kalshi ML Trading Bot V2.

## Directory Layout

```
weather-hunters/
├── src/                          # Main source code
│   ├── __init__.py
│   ├── main.py                   # Main trading engine entry point
│   ├── test_installation.py      # Installation test script
│   │
│   ├── api/                      # Kalshi API connector
│   │   ├── __init__.py
│   │   └── kalshi_connector.py   # API wrapper and authentication
│   │
│   ├── strategies/               # Trading strategies
│   │   ├── __init__.py
│   │   └── flb_harvester.py     # FLB (Favorite-Longshot Bias) strategy
│   │
│   ├── backtest/                 # Backtesting engine
│   │   ├── __init__.py
│   │   ├── event_backtester.py  # Fee-accurate event-driven backtester
│   │   └── weather_backtester.py # Weather market backtester
│   │
│   ├── features/                  # Feature extraction and data collection
│   │   ├── __init__.py
│   │   ├── weather_data_collector.py # Historical weather data collection
│   │   ├── kalshi_historical_collector.py # Kalshi historical data framework
│   │   └── weather_pipeline.py  # Weather feature pipeline for ML
│   │
│   ├── risk/                     # Risk management system
│   │   ├── __init__.py
│   │   └── risk_manager.py      # Position sizing, kill-switches, limits
│   │
│   └── monitoring/               # Metrics and monitoring
│       ├── __init__.py
│       └── metrics_collector.py # Performance tracking and metrics
│
├── scripts/                      # Utility scripts
│   └── run_weather_strategy.py # Master script for weather strategy
│
├── notebooks/                     # Jupyter notebooks for analysis
│   └── flb_backtest.ipynb       # FLB strategy backtesting notebook
│
├── logs/                         # Application logs (auto-created)
│   └── trading_YYYY-MM-DD.log
│
├── metrics/                      # Metrics output (auto-created)
│   ├── trades_log.csv           # Real-time trade log
│   ├── bucket_metrics_*.json    # Price bucket performance
│   ├── strategy_metrics_*.json  # Strategy performance
│   └── family_metrics_*.json   # Market family performance
│
├── data/                         # Historical data (optional)
│   ├── weather/                 # Weather data (actuals, forecasts, climatology)
│   ├── kalshi_history/         # Kalshi historical market data
│   └── backtest_results/        # Backtest results
│
├── config/                       # Configuration files (optional)
│
├── requirements.txt              # Python dependencies
├── README.md                     # Main documentation
├── PROGRESS.md                   # Change log
│
├── Documentation/                 # Comprehensive documentation
│   ├── 00_START_HERE_V2.txt     # Quick start guide
│   ├── V2_UPDATE_SUMMARY.md      # What's new in V2
│   ├── PRODUCTION_HARDENING.md   # Production implementation guide
│   ├── PHASE4_ENHANCEMENTS.md    # Future enhancements
│   ├── GETTING_STARTED.md        # Setup instructions
│   ├── QUICK_REFERENCE.md        # Quick reference guide
│   ├── IMPLEMENTATION_SUMMARY.md # Implementation details
│   ├── PROJECT_DELIVERY.md      # Project delivery info
│   ├── INTEGRATION_COMPLETE.md   # Integration completion doc
│   └── PROJECT_STRUCTURE.md      # This file
│
└── LICENSE                        # MIT License
```

## Key Directories

### `src/`
Main source code directory containing all Python modules organized by functionality:
- **api/**: Kalshi API integration
- **strategies/**: Trading strategies (FLB, future Alpha Specialist)
- **backtest/**: Fee-accurate backtesting engine
- **risk/**: Risk management and position sizing
- **monitoring/**: Metrics collection and performance tracking

### `notebooks/`
Jupyter notebooks for research, analysis, and development.

### `logs/`
Application logs are written here automatically. Files are rotated daily.

### `metrics/`
All metrics output files:
- CSV trade logs (real-time)
- JSON metrics exports (periodic)
- Performance summaries

### `data/`
Optional directory for historical market data, if collected.

### `config/`
Optional directory for configuration files (YAML, JSON, etc.).

## Running the Bot

From the project root:

```bash
# Dry run (default)
python -m src.main

# Live trading (demo)
python -m src.main --live --demo

# Live trading (production)
python -m src.main --live
```

## Import Structure

All imports use the `src.` prefix:

```python
from src.api.kalshi_connector import create_connector_from_env
from src.strategies.flb_harvester import FLBHarvester, FLBConfig
from src.risk.risk_manager import RiskManager, RiskLimits
from src.monitoring.metrics_collector import MetricsCollector
from src.backtest.event_backtester import EventBacktester
from src.features.weather_data_collector import HistoricalWeatherCollector
from src.features.weather_pipeline import WeatherFeaturePipeline
```

## Organization Benefits

1. **Clear separation of concerns**: Each module has a specific purpose
2. **Easy to navigate**: Find code by functionality
3. **Scalable**: Easy to add new strategies, risk modules, etc.
4. **Professional structure**: Follows Python package best practices
5. **Documentation organized**: All docs in one place

---

**Last Updated:** 2024-12-19

