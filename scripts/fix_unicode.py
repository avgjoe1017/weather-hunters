"""
Fix Unicode characters in scripts for Windows compatibility
"""
import re
from pathlib import Path

files = [
    "scripts/verify_setup.py",
    "scripts/health_check.py",
]

replacements = {
    "✓": "[OK]",
    "❌": "[X]",
    "⚠️": "[!]",
    "✅": "[OK]",
    "🎉": "[OK]",
    "ℹ️": "[i]",
}

for file_path in files:
    path = Path(file_path)
    if path.exists():
        content = path.read_text(encoding='utf-8')
        for old, new in replacements.items():
            content = content.replace(old, new)
        path.write_text(content, encoding='utf-8')
        print(f"Fixed: {file_path}")

