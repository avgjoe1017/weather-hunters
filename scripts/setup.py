"""
Automated Setup Script for Kalshi ML Trading Bot

This script automates the initial setup process:
1. Creates virtual environment (optional)
2. Installs dependencies
3. Creates .env template if missing
4. Runs verification tests

Usage: python scripts/setup.py [--venv] [--skip-tests]
"""

import sys
import subprocess
import os
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8+."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print("[X] Python 3.8 or higher is required")
        print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro}")
    return True


def create_venv():
    """Create virtual environment."""
    venv_path = Path("venv")
    if venv_path.exists():
        print("[OK] Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print("[OK] Virtual environment created")
        return True
    except subprocess.CalledProcessError:
        print("[X] Failed to create virtual environment")
        return False


def install_dependencies():
    """Install dependencies from requirements.txt."""
    print("Installing dependencies...")
    try:
        pip_cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]
        subprocess.run(pip_cmd, check=True)
        print("[OK] Dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("[X] Failed to install dependencies")
        return False


def create_env_template():
    """Create .env template if it doesn't exist."""
    env_path = Path(".env")
    env_template_path = Path(".env.template")
    
    if env_path.exists():
        print("[OK] .env file already exists")
        return True
    
    if env_template_path.exists():
        print("[OK] .env.template already exists")
        return True
    
    # Create .env.template
    template_content = """# Kalshi API Configuration
# Copy this file to .env and fill in your credentials

# Your Kalshi account email
KALSHI_EMAIL=your_email@example.com

# Your Kalshi account password
KALSHI_PASSWORD=your_password

# Use demo environment (true = play money, false = real money)
# IMPORTANT: Start with true for testing!
KALSHI_USE_DEMO=true
"""
    
    try:
        env_template_path.write_text(template_content)
        print("[OK] Created .env.template")
        
        if not env_path.exists():
            print("\n[!] IMPORTANT: Create .env file from template:")
            print("   On Windows: copy .env.template .env")
            print("   On Mac/Linux: cp .env.template .env")
            print("   Then edit .env with your actual Kalshi credentials")
        
        return True
    except Exception as e:
        print(f"[X] Failed to create .env.template: {e}")
        return False


def create_directories():
    """Create required directories."""
    dirs = ["logs", "metrics", "data", "config"]
    for dir_path in dirs:
        Path(dir_path).mkdir(exist_ok=True)
    print("[OK] Required directories created")


def run_tests():
    """Run installation tests."""
    print("\nRunning verification tests...")
    try:
        result = subprocess.run(
            [sys.executable, "src/test_installation.py"],
            cwd=Path.cwd()
        )
        return result.returncode == 0
    except Exception as e:
        print(f"[X] Failed to run tests: {e}")
        return False


def main():
    """Main setup function."""
    print("=" * 60)
    print("KALSHI ML TRADING BOT - AUTOMATED SETUP")
    print("=" * 60)
    print()
    
    # Parse arguments
    create_venv_flag = "--venv" in sys.argv
    skip_tests = "--skip-tests" in sys.argv
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Create virtual environment (optional)
    if create_venv_flag:
        if not create_venv():
            return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Create directories
    create_directories()
    
    # Create .env template
    if not create_env_template():
        return 1
    
    # Run tests (optional)
    if not skip_tests:
        if not run_tests():
            print("\n[!] Some tests failed. Please review the output above.")
            print("   You can skip tests with: python scripts/setup.py --skip-tests")
            return 1
    
    print()
    print("=" * 60)
    print("[OK] SETUP COMPLETE!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Create .env file: copy .env.template .env")
    print("2. Edit .env with your Kalshi credentials")
    print("3. Run test: python src/test_installation.py")
    print("4. Run dry run: python -m src.main")
    print()
    print("For more information, see:")
    print("- Documentation/README_FIRST.md")
    print("- Documentation/GETTING_STARTED.md")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

