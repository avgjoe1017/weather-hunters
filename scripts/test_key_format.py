"""Test script to diagnose private key format issues."""

import os
from dotenv import load_dotenv
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

load_dotenv()

# Get the private key from environment
private_key = os.getenv('KALSHI_PRIVATE_KEY')

print("=" * 60)
print("PRIVATE KEY DIAGNOSTICS")
print("=" * 60)
print()

if not private_key:
    print("[X] KALSHI_PRIVATE_KEY not found in environment")
    exit(1)

print(f"Key length: {len(private_key)}")
print(f"Number of newlines: {private_key.count(chr(10))}")
print(f"Number of carriage returns: {private_key.count(chr(13))}")
print()

# Show first and last 100 characters
print("First 100 chars:")
print(repr(private_key[:100]))
print()
print("Last 100 chars:")
print(repr(private_key[-100:]))
print()

# Check for markers
has_begin_rsa = 'BEGIN RSA PRIVATE KEY' in private_key
has_begin = 'BEGIN PRIVATE KEY' in private_key
has_end_rsa = 'END RSA PRIVATE KEY' in private_key
has_end = 'END PRIVATE KEY' in private_key

print("Markers found:")
print(f"  BEGIN RSA PRIVATE KEY: {has_begin_rsa}")
print(f"  BEGIN PRIVATE KEY: {has_begin}")
print(f"  END RSA PRIVATE KEY: {has_end_rsa}")
print(f"  END PRIVATE KEY: {has_end}")
print()

# Try to extract and reconstruct
if has_begin_rsa and has_end_rsa:
    start_marker = '-----BEGIN RSA PRIVATE KEY-----'
    end_marker = '-----END RSA PRIVATE KEY-----'
    start_idx = private_key.find(start_marker)
    end_idx = private_key.find(end_marker)
    
    if start_idx != -1 and end_idx != -1:
        key_content = private_key[start_idx + len(start_marker):end_idx].strip()
        print(f"Key content length (raw): {len(key_content)}")
        print(f"Key content has newlines: {chr(10) in key_content}")
        
        # Clean the content
        key_content_clean = key_content.replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
        print(f"Key content length (cleaned): {len(key_content_clean)}")
        
        # Reconstruct
        reconstructed = f"{start_marker}\n"
        for i in range(0, len(key_content_clean), 64):
            reconstructed += key_content_clean[i:i+64] + "\n"
        reconstructed += end_marker
        
        print()
        print("Attempting to load reconstructed key...")
        
        try:
            key_bytes = reconstructed.encode('utf-8')
            loaded_key = serialization.load_pem_private_key(
                key_bytes,
                password=None,
                backend=default_backend()
            )
            print("[OK] Private key loaded successfully!")
            print(f"Key size: {loaded_key.key_size} bits")
        except Exception as e:
            print(f"[X] Failed to load key: {e}")
            print()
            print("First 500 chars of reconstructed key:")
            print(reconstructed[:500])
            print()
            print("Last 200 chars of reconstructed key:")
            print(reconstructed[-200:])

