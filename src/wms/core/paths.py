"""
Centralized Path Management

All file paths in the application should use these constants.
This ensures the app works correctly in both development and production (PyInstaller).

When running as script, ROOT = project root (3 levels up from src/wms/core/).
When running as PyInstaller bundle, ROOT = directory containing the .exe.
"""

import sys
import os
from pathlib import Path


def _find_project_root() -> Path:
    """Walk up from this file to find project root (contains pyproject.toml)."""
    current = Path(__file__).resolve().parent
    for parent in [current] + list(current.parents):
        if (parent / "pyproject.toml").exists():
            return parent
    # Fallback: src/wms/core/paths.py → parents[3] = project root
    return Path(__file__).resolve().parents[3]


# Determine if running as PyInstaller bundle
if getattr(sys, "frozen", False):
    # Running as compiled executable
    ROOT = Path(sys.executable).parent
    # PyInstaller extracts to a temp folder
    BUNDLE = Path(sys._MEIPASS)
else:
    # Running as script: src/wms/core/paths.py -> parents[3] = project root
    ROOT = _find_project_root()
    BUNDLE = ROOT


def _resolve_data_root() -> Path:
    """Resolve writable data root for runtime files."""
    override = os.getenv("WMS_DATA_DIR")
    if override:
        return Path(override).expanduser()

    if getattr(sys, "frozen", False):
        if sys.platform == "win32":
            local_appdata = os.getenv("LOCALAPPDATA")
            if local_appdata:
                return Path(local_appdata) / "WMS"
            return Path.home() / "AppData" / "Local" / "WMS"
        return Path.home() / ".wms"

    return ROOT / "data"


# Data directories
DATA = _resolve_data_root()
LOGS = DATA / "logs"
EXPORTS = DATA / "exports"
BACKUPS = DATA / "backups"
CACHE = DATA / "cache"

# Database
if getattr(sys, "frozen", False):
    DATABASE = DATA / "storage.db"
else:
    DATABASE = ROOT / "storage.db"

# Build directories
BUILD = ROOT / "build"

# Assets (bundled resources)
# In dev mode: ROOT/src/wms/assets
# In frozen mode: BUNDLE/assets  (spec copies src/wms/assets → assets)
if getattr(sys, "frozen", False):
    # PyInstaller bundle: assets are extracted to BUNDLE/assets
    ASSETS = BUNDLE / "assets"
else:
    # Development: assets are in src/wms/assets
    ASSETS = ROOT / "src" / "wms" / "assets"


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
