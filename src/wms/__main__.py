"""
WMS - Warehouse Management System
Entry point for: python -m wms

Usage:
    python -m wms
"""

import os
import sys

# Fix package context for PyInstaller / direct execution
# Without this, relative imports fail with:
#   "attempted relative import with no known parent package"
if __name__ == "__main__" and (not __package__ or __package__ == ""):
    import importlib

    if getattr(sys, 'frozen', False):
        # PyInstaller frozen app – modules live in the archive,
        # so we must NOT touch sys.path with filesystem paths.
        # Just declare the package and let PyInstaller's import hooks
        # resolve everything.
        __package__ = "wms"
        importlib.import_module("wms")
    else:
        # Development / direct script execution
        from pathlib import Path

        _pkg_dir = Path(__file__).resolve().parent        # .../src/wms
        _src_dir = str(_pkg_dir.parent)                   # .../src

        if _src_dir not in sys.path:
            sys.path.insert(0, _src_dir)

        __package__ = "wms"
        importlib.import_module("wms")

# Fix Unicode encoding for Windows console BEFORE any imports
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    """
    Main application entry point.

    Returns:
        int: Exit code (0 for success, non-zero for error)
    """
    from .runtime.bootstrap import ApplicationBootstrap
    from .runtime.lifecycle import ApplicationLifecycle

    # Step 1: Bootstrap the application
    bootstrap = ApplicationBootstrap()

    if not bootstrap.initialize():
        return 1

    # Step 2: Get initialized components
    config = bootstrap.get_config()
    container = bootstrap.get_container()
    qt_app = bootstrap.get_qt_app()
    logger = container.get("logger")
    profiler = bootstrap.get_profiler()
    watchdog = bootstrap.get_watchdog()

    # Step 3: Create lifecycle manager
    lifecycle = ApplicationLifecycle(
        config=config,
        container=container,
        qt_app=qt_app,
        logger=logger,
        profiler=profiler,
        watchdog=watchdog,
    )

    # Step 4: Create main window (deferred import for dependency readiness)
    from .ui.main_window import MainWindow

    main_window = MainWindow(container=container)

    # Step 5: Start the application
    exit_code = lifecycle.start(main_window)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
