"""
WMS - Warehouse Management System

Quick-start entry point for local development.

Usage:
    python main.py          # Run via this wrapper
    python -m wms           # Run as package (recommended)
    wms                     # After: pip install -e .
"""

import sys
from pathlib import Path

# Add src directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def main() -> int:
    from wms.__main__ import main as _main
    return _main()


if __name__ == "__main__":
    sys.exit(main())
