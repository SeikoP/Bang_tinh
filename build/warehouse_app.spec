# PyInstaller spec for WMS (Warehouse Management System)
# Run from project root: pyinstaller build/warehouse_app.spec

import os
import sys
from pathlib import Path
from PyInstaller.utils.hooks import collect_submodules

PROJECT_ROOT = Path(SPECPATH).parent  # build/ -> project root

# Add src/ to sys.path so collect_submodules can find the 'wms' package
_src_dir = str(PROJECT_ROOT / 'src')
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Auto-collect ALL wms submodules to avoid ModuleNotFoundError in built app
wms_hiddenimports = collect_submodules('wms')

block_cipher = None

a = Analysis(
    [str(PROJECT_ROOT / 'src' / 'wms' / '__main__.py')],
    pathex=[str(PROJECT_ROOT / 'src')],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / 'src' / 'wms' / 'assets'), 'assets'),
        *( [(str(PROJECT_ROOT / 'config'), 'config')] if (PROJECT_ROOT / 'config').exists() else [] ),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'PyQt6.QtMultimedia',
        'build',
        'sqlite3',
        'logging.handlers',
        'decimal',
        'dataclasses',
        'http.server',
        'socketserver',
        'json',
        'pathlib',
        'qrcode',
        'qrcode.image.pure',
        'openpyxl',
        'openpyxl.styles',
    ] + wms_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'tkinter',
        'test',
        'unittest',
        'pytest',
        'PySide6',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WarehouseManagement',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
    ],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(PROJECT_ROOT / 'src' / 'wms' / 'assets' / 'icons' / 'icon.ico'),
    version=str(PROJECT_ROOT / 'build' / 'version_info.txt'),
)
