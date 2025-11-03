"""Backtesting module."""

from .event_backtester import (
    EventBacktester,
    FeeSchedule,
    OrderSide,
    OrderAction,
    MarketSnapshot,
    SlippageModel,
    LatencyModel,
    run_walk_forward_backtest
)

# Weather backtester (optional - may not exist in all installations)
try:
    from .weather_backtester import WeatherBacktester
    __all__ = [
        "EventBacktester",
        "FeeSchedule",
        "OrderSide",
        "OrderAction",
        "MarketSnapshot",
        "SlippageModel",
        "LatencyModel",
        "run_walk_forward_backtest",
        "WeatherBacktester"
    ]
except ImportError:
    __all__ = [
        "EventBacktester",
        "FeeSchedule",
        "OrderSide",
        "OrderAction",
        "MarketSnapshot",
        "SlippageModel",
        "LatencyModel",
        "run_walk_forward_backtest"
    ]

