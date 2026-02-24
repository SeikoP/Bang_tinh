"""
Project Structure Reference

This module documents the clean project structure.
Import this module to see the structure in your IDE.

Structure:
    project_root/
    ├── app/                    # Main application source
    │   ├── core/              # Core infrastructure
    │   │   ├── paths.py       # Centralized path management
    │   │   ├── config.py      # Configuration management
    │   │   ├── container.py   # Dependency injection
    │   │   └── ...
    │   ├── ui/                # User interface
    │   │   ├── qt_views/      # PyQt6 views
    │   │   └── qt_theme.py    # Theme configuration
    │   ├── services/          # Business logic services
    │   ├── database/          # Database layer
    │   ├── utils/             # Utility functions
    │   ├── runtime/           # Runtime management
    │   └── resources/         # Bundled resources
    │       ├── fonts/
    │       ├── icons/
    │       └── themes/
    │
    ├── config/                # Configuration files
    │   ├── app.yaml          # Application config
    │   ├── logging.yaml      # Logging config
    │   └── paths.yaml        # Path config
    │
    ├── data/                  # Runtime data (gitignored)
    │   ├── logs/             # Application logs
    │   ├── exports/          # Exported files
    │   ├── backups/          # Database backups
    │   └── cache/            # Cache files
    │
    ├── build/                 # Build artifacts
    │   ├── pyinstaller/      # PyInstaller work dir
    │   ├── dist/             # Distribution files
    │   └── installer/        # Installer files
    │
    ├── scripts/               # Development scripts
    │   ├── restructure.py    # Migration script
    │   ├── build_clean.py    # Build script
    │   └── validate_structure.py
    │
    ├── tests/                 # Test suite
    │   ├── unit/
    │   ├── integration/
    │   ├── e2e/
    │   ├── property/
    │   └── security/
    │
    ├── android/               # Android client
    ├── docs/                  # Documentation (if needed)
    │
    ├── main.py               # Application entry point
    ├── app_window.py         # Main window (legacy location)
    ├── config.py             # Legacy config (deprecated)
    ├── warehouse_app_clean.spec  # PyInstaller spec
    └── .gitignore

Path Management:
    Always use: from app.core.paths import ROOT, DATA, LOGS, etc.
    Never hardcode paths or manipulate sys.path

Configuration:
    Configs are in config/ directory
    Load via core.config.Config.from_env()

Building:
    python scripts/build_clean.py
    or: pyinstaller warehouse_app_clean.spec

Testing:
    pytest tests/
    python scripts/validate_structure.py
"""

# This is a documentation module - no executable code needed
__all__ = []
