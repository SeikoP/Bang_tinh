# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File - Production Optimized

Features:
- Single file executable
- Optimized size
- Hidden imports included
- Runtime system integrated
- Icon and version info
"""

import sys
from pathlib import Path

block_cipher = None

# Application metadata
APP_NAME = 'WarehouseManagement'
APP_VERSION = '2.0.0'
APP_DESCRIPTION = 'Warehouse Management System'
APP_COMPANY = 'Bangla Team'

# Paths
BASE_DIR = Path('.').absolute()
ASSETS_DIR = BASE_DIR / 'assets'
ICON_FILE = ASSETS_DIR / 'icon.png'

# Hidden imports - modules that PyInstaller might miss
hidden_imports = [
    # Runtime system
    'runtime.bootstrap',
    'runtime.crash_handler',
    'runtime.lifecycle',
    'runtime.profiler',
    'runtime.watchdog',
    'runtime.healthcheck',
    
    # Core modules
    'core.config',
    'core.container',
    'core.exceptions',
    'core.interfaces',
    'core.license',
    'core.models',
    'core.updater',
    
    # Database
    'database.connection',
    'database.migrations',
    'database.models',
    'database.repositories',
    
    # Services
    'services.ai_service',
    'services.calculator',
    'services.exporter',
    'services.notification_service',
    'services.report_service',
    
    # UI
    'ui.qt_theme',
    'ui.qt_views.calculation_view',
    'ui.qt_views.history_view',
    'ui.qt_views.product_dialog',
    'ui.qt_views.product_view',
    'ui.qt_views.settings_view',
    'ui.qt_views.stock_view',
    
    # Utils
    'utils.error_handler',
    'utils.formatters',
    'utils.logging',
    'utils.validators',
    
    # PyQt6 modules
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtNetwork',
    
    # Standard library
    'sqlite3',
    'csv',
    'json',
    'logging',
    'threading',
    'queue',
    'http.server',
    'socketserver',
    'urllib.parse',
    
    # Optional dependencies
    'psutil',  # For system monitoring
]

# Data files to include
datas = [
    (str(ASSETS_DIR), 'assets'),  # Include assets folder
    ('.env.example', '.'),  # Include example env file
]

# Binaries (if any)
binaries = []

a = Analysis(
    ['main.py'],
    pathex=[str(BASE_DIR)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'matplotlib',
        'numpy',
        'pandas',
        'PIL',
        'tkinter',
        'test',
        'unittest',
        'pydoc',
        'doctest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure, 
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Enable UPX compression
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_FILE) if ICON_FILE.exists() else None,
    version='version_info.txt' if Path('version_info.txt').exists() else None,
)
