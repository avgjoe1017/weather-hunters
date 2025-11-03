"""
Quick Verification Script

Verifies that your setup is complete and ready to trade.

Usage: python scripts/verify_setup.py
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_env_file():
    """Check if .env file exists and is configured."""
    env_path = Path(".env")
    
    if not env_path.exists():
        print("[X] .env file not found")
        print("   Create it from template: copy .env.template .env")
        print("   Then edit with your Kalshi credentials")
        return False
    
    # Check if configured (not template values)
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    
    # Check for API key authentication (new method)
    api_key_id = os.getenv("KALSHI_API_KEY_ID") or os.getenv("KALSHI_API_KEY")
    private_key = os.getenv("KALSHI_PRIVATE_KEY") or os.getenv("KALSHI_PY_PRIVATE_KEY_PEM")
    private_key_file = os.getenv("KALSHI_PRIVATE_KEY_FILE")
    
    # Check for legacy email/password (deprecated)
    email = os.getenv("KALSHI_EMAIL", "")
    password = os.getenv("KALSHI_PASSWORD", "")
    
    if api_key_id and (private_key or private_key_file):
        # Using API key authentication
        if not api_key_id:
            print("[X] KALSHI_API_KEY_ID not configured in .env")
            return False
        if not private_key and not private_key_file:
            print("[X] KALSHI_PRIVATE_KEY or KALSHI_PRIVATE_KEY_FILE not configured in .env")
            return False
        use_demo = os.getenv("KALSHI_USE_DEMO", "false").lower()
        if use_demo == "true":
            print("[!]  Using DEMO mode (safe for testing)")
        else:
            print("[!]  Using LIVE mode (real money!)")
        print("[OK] .env file configured (API key authentication)")
        return True
    elif email and password:
        # Legacy email/password (deprecated)
        if "your_email" in email or "@example.com" in email:
            print("[X] KALSHI_EMAIL not configured in .env")
            return False
        if "your_password" in password:
            print("[X] KALSHI_PASSWORD not configured in .env")
            return False
        print("[!]  Warning: Email/password authentication is deprecated")
        print("   Please migrate to API keys. See: https://docs.kalshi.com/getting_started/api_keys")
        use_demo = os.getenv("KALSHI_USE_DEMO", "true").lower()
        if use_demo == "true":
            print("[!]  Using DEMO mode (safe for testing)")
        else:
            print("[!]  Using LIVE mode (real money!)")
        print("[OK] .env file configured (legacy email/password)")
        return True
    else:
        print("[X] No authentication credentials found in .env")
        print("   Configure either:")
        print("   - KALSHI_API_KEY_ID and KALSHI_PRIVATE_KEY (recommended), or")
        print("   - KALSHI_EMAIL and KALSHI_PASSWORD (deprecated)")
        return False


def check_directories():
    """Check that required directories exist."""
    required = ["src", "src/api", "src/strategies", "src/risk", "src/monitoring"]
    missing = []
    
    for dir_path in required:
        if not Path(dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"[X] Missing directories: {', '.join(missing)}")
        return False
    
    print("[OK] Required directories exist")
    return True


def check_dependencies():
    """Quick check for key dependencies."""
    required = ["pandas", "numpy", "requests", "sklearn", "loguru", "dotenv"]
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"[X] Missing packages: {', '.join(missing)}")
        print("   Run: pip install -r requirements.txt")
        return False
    
    print("[OK] Required packages installed")
    return True


def check_api_connection():
    """Test API connection."""
    try:
        from src.api.kalshi_connector import create_connector_from_env
        api = create_connector_from_env()
        balance = api.get_balance()
        balance_amount = balance.get('balance', 0) / 100.0
        print(f"[OK] API connection successful")
        print(f"  Account balance: ${balance_amount:,.2f}")
        return True
    except Exception as e:
        print(f"[X] API connection failed: {e}")
        print("   Check your .env credentials")
        return False


def main():
    """Run all checks."""
    print("=" * 60)
    print("SETUP VERIFICATION")
    print("=" * 60)
    print()
    
    checks = [
        ("Directory Structure", check_directories),
        ("Dependencies", check_dependencies),
        ("Environment Config", check_env_file),
        ("API Connection", check_api_connection),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"[X] {name} check failed: {e}")
            results.append((name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "[OK] PASS" if result else "[X] FAIL"
        print(f"{status} - {name}")
    
    print()
    if passed == total:
        print("[OK] All checks passed! You're ready to trade.")
        print()
        print("Next steps:")
        print("1. Run dry run: python -m src.main")
        print("2. Review logs: tail -f logs/trading_*.log")
        print("3. When ready: python -m src.main --live --demo")
        return 0
    else:
        print(f"[!]  {total - passed} check(s) failed. Please address above issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

