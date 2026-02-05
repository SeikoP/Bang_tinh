"""
Main Application Entry Point - Production Ready

This is the main entry point using the runtime system.
It provides proper bootstrap, lifecycle management, and crash handling.

Usage:
    python main.py
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from runtime.bootstrap import ApplicationBootstrap
from runtime.lifecycle import ApplicationLifecycle


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
    logger = container.get('logger')
    
    # Step 3: Create lifecycle manager
    lifecycle = ApplicationLifecycle(
        config=config,
        container=container,
        qt_app=qt_app,
        logger=logger
    )
    
    # Step 4: Create main window
    # Import here to avoid circular imports and ensure all dependencies are ready
    from app_window import MainWindow
    
    main_window = MainWindow(container=container)
    
    # Step 5: Register shutdown handlers (if needed)
    # lifecycle.register_shutdown_handler(some_cleanup_function)
    
    # Step 6: Start the application
    exit_code = lifecycle.start(main_window)
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
