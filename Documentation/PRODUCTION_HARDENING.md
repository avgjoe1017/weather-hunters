# Production Hardening Implementation Guide

## Based on Expert Feedback: From "Working" to "Production-Ready"

This guide addresses the critical gaps identified in the initial implementation and provides a roadmap for hardening the system for real-money trading.

---

## 🚨 Critical Issues Fixed

### 1. **Fee-Accurate Backtesting** ✅

**Problem:** Original backtest notebook didn't model exact fee schedules, order mechanics, or slippage.

**Solution:** `src/backtest/event_backtester.py`

**Key Features:**
- ✅ Exact Kalshi fee model (7% of profit, only on winners)
- ✅ Order queue simulation with partial fills
- ✅ API latency and clock skew modeling
- ✅ Realistic slippage based on order size
- ✅ Walk-forward validation (no data leakage)

**Usage:**
```python
from src.backtest.event_backtester import EventBacktester, FeeSchedule

# Initialize with exact fee schedule
backtester = EventBacktester(
    fee_schedule=FeeSchedule(profit_fee_rate=0.07),
    initial_capital=10000
)

# Submit orders with realistic execution
order = backtester.submit_order(
    timestamp=datetime.now(),
    ticker="WEATHER-LAX-2024",
    side=OrderSide.YES,
    action=OrderAction.BUY,
    contracts=10,
    market_snapshot=snapshot
)

# Resolve market and calculate fee-accurate P&L
trade = backtester.resolve_market(
    ticker="WEATHER-LAX-2024",
    resolution="yes",
    resolution_time=datetime.now()
)

# Get comprehensive metrics
metrics = backtester.get_metrics()
print(f"Total P&L after fees: ${metrics['total_pnl']:.2f}")
print(f"Fee drag: {metrics['fee_pct_of_pnl']:.1f}%")
```

**Critical Outputs:**
- Net basis points by threshold (for tuning `favorite_threshold`, `longshot_threshold`)
- Fee impact analysis (shows if edge survives fees)
- Slippage distribution (realistic fill prices)

---

### 2. **Fractional Kelly + Correlation Caps** ✅

**Problem:** Original Kelly implementation could overbet, especially with correlated markets.

**Solution:** `src/risk/risk_manager.py`

**Key Features:**
- ✅ Fractional Kelly (¼ Kelly default, configurable)
- ✅ Per-theme correlation caps (15% max per correlated group)
- ✅ Dynamic position sizing with hard limits
- ✅ Kelly + correlation-aware sizing

**Usage:**
```python
from src.risk.risk_manager import RiskManager, RiskLimits

# Initialize with conservative limits
limits = RiskLimits(
    kelly_fraction=0.25,  # Quarter Kelly
    max_single_position_pct=0.05,  # 5% per position
    max_correlated_group_pct=0.15,  # 15% per correlated group
    max_total_exposure_pct=0.20  # 20% total
)

risk_mgr = RiskManager(
    initial_capital=10000,
    limits=limits
)

# Calculate position size with correlation awareness
contracts, reason = risk_mgr.calculate_position_size(
    edge=0.05,  # 5% expected edge
    win_probability=0.65,
    price_cents=90,
    market_group="weather_california"  # Correlation group
)

if contracts > 0:
    print(f"Trade approved: {contracts} contracts")
else:
    print(f"Trade rejected: {reason}")
```

**Correlation Grouping:**
```python
from src.risk.risk_manager import identify_correlated_markets

# Identify correlated markets from historical returns
groups = identify_correlated_markets(
    historical_returns_df,
    correlation_threshold=0.5
)

# Markets with >50% correlation are grouped together
# Example: all weather markets in California might be one group
```

---

### 3. **Kill-Switches & Circuit Breakers** ✅

**Problem:** No automated safety stops.

**Solution:** Built into `RiskManager`

**Kill-Switches Implemented:**
- ✅ **Daily loss limit** (dollar and percentage)
- ✅ **Streak loss** (5 consecutive losses → 4-hour pause)
- ✅ **Slippage excessive** (>50 bps consistently)
- ✅ **Error burst** (>10 errors/hour)
- ✅ **Stale book** (data >30 seconds old)
- ✅ **No fills** (no fills in 20 scans)
- ✅ **Correlation breach** (group exposure exceeded)

