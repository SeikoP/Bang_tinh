"""
Application Lifecycle Management

Handles the application lifecycle:
- Startup
- Running
- Graceful shutdown
- Cleanup
"""

import sys
import signal
import logging
from typing import Optional, Callable
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtCore import QTimer

from core.config import Config
from core.container import Container


class ApplicationLifecycle:
    """
    Manages the application lifecycle from startup to shutdown.

    This class handles:
    - Application startup
    - Main event loop
    - Graceful shutdown
    - Resource cleanup
    """

    def __init__(
        self,
        config: Config,
        container: Container,
        qt_app: QApplication,
        logger: logging.Logger,
    ):
        self.config = config
        self.container = container
        self.qt_app = qt_app
        self.logger = logger
        self.main_window: Optional[QMainWindow] = None
        self._shutdown_handlers: list[Callable] = []
        self._is_shutting_down = False

        # Set up signal handlers for graceful shutdown
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Set up signal handlers for graceful shutdown"""
        # Handle Ctrl+C and termination signals
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # On Windows, also handle SIGBREAK
        if sys.platform == "win32":
            signal.signal(signal.SIGBREAK, self._signal_handler)

        self.logger.debug("Signal handlers configured")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown()

    def register_shutdown_handler(self, handler: Callable):
        """
        Register a handler to be called during shutdown.

        Args:
            handler: Callable that will be invoked during shutdown
        """
        self._shutdown_handlers.append(handler)
        self.logger.debug(f"Registered shutdown handler: {handler.__name__}")

    def start(self, main_window: QMainWindow) -> int:
        """
        Start the application.

        Args:
            main_window: The main application window

        Returns:
            int: Application exit code
        """
        self.main_window = main_window

        try:
            self.logger.info("Starting application...")

            # Show main window
            self.main_window.show()

            # Log window info
            self.logger.info(
                f"Main window displayed: {self.main_window.width()}x{self.main_window.height()}"
            )

            # Set up periodic tasks (if needed)
            self._setup_periodic_tasks()

            # Start Qt event loop
            self.logger.info("Entering Qt event loop...")
            exit_code = self.qt_app.exec()

            self.logger.info(f"Qt event loop exited with code: {exit_code}")

            # Perform cleanup
            self.shutdown()

            return exit_code

        except Exception as e:
            self.logger.exception("Error during application execution")
            self.shutdown()
            return 1

    def _setup_periodic_tasks(self):
        """Set up periodic tasks (e.g., auto-save, health checks)"""
        # Example: Auto-save timer
        # auto_save_timer = QTimer()
        # auto_save_timer.timeout.connect(self._auto_save)
        # auto_save_timer.start(300000)  # Every 5 minutes

        # Example: Health check timer
        # health_timer = QTimer()
        # health_timer.timeout.connect(self._health_check)
        # health_timer.start(60000)  # Every minute

        pass

    def _auto_save(self):
        """Periodic auto-save (example)"""
        try:
            self.logger.debug("Auto-save triggered")
            # Implement auto-save logic here
        except Exception as e:
            self.logger.error(f"Auto-save failed: {e}")

    def _health_check(self):
        """Periodic health check (example)"""
        try:
            self.logger.debug("Health check triggered")
            # Implement health check logic here
            # - Check database connection
            # - Check disk space
            # - Check memory usage
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")

    def shutdown(self):
        """Perform graceful shutdown"""
        if self._is_shutting_down:
            return

        self._is_shutting_down = True
        self.logger.info("=" * 70)
        self.logger.info("Initiating graceful shutdown...")
        self.logger.info("=" * 70)

        try:
            # Call registered shutdown handlers
            for handler in self._shutdown_handlers:
                try:
                    self.logger.debug(f"Calling shutdown handler: {handler.__name__}")
                    handler()
                except Exception as e:
                    self.logger.error(
                        f"Shutdown handler {handler.__name__} failed: {e}"
                    )

            # Close main window
            if self.main_window:
                self.logger.info("Closing main window...")
                self.main_window.close()

            # Stop notification server (if running)
            self._stop_notification_server()

            # Close database connections
            self._close_database_connections()

            # Flush logs
            self.logger.info("Shutdown complete")
            logging.shutdown()

        except Exception as e:
            self.logger.exception("Error during shutdown")

    def _stop_notification_server(self):
        """Stop notification server if running"""
        try:
            notification_service = self.container.get("notification_service")
            if notification_service and hasattr(notification_service, "stop_server"):
                self.logger.info("Stopping notification server...")
                notification_service.stop_server()
        except Exception as e:
            self.logger.error(f"Failed to stop notification server: {e}")

    def _close_database_connections(self):
        """Close database connections"""
        try:
            self.logger.info("Closing database connections...")
            # Database connections will be closed automatically
            # but we can explicitly close them here if needed
        except Exception as e:
            self.logger.error(f"Failed to close database connections: {e}")

    def restart(self):
        """Restart the application"""
        self.logger.info("Restarting application...")

        # Shutdown current instance
        self.shutdown()

        # Restart using sys.executable
        import os

        os.execv(sys.executable, [sys.executable] + sys.argv)
