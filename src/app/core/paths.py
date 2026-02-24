"""
Centralized Path Management

All file paths in the application should use these constants.
This ensures the app works correctly in both development and production (PyInstaller).

Layout: project_root/src/app/core/paths.py
  - With editable install (pip install -e .), packages are importable from src/
  - ROOT always points to project_root (contains pyproject.toml)
"""

import sys
from pathlib import Path


def _find_project_root() -> Path:
    """Walk up from this file to find project root (contains pyproject.toml)."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    # Fallback: src/app/core/paths.py → parents[3] = project root
    return Path(__file__).resolve().parents[3]


# Determine if running as PyInstaller bundle
if getattr(sys, "frozen", False):
    # Running as compiled executable
    ROOT = Path(sys.executable).parent
    # PyInstaller extracts to a temp folder
    BUNDLE = Path(sys._MEIPASS)
else:
    # Running as script / editable install
    ROOT = _find_project_root()
    BUNDLE = ROOT

# Application structure
SRC = ROOT / "src"
APP = SRC / "app"
CONFIG = ROOT / "config"
DATA = ROOT / "data"
BUILD = ROOT / "build"
SCRIPTS = ROOT / "scripts"
TESTS = ROOT / "tests"
DOCS = ROOT / "docs"

# App subdirectories (all under src/)
APP_CORE = APP / "core"
APP_UI = SRC / "ui"
APP_SERVICES = SRC / "services"
APP_DATABASE = SRC / "database"
APP_UTILS = SRC / "utils"
APP_RUNTIME = SRC / "runtime"
APP_RESOURCES = APP / "resources"

# Resources
RESOURCES_FONTS = APP_RESOURCES / "fonts"
RESOURCES_ICONS = APP_RESOURCES / "icons"
RESOURCES_THEMES = APP_RESOURCES / "themes"

# Data directories
LOGS = DATA / "logs"
EXPORTS = DATA / "exports"
BACKUPS = DATA / "backups"
CACHE = DATA / "cache"

# Database
DATABASE = ROOT / "storage.db"

# Build directories
BUILD_PYINSTALLER = BUILD / "pyinstaller"
BUILD_DIST = BUILD / "dist"
BUILD_INSTALLER = BUILD / "installer"

# Assets (bundled resources)
ASSETS = BUNDLE / "assets"


def ensure_data_dirs():
    """Ensure all data directories exist"""
    for path in [LOGS, EXPORTS, BACKUPS, CACHE]:
        path.mkdir(parents=True, exist_ok=True)


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and PyInstaller.

    Args:
        relative_path: Path relative to resources directory

    Returns:
        Absolute path to resource
    """
    if getattr(sys, "frozen", False):
        # PyInstaller bundle
        return BUNDLE / relative_path
    else:
        # Development
        return ROOT / relative_path


# Initialize data directories on import
ensure_data_dirs()
