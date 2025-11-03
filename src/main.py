"""
Main Trading Engine

Orchestrates the execution of trading strategies, manages risk,
and provides the main event loop for the bot.
"""

import time
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
import sys

from src.api.kalshi_connector import create_connector_from_env
from src.strategies.flb_harvester import FLBHarvester, FLBConfig
from src.risk.risk_manager import RiskManager, RiskLimits
from src.monitoring.metrics_collector import MetricsCollector


class TradingEngine:
    """
    Main trading engine that coordinates all strategies.
    """
    
    def __init__(self, dry_run: bool = True, use_demo: bool = True):
        """
        Initialize the trading engine.
        
        Args:
            dry_run: If True, log trades but don't execute
            use_demo: If True, use Kalshi demo environment
        """
        self.dry_run = dry_run
        self.use_demo = use_demo
        
        # Initialize API connector
        logger.info("Initializing Kalshi API connector...")
        self.api = create_connector_from_env()
        
        # Get initial capital
        initial_capital = self._get_starting_capital()
        
        # Initialize risk manager
        logger.info("Initializing risk management system...")
        risk_limits = RiskLimits(
            kelly_fraction=0.25,  # Quarter Kelly
            max_total_exposure_pct=0.20,  # 20% max exposure
            max_single_position_pct=0.05,  # 5% per position
            max_correlated_group_pct=0.15,  # 15% per correlated group
            max_daily_loss_dollars=500.0,
            max_daily_loss_pct=0.05,
            max_consecutive_losses=5,
            loss_streak_pause_hours=4
        )
        self.risk_mgr = RiskManager(
            initial_capital=initial_capital,
            limits=risk_limits
        )
        
        # Initialize metrics collector
        logger.info("Initializing metrics collection system...")
        import os
        metrics_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "metrics")
        self.metrics = MetricsCollector(output_dir=metrics_dir)
        
        # Initialize strategies
        logger.info("Initializing trading strategies...")
        self.flb_strategy = FLBHarvester(
            api_connector=self.api,
            config=FLBConfig(),
            risk_manager=self.risk_mgr  # Pass risk manager
        )
        
        # Trading state
        self.is_running = False
        self.cycle_count = 0
        self.start_time = None
        
        # Performance tracking
        self.trades_executed = []
        self.errors = []
        
        logger.success("Trading engine initialized")
        logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")
        logger.info(f"Environment: {'DEMO' if use_demo else 'PRODUCTION'}")
        logger.info(f"Initial capital: ${initial_capital:,.2f}")
    
    def start(self, scan_interval: int = 300):
        """
        Start the main trading loop.
        
        Args:
            scan_interval: Seconds between market scans (default: 5 minutes)
        """
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info("STARTING TRADING ENGINE")
        logger.info("=" * 60)
        
        # Initial balance check
        self._check_balance()
        
        try:
            while self.is_running:
                self.cycle_count += 1
                cycle_start = time.time()
                
                logger.info(f"\n{'=' * 60}")
                logger.info(f"CYCLE #{self.cycle_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'=' * 60}\n")
                
                # Check if trading is allowed (kill-switches)
                can_trade, reason = self.risk_mgr.can_trade()
                if not can_trade:
                    logger.warning(f"Trading paused: {reason}")
                    logger.info("Waiting 60 seconds before retrying...")
                    time.sleep(60)
                    continue
                
                # Run Strategy A: FLB Harvester
                try:
                    logger.info("Running Strategy A: FLB Harvester")
                    trades = self.flb_strategy.scan_and_trade(dry_run=self.dry_run)
                    
                    # Process executed trades
                    for trade in trades:
                        if 'execution' in trade:
                            self.trades_executed.append(trade)
                            
                            # Add position to risk manager
                            if not self.dry_run:
                                market_group = self.flb_strategy._identify_market_group(trade['ticker'])
                                self.risk_mgr.add_position(
                                    ticker=trade['ticker'],
                                    side=trade['side'],
                                    contracts=trade['count'],
                                    entry_price_cents=trade['price'],
                                    market_group=market_group
                                )
                                
                                # Record scan result (had fills)
                                self.risk_mgr.record_scan_result(had_fills=True)
                        
                        # Record metrics (for both dry-run and live)
                        # Note: For dry-run, we'll use placeholder values
                        # In live mode, we'll update when positions close
                        if not self.dry_run and 'execution' in trade:
                            # Track API latency
                            api_start = time.time()
                            # API calls happen in strategy, latency tracked there if available
                            latency_ms = (time.time() - api_start) * 1000 if 'latency' not in trade else trade.get('latency', 0.0)
                            
                            # Record API call
                            self.metrics.record_api_call(
                                endpoint=trade.get('endpoint', '/markets'),
                                response_time_ms=latency_ms,
                                success=True
                            )
                    
                    # Show stats
                    stats = self.flb_strategy.get_stats()
                    logger.info(f"FLB Stats: {stats}")
                    
                    # Show risk status
                    risk_status = self.risk_mgr.get_status()
                    logger.info(f"Risk Status: {risk_status['trading_state']} | "
                              f"Exposure: {risk_status['exposure_pct']:.1f}% | "
                              f"Daily P&L: ${risk_status['daily_pnl']:.2f}")
                    
                except Exception as e:
                    logger.error(f"Error in FLB strategy: {e}")
                    self.errors.append({
                        'time': datetime.now(),
                        'strategy': 'FLB',
                        'error': str(e)
                    })
                    # Record error in risk manager
                    self.risk_mgr.record_error(str(e))
                
                # Strategy B (Alpha Specialist / Weather) can be added here
                # See scripts/run_weather_strategy.py for weather strategy implementation
                
                # Check for closed positions and update P&L
                self._update_positions_and_pnl()
                
                # Get and display system health
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
                
                # Calculate cycle duration
                cycle_duration = time.time() - cycle_start
                logger.info(f"\nCycle completed in {cycle_duration:.2f}s")
                
                # Show summary
                self._print_summary()
                
                # Sleep until next scan
                sleep_time = max(0, scan_interval - cycle_duration)
                if sleep_time > 0:
                    logger.info(f"Sleeping for {sleep_time:.0f}s until next scan...\n")
                    time.sleep(sleep_time)
                
        except KeyboardInterrupt:
            logger.info("\nReceived shutdown signal...")
            self.stop()
        except Exception as e:
            logger.error(f"Fatal error in trading engine: {e}")
            self.stop()
    
    def _update_positions_and_pnl(self):
        """Check for closed positions and update P&L."""
        if self.dry_run:
            return
        
        try:
            # Get current positions from API
            api_positions = self.api.get_positions()
            api_positions_dict = {pos.get('ticker'): pos for pos in api_positions}
            
            # Check which positions are closed
            closed_positions = []
            for ticker, position in list(self.risk_mgr.positions.items()):
                if ticker not in api_positions_dict:
                    # Position closed - need to get resolution
                    market_info = self.api.get_market(ticker)
                    resolution = market_info.get('resolution', 'unknown')
                    
                    if resolution in ['yes', 'no']:
                        # Calculate P&L
                        entry_price = position.entry_price_cents
                        contracts = position.contracts
                        
                        # Determine if we won
                        won = (position.side == resolution.lower())
                        
                        if won:
                            # Profit = (100 - entry_price) per contract
                            gross_pnl = ((100 - entry_price) / 100.0) * contracts
                            # Fee is 7% of profit
                            fee = gross_pnl * 0.07
                            net_pnl = gross_pnl - fee
                        else:
                            # Loss = entry_cost
                            gross_pnl = -(entry_price / 100.0) * contracts
                            fee = 0.0
                            net_pnl = gross_pnl
                        
                        # Calculate slippage (simplified - assume 5 bps)
                        slippage_bps = 5.0
                        
                        # Record trade in metrics
                        self.metrics.record_trade(
                            ticker=ticker,
                            side=position.side,
                            action='buy',
                            contracts=contracts,
                            entry_price=entry_price / 100.0,
                            exit_price=100.0 if won else 0.0,
                            gross_pnl=gross_pnl,
                            net_pnl=net_pnl,
                            fee=fee,
                            slippage_bps=slippage_bps,
                            holding_period_hours=(datetime.now() - position.entry_timestamp).total_seconds() / 3600.0,
                            market_family=self.flb_strategy._identify_market_group(ticker),
                            strategy='FLB_FAVORITE' if position.side == 'yes' else 'FLB_LONGSHOT'
                        )
                        
                        # Update risk manager
                        self.risk_mgr.close_position(ticker, resolution, net_pnl)
                        
                        logger.info(f"Position closed: {ticker} | Resolution: {resolution} | "
                                  f"Net P&L: ${net_pnl:.2f} | Fee: ${fee:.2f}")
                        closed_positions.append(ticker)
            
        except Exception as e:
            logger.error(f"Error updating positions: {e}")
    
    def stop(self):
        """Stop the trading engine gracefully."""
        self.is_running = False
        
        logger.info("\n" + "=" * 60)
        logger.info("SHUTTING DOWN TRADING ENGINE")
        logger.info("=" * 60)
        
        # Update positions one last time
        self._update_positions_and_pnl()
        
        # Print daily summary from metrics
        self.metrics.print_daily_summary(capital=self.risk_mgr.current_capital)
        
        # Export all metrics
        self.metrics.export_all_metrics()
        
        # Final summary
        self._print_final_summary()
        
        logger.info("Shutdown complete")
    
    def _get_starting_capital(self) -> float:
        """Get starting capital from account balance."""
        try:
            balance = self.api.get_balance()
            available = balance.get('balance', 0) / 100.0
            
            if available == 0:
                logger.warning("Balance is $0, using default $10,000")
                return 10000.0
            
            return available
                
        except Exception as e:
            logger.error(f"Could not check balance: {e}, using default $10,000")
            return 10000.0
    
    def _check_balance(self):
        """Check and log account balance."""
        try:
            balance = self.api.get_balance()
            available = balance.get('balance', 0) / 100.0
            
            logger.info(f"Account balance: ${available:.2f}")
            
            if available < 100:
                logger.warning("Low balance! Consider adding funds.")
                
        except Exception as e:
            logger.error(f"Could not check balance: {e}")
    
    def _print_summary(self):
        """Print cycle summary statistics."""
        logger.info("\n--- Cycle Summary ---")
        logger.info(f"Total trades executed: {len(self.trades_executed)}")
        logger.info(f"Total errors: {len(self.errors)}")
        
        # Calculate total exposure
        if not self.dry_run:
            try:
                positions = self.api.get_positions()
                total_exposure = sum(abs(p.get('total_cost', 0)) for p in positions) / 100.0
                logger.info(f"Total exposure: ${total_exposure:.2f}")
            except:
                pass
    
    def _print_final_summary(self):
        """Print final summary before shutdown."""
        runtime = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        
        logger.info("\n--- Final Summary ---")
        logger.info(f"Total runtime: {runtime/3600:.2f} hours")
        logger.info(f"Total cycles: {self.cycle_count}")
        logger.info(f"Total trades: {len(self.trades_executed)}")
        logger.info(f"Total errors: {len(self.errors)}")
        
        if self.errors:
            logger.warning(f"\nErrors encountered:")
            for err in self.errors[-5:]:  # Show last 5 errors
                logger.warning(f"  [{err['time']}] {err['strategy']}: {err['error']}")
        
        # Try to get final balance
        try:
            balance = self.api.get_balance()
            final_balance = balance.get('balance', 0) / 100.0
            logger.info(f"\nFinal balance: ${final_balance:.2f}")
        except:
            pass


