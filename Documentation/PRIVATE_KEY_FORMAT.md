# Private Key Format in .env File

## Issue

Python-dotenv does not handle multiline values well by default. If your private key spans multiple lines in your `.env` file, only the first line may be read.

## Solutions

### Option 1: Single Line with Escaped Newlines (Recommended)

Put the entire private key on one line with `\n` escape sequences:

```bash
KALSHI_PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIEogIBAAKCAQEAqZatJemqnGo/csAf46AMyseOdE/vjXOjyVbtCbyUGKLNxr8i\nLUsSP+q4FnSfCtPBHEPQZWFTj3lOV8SkXrhi+8lsamjOgvGReBRmeRXx6KRN4JxI\n...\n-----END RSA PRIVATE KEY-----"
```

### Option 2: Use a File Instead

Save your private key to a file (e.g., `kalshi_private_key.pem`) and reference it:

```bash
KALSHI_PRIVATE_KEY_FILE=kalshi_private_key.pem
```

**Important**: Make sure the file is not committed to git! Add it to `.gitignore`.

### Option 3: Base64 Encoded Single Line

Convert your private key to base64 (if it's not already) and put it on one line, or use the base64 content directly (the code will add the PEM headers automatically).

## Your Current .env File

Your `.env` file currently has the private key formatted across multiple lines, which python-dotenv is not reading correctly. You need to reformat it using one of the options above.

## Quick Fix Script

Run this to convert your multiline key to a single-line format:

```bash
python scripts/convert_key_to_oneline.py
```

(We can create this script if needed)

