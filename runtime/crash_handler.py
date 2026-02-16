"""
Global Crash Handler - Production Ready

Handles uncaught exceptions and provides comprehensive crash reporting:
- Detailed crash logs with system info
- Automatic crash report zipping
- Auto-restart capability
- Crash analytics
- User-friendly error dialogs
"""

import logging
import os
import sys
import traceback
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMessageBox

from core.config import Config


class CrashHandler:
    """
    Production-ready crash handler.

    Features:
    - Comprehensive crash logging
    - Automatic report zipping
    - Auto-restart option
    - Crash statistics
    - System diagnostics
    """

    def __init__(
        self, logger: logging.Logger, config: Config, auto_restart: bool = False
    ):
        self.logger = logger
        self.config = config
        self.auto_restart = auto_restart
        self.crash_dir = config.log_dir / "crashes"
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        self.crash_count = 0

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

        self.crash_count += 1

        # Log the exception
        self.logger.critical("=" * 70)
        self.logger.critical(f"UNCAUGHT EXCEPTION #{self.crash_count}")
        self.logger.critical("=" * 70)
        self.logger.critical(
            "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        )

        # Save crash report
        crash_file = self._save_crash_report(exc_type, exc_value, exc_traceback)

        # Create zip archive
        zip_file = self._create_crash_archive(crash_file)

        # Show error dialog to user
        should_restart = self._show_crash_dialog(
            exc_type, exc_value, crash_file, zip_file
        )

        # Auto-restart if enabled and user agrees
        if should_restart and self.auto_restart:
            self._restart_application()
        else:
            # Exit application
            sys.exit(1)

    def _save_crash_report(self, exc_type, exc_value, exc_traceback) -> Path:
        """
        Save comprehensive crash report to file.

        Returns:
            Path: Path to crash report file
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = self.crash_dir / f"crash_{timestamp}.txt"

        try:
            with open(crash_file, "w", encoding="utf-8") as f:
                f.write("=" * 70 + "\n")
                f.write(f"CRASH REPORT #{self.crash_count}\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 70 + "\n\n")

                # Application info
                f.write("Application Information:\n")
                f.write(f"  Name: {self.config.app_name}\n")
                f.write(f"  Version: {self.config.app_version}\n")
                f.write(f"  Environment: {self.config.environment}\n")
                f.write(f"  Python: {sys.version}\n")
                f.write(f"  Platform: {sys.platform}\n")
                f.write(f"  Executable: {sys.executable}\n")
                f.write("\n")

                # Exception info
                f.write("Exception Information:\n")
                f.write(f"  Type: {exc_type.__name__}\n")
                f.write(f"  Module: {exc_type.__module__}\n")
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
                    f.write(f"  Version: {platform.version()}\n")
                    f.write(f"  Machine: {platform.machine()}\n")
                    f.write(f"  Processor: {platform.processor()}\n")
                    f.write(f"  Architecture: {platform.architecture()}\n")
                except:
                    f.write("  (Unable to retrieve system info)\n")
                f.write("\n")

                # Resource info
                f.write("Resource Information:\n")
                try:
                    import psutil

                    mem = psutil.virtual_memory()
                    disk = psutil.disk_usage("/")
                    f.write(
                        f"  Memory: {mem.percent:.1f}% used ({mem.used / 1024 / 1024 / 1024:.2f} GB / {mem.total / 1024 / 1024 / 1024:.2f} GB)\n"
                    )
                    f.write(
                        f"  Disk: {disk.percent:.1f}% used ({disk.free / 1024 / 1024 / 1024:.2f} GB free)\n"
                    )
                    f.write(f"  CPU: {psutil.cpu_percent()}%\n")
                except:
                    f.write("  (psutil not available)\n")
                f.write("\n")

                # Environment variables (filtered)
                f.write("Environment Variables:\n")
                safe_vars = [
                    "PATH",
                    "PYTHONPATH",
                    "TEMP",
                    "TMP",
                    "USERNAME",
                    "COMPUTERNAME",
                ]
                for var in safe_vars:
                    value = os.environ.get(var, "N/A")
                    f.write(f"  {var}: {value}\n")
                f.write("\n")

                # Loaded modules
                f.write("Loaded Modules:\n")
                for name, module in sorted(sys.modules.items())[:50]:  # First 50
                    if hasattr(module, "__version__"):
                        f.write(f"  {name}: {module.__version__}\n")
                    elif hasattr(module, "__file__"):
                        f.write(f"  {name}: {module.__file__}\n")
                    else:
                        f.write(f"  {name}\n")

            self.logger.info(f"Crash report saved: {crash_file}")

        except Exception as e:
            self.logger.error(f"Failed to save crash report: {e}")

        return crash_file

    def _create_crash_archive(self, crash_file: Path) -> Optional[Path]:
        """
        Create zip archive with crash report and recent logs.

        Args:
            crash_file: Path to crash report

        Returns:
            Path to zip file or None if failed
        """
        try:
            zip_path = crash_file.with_suffix(".zip")

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
                # Add crash report
                zipf.write(crash_file, crash_file.name)

                # Add recent log files (last 3)
                log_files = sorted(
                    self.config.log_dir.glob("*.log"),
                    key=lambda p: p.stat().st_mtime,
                    reverse=True,
                )[:3]
                for log_file in log_files:
                    zipf.write(log_file, f"logs/{log_file.name}")

                # Add config (without sensitive data)
                try:
                    config_info = f"""Application Configuration:
Name: {self.config.app_name}
Version: {self.config.app_version}
Environment: {self.config.environment}
Database: {self.config.db_path}
Log Level: {self.config.log_level}
"""
                    zipf.writestr("config.txt", config_info)
                except:
                    pass

            self.logger.info(f"Crash archive created: {zip_path}")
            return zip_path

        except Exception as e:
            self.logger.error(f"Failed to create crash archive: {e}")
            return None

    def _show_crash_dialog(
        self, exc_type, exc_value, crash_file: Path, zip_file: Optional[Path]
    ) -> bool:
        """
        Show crash dialog to user.

        Returns:
            bool: True if user wants to restart, False otherwise
        """
        try:
            # Ensure QApplication exists
            if not QApplication.instance():
                QApplication(sys.argv)

            # Create error message
            error_msg = (
                f"Ứng dụng đã gặp lỗi nghiêm trọng và cần phải đóng.\n\n"
                f"Lỗi: {exc_type.__name__}\n"
                f"Chi tiết: {str(exc_value)}\n\n"
            )

            if zip_file:
                error_msg += f"Báo cáo lỗi đã được lưu tại:\n{zip_file}\n\n"
            else:
                error_msg += f"Báo cáo lỗi đã được lưu tại:\n{crash_file}\n\n"

            error_msg += "Vui lòng liên hệ bộ phận hỗ trợ và gửi file báo cáo lỗi."

            # Show dialog with restart option
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("Lỗi nghiêm trọng")
            msg_box.setText(error_msg)

            if self.auto_restart:
                msg_box.setInformativeText("Bạn có muốn khởi động lại ứng dụng?")
                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                msg_box.setDefaultButton(QMessageBox.StandardButton.Yes)
                result = msg_box.exec()
                return result == QMessageBox.StandardButton.Yes
            else:
                msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
                msg_box.exec()
                return False

        except Exception as e:
            # If we can't show dialog, just print to console
            print(f"CRITICAL ERROR: {exc_type.__name__}: {exc_value}")
            print(f"Crash report: {crash_file}")
            self.logger.error(f"Failed to show crash dialog: {e}")
            return False

    def _restart_application(self):
        """Restart the application"""
        try:
            self.logger.info("Restarting application...")

            # Windows-safe restart
            if sys.platform == "win32":
                import subprocess

                # Use subprocess.Popen for Windows
                subprocess.Popen([sys.executable] + sys.argv)
                sys.exit(0)
            else:
                # Unix-like systems can use os.execv
                import os

                os.execv(sys.executable, [sys.executable] + sys.argv)

        except Exception as e:
            self.logger.error(f"Failed to restart application: {e}")
            sys.exit(1)


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