**Usage:**
```python
# Check if trading is allowed
can_trade, reason = risk_mgr.can_trade()

if not can_trade:
    logger.error(f"Trading halted: {reason}")
    # Alert operator
    send_alert(reason)
    return

# Trading state is monitored automatically
status = risk_mgr.get_status()
if status['trading_state'] == 'HALTED':
    print(f"Kill switch triggered: {status['kill_switch_reason']}")
```

**Manual Override:**
```python
# After addressing the issue, manually resume
risk_mgr.manual_resume()
```

---

### 4. **Production Metrics & Monitoring** ✅

**Problem:** No systematic tracking of performance, slippage, or edge decay.

**Solution:** `src/monitoring/metrics_collector.py`

**Key Features:**
- ✅ Hit rate by price bucket (validates FLB edge)
- ✅ Net bps after fees (validates profitable thresholds)
- ✅ Fill ratio and slippage histograms
- ✅ P&L attribution by market family
- ✅ Real-time system health monitoring

**Usage:**
```python
from src.monitoring.metrics_collector import MetricsCollector

metrics = MetricsCollector(output_dir="metrics")

# Record every trade
metrics.record_trade(
    ticker="WEATHER-LAX-2024",
    side="yes",
    action="buy",
    contracts=10,
    entry_price=92.5,
    exit_price=100,
    gross_pnl=7.5,
    net_pnl=6.97,  # After 0.07 * 7.5 = 0.53 fee
    fee=0.53,
    slippage_bps=5.0,
    holding_period_hours=48,
    market_family="weather_california",
    strategy="FLB_FAVORITE"
)

# Get bucketed analysis
bucket_summary = metrics.get_bucket_summary()
print(bucket_summary['favorite_extreme'])
# Output: {
#   'price_range': '90-100',
#   'trades': 15,
#   'win_rate': '80.0%',
#   'net_bps': '120.5',  # This is your real edge!
#   'fee_drag_bps': '15.2'
# }

# Print daily summary
metrics.print_daily_summary(capital=10000)
```

**Continuous Export:**
- Trades logged to `metrics/trades_log.csv` in real-time
- Metrics exported to JSON at shutdown
- Enables Grafana/Prometheus integration (Phase 4)

---

## 🔧 Integration Into Existing Code

### Step 1: Update FLB Strategy with Risk Manager

**File:** `src/strategies/flb_harvester.py`

```python
# Add to __init__:
from src.risk.risk_manager import RiskManager, RiskLimits

class FLBHarvester:
    def __init__(self, api_connector, config, risk_manager):
        self.api = api_connector
        self.config = config
        self.risk_mgr = risk_manager  # NEW
        # ...

    def _calculate_position_size(self, price_cents: int, edge: float) -> int:
        # REPLACE Kelly calculation with risk manager
        win_prob = self._estimate_win_probability(price_cents, edge)
        
        contracts, reason = self.risk_mgr.calculate_position_size(
            edge=edge,
            win_probability=win_prob,
            price_cents=price_cents,
            market_group=self._identify_market_group(ticker)
        )
        
        if contracts == 0:
            logger.info(f"Position sizing rejected: {reason}")
        
        return contracts
```

### Step 2: Update Trading Engine with Metrics

**File:** `src/main.py`

