"""
Production Monitoring & Metrics System

Tracks and exports:
- Hit rate by price bucket
- Net basis points after fees
- Fill ratio and slippage
- P&L attribution by market family
- Real-time health metrics
- Alert conditions
"""

import json
import csv
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradeMetrics:
    """Metrics for a single trade"""
    timestamp: datetime
    ticker: str
    side: str
    action: str
    contracts: int
    entry_price: float
    exit_price: float
    gross_pnl: float
    net_pnl: float
    fee: float
    slippage_bps: float
    holding_period_hours: float
    win: bool
    market_family: Optional[str] = None
    strategy: Optional[str] = None


@dataclass
class BucketMetrics:
    """Metrics for a price bucket"""
    bucket_name: str
    price_range: Tuple[float, float]
    trades: int = 0
    wins: int = 0
    losses: int = 0
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    total_fees: float = 0.0
    avg_slippage_bps: float = 0.0
    
    @property
    def win_rate(self) -> float:
        return (self.wins / self.trades * 100) if self.trades > 0 else 0.0
    
    @property
    def net_bps(self) -> float:
        """Net return in basis points"""
        if self.trades == 0:
            return 0.0
        avg_entry = (self.price_range[0] + self.price_range[1]) / 2
        return (self.net_pnl / (avg_entry * self.trades)) * 10000
    
    @property
    def fee_drag_bps(self) -> float:
        """Fee impact in basis points"""
        if self.trades == 0:
            return 0.0
        avg_entry = (self.price_range[0] + self.price_range[1]) / 2
        return (self.total_fees / (avg_entry * self.trades)) * 10000


@dataclass
class StrategyMetrics:
    """Metrics for a specific strategy"""
    strategy_name: str
    trades: int = 0
    wins: int = 0
    net_pnl: float = 0.0
    total_fees: float = 0.0
    total_slippage: float = 0.0
    avg_holding_hours: float = 0.0
    
    @property
    def win_rate(self) -> float:
        return (self.wins / self.trades * 100) if self.trades > 0 else 0.0
    
    @property
    def avg_pnl_per_trade(self) -> float:
        return self.net_pnl / self.trades if self.trades > 0 else 0.0


@dataclass
class MarketFamilyMetrics:
    """Metrics by market family/theme"""
    family_name: str
    trades: int = 0
    wins: int = 0
    net_pnl: float = 0.0
    exposure_peak: float = 0.0
    
    @property
    def win_rate(self) -> float:
        return (self.wins / self.trades * 100) if self.trades > 0 else 0.0


@dataclass
class SystemHealth:
    """Real-time system health metrics"""
    timestamp: datetime
    trading_state: str
    uptime_hours: float
    
    # API health
    api_success_rate: float
    api_avg_latency_ms: float
    api_errors_last_hour: int
    
    # Trading metrics
    active_positions: int
    total_exposure: float
    exposure_pct: float
    daily_pnl: float
    
    # Quality metrics
    avg_fill_ratio: float
    avg_slippage_bps: float
    recent_win_rate: float
    
    # Alerts
    alerts_active: List[str] = field(default_factory=list)


