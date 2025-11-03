"""
System Health Check Script

Quick health check for the trading bot system:
- Check system status
- Verify API connectivity
- Check risk manager status
- Review recent metrics
- Display active positions

Usage: python scripts/health_check.py
"""

import sys
from pathlib import Path
from datetime import datetime
import os

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_imports():
    """Check if all required modules can be imported."""
    try:
        from src.api.kalshi_connector import create_connector_from_env
        from src.risk.risk_manager import RiskManager, RiskLimits
        from src.monitoring.metrics_collector import MetricsCollector
        print("[OK] All modules imported successfully")
        return True
    except Exception as e:
        print(f"[X] Import error: {e}")
        return False


def check_api_connection():
    """Check API connection and account status."""
    try:
        from src.api.kalshi_connector import create_connector_from_env
        
        print("\n" + "=" * 60)
        print("API CONNECTION CHECK")
        print("=" * 60)
        
        api = create_connector_from_env()
        balance = api.get_balance()
        balance_amount = balance.get('balance', 0) / 100.0
        
        print(f"[OK] Connected successfully")
        print(f"  Account balance: ${balance_amount:,.2f}")
        
        # Check demo vs production
        env_demo = os.getenv("KALSHI_USE_DEMO", "true").lower() == "true"
        if env_demo:
            print(f"  Mode: DEMO (play money)")
        else:
            print(f"  Mode: PRODUCTION (real money!)")
        
        # Get positions
        positions = api.get_positions()
        print(f"  Active positions: {len(positions)}")
        
        return True
    except Exception as e:
        print(f"[X] API connection failed: {e}")
        return False


def check_risk_manager():
    """Check risk manager status."""
    try:
        from src.api.kalshi_connector import create_connector_from_env
        from src.risk.risk_manager import RiskManager, RiskLimits
        
        print("\n" + "=" * 60)
        print("RISK MANAGER STATUS")
        print("=" * 60)
        
        api = create_connector_from_env()
        balance = api.get_balance()
        initial_capital = balance.get('balance', 0) / 100.0
        
        limits = RiskLimits()
        risk_mgr = RiskManager(initial_capital=initial_capital, limits=limits)
        
        status = risk_mgr.get_status()
        
        print(f"  Trading state: {status['trading_state']}")
        if status['kill_switch_reason']:
            print(f"  [!]  Kill switch: {status['kill_switch_reason']}")
        print(f"  Current capital: ${status['current_capital']:,.2f}")
        print(f"  Capital change: {status['capital_change_pct']:.2f}%")
        print(f"  Total exposure: ${status['total_exposure']:,.2f}")
        print(f"  Exposure: {status['exposure_pct']:.1f}%")
        print(f"  Active positions: {status['active_positions']}")
        print(f"  Daily P&L: ${status['daily_pnl']:,.2f}")
        print(f"  Daily trades: {status['daily_trades']}")
        print(f"  Consecutive losses: {status['consecutive_losses']}")
        
        can_trade, reason = risk_mgr.can_trade()
        if can_trade:
            print(f"  [OK] Trading enabled")
        else:
            print(f"  [!]  Trading paused: {reason}")
        
        return True
    except Exception as e:
        print(f"[X] Risk manager check failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_metrics():
    """Check metrics collection status."""
    try:
        from src.monitoring.metrics_collector import MetricsCollector
        
        print("\n" + "=" * 60)
        print("METRICS COLLECTOR STATUS")
        print("=" * 60)
        
        metrics_dir = Path("metrics")
        if not metrics_dir.exists():
            print("  [i]  Metrics directory not created yet (will be created on first run)")
            return True
        
        metrics_files = list(metrics_dir.glob("*.json"))
        if metrics_files:
            print(f"  [OK] Found {len(metrics_files)} metrics file(s)")
            # Find most recent
            latest = max(metrics_files, key=lambda p: p.stat().st_mtime)
            print(f"  Latest: {latest.name}")
            print(f"  Modified: {datetime.fromtimestamp(latest.stat().st_mtime)}")
        else:
            print("  [i]  No metrics files yet (will be created on first trade)")
        
        return True
    except Exception as e:
        print(f"[X] Metrics check failed: {e}")
        return False


def check_logs():
    """Check log files."""
    print("\n" + "=" * 60)
    print("LOG FILES STATUS")
    print("=" * 60)
    
    logs_dir = Path("logs")
    if not logs_dir.exists():
        print("  [i]  Logs directory not created yet (will be created on first run)")
        return True
    
    log_files = list(logs_dir.glob("*.log"))
    if log_files:
        print(f"  [OK] Found {len(log_files)} log file(s)")
        # Find most recent
        latest = max(log_files, key=lambda p: p.stat().st_mtime)
        print(f"  Latest: {latest.name}")
        size_kb = latest.stat().st_size / 1024
        print(f"  Size: {size_kb:.1f} KB")
        print(f"  Modified: {datetime.fromtimestamp(latest.stat().st_mtime)}")
    else:
        print("  [i]  No log files yet (will be created on first run)")
    
    return True


def main():
    """Run all health checks."""
    print("=" * 60)
    print("KALSHI ML TRADING BOT - HEALTH CHECK")
    print("=" * 60)
    
    checks = [
        ("Module Imports", check_imports),
        ("API Connection", check_api_connection),
        ("Risk Manager", check_risk_manager),
        ("Metrics Collector", check_metrics),
        ("Log Files", check_logs),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"[X] {name} check failed with exception: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("HEALTH CHECK SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status} - {name}")
    
    print()
    if passed == total:
        print("[OK] All systems operational!")
        return 0
    else:
        print(f"[!]  {total - passed} check(s) failed. Review output above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

