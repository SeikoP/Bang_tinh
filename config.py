"""
Cấu hình và constants cho ứng dụng Quản lý Xuất kho & Dịch vụ
"""

import os
import sys
from pathlib import Path

# === Đường dẫn (hỗ trợ cả dev và build exe) ===
# Khi build exe với PyInstaller, sys.frozen = True
if getattr(sys, "frozen", False):
    # Running as compiled exe
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as script
    BASE_DIR = Path(__file__).parent

# Load from environment variables with fallbacks
DB_PATH = Path(os.getenv("DB_PATH", BASE_DIR / "storage.db"))
BACKUP_DIR = Path(os.getenv("BACKUP_DIR", BASE_DIR / "backups"))
EXPORT_DIR = Path(os.getenv("EXPORT_DIR", BASE_DIR / "exports"))


# === Theme Colors ===
class Colors:
    PRIMARY = "#334e88"
    PRIMARY_LIGHT = "#5472b8"
    PRIMARY_DARK = "#1a2d5a"

    SECONDARY = "#ff7043"
    SECONDARY_LIGHT = "#ffa270"
    SECONDARY_DARK = "#c63f17"

    BACKGROUND = "#f5f6f9"
    BACKGROUND_DARK = "#1e1e2e"

    SURFACE = "#ffffff"
    SURFACE_DARK = "#2d2d3f"

    SUCCESS = "#4caf50"
    WARNING = "#ff9800"
    ERROR = "#f44336"
    INFO = "#2196f3"

    TEXT_PRIMARY = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_PRIMARY_DARK = "#ffffff"
    TEXT_SECONDARY_DARK = "#b0b0b0"


# === Đơn vị mặc định ===
DEFAULT_UNITS = [
    {"name": "Thùng", "char": "t"},
    {"name": "Vỉ", "char": "v"},
    {"name": "Gói", "char": "g"},
    {"name": "Két", "char": "k"},
    {"name": "Hộp", "char": "h"},
    {"name": "Chai", "char": "c"},
]

# === Window Settings ===
# Load from environment variables with fallbacks
WINDOW_WIDTH = int(os.getenv("WINDOW_WIDTH", "1200"))
WINDOW_HEIGHT = int(os.getenv("WINDOW_HEIGHT", "800"))
WINDOW_MIN_WIDTH = 850
WINDOW_MIN_HEIGHT = 600

# === App Info ===
APP_NAME = os.getenv("APP_NAME", "Phần mềm Quản lý Xuất kho & Dịch vụ")
APP_VERSION = os.getenv("APP_VERSION", "2.0.0")
APP_AUTHOR = "Bang_tinh Team"

# === Export Settings ===
EXPORT_DATE_FORMAT = "%Y-%m-%d_%H%M%S"
PDF_PAGE_SIZE = "A4"

# === Pagination ===
ITEMS_PER_PAGE = 20
HISTORY_DAYS_DEFAULT = 30
