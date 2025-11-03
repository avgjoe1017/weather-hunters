"""
Strategy A: FLB (Favorite-Longshot Bias) Harvester

This strategy exploits the documented systemic bias in prediction markets
where favorites are underpriced and longshots are overpriced.

Based on: "Makers and Takers: The Economics of the Kalshi Prediction Market"
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from loguru import logger
import time


@dataclass
class FLBConfig:
    """Configuration for the FLB strategy."""
    
    # Price thresholds (in decimal form, e.g., 0.90 = 90¢)
    favorite_threshold: float = 0.90
    longshot_threshold: float = 0.10
    
    # Position sizing
    max_contracts_per_trade: int = 10
    max_total_exposure: float = 1000.0  # Maximum $ at risk
    
    # Risk management
    min_edge_to_trade: float = 0.02  # Minimum expected edge to enter
    max_positions_per_market: int = 1  # Avoid doubling down
    
    # Market filters
    min_liquidity: int = 50  # Minimum contracts of liquidity
    exclude_series: List[str] = None  # Series to exclude
    
    def __post_init__(self):
        if self.exclude_series is None:
            self.exclude_series = []


class FLBHarvester:
    """
    The FLB Harvester scans all active markets and trades based on
    the Favorite-Longshot Bias.
    
    Strategy Logic:
    - When market price >= favorite_threshold: BUY YES
    - When market price <= longshot_threshold: BUY NO (fade the longshot)
    """
    
    def __init__(self, api_connector, config: Optional[FLBConfig] = None, risk_manager=None):
        """
        Initialize the FLB Harvester.
        
        Args:
            api_connector: Instance of KalshiAPIConnector
            config: Strategy configuration (uses defaults if None)
            risk_manager: Optional RiskManager instance for position sizing
        """
        self.api = api_connector
        self.config = config or FLBConfig()
        self.risk_mgr = risk_manager
        
        # Track positions to avoid overexposure
        self.active_positions: Dict[str, int] = {}  # ticker -> contract count
        self.total_exposure: float = 0.0
        
        logger.info("Initialized FLB Harvester strategy")
        logger.info(f"Favorite threshold: {self.config.favorite_threshold:.2f}")
        logger.info(f"Longshot threshold: {self.config.longshot_threshold:.2f}")
        if self.risk_mgr:
            logger.info("Risk manager integrated for position sizing")
    
    def scan_and_trade(self, dry_run: bool = True) -> List[Dict]:
        """
        Scan all markets and execute FLB trades.
        
        Args:
            dry_run: If True, log opportunities but don't execute trades
            
        Returns:
            List of trade signals/executions
        """
        logger.info("Starting FLB market scan...")
        
        # Get all open markets
        markets = self.api.get_markets(limit=1000, status="open")
        logger.info(f"Scanning {len(markets)} open markets")
        
        trades_executed = []
        opportunities_found = 0
        
        for market in markets:
            # Apply filters
            if not self._should_trade_market(market):
                continue
            
            # Check for FLB opportunity
            trade_signal = self._evaluate_market(market)
            
            if trade_signal:
                opportunities_found += 1
                
                if dry_run:
                    logger.info(f"[DRY RUN] Found opportunity: {trade_signal}")
                else:
                    # Execute the trade
                    result = self._execute_trade(trade_signal)
                    if result:
                        trades_executed.append(result)
                        
                        # Update exposure tracking
                        ticker = trade_signal['ticker']
                        contracts = trade_signal['count']
                        self.active_positions[ticker] = contracts
                        self.total_exposure += trade_signal['cost']
        
        logger.info(f"Scan complete. Found {opportunities_found} opportunities")
        if not dry_run:
            logger.info(f"Executed {len(trades_executed)} trades")
        
        return trades_executed
    
    def _should_trade_market(self, market: Dict) -> bool:
        """
        Apply filters to determine if we should consider this market.
        
        Args:
            market: Market dictionary from API
            
        Returns:
            True if market passes filters
        """
        ticker = market.get("ticker", "")
        series_ticker = market.get("series_ticker", "")
        
        # Check if already have position
        if ticker in self.active_positions:
            if self.active_positions[ticker] >= self.config.max_positions_per_market:
                return False
        
        # Check exposure limits
        if self.total_exposure >= self.config.max_total_exposure:
            logger.warning("Max total exposure reached, pausing new trades")
            return False
        
        # Check series exclusions
        if series_ticker in self.config.exclude_series:
            return False
        
        return True
    
    def _evaluate_market(self, market: Dict) -> Optional[Dict]:
        """
        Evaluate if market presents an FLB trading opportunity.
        
        Args:
            market: Market dictionary from API
            
        Returns:
            Trade signal dict if opportunity exists, None otherwise
        """
        ticker = market.get("ticker")
        yes_bid = market.get("yes_bid")
        yes_ask = market.get("yes_ask")
        no_bid = market.get("no_bid")
        no_ask = market.get("no_ask")
        
        # Need valid prices
        if yes_bid is None or yes_ask is None:
            return None
        
        # Convert to decimal
        yes_price = yes_ask / 100.0  # We'd be buying at the ask
        no_price = yes_bid / 100.0   # Buying NO = selling YES
        
        # Check for FAVORITE opportunity (underpriced high-probability events)
        if yes_price >= self.config.favorite_threshold:
            # Calculate edge
            # Paper shows favorites win MORE than their price implies
            # Conservative assumption: they win at (price + edge) rate
            implied_prob = yes_price
            estimated_true_prob = min(0.98, yes_price + 0.03)  # Conservative 3% edge
            edge = estimated_true_prob - implied_prob
            
            if edge >= self.config.min_edge_to_trade:
                # Estimate win probability
                win_prob = self._estimate_win_probability(yes_ask, edge, is_favorite=True)
                
                # Calculate position size with risk manager
                contracts = self._calculate_position_size(yes_ask, edge, win_prob, ticker)
                
                if contracts > 0:
                    return {
                        'ticker': ticker,
                        'side': 'yes',
                        'action': 'buy',
                        'price': yes_ask,
                        'count': contracts,
                        'cost': (yes_ask / 100.0) * contracts,
                        'edge': edge,
                        'win_prob': win_prob,
                        'strategy': 'FLB_FAVORITE',
                        'reason': f'Favorite at {yes_price:.2%}, edge={edge:.2%}'
                    }
                else:
                    logger.debug(f"Trade rejected by risk manager: {ticker}")
        
        # Check for LONGSHOT opportunity (overpriced low-probability events)
        elif yes_price <= self.config.longshot_threshold:
            # Longshots win LESS than their price implies
            # We profit by betting against them (buying NO)
            implied_prob = yes_price
            estimated_true_prob = max(0.02, yes_price - 0.03)  # Conservative 3% edge
            edge = implied_prob - estimated_true_prob
            
            if edge >= self.config.min_edge_to_trade:
                # Buying NO is equivalent to selling YES
                no_price = no_ask if no_ask else int((1 - yes_price) * 100)
                no_price_to_pay = no_price / 100.0
                
                # For NO positions, win probability is (1 - yes_price_true_prob)
                yes_win_prob = max(0.02, yes_price - 0.03)
                no_win_prob = 1.0 - yes_win_prob  # We win if NO wins
                
                # Calculate position size with risk manager
                contracts = self._calculate_position_size(no_price, edge, no_win_prob, ticker)
                
                if contracts > 0:
                    return {
                        'ticker': ticker,
                        'side': 'no',
                        'action': 'buy',
                        'price': no_price,
                        'count': contracts,
                        'cost': no_price_to_pay * contracts,
                        'edge': edge,
                        'win_prob': no_win_prob,
                        'strategy': 'FLB_LONGSHOT',
                        'reason': f'Longshot at {yes_price:.2%}, edge={edge:.2%}'
                    }
                else:
                    logger.debug(f"Trade rejected by risk manager: {ticker}")
        
        return None
    
    def _identify_market_group(self, ticker: str) -> Optional[str]:
        """
        Identify correlation group for a market ticker.
        
        Simple heuristic: markets with same series or similar prefixes
        are likely correlated. For production, use historical correlation analysis.
        
        Args:
            ticker: Market ticker (e.g., "WEATHER-LAX-2024-01-15")
            
        Returns:
            Market group identifier or None
        """
        # Extract series or category prefix
        # Examples: "WEATHER-LAX" -> "weather_california"
        #          "PRES-2024" -> "president_2024"
        if "-" in ticker:
            parts = ticker.split("-")
            if len(parts) >= 2:
                category = parts[0].lower()
                location = parts[1].lower() if len(parts) > 1 else "general"
                
                # Group weather markets by region
                if category == "weather":
                    if location in ["lax", "sfo", "san"]:
                        return "weather_california"
                    elif location in ["nyc", "jfk", "lga"]:
                        return "weather_newyork"
                    else:
                        return f"weather_{location}"
                
                # Group other markets by category
                return f"{category}_general"
        
        return None
    
    def _estimate_win_probability(self, price_cents: int, edge: float, is_favorite: bool) -> float:
        """
        Estimate true win probability based on price and edge.
        
        Args:
            price_cents: Market price in cents
            edge: Expected edge
            is_favorite: True if this is a favorite trade (buy YES)
            
        Returns:
            Estimated win probability (0.0 to 1.0)
        """
        implied_prob = price_cents / 100.0
        
        if is_favorite:
            # Favorites win more than implied
            return min(0.98, implied_prob + edge)
        else:
            # Longshots win less than implied
            return max(0.02, implied_prob - edge)
    
    def _calculate_position_size(self, price_cents: int, edge: float, win_prob: float, ticker: str) -> int:
        """
        Calculate optimal position size using RiskManager if available,
        otherwise fall back to simple Kelly.
        
        Args:
            price_cents: Price in cents
            edge: Expected edge as decimal
            win_prob: Estimated win probability
            ticker: Market ticker for correlation grouping
            
        Returns:
            Number of contracts to trade
        """
        # Use RiskManager if available
        if self.risk_mgr:
            market_group = self._identify_market_group(ticker)
            contracts, reason = self.risk_mgr.calculate_position_size(
                edge=edge,
                win_probability=win_prob,
                price_cents=price_cents,
                market_group=market_group
            )
            
            if contracts == 0:
                logger.debug(f"Position sizing rejected for {ticker}: {reason}")
            
            return contracts
        
        # Fallback to simple fractional Kelly
        kelly_fraction = 0.25  # Quarter Kelly for safety
        
        if price_cents == 0:
            return 0
        
        kelly_bet = (edge * kelly_fraction * self.config.max_total_exposure) / (price_cents / 100.0)
        
        # Round to contracts and apply max limit
        contracts = int(kelly_bet)
        contracts = max(1, min(contracts, self.config.max_contracts_per_trade))
        
        return contracts
    
    def _execute_trade(self, signal: Dict) -> Optional[Dict]:
        """
        Execute a trade based on the signal.
        
        Args:
            signal: Trade signal dictionary
            
        Returns:
            Execution result or None if failed
        """
        try:
            logger.info(f"Executing {signal['strategy']}: {signal['action']} {signal['count']} "
                       f"{signal['side']} @ {signal['ticker']}")
            
            result = self.api.create_order(
                ticker=signal['ticker'],
                side=signal['side'],
                action=signal['action'],
                count=signal['count'],
                type='market'
            )
            
            logger.success(f"Trade executed successfully: {result}")
            return {**signal, 'execution': result}
            
        except Exception as e:
            logger.error(f"Failed to execute trade: {e}")
            return None
    
    def update_positions(self):
        """
        Update active positions from API to keep tracking accurate.
        """
        try:
            positions = self.api.get_positions()
            self.active_positions = {}
            self.total_exposure = 0.0
            
            for pos in positions:
                ticker = pos.get('ticker')
                contracts = abs(pos.get('position', 0))
                cost_basis = abs(pos.get('total_cost', 0)) / 100.0
                
                self.active_positions[ticker] = contracts
                self.total_exposure += cost_basis
            
            logger.info(f"Updated positions: {len(self.active_positions)} active, "
                       f"${self.total_exposure:.2f} exposed")
                       
        except Exception as e:
            logger.error(f"Failed to update positions: {e}")
    
    def get_stats(self) -> Dict:
        """
        Get current strategy statistics.
        
        Returns:
            Dictionary of strategy stats
        """
        return {
            'active_positions': len(self.active_positions),
            'total_exposure': self.total_exposure,
            'available_capital': self.config.max_total_exposure - self.total_exposure,
            'utilization': self.total_exposure / self.config.max_total_exposure
        }
