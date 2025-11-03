"""Helper script to save the private key from .env to a proper file."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("SAVE PRIVATE KEY TO FILE")
print("=" * 60)
print()

# Read the private key from .env directly (raw file read)
env_file = project_root / ".env"

if not env_file.exists():
    print("[X] .env file not found")
    exit(1)

# Read .env file and extract the private key lines
with open(env_file, 'r') as f:
    lines = f.readlines()

# Find the KALSHI_PRIVATE_KEY line and collect all key lines
key_lines = []
in_key = False
begin_marker_found = False

for i, line in enumerate(lines):
    line_stripped = line.strip()
    
    # Check if this line starts with KALSHI_PRIVATE_KEY=
    if line_stripped.startswith('KALSHI_PRIVATE_KEY='):
        in_key = True
        # Extract everything after the =
        key_start = line_stripped.split('=', 1)[1]
        if key_start:
            key_lines.append(key_start)
            if 'BEGIN' in key_start:
                begin_marker_found = True
        continue
    
    # If we're in the key section, keep collecting lines
    if in_key:
        if line_stripped:
            key_lines.append(line_stripped)
            if 'END' in line_stripped:
                # Found end of key
                break
        elif not line_stripped and begin_marker_found:
            # Empty line after we started reading key - might be end
            continue

print(f"Found {len(key_lines)} lines of key data")
print()

if not key_lines:
    print("[X] Could not find KALSHI_PRIVATE_KEY in .env")
    print()
    print("Make sure your .env has:")
    print("KALSHI_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----")
    print("MIIEogIBAAKCAQEA...")
    print("...")
    print("-----END RSA PRIVATE KEY-----")
    exit(1)

# Reconstruct the key
private_key_content = '\n'.join(key_lines)

print("Key content preview:")
print(private_key_content[:100] + "...")
print("..." + private_key_content[-100:])
print()

# Check if it has proper markers
if 'BEGIN' not in private_key_content or 'END' not in private_key_content:
    print("[X] Private key doesn't have BEGIN/END markers")
    print()
    print("Current content:")
    print(private_key_content)
    exit(1)

# Save to file
key_file = project_root / "kalshi_private_key.pem"

print(f"Saving private key to: {key_file}")

try:
    with open(key_file, 'w') as f:
        f.write(private_key_content)
    
    print("[OK] Private key saved successfully!")
    print()
    print("Next steps:")
    print("1. Add to .gitignore:")
    print("   echo 'kalshi_private_key.pem' >> .gitignore")
    print()
    print("2. Update your .env file:")
    print("   Remove or comment out the multiline KALSHI_PRIVATE_KEY")
    print("   Add: KALSHI_PRIVATE_KEY_FILE=kalshi_private_key.pem")
    print()
    print("3. Run verification:")
    print("   python scripts/verify_setup.py")
    
except Exception as e:
    print(f"[X] Error saving file: {e}")
    exit(1)