```python
from src.monitoring.metrics_collector import MetricsCollector
from src.risk.risk_manager import RiskManager, RiskLimits

class TradingEngine:
    def __init__(self, dry_run, use_demo):
        # ... existing init ...
        
        # Add risk manager
        initial_capital = self._get_starting_capital()
        self.risk_mgr = RiskManager(
            initial_capital=initial_capital,
            limits=RiskLimits()
        )
        
        # Add metrics collector
        self.metrics = MetricsCollector(output_dir="metrics")
        
        # Pass to strategies
        self.flb_strategy = FLBHarvester(
            api_connector=self.api,
            config=FLBConfig(),
            risk_manager=self.risk_mgr  # NEW
        )
    
    def start(self, scan_interval):
        while self.is_running:
            # Check if trading allowed
            can_trade, reason = self.risk_mgr.can_trade()
            if not can_trade:
                logger.warning(f"Trading paused: {reason}")
                time.sleep(60)
                continue
            
            # Run strategies
            trades = self.flb_strategy.scan_and_trade(dry_run=self.dry_run)
            
            # Record metrics for each trade
            for trade in trades:
                if 'execution' in trade:
                    self.metrics.record_trade(
                        ticker=trade['ticker'],
                        # ... all trade details
                    )
            
            # Print health status
            health = self.metrics.get_system_health(
                trading_state=self.risk_mgr.trading_state.value,
                active_positions=len(self.risk_mgr.positions),
                total_exposure=self.risk_mgr._get_total_exposure(),
                capital=self.risk_mgr.current_capital,
                daily_pnl=self.risk_mgr.daily_pnl
            )
            
            if health.alerts_active:
                for alert in health.alerts_active:
                    logger.warning(f"ALERT: {alert}")
            
            time.sleep(scan_interval)
    
    def stop(self):
        # Print final summary
        self.metrics.print_daily_summary(
            capital=self.risk_mgr.current_capital
        )
        
        # Export all metrics
        self.metrics.export_all_metrics()
```

---

## 📊 Critical Analyses to Run Before Live Trading

### Analysis 1: Fee Impact on FLB Strategy

**Goal:** Verify that FLB edge survives after 7% profit fees.

```python
from src.backtest.event_backtester import EventBacktester, run_walk_forward_backtest

# Load 3-6 months of historical data
historical_df = pd.read_csv('data/kalshi_historical.csv')

# Test different thresholds
thresholds_to_test = [
    (85, 15),  # Wider thresholds
    (90, 10),  # Current thresholds
    (92, 8),   # Tighter thresholds
    (95, 5)    # Very tight
]

results = []
for fav_thresh, long_thresh in thresholds_to_test:
    backtester = EventBacktester(
        fee_schedule=FeeSchedule(profit_fee_rate=0.07),
        initial_capital=10000
    )
    
    # Run backtest
    # ... (filter markets, execute strategy)
    
    metrics = backtester.get_metrics()
    results.append({
        'fav_threshold': fav_thresh,
        'long_threshold': long_thresh,
        'total_trades': metrics['total_trades'],
        'win_rate': metrics['win_rate'],
        'net_pnl': metrics['total_pnl'],
        'total_fees': metrics['total_fees'],
        'fee_pct': metrics['fee_pct_of_pnl'],
        'sharpe': metrics['sharpe_ratio']
    })

# Find optimal thresholds AFTER fees
results_df = pd.DataFrame(results)
best = results_df.loc[results_df['net_pnl'].idxmax()]
print(f"Optimal thresholds: {best['fav_threshold']}¢ / {best['long_threshold']}¢")
print(f"Expected net P&L: ${best['net_pnl']:.2f}")
print(f"Fee drag: {best['fee_pct']:.1f}%")
```

### Analysis 2: Correlation Identification

**Goal:** Identify which markets move together.

```python
# Calculate returns for all markets
returns_df = calculate_market_returns(historical_df)

# Identify correlated groups
groups = identify_correlated_markets(
    returns_df,
    correlation_threshold=0.5
)

print(f"Found {len(groups)} correlated market groups:")
for group_id, tickers in groups.items():
    print(f"  {group_id}: {len(tickers)} markets")
    print(f"    Example: {tickers[:3]}")

# Configure strategy with correlation awareness
# Weather markets in same region likely correlated
# Political markets about same race correlated
# Sports markets on same team correlated
```

### Analysis 3: Slippage Distribution

**Goal:** Understand realistic execution costs.

```python
# Run backtest with slippage model
slippage_model = SlippageModel(
    base_slippage_bps=5.0,
    size_impact_factor=0.1
)

backtester = EventBacktester(
    slippage_model=slippage_model,
    initial_capital=10000
)

# Run full backtest
# ...

# Analyze slippage
trades_df = backtester.get_trades_df()
print(f"Average slippage: {trades_df['slippage_bps'].mean():.1f} bps")
print(f"95th percentile: {trades_df['slippage_bps'].quantile(0.95):.1f} bps")

# Plot distribution
import matplotlib.pyplot as plt
plt.hist(trades_df['slippage_bps'], bins=50)
plt.title("Slippage Distribution")
plt.xlabel("Slippage (bps)")
plt.show()
```