def main():
    """Main entry point for the trading bot."""
    import argparse
    
    # Configure logging
    import os
    logger.remove()
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    # Create logs directory relative to project root
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = os.path.join(project_root, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    logger.add(
        os.path.join(logs_dir, "trading_{time:YYYY-MM-DD}.log"),
        rotation="1 day",
        retention="30 days",
        level="DEBUG"
    )
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Kalshi ML Trading Bot")
    parser.add_argument(
        "--live",
        action="store_true",
        help="Run in LIVE mode (executes real trades)"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        default=True,
        help="Use demo environment (default: True)"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=300,
        help="Scan interval in seconds (default: 300)"
    )
    
    args = parser.parse_args()
    
    # Safety check
    if not args.live:
        logger.warning("Running in DRY RUN mode - no trades will be executed")
        logger.warning("Use --live flag to execute real trades")
        dry_run = True
    else:
        logger.warning("=" * 60)
        logger.warning("LIVE MODE ENABLED - REAL TRADES WILL BE EXECUTED")
        logger.warning("=" * 60)
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Aborted by user")
            return
        dry_run = False
    
    # Create and start engine
    engine = TradingEngine(
        dry_run=dry_run,
        use_demo=args.demo
    )
    
    engine.start(scan_interval=args.interval)


if __name__ == "__main__":
    main()
