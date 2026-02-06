# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Warehouse Management Application
This file configures the build process for creating a standalone Windows executable.
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('.env.example', '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'sqlite3',
        'logging.handlers',
        'decimal',
        'dataclasses',
        'http.server',
        'socketserver',
        'json',
        'pathlib',
        'runtime',
        'runtime.bootstrap',
        'runtime.lifecycle',
        'runtime.crash_handler',
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
    upx=True,  # Compress to reduce size
    upx_exclude=[
        'Qt6Core.dll',
        'Qt6Gui.dll',
        'Qt6Widgets.dll',
    ],  # Don't compress Qt DLLs for better performance
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png',
    version='version_info.txt',
)