class MetricsCollector:
    """
    Comprehensive metrics collection and analysis.
    """
    
    # Price buckets for analysis
    PRICE_BUCKETS = [
        (0, 10, "longshot_extreme"),
        (10, 20, "longshot"),
        (20, 40, "underdog"),
        (40, 60, "tossup"),
        (60, 80, "likely"),
        (80, 90, "favorite"),
        (90, 100, "favorite_extreme")
    ]
    
    def __init__(self, output_dir: str = "metrics"):
        """
        Initialize metrics collector.
        
        Args:
            output_dir: Directory for metrics output
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Storage
        self.trades: List[TradeMetrics] = []
        self.bucket_metrics: Dict[str, BucketMetrics] = {}
        self.strategy_metrics: Dict[str, StrategyMetrics] = {}
        self.family_metrics: Dict[str, MarketFamilyMetrics] = {}
        
        # Real-time tracking
        self.api_calls = deque(maxlen=1000)
        self.api_errors = deque(maxlen=100)
        self.fill_ratios = deque(maxlen=100)
        self.recent_trades = deque(maxlen=50)
        
        # Initialize buckets
        for min_price, max_price, name in self.PRICE_BUCKETS:
            self.bucket_metrics[name] = BucketMetrics(
                bucket_name=name,
                price_range=(min_price, max_price)
            )
        
        self.start_time = datetime.now()
        
        logger.info(f"Metrics collector initialized, output: {self.output_dir}")
    
    def record_trade(
        self,
        ticker: str,
        side: str,
        action: str,
        contracts: int,
        entry_price: float,
        exit_price: float,
        gross_pnl: float,
        net_pnl: float,
        fee: float,
        slippage_bps: float,
        holding_period_hours: float,
        market_family: Optional[str] = None,
        strategy: Optional[str] = None
    ):
        """Record a completed trade"""
        
        trade = TradeMetrics(
            timestamp=datetime.now(),
            ticker=ticker,
            side=side,
            action=action,
            contracts=contracts,
            entry_price=entry_price,
            exit_price=exit_price,
            gross_pnl=gross_pnl,
            net_pnl=net_pnl,
            fee=fee,
            slippage_bps=slippage_bps,
            holding_period_hours=holding_period_hours,
            win=(net_pnl > 0),
            market_family=market_family,
            strategy=strategy
        )
        
        self.trades.append(trade)
        self.recent_trades.append(trade)
        
        # Update bucket metrics
        bucket_name = self._get_bucket_name(entry_price)
        if bucket_name:
            bucket = self.bucket_metrics[bucket_name]
            bucket.trades += 1
            bucket.wins += 1 if trade.win else 0
            bucket.losses += 0 if trade.win else 1
            bucket.gross_pnl += gross_pnl
            bucket.net_pnl += net_pnl
            bucket.total_fees += fee
            
            # Update rolling average slippage
            n = bucket.trades
            bucket.avg_slippage_bps = (
                (bucket.avg_slippage_bps * (n-1) + slippage_bps) / n
            )
        
        # Update strategy metrics
        if strategy:
            if strategy not in self.strategy_metrics:
                self.strategy_metrics[strategy] = StrategyMetrics(strategy_name=strategy)
            
            strat = self.strategy_metrics[strategy]
            strat.trades += 1
            strat.wins += 1 if trade.win else 0
            strat.net_pnl += net_pnl
            strat.total_fees += fee
            strat.total_slippage += slippage_bps
            
            # Update rolling average holding period
            n = strat.trades
            strat.avg_holding_hours = (
                (strat.avg_holding_hours * (n-1) + holding_period_hours) / n
            )
        
        # Update family metrics
        if market_family:
            if market_family not in self.family_metrics:
                self.family_metrics[market_family] = MarketFamilyMetrics(
                    family_name=market_family
                )
            
            family = self.family_metrics[market_family]
            family.trades += 1
            family.wins += 1 if trade.win else 0
            family.net_pnl += net_pnl
        
        # Export immediately for real-time monitoring
        self._export_trade_to_csv(trade)
    
    def record_api_call(self, success: bool, latency_ms: float, error_type: Optional[str] = None):
        """Record an API call"""
        self.api_calls.append({
            'timestamp': datetime.now(),
            'success': success,
            'latency_ms': latency_ms
        })
        
        if not success:
            self.api_errors.append({
                'timestamp': datetime.now(),
                'error_type': error_type
            })
    
    def record_fill_ratio(self, filled: int, attempted: int):
        """Record fill success ratio"""
        ratio = filled / attempted if attempted > 0 else 0.0
        self.fill_ratios.append(ratio)
    
    def _get_bucket_name(self, price: float) -> Optional[str]:
        """Get bucket name for a price"""
        for min_price, max_price, name in self.PRICE_BUCKETS:
            if min_price <= price < max_price:
                return name
        return None
    
    def get_bucket_summary(self) -> Dict[str, Dict]:
        """Get summary of all bucket metrics"""
        return {
            name: {
                'price_range': f"{bucket.price_range[0]}-{bucket.price_range[1]}",
                'trades': bucket.trades,
                'win_rate': f"{bucket.win_rate:.1f}%",
                'net_pnl': f"${bucket.net_pnl:.2f}",
                'net_bps': f"{bucket.net_bps:.1f}",
                'fee_drag_bps': f"{bucket.fee_drag_bps:.1f}",
                'avg_slippage_bps': f"{bucket.avg_slippage_bps:.1f}"
            }
            for name, bucket in self.bucket_metrics.items()
            if bucket.trades > 0
        }
    
    def get_strategy_summary(self) -> Dict[str, Dict]:
        """Get summary of all strategy metrics"""
        return {
            name: {
                'trades': strat.trades,
                'win_rate': f"{strat.win_rate:.1f}%",
                'net_pnl': f"${strat.net_pnl:.2f}",
                'avg_pnl_per_trade': f"${strat.avg_pnl_per_trade:.2f}",
                'total_fees': f"${strat.total_fees:.2f}",
                'avg_holding_hours': f"{strat.avg_holding_hours:.1f}h"
            }
            for name, strat in self.strategy_metrics.items()
        }
    
    def get_family_summary(self) -> Dict[str, Dict]:
        """Get summary of market family performance"""
        return {
            name: {
                'trades': family.trades,
                'win_rate': f"{family.win_rate:.1f}%",
                'net_pnl': f"${family.net_pnl:.2f}",
                'exposure_peak': f"${family.exposure_peak:.2f}"
            }
            for name, family in self.family_metrics.items()
        }
    
    def get_system_health(
        self,
        trading_state: str,
        active_positions: int,
        total_exposure: float,
        capital: float,
        daily_pnl: float
    ) -> SystemHealth:
        """Generate system health snapshot"""
        
        # Calculate API metrics
        if self.api_calls:
            recent_calls = [c for c in self.api_calls 
                          if (datetime.now() - c['timestamp']).total_seconds() < 300]  # 5 min
            api_success_rate = sum(1 for c in recent_calls if c['success']) / len(recent_calls) if recent_calls else 1.0
            api_avg_latency = sum(c['latency_ms'] for c in recent_calls) / len(recent_calls) if recent_calls else 0.0
        else:
            api_success_rate = 1.0
            api_avg_latency = 0.0
        
        # Errors in last hour
        cutoff = datetime.now() - timedelta(hours=1)
        errors_last_hour = sum(1 for e in self.api_errors if e['timestamp'] >= cutoff)
        
        # Fill ratio
        avg_fill_ratio = sum(self.fill_ratios) / len(self.fill_ratios) if self.fill_ratios else 1.0
        
        # Recent slippage
        avg_slippage = sum(t.slippage_bps for t in self.recent_trades) / len(self.recent_trades) if self.recent_trades else 0.0
        
        # Recent win rate
        recent_wins = sum(1 for t in self.recent_trades if t.win)
        recent_win_rate = (recent_wins / len(self.recent_trades) * 100) if self.recent_trades else 0.0
        
        # Calculate alerts
        alerts = []
        if api_success_rate < 0.95:
            alerts.append(f"API success rate low: {api_success_rate:.1%}")
        if errors_last_hour > 10:
            alerts.append(f"High error rate: {errors_last_hour} errors/hour")
        if avg_fill_ratio < 0.8:
            alerts.append(f"Low fill ratio: {avg_fill_ratio:.1%}")
        if avg_slippage > 50:
            alerts.append(f"High slippage: {avg_slippage:.1f} bps")
        if exposure_pct := (total_exposure / capital * 100 if capital > 0 else 0) > 20:
            alerts.append(f"High exposure: {exposure_pct:.1f}%")
        
        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
        
        return SystemHealth(
            timestamp=datetime.now(),
            trading_state=trading_state,
            uptime_hours=uptime_hours,
            api_success_rate=api_success_rate,
            api_avg_latency_ms=api_avg_latency,
            api_errors_last_hour=errors_last_hour,
            active_positions=active_positions,
            total_exposure=total_exposure,
            exposure_pct=(total_exposure / capital * 100) if capital > 0 else 0,
            daily_pnl=daily_pnl,
            avg_fill_ratio=avg_fill_ratio,
            avg_slippage_bps=avg_slippage,
            recent_win_rate=recent_win_rate,
            alerts_active=alerts
        )
    
    def print_daily_summary(self, capital: float):
        """Print comprehensive daily summary"""
        print("\n" + "=" * 80)
        print("DAILY PERFORMANCE SUMMARY")
        print("=" * 80)
        
        # Overall stats
        total_trades = len(self.trades)
        if total_trades > 0:
            wins = sum(1 for t in self.trades if t.win)
            total_net_pnl = sum(t.net_pnl for t in self.trades)
            total_fees = sum(t.fee for t in self.trades)
            
            print(f"\nOverall Performance:")
            print(f"  Total Trades: {total_trades}")
            print(f"  Win Rate: {wins/total_trades*100:.1f}%")
            print(f"  Net P&L: ${total_net_pnl:.2f}")
            print(f"  Total Fees: ${total_fees:.2f}")
            print(f"  Return on Capital: {total_net_pnl/capital*100:.2f}%")
        
        # Bucket performance
        print(f"\nPerformance by Price Bucket:")
        for name, bucket in sorted(self.bucket_metrics.items(), 
                                   key=lambda x: x[1].price_range[0]):
            if bucket.trades > 0:
                print(f"  {bucket.bucket_name:20s} | Trades: {bucket.trades:3d} | "
                      f"Win Rate: {bucket.win_rate:5.1f}% | "
                      f"Net bps: {bucket.net_bps:6.1f} | "
                      f"P&L: ${bucket.net_pnl:8.2f}")
        
        # Strategy performance
        if self.strategy_metrics:
            print(f"\nPerformance by Strategy:")
            for name, strat in self.strategy_metrics.items():
                print(f"  {name:20s} | Trades: {strat.trades:3d} | "
                      f"Win Rate: {strat.win_rate:5.1f}% | "
                      f"P&L: ${strat.net_pnl:8.2f}")
        
        # Family performance
        if self.family_metrics:
            print(f"\nPerformance by Market Family:")
            for name, family in sorted(self.family_metrics.items(),
                                      key=lambda x: x[1].net_pnl,
                                      reverse=True):
                print(f"  {name:20s} | Trades: {family.trades:3d} | "
                      f"Win Rate: {family.win_rate:5.1f}% | "
                      f"P&L: ${family.net_pnl:8.2f}")
        
        print("=" * 80 + "\n")
    
    def _export_trade_to_csv(self, trade: TradeMetrics):
        """Append trade to CSV for real-time monitoring"""
        csv_path = self.output_dir / "trades_log.csv"
        
        # Check if file exists to write header
        file_exists = csv_path.exists()
        
        with open(csv_path, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'ticker', 'side', 'action', 'contracts',
                'entry_price', 'exit_price', 'gross_pnl', 'net_pnl',
                'fee', 'slippage_bps', 'holding_period_hours', 'win',
                'market_family', 'strategy'
            ])
            
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(asdict(trade))
    
    def export_all_metrics(self):
        """Export all metrics to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Bucket metrics
        with open(self.output_dir / f"bucket_metrics_{timestamp}.json", 'w') as f:
            json.dump(self.get_bucket_summary(), f, indent=2)
        
        # Strategy metrics
        with open(self.output_dir / f"strategy_metrics_{timestamp}.json", 'w') as f:
            json.dump(self.get_strategy_summary(), f, indent=2)
        
        # Family metrics
        with open(self.output_dir / f"family_metrics_{timestamp}.json", 'w') as f:
            json.dump(self.get_family_summary(), f, indent=2)
        
        logger.info(f"Exported metrics to {self.output_dir}")
