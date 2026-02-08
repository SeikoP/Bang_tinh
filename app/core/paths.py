"""
Centralized Path Management

All file paths in the application should use these constants.
This ensures the app works correctly in both development and production (PyInstaller).
"""

import sys
from pathlib import Path

# Determine if running as PyInstaller bundle
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    ROOT = Path(sys.executable).parent
    # PyInstaller extracts to a temp folder
    BUNDLE = Path(sys._MEIPASS)
else:
    # Running as script
    ROOT = Path(__file__).resolve().parents[2]
    BUNDLE = ROOT

# Application structure
APP = ROOT / "app"
CONFIG = ROOT / "config"
DATA = ROOT / "data"
BUILD = ROOT / "build"
SCRIPTS = ROOT / "scripts"
TESTS = ROOT / "tests"
DOCS = ROOT / "docs"

# App subdirectories
APP_CORE = APP / "core"
APP_UI = APP / "ui"
APP_SERVICES = APP / "services"
APP_DATABASE = APP / "database"
APP_UTILS = APP / "utils"
APP_RUNTIME = APP / "runtime"
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
    if getattr(sys, 'frozen', False):
        # PyInstaller bundle
        return BUNDLE / relative_path
    else:
        # Development
        return ROOT / relative_path

# Initialize data directories on import
ensure_data_dirs()
