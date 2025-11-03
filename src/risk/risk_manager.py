"""
Production Risk Management System

Features:
- Fractional Kelly sizing (¼–½ Kelly)
- Per-theme correlation caps
- Circuit breakers and kill-switches
- Daily loss limits
- Streak loss detection
- Slippage monitoring
- Dynamic trade throttling
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
from enum import Enum
import logging

try:
    from scipy.cluster.hierarchy import linkage, fcluster
except ImportError:
    # Optional dependency for correlation clustering
    linkage = None
    fcluster = None

logger = logging.getLogger(__name__)


class TradingState(Enum):
    """Trading system state"""
    ACTIVE = "active"
    THROTTLED = "throttled"
    PAUSED = "paused"
    HALTED = "halted"


class KillSwitchReason(Enum):
    """Reasons for killing trading"""
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    STREAK_LOSS = "streak_loss"
    SLIPPAGE_EXCESSIVE = "slippage_excessive"
    ERROR_BURST = "error_burst"
    STALE_BOOK = "stale_book"
    NO_FILLS = "no_fills"
    CORRELATION_BREACH = "correlation_breach"
    MANUAL = "manual"


@dataclass
class RiskLimits:
    """Risk limit configuration"""
    
    # Capital limits
    max_total_exposure_pct: float = 0.20  # 20% of capital max
    max_single_position_pct: float = 0.05  # 5% per position
    max_correlated_group_pct: float = 0.15  # 15% per correlated group
    
    # Kelly parameters
    kelly_fraction: float = 0.25  # Quarter Kelly (conservative)
    min_kelly_bet: float = 0.01  # Minimum 1% of capital
    max_kelly_bet: float = 0.10  # Maximum 10% of capital
    
    # Daily limits
    max_daily_loss_dollars: float = 500.0
    max_daily_loss_pct: float = 0.05  # 5% of capital
    max_daily_trades: int = 50
    
    # Streak limits
    max_consecutive_losses: int = 5
    loss_streak_pause_hours: int = 4
    
    # Quality thresholds
    max_slippage_bps: float = 50.0  # 50 basis points
    max_spread_bps: float = 200.0  # 200 basis points
    min_edge_to_trade: float = 0.03  # 3% minimum edge
    
    # System health
    max_error_rate_per_hour: int = 10
    max_stale_book_seconds: int = 30
    min_fills_per_scan: int = 1  # Expect at least 1 fill per N scans
    min_fills_lookback_scans: int = 20
    
    # Correlation
    correlation_threshold: float = 0.5  # Markets with >50% correlation grouped
    max_correlated_positions: int = 3  # Max positions in one correlated group


@dataclass
class MarketGroup:
    """Group of correlated markets"""
    group_id: str
    tickers: Set[str] = field(default_factory=set)
    correlation_score: float = 0.0
    
    def add_market(self, ticker: str):
        """Add market to group"""
        self.tickers.add(ticker)
    
    def remove_market(self, ticker: str):
        """Remove market from group"""
        self.tickers.discard(ticker)
    
    @property
    def size(self) -> int:
        """Number of markets in group"""
        return len(self.tickers)


@dataclass
class Position:
    """Position tracking"""
    ticker: str
    side: str
    contracts: int
    entry_price_cents: float
    entry_timestamp: datetime
    market_group: Optional[str] = None
    

class RiskManager:
    """
    Production risk management system.
    
    Implements:
    - Kelly Criterion position sizing
    - Correlation-based exposure limits
    - Multiple kill-switches
    - Real-time risk monitoring
    """
    
    def __init__(
        self,
        initial_capital: float,
        limits: Optional[RiskLimits] = None
    ):
        """
        Initialize risk manager.
        
        Args:
            initial_capital: Starting capital
            limits: Risk limit configuration
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.limits = limits or RiskLimits()
        
        # State
        self.trading_state = TradingState.ACTIVE
        self.kill_switch_reason: Optional[KillSwitchReason] = None
        
        # Position tracking
        self.positions: Dict[str, Position] = {}
        self.market_groups: Dict[str, MarketGroup] = {}
        
        # Daily tracking
        self.daily_pnl = 0.0
        self.daily_trades = 0
        self.daily_reset_time = datetime.now().replace(hour=0, minute=0, second=0)
        
        # Streak tracking
        self.consecutive_losses = 0
        self.last_loss_time: Optional[datetime] = None
        
        # Quality tracking
        self.recent_slippage = deque(maxlen=100)
        self.recent_errors = deque(maxlen=100)
        self.recent_fills = deque(maxlen=self.limits.min_fills_lookback_scans)
        
        # Performance tracking
        self.realized_edge_window = deque(maxlen=50)
        
        logger.info("Risk manager initialized")
        logger.info(f"Initial capital: ${initial_capital:,.2f}")
        logger.info(f"Kelly fraction: {self.limits.kelly_fraction}")
    
    def _reset_daily_limits(self):
        """Reset daily counters"""
        now = datetime.now()
        if now.date() > self.daily_reset_time.date():
            logger.info("Resetting daily limits")
            self.daily_pnl = 0.0
            self.daily_trades = 0
            self.daily_reset_time = now.replace(hour=0, minute=0, second=0)
    
    def can_trade(self) -> Tuple[bool, Optional[str]]:
        """
        Check if trading is allowed.
        
        Returns:
            (allowed, reason) tuple
        """
        self._reset_daily_limits()
        
        if self.trading_state == TradingState.HALTED:
            return False, f"Trading halted: {self.kill_switch_reason.value}"
        
        if self.trading_state == TradingState.PAUSED:
            # Check if pause should be lifted
            if self.last_loss_time:
                pause_duration = datetime.now() - self.last_loss_time
                if pause_duration.total_seconds() / 3600 < self.limits.loss_streak_pause_hours:
                    return False, f"Paused due to loss streak ({self.consecutive_losses} losses)"
                else:
                    # Lift pause
                    self.trading_state = TradingState.ACTIVE
                    self.consecutive_losses = 0
                    logger.info("Trading pause lifted")
        
        # Check daily limits
        if abs(self.daily_pnl) >= self.limits.max_daily_loss_dollars:
            self._trigger_kill_switch(KillSwitchReason.DAILY_LOSS_LIMIT)
            return False, f"Daily loss limit reached: ${self.daily_pnl:.2f}"
        
        daily_loss_pct = abs(self.daily_pnl) / self.current_capital
        if daily_loss_pct >= self.limits.max_daily_loss_pct:
            self._trigger_kill_switch(KillSwitchReason.DAILY_LOSS_LIMIT)
            return False, f"Daily loss % limit reached: {daily_loss_pct:.1%}"
        
        if self.daily_trades >= self.limits.max_daily_trades:
            return False, f"Daily trade limit reached: {self.daily_trades}"
        
        # Check error rate
        if self._check_error_burst():
            self._trigger_kill_switch(KillSwitchReason.ERROR_BURST)
            return False, "Error burst detected"
        
        # Check fill rate
        if self._check_no_fills():
            self._trigger_kill_switch(KillSwitchReason.NO_FILLS)
            return False, "No fills detected in recent scans"
        
        if self.trading_state == TradingState.THROTTLED:
            return False, "Trading throttled due to poor realized edge"
        
        return True, None
    
    def calculate_position_size(
        self,
        edge: float,
        win_probability: float,
        price_cents: int,
        market_group: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        Calculate optimal position size using fractional Kelly.
        
        Args:
            edge: Expected edge (decimal, e.g., 0.05 = 5%)
            win_probability: Estimated win probability
            price_cents: Entry price in cents
            market_group: Optional market group for correlation limits
            
        Returns:
            (contracts, reason) tuple
        """
        # Check if we can trade
        can_trade, reason = self.can_trade()
        if not can_trade:
            return 0, reason
        
        # Check minimum edge
        if edge < self.limits.min_edge_to_trade:
            return 0, f"Edge too small: {edge:.2%} < {self.limits.min_edge_to_trade:.2%}"
        
        # Kelly Criterion: f = (p * b - q) / b
        # where p = win_prob, q = 1-p, b = (100-price)/price (odds)
        if price_cents <= 0 or price_cents >= 100:
            return 0, "Invalid price"
        
        odds = (100 - price_cents) / price_cents
        kelly = (win_probability * odds - (1 - win_probability)) / odds
        
        # Apply Kelly fraction
        fractional_kelly = kelly * self.limits.kelly_fraction
        
        # Calculate position size in dollars
        position_size_dollars = self.current_capital * fractional_kelly
        
        # Apply limits
        min_size = self.current_capital * self.limits.min_kelly_bet
        max_size = self.current_capital * self.limits.max_kelly_bet
        position_size_dollars = max(min_size, min(max_size, position_size_dollars))
        
        # Check single position limit
        max_single_position = self.current_capital * self.limits.max_single_position_pct
        if position_size_dollars > max_single_position:
            position_size_dollars = max_single_position
        
        # Check correlation group limit
        if market_group and market_group in self.market_groups:
            group_exposure = self._get_group_exposure(market_group)
            max_group_exposure = self.current_capital * self.limits.max_correlated_group_pct
            
            if group_exposure + position_size_dollars > max_group_exposure:
                position_size_dollars = max(0, max_group_exposure - group_exposure)
                if position_size_dollars == 0:
                    return 0, f"Correlation group limit reached: {market_group}"
        
        # Check total exposure limit
        total_exposure = self._get_total_exposure()
        max_total_exposure = self.current_capital * self.limits.max_total_exposure_pct
        
        if total_exposure + position_size_dollars > max_total_exposure:
            position_size_dollars = max(0, max_total_exposure - total_exposure)
            if position_size_dollars == 0:
                return 0, "Total exposure limit reached"
        
        # Convert to contracts
        price_dollars = price_cents / 100.0
        contracts = int(position_size_dollars / price_dollars)
        
        if contracts < 1:
            return 0, "Position size too small for 1 contract"
        
        return contracts, "OK"
    
    def add_position(
        self,
        ticker: str,
        side: str,
        contracts: int,
        entry_price_cents: float,
        market_group: Optional[str] = None
    ):
        """
        Add a new position.
        
        Args:
            ticker: Market ticker
            side: 'yes' or 'no'
            contracts: Number of contracts
            entry_price_cents: Entry price
            market_group: Optional correlation group
        """
        position = Position(
            ticker=ticker,
            side=side,
            contracts=contracts,
            entry_price_cents=entry_price_cents,
            entry_timestamp=datetime.now(),
            market_group=market_group
        )
        
        self.positions[ticker] = position
        self.daily_trades += 1
        
        # Add to market group
        if market_group:
            if market_group not in self.market_groups:
                self.market_groups[market_group] = MarketGroup(group_id=market_group)
            self.market_groups[market_group].add_market(ticker)
        
        logger.info(f"Added position: {ticker} {side} {contracts}@{entry_price_cents:.1f}¢")
    
    def close_position(
        self,
        ticker: str,
        resolution: str,
        pnl: float
    ):
        """
        Close a position and update risk metrics.
        
        Args:
            ticker: Market ticker
            resolution: Market resolution
            pnl: Net P&L
        """
        if ticker not in self.positions:
            logger.warning(f"Attempted to close non-existent position: {ticker}")
            return
        
        position = self.positions[ticker]
        
        # Update capital
        self.current_capital += pnl
        self.daily_pnl += pnl
        
        # Track win/loss streak
        if pnl < 0:
            self.consecutive_losses += 1
            self.last_loss_time = datetime.now()
            
            # Check streak limit
            if self.consecutive_losses >= self.limits.max_consecutive_losses:
                self.trading_state = TradingState.PAUSED
                logger.warning(f"Trading paused: {self.consecutive_losses} consecutive losses")
        else:
            self.consecutive_losses = 0
        
        # Calculate realized edge
        entry_cost = (position.entry_price_cents / 100.0) * position.contracts
        roi = (pnl / entry_cost) if entry_cost > 0 else 0
        self.realized_edge_window.append(roi)
        
        # Check if realized edge is below target
        if len(self.realized_edge_window) >= 20:
            avg_realized_edge = np.mean(list(self.realized_edge_window))
            if avg_realized_edge < 0:
                self.trading_state = TradingState.THROTTLED
                logger.warning(f"Trading throttled: negative realized edge ({avg_realized_edge:.2%})")
        
        # Remove from market group
        if position.market_group and position.market_group in self.market_groups:
            self.market_groups[position.market_group].remove_market(ticker)
        
        # Remove position
        del self.positions[ticker]
        
        logger.info(f"Closed position: {ticker} P&L=${pnl:.2f} ROI={roi:.2%}")
    
    def check_market_quality(
        self,
        spread_bps: float,
        last_update_time: datetime
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if market quality is acceptable.
        
        Args:
            spread_bps: Bid-ask spread in basis points
            last_update_time: Time of last market data update
            
        Returns:
            (acceptable, reason) tuple
        """
        # Check spread
        if spread_bps > self.limits.max_spread_bps:
            return False, f"Spread too wide: {spread_bps:.1f} bps"
        
        # Check staleness
        age_seconds = (datetime.now() - last_update_time).total_seconds()
        if age_seconds > self.limits.max_stale_book_seconds:
            return False, f"Stale book: {age_seconds:.1f}s old"
        
        return True, None
    
    def record_slippage(self, slippage_bps: float):
        """Record slippage for monitoring"""
        self.recent_slippage.append((datetime.now(), slippage_bps))
        
        # Check if excessive
        if slippage_bps > self.limits.max_slippage_bps:
            logger.warning(f"Excessive slippage: {slippage_bps:.1f} bps")
            
            # Check if this is a pattern
            recent_high_slippage = sum(
                1 for _, s in self.recent_slippage
                if s > self.limits.max_slippage_bps
            )
            
            if recent_high_slippage > len(self.recent_slippage) * 0.3:  # 30% of recent
                self._trigger_kill_switch(KillSwitchReason.SLIPPAGE_EXCESSIVE)
    
    def record_error(self, error_type: str):
        """Record an error for monitoring"""
        self.recent_errors.append((datetime.now(), error_type))
    
    def record_scan_result(self, had_fills: bool):
        """Record whether a scan resulted in fills"""
        self.recent_fills.append(had_fills)
    
    def _check_error_burst(self) -> bool:
        """Check for error burst"""
        if len(self.recent_errors) < 5:
            return False
        
        # Check errors in last hour
        cutoff = datetime.now() - timedelta(hours=1)
        recent_errors_count = sum(
            1 for ts, _ in self.recent_errors
            if ts >= cutoff
        )
        
        return recent_errors_count >= self.limits.max_error_rate_per_hour
    
    def _check_no_fills(self) -> bool:
        """Check if we're getting fills"""
        if len(self.recent_fills) < self.limits.min_fills_lookback_scans:
            return False
        
        # Should have at least 1 fill in last N scans
        recent_fill_count = sum(self.recent_fills)
        return recent_fill_count < self.limits.min_fills_per_scan
    
    def _get_total_exposure(self) -> float:
        """Calculate total exposure across all positions"""
        return sum(
            (pos.entry_price_cents / 100.0) * pos.contracts
            for pos in self.positions.values()
        )
    
    def _get_group_exposure(self, group_id: str) -> float:
        """Calculate exposure for a correlation group"""
        if group_id not in self.market_groups:
            return 0.0
        
        group_tickers = self.market_groups[group_id].tickers
        return sum(
            (pos.entry_price_cents / 100.0) * pos.contracts
            for ticker, pos in self.positions.items()
            if ticker in group_tickers
        )
    
    def _trigger_kill_switch(self, reason: KillSwitchReason):
        """Trigger a kill switch"""
        self.trading_state = TradingState.HALTED
        self.kill_switch_reason = reason
        logger.error(f"KILL SWITCH TRIGGERED: {reason.value}")
    
    def manual_resume(self):
        """Manually resume trading after kill switch"""
        logger.warning("Trading manually resumed")
        self.trading_state = TradingState.ACTIVE
        self.kill_switch_reason = None
        self.consecutive_losses = 0
    
    def get_status(self) -> Dict:
        """Get current risk status"""
        total_exposure = self._get_total_exposure()
        exposure_pct = (total_exposure / self.current_capital) * 100 if self.current_capital > 0 else 0
        
        return {
            'trading_state': self.trading_state.value,
            'kill_switch_reason': self.kill_switch_reason.value if self.kill_switch_reason else None,
            'current_capital': self.current_capital,
            'capital_change_pct': ((self.current_capital - self.initial_capital) / self.initial_capital) * 100,
            'total_exposure': total_exposure,
            'exposure_pct': exposure_pct,
            'active_positions': len(self.positions),
            'daily_pnl': self.daily_pnl,
            'daily_trades': self.daily_trades,
            'consecutive_losses': self.consecutive_losses,
            'realized_edge_avg': np.mean(list(self.realized_edge_window)) if self.realized_edge_window else 0,
            'recent_slippage_avg': np.mean([s for _, s in self.recent_slippage]) if self.recent_slippage else 0
        }


def identify_correlated_markets(
    historical_returns: pd.DataFrame,
    correlation_threshold: float = 0.5
) -> Dict[str, List[str]]:
    """
    Identify groups of correlated markets.
    
    Args:
        historical_returns: DataFrame with returns by ticker
        correlation_threshold: Minimum correlation to group together
        
    Returns:
        Dictionary mapping group_id to list of tickers
    """
    if linkage is None or fcluster is None:
        raise ImportError("scipy is required for correlation clustering. Install with: pip install scipy")
    
    # Calculate correlation matrix
    corr_matrix = historical_returns.corr()
    
    # Convert to distance matrix
    distance_matrix = 1 - corr_matrix.abs()
    
    # Perform hierarchical clustering
    linkage_matrix = linkage(distance_matrix, method='average')
    
    # Form clusters
    clusters = fcluster(
        linkage_matrix,
        t=1 - correlation_threshold,
        criterion='distance'
    )
    
    # Create groups
    groups = defaultdict(list)
    for ticker, cluster_id in zip(corr_matrix.columns, clusters):
        groups[f"group_{cluster_id}"].append(ticker)
    
    return dict(groups)
