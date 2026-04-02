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
        # Qt
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.QtNetwork',
        'PyQt6.QtMultimedia',
        # Standard library
        'sqlite3',
        'logging.handlers',
        'decimal',
        'dataclasses',
        'http.server',
        'socketserver',
        'json',
        'pathlib',
        # Third-party
        'qrcode',
        'qrcode.image.pure',
        'segno',
        'openpyxl',
        'openpyxl.styles',
        # ── Explicit WMS modules (ensures they're ALWAYS included) ──
        'wms',
        'wms.__main__',
        'wms.core.config',
        'wms.core.constants',
        'wms.core.container',
        'wms.core.exceptions',
        'wms.core.interfaces',
        'wms.core.models',
        'wms.core.paths',
        'wms.core.security',
        'wms.core.updater',
        'wms.database.base_repository',
        'wms.database.connection',
        'wms.database.connection_pool',
        'wms.database.migrations',
        'wms.database.models',
        'wms.database.repositories',
        'wms.database.task_models',
        'wms.database.task_repository',
        'wms.network.connection_heartbeat',
        'wms.network.discovery_server',
        'wms.network.network_monitor',
        'wms.network.notification_handler',
        'wms.network.notification_server',
        'wms.runtime.bootstrap',
        'wms.runtime.crash_handler',
        'wms.runtime.healthcheck',
        'wms.runtime.lifecycle',
        'wms.runtime.profiler',
        'wms.runtime.watchdog',
        'wms.services.alert_service',
        'wms.services.backup_service',
        'wms.services.bank_parser',
        'wms.services.calculator',
        'wms.services.command_service',
        'wms.services.exporter',
        'wms.services.ngrok_service',
        'wms.services.notification_service',
        'wms.services.report_service',
        'wms.services.tunnel_service',
        'wms.services.tts_service',
        'wms.ui',
        'wms.ui.dpi',
        'wms.ui.main_window',
        'wms.ui.theme',
        'wms.ui.views.bank_view',
        'wms.ui.views.calculation_view',
        'wms.ui.views.calculator_tool_view',
        'wms.ui.views.history_view',
        'wms.ui.views.product_dialog',
        'wms.ui.views.product_view',
        'wms.ui.views.settings_view',
        'wms.ui.views.stock_view',
        'wms.ui.views.task_view',
        'wms.ui.widgets.alert_panel',
        'wms.ui.widgets.data_table',
        'wms.ui.widgets.loading_spinner',
        'wms.ui.widgets.notification_banners',
        'wms.ui.widgets.notification_toast',
        'wms.ui.widgets.quick_bank_peek',
        'wms.ui.widgets.status_indicator',
        'wms.utils.error_handler',
        'wms.utils.formatters',
        'wms.utils.log_sanitizer',
        'wms.utils.logging',
        'wms.utils.validators',
        'wms.workers.backup_worker',
        'wms.workers.base_worker',
        'wms.workers.export_worker',
        'wms.workers.notification_processor',
        'wms.workers.notification_worker',
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
