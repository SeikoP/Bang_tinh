"""
Global Crash Handler

Handles uncaught exceptions and provides crash reporting.
"""

import logging
import sys
import traceback
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QApplication, QMessageBox

from core.config import Config


class CrashHandler:
    """
    Handles uncaught exceptions and crashes.

    This class:
    - Logs crash details
    - Saves crash reports
    - Shows user-friendly error dialogs
    - Attempts graceful recovery
    """

    def __init__(self, logger: logging.Logger, config: Config):
        self.logger = logger
        self.config = config
        self.crash_dir = config.log_dir / "crashes"
        self.crash_dir.mkdir(parents=True, exist_ok=True)

    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """
        Handle uncaught exception.

        This is the global exception hook that catches all unhandled exceptions.

        Args:
            exc_type: Exception type
            exc_value: Exception value
            exc_traceback: Exception traceback
        """
        # Ignore KeyboardInterrupt
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log the exception
        self.logger.critical("=" * 70)
        self.logger.critical("UNCAUGHT EXCEPTION")
        self.logger.critical("=" * 70)
        self.logger.critical(
            "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        )

        # Save crash report
        crash_file = self._save_crash_report(exc_type, exc_value, exc_traceback)

        # Show error dialog to user
        self._show_crash_dialog(exc_type, exc_value, crash_file)

        # Exit application
        sys.exit(1)

    def _save_crash_report(self, exc_type, exc_value, exc_traceback) -> Path:
        """
        Save crash report to file.

        Returns:
            Path: Path to crash report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = self.crash_dir / f"crash_{timestamp}.txt"

        try:
            with open(crash_file, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write(f"CRASH REPORT - {datetime.now().isoformat()}\n")
                f.write("=" * 70 + "\n\n")

                # Application info
                f.write("Application Information:\n")
                f.write(f"  Name: {self.config.app_name}\n")
                f.write(f"  Version: {self.config.app_version}\n")
                f.write(f"  Environment: {self.config.environment}\n")
                f.write(f"  Python: {sys.version}\n")
                f.write(f"  Platform: {sys.platform}\n")
                f.write("\n")

                # Exception info
                f.write("Exception Information:\n")
                f.write(f"  Type: {exc_type.__name__}\n")
                f.write(f"  Message: {str(exc_value)}\n")
                f.write("\n")

                # Full traceback
                f.write("Traceback:\n")
                f.write(
                    "".join(
                        traceback.format_exception(exc_type, exc_value, exc_traceback)
                    )
                )
                f.write("\n")

                # System info
                f.write("System Information:\n")
                try:
                    import platform

                    f.write(f"  OS: {platform.system()} {platform.release()}\n")
                    f.write(f"  Machine: {platform.machine()}\n")
                    f.write(f"  Processor: {platform.processor()}\n")
                except:
                    f.write("  (Unable to retrieve system info)\n")

            self.logger.info(f"Crash report saved: {crash_file}")

        except Exception as e:
            self.logger.error(f"Failed to save crash report: {e}")

        return crash_file

    def _show_crash_dialog(self, exc_type, exc_value, crash_file: Path):
        """Show crash dialog to user"""
        try:
            # Ensure QApplication exists
            if not QApplication.instance():
                app = QApplication(sys.argv)

            # Create error message
            error_msg = (
                f"Ứng dụng đã gặp lỗi nghiêm trọng và cần phải đóng.\n\n"
                f"Lỗi: {exc_type.__name__}\n"
                f"Chi tiết: {str(exc_value)}\n\n"
                f"Báo cáo lỗi đã được lưu tại:\n{crash_file}\n\n"
                f"Vui lòng liên hệ bộ phận hỗ trợ và gửi file báo cáo lỗi."
            )

            # Show dialog
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Lỗi nghiêm trọng")
            msg_box.setText(error_msg)
            msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg_box.exec()

        except Exception as e:
            # If we can't show dialog, just print to console
            print(f"CRITICAL ERROR: {exc_type.__name__}: {exc_value}")
            print(f"Crash report: {crash_file}")
            self.logger.error(f"Failed to show crash dialog: {e}")


class QtExceptionHandler:
    """
    Handler for Qt-specific exceptions.

    Qt has its own exception handling that sometimes swallows exceptions.
    This class helps catch those.
    """

    def __init__(self, crash_handler: CrashHandler):
        self.crash_handler = crash_handler

    def handle_qt_exception(self, exc_type, exc_value, exc_traceback):
        """Handle Qt exception"""
        self.crash_handler.handle_exception(exc_type, exc_value, exc_traceback)