---

## ⚙️ Configuration for Production

### config/production.yml

```yaml
risk:
  kelly_fraction: 0.25  # Quarter Kelly
  max_total_exposure_pct: 0.20
  max_single_position_pct: 0.05
  max_correlated_group_pct: 0.15
  max_daily_loss_dollars: 500
  max_daily_loss_pct: 0.05
  max_consecutive_losses: 5
  loss_streak_pause_hours: 4

strategy_flb:
  favorite_threshold: 90  # Update after backtesting!
  longshot_threshold: 10
  min_edge_to_trade: 0.03  # 3% minimum after fees

fees:
  profit_fee_rate: 0.07  # 7% of profit on winners

slippage:
  base_slippage_bps: 5.0
  size_impact_factor: 0.1

quality:
  max_spread_bps: 200.0
  max_stale_book_seconds: 30
  max_slippage_bps: 50.0

monitoring:
  metrics_output_dir: "metrics"
  export_interval_seconds: 300
  alert_on_kill_switch: true
  alert_on_high_slippage: true
```

---

## 🎯 Pre-Flight Checklist

Before enabling real-money trading:

### Data & Backtesting
- [ ] Collect 3-6 months of historical Kalshi data
- [ ] Run fee-accurate backtests with exact fee schedule
- [ ] Verify FLB edge survives fees (net bps > 0)
- [ ] Optimize thresholds based on post-fee performance
- [ ] Test walk-forward validation (no data leakage)
- [ ] Document expected win rate, Sharpe ratio, drawdown

### Risk Management
- [ ] Configure fractional Kelly (start with 0.25)
- [ ] Identify correlated market groups
- [ ] Set group exposure limits (15% per group)
- [ ] Set daily loss limits (both $ and %)
- [ ] Test all kill-switches in simulation
- [ ] Verify manual resume works

### System Health
- [ ] Set up metrics export directory
- [ ] Configure logging (console + file)
- [ ] Test alert system (kill-switch, errors, P&L)
- [ ] Verify time sync with exchange
- [ ] Test graceful shutdown
- [ ] Document recovery procedures

### Operational
- [ ] Start with demo environment
- [ ] Run for 1 week in demo mode
- [ ] Verify all metrics are logged
- [ ] Review daily summaries
- [ ] Test with minimal capital ($100-500)
- [ ] Scale slowly based on performance

---

## 🔄 Continuous Monitoring

### Daily Tasks
1. Review `metrics/trades_log.csv` for all trades
2. Check `metrics.print_daily_summary()` output
3. Verify no kill-switches triggered
4. Monitor slippage distribution
5. Track realized edge vs. expected edge

### Weekly Tasks
1. Run `metrics.get_bucket_summary()` - check if FLB edge persists
2. Review fee impact - ensure fees < 20% of gross P&L
3. Check correlation group performance
4. Verify no systematic losses in any bucket
5. Update thresholds if edge has shifted

### Monthly Tasks
1. Full backtest on last month's data
2. Recalculate correlated groups
3. Reoptimize Kelly fraction based on actual volatility
4. Review all kill-switch triggers
5. Update risk limits if capital has grown

---

## 📈 Expected Improvements

With these changes, you should see:

**Backtesting:**
- Realistic P&L (10-20% lower due to fees/slippage)
- No data leakage (walk-forward validation)
- Accurate edge measurement

**Risk Management:**
- Smaller positions (but safer)
- Better risk-adjusted returns (higher Sharpe)
- Automatic protection from blowups

**Monitoring:**
- Clear visibility into what's working
- Early warning of edge decay
- Systematic improvement based on data

---

## 🚀 Next Steps

1. **Week 1:** Implement risk manager integration
2. **Week 2:** Run fee-accurate backtests, optimize thresholds
3. **Week 3:** Set up monitoring and alerts
4. **Week 4:** Test in demo mode with full stack
5. **Week 5+:** Gradual production rollout

**Remember:** Measure twice, trade once. These improvements turn a promising strategy into a robust, production-ready system.
