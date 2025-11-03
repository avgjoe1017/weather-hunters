"""
Installation and API Test Script

Run this script to verify that:
1. All dependencies are installed
2. Your .env configuration is correct
3. You can connect to the Kalshi API
4. The bot components are working
5. V2 features (risk manager, metrics collector) are functional

Usage: python src/test_installation.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all required packages are installed."""
    print("Testing package imports...")
    
    required_packages = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('requests', 'requests'),
        ('sklearn', 'scikit-learn'),
        ('loguru', 'loguru'),
        ('dotenv', 'python-dotenv'),
    ]
    
    # Optional packages for V2 features
    optional_packages = [
        ('scipy', 'scipy'),  # For correlation clustering
    ]
    
    missing_packages = []
    
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
            print(f"  [OK] {package_name}")
        except ImportError:
            print(f"  [X] {package_name} - MISSING")
            missing_packages.append(package_name)
    
    # Check optional packages
    for module_name, package_name in optional_packages:
        try:
            __import__(module_name)
            print(f"  [OK] {package_name} (optional)")
        except ImportError:
            print(f"  i {package_name} (optional) - not installed (some features may be limited)")
    
    if missing_packages:
        print(f"\n[X] Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("[OK] All packages installed\n")
    return True


def test_env_file():
    """Test that .env file exists and has required variables."""
    print("Testing .env configuration...")
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("  [X] .env file not found")
        print("\n[X] Create .env file from template:")
        print("   cp .env.template .env")
        print("   Then edit .env with your credentials")
        return False
    
    print("  [OK] .env file exists")
    
    # Load environment variables
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    required_vars = ['KALSHI_EMAIL', 'KALSHI_PASSWORD']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or 'your_' in value.lower() or '@example.com' in value.lower():
            print(f"  [X] {var} - not configured")
            missing_vars.append(var)
        else:
            print(f"  [OK] {var} - configured")
    
    if missing_vars:
        print(f"\n[X] Missing or invalid configuration: {', '.join(missing_vars)}")
        print("Edit .env file with your actual Kalshi credentials")
        return False
    
    print("[OK] Configuration valid\n")
    return True


def test_api_connection():
    """Test connection to Kalshi API."""
    print("Testing Kalshi API connection...")
    
    try:
        from src.api.kalshi_connector import create_connector_from_env
        
        print("  Creating API connector...")
        api = create_connector_from_env()
        
        print("  Authenticating...")
        # This will trigger authentication
        balance = api.get_balance()
        
        balance_amount = balance.get('balance', 0) / 100.0
        print(f"  [OK] Connected successfully")
        print(f"  [OK] Account balance: ${balance_amount:,.2f}")
        
        # Test getting markets
        print("  Testing market data...")
        markets = api.get_markets(limit=5)
        print(f"  [OK] Retrieved {len(markets)} markets")
        
        if markets:
            print(f"  Example market: {markets[0].get('ticker', 'N/A')}")
        
        print("[OK] API connection successful\n")
        return True
        
    except Exception as e:
        print(f"  [X] Connection failed: {e}")
        print("\n[X] API connection failed")
        print("Check your credentials in .env file")
        print("Make sure KALSHI_USE_DEMO=true for testing")
        return False


def test_strategy():
    """Test that strategies can be initialized."""
    print("Testing strategy initialization...")
    
    try:
        from src.strategies.flb_harvester import FLBHarvester, FLBConfig
        from src.api.kalshi_connector import create_connector_from_env
        
        api = create_connector_from_env()
        config = FLBConfig()
        strategy = FLBHarvester(api, config)
        
        print(f"  [OK] FLB Harvester initialized")
        print(f"  [OK] Favorite threshold: {config.favorite_threshold}")
        print(f"  [OK] Longshot threshold: {config.longshot_threshold}")
        
        print("[OK] Strategy initialization successful\n")
        return True
        
    except Exception as e:
        print(f"  [X] Strategy initialization failed: {e}")
        print("\n[X] Strategy test failed")
        return False


def test_risk_manager():
    """Test that V2 risk manager can be initialized."""
    print("Testing risk manager (V2 feature)...")
    
    try:
        from src.risk.risk_manager import RiskManager, RiskLimits
        
        # Test initialization
        limits = RiskLimits(
            kelly_fraction=0.25,
            max_total_exposure_pct=0.20,
            max_single_position_pct=0.05
        )
        risk_mgr = RiskManager(initial_capital=10000.0, limits=limits)
        
        print(f"  [OK] Risk Manager initialized")
        print(f"  [OK] Initial capital: ${risk_mgr.initial_capital:,.2f}")
        print(f"  [OK] Kelly fraction: {risk_mgr.limits.kelly_fraction}")
        
        # Test can_trade method
        can_trade, reason = risk_mgr.can_trade()
        print(f"  [OK] Trading status check: {'Active' if can_trade else f'Paused ({reason})'}")
        
        # Test position size calculation
        contracts, reason = risk_mgr.calculate_position_size(
            edge=0.15,  # 15% edge
            win_probability=0.6,
            price_cents=60  # $0.60 entry price
        )
        position_size_dollars = (contracts * 60) / 100.0
        print(f"  [OK] Position size calculation: {contracts} contracts (${position_size_dollars:.2f})")
        
        print("[OK] Risk manager test successful\n")
        return True
        
    except Exception as e:
        print(f"  [X] Risk manager test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n[X] Risk manager test failed")
        return False


def test_metrics_collector():
    """Test that V2 metrics collector can be initialized."""
    print("Testing metrics collector (V2 feature)...")
    
    try:
        from src.monitoring.metrics_collector import MetricsCollector
        from pathlib import Path
        import tempfile
        
        # Create temporary directory for testing
        temp_dir = Path(tempfile.mkdtemp())
        metrics = MetricsCollector(output_dir=str(temp_dir))
        
        print(f"  [OK] Metrics Collector initialized")
        print(f"  [OK] Output directory: {temp_dir}")
        
        # Test recording a trade
        from datetime import datetime
        metrics.record_trade(
            ticker="TEST-123",
            side="yes",
            action="buy",
            contracts=10,
            entry_price=0.60,
            exit_price=0.65,
            gross_pnl=50.0,
            net_pnl=46.5,
            fee=3.5,
            slippage_bps=5.0,
            holding_period_hours=24.0,
            market_family="test",
            strategy="TEST"
        )
        print(f"  [OK] Trade recording successful")
        
        # Test API call recording
        metrics.record_api_call(
            success=True,
            latency_ms=150.0
        )
        print(f"  [OK] API call recording successful")
        
        # Clean up
        import shutil
        shutil.rmtree(temp_dir)
        
        print("[OK] Metrics collector test successful\n")
        return True
        
    except Exception as e:
        print(f"  [X] Metrics collector test failed: {e}")
        import traceback
        traceback.print_exc()
        print("\n[X] Metrics collector test failed")
        return False


def test_directories():
    """Test that required directories exist."""
    print("Testing directory structure...")
    
    required_dirs = [
        'src', 
        'src/api', 
        'src/strategies', 
        'src/risk', 
        'src/monitoring', 
        'src/backtest',
        'src/features',
        'notebooks'
    ]
    optional_dirs = ['data', 'logs', 'metrics', 'config']
    
    all_exist = True
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [X] {dir_path} - MISSING")
            all_exist = False
    
    for dir_path in optional_dirs:
        if not Path(dir_path).exists():
            print(f"  i {dir_path} - will be created as needed")
    
    if not all_exist:
        print("\n[X] Required directories missing")
        return False
    
    print("[OK] Directory structure valid\n")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("KALSHI ML TRADING BOT - INSTALLATION TEST")
    print("=" * 60)
    print()
    
    tests = [
        ("Package Dependencies", test_imports),
        ("Directory Structure", test_directories),
        ("Environment Configuration", test_env_file),
        ("API Connection", test_api_connection),
        ("Strategy Initialization", test_strategy),
        ("Risk Manager (V2)", test_risk_manager),
        ("Metrics Collector (V2)", test_metrics_collector),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"[X] {test_name} failed with exception: {e}\n")
            results.append((test_name, False))
    
    # Summary
    print("=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status} - {test_name}")
    
    print()
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print()
        print("[OK] All tests passed! Your installation is ready.")
        print()
        print("Next steps:")
        print("1. Run a dry run: python src/main.py")
        print("2. Review logs in logs/ directory")
        print("3. When ready, test with demo money: python src/main.py --live --demo")
        print()
        return 0
    else:
        print()
        print("[!]  Some tests failed. Please address the issues above.")
        print("See GETTING_STARTED.md for detailed setup instructions.")
        print()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
