"""Test with properly formatted key file."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
from dotenv import load_dotenv
from kalshi_python import Configuration, KalshiClient

load_dotenv()

print("=" * 60)
print("TEST WITH KEY FILE")
print("=" * 60)
print()

api_key_id = os.getenv('KALSHI_API_KEY_ID')
key_file = project_root / "kalshi_private_key.pem"

if not key_file.exists():
    print("[X] Key file not found")
    exit(1)

# Read the key from file
with open(key_file, 'r') as f:
    private_key = f.read()

print(f"Key ID: {api_key_id[:8]}...")
print(f"Key file: {key_file}")
print(f"Key length: {len(private_key)} chars")
print(f"Key lines: {private_key.count(chr(10))} newlines")
print()

# Test with official SDK
print("Testing with Official Kalshi SDK...")
print()

try:
    # Configure
    config = Configuration(
        host="https://api.elections.kalshi.com/trade-api/v2"
    )
    
    config.api_key_id = api_key_id
    config.private_key_pem = private_key
    
    # Initialize client
    client = KalshiClient(config)
    
    print("[OK] Client created")
    print()
    
    # Test balance endpoint
    print("Fetching balance...")
    balance = client.get_balance()
    
    print(f"[OK] SUCCESS! Balance: ${balance.balance / 100:.2f}")
    print()
    print("=" * 60)
    print("AUTHENTICATION WORKING!")
    print("=" * 60)
    
except Exception as e:
    print(f"[X] Error: {e}")
    print()
    import traceback
    traceback.print_exc()

