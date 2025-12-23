#!/usr/bin/env python3
"""
Script to fix bare except clauses in TUI code.

This script replaces bare `except:` with specific exception types
to prevent catching KeyboardInterrupt, SystemExit, etc.
"""

import re
from pathlib import Path

# Mapping of context to appropriate exception types
FIXES = [
    # File I/O operations
    (r"except:\s*\n\s*content = None", "except (OSError, UnicodeDecodeError):\n            content = None"),

    # ChucK operations
    (r"except:\s*\n\s*current_time = 0\.0", "except (RuntimeError, AttributeError):\n                current_time = 0.0"),
    (r"except:\s*\n\s*srate = 44100", "except (RuntimeError, AttributeError):\n                    srate = 44100"),
    (r"except:\s*\n\s*sample_rate = 44100", "except (RuntimeError, AttributeError):\n                    sample_rate = 44100"),

    # Path operations
    (r"except:\s*\n\s*name = full_name", "except (ValueError, OSError):\n                    name = full_name"),

    # Generic cleanup (last resort)
    (r"except:\s*\n\s*pass", "except Exception:\n                pass"),
]

def fix_file(filepath):
    """Fix bare except clauses in a single file."""
    content = filepath.read_text()
    original = content

    for pattern, replacement in FIXES:
        content = re.sub(pattern, replacement, content)

    if content != original:
        filepath.write_text(content)
        print(f"Fixed: {filepath}")
        return True
    return False

def main():
    """Fix all TUI files."""
    tui_dir = Path(__file__).parent.parent / "src" / "numchuck" / "tui"

    fixed_count = 0
    for py_file in tui_dir.glob("*.py"):
        if fix_file(py_file):
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()
