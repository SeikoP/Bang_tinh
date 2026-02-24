"""
WMS - Warehouse Management System

Quick-start entry point for local development.

Usage:
    python main.py          # Run via this wrapper
    python -m wms           # Run as package (recommended)
    wms                     # After: pip install -e .
"""

import sys


def main() -> int:
    from wms.__main__ import main as _main
    return _main()


if __name__ == "__main__":
    sys.exit(main())
