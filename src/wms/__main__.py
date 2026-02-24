"""
WMS - Warehouse Management System
Entry point for: python -m wms

Usage:
    python -m wms
"""

import os
import sys

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
