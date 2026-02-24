"""
Main Application Entry Point - QML Edition

This is the main entry point using the runtime system with QML UI.
It provides proper bootstrap, lifecycle management, and crash handling.

Usage:
    python main.py
"""

import sys
import os
from pathlib import Path

# Prefer src/ as canonical source root to avoid duplicate module ambiguity
PROJECT_ROOT = Path(__file__).parent
SRC_ROOT = PROJECT_ROOT / "src"
if SRC_ROOT.exists():
    sys.path.insert(0, str(SRC_ROOT))

# Fix Unicode encoding for Windows console BEFORE any imports
if sys.platform == 'win32':
    # Set environment variable for Python I/O encoding
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    
    # Reconfigure stdout/stderr to use UTF-8
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')

from PySide6.QtCore import QUrl

from runtime.bootstrap import ApplicationBootstrap
from runtime.lifecycle import ApplicationLifecycle


def _resolve_qml_path() -> Path:
    """Resolve the path to the qml/ directory, handling frozen builds."""
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "qml"
    return Path(__file__).parent / "qml"


def main() -> int:
    """
    Main application entry point.

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    # Step 1: Bootstrap the application
    bootstrap = ApplicationBootstrap()

    if not bootstrap.initialize():
        return 1

    # Step 2: Get initialized components
    config = bootstrap.get_config()
    container = bootstrap.get_container()
    qt_app = bootstrap.get_qt_app()
    qml_engine = bootstrap.get_qml_engine()
    logger = container.get("logger")
    profiler = bootstrap.get_profiler()
    watchdog = bootstrap.get_watchdog()

    # Step 3: Register QML import path
    qml_dir = _resolve_qml_path()
    qml_engine.addImportPath(str(qml_dir.parent))  # parent so "qml" is the module
    qml_engine.addImportPath(str(qml_dir))

    # Step 4: Create and register ViewModels as QML context properties
    from viewmodels import (
        AppViewModel,
        CalculationViewModel,
        StockViewModel,
        ProductViewModel,
        TaskViewModel,
        BankViewModel,
        HistoryViewModel,
        SettingsViewModel,
        CalculatorToolViewModel,
    )

    view_models = {
        "appVM": AppViewModel(container),
        "calculationVM": CalculationViewModel(container),
        "stockVM": StockViewModel(container),
        "productVM": ProductViewModel(container),
        "taskVM": TaskViewModel(container),
        "bankVM": BankViewModel(container),
        "historyVM": HistoryViewModel(container),
        "settingsVM": SettingsViewModel(container),
        "calculatorToolVM": CalculatorToolViewModel(container),
    }

    for name, vm in view_models.items():
        qml_engine.rootContext().setContextProperty(name, vm)
        logger.debug(f"Registered QML context property: {name}")

    # Step 5: Create lifecycle manager
    lifecycle = ApplicationLifecycle(
        config=config,
        container=container,
        qt_app=qt_app,
        qml_engine=qml_engine,
        logger=logger,
        profiler=profiler,
        watchdog=watchdog,
    )

    # Step 6: Register shutdown handlers (if needed)
    # lifecycle.register_shutdown_handler(some_cleanup_function)

    # Step 7: Load QML and start the application
    main_qml = QUrl.fromLocalFile(str(qml_dir / "main.qml"))
    exit_code = lifecycle.start(main_qml)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
