# PyInstaller spec for WMS (Warehouse Management System)
# Run from project root: pyinstaller build/warehouse_app.spec

import os
from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parent  # build/ -> project root

block_cipher = None

a = Analysis(
    [str(PROJECT_ROOT / 'src' / 'wms' / '__main__.py')],
    pathex=[str(PROJECT_ROOT / 'src')],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / 'src' / 'wms' / 'assets'), 'wms/assets'),
        *( [(str(PROJECT_ROOT / 'config'), 'config')] if (PROJECT_ROOT / 'config').exists() else [] ),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'PyQt6.QtMultimedia',
        'sqlite3',
        'logging.handlers',
        'decimal',
        'dataclasses',
        'http.server',
        'socketserver',
        'json',
        'pathlib',
        'wms',
        'wms.core',
        'wms.runtime',
        'wms.runtime.bootstrap',
        'wms.runtime.lifecycle',
        'wms.runtime.crash_handler',
        'wms.database',
        'wms.services',
        'wms.ui',
        'wms.utils',
        'wms.workers',
        'wms.network',
    ],
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
