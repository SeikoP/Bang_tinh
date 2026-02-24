"""
Main Window with Background Workers
Example of how to integrate workers
"""

from PyQt6.QtWidgets import QMainWindow

from core.container import Container
from workers.backup_worker import BackupWorker
from workers.base_worker import WorkerPool
from workers.export_worker import ExportWorker
from workers.notification_worker import NotificationWorker


class MainWindowWithWorkers(QMainWindow):
    """Main window with background workers"""

    def __init__(self, container: Container):
        super().__init__()

        self.container = container
        self.logger = container.get("logger")
        self.config = container.get("config")

        # Initialize workers
        self._init_workers()

        # Setup UI
        self._setup_ui()

    def _init_workers(self):
        """Initialize background workers"""
        # Notification worker
        bank_repo = self.container.get("bank_repo")
        self.notification_worker = NotificationWorker(self.logger, bank_repo)
        self.notification_worker.start()

        # Connect signal
        self.notification_worker.notification_parsed.connect(
            self._on_notification_parsed
        )

        # Export worker
        self.export_worker = ExportWorker(self.logger, self.config.export_dir)
        self.export_worker.start()

        # Connect signals
        self.export_worker.export_completed.connect(self._on_export_completed)
        self.export_worker.export_progress.connect(self._on_export_progress)

        # Backup worker
        self.backup_worker = BackupWorker(
            logger=self.logger,
            db_path=self.config.db_path,
            backup_dir=self.config.backup_dir,
            interval_hours=24,  # Backup every 24 hours
            retention_days=30,  # Keep backups for 30 days
        )
        self.backup_worker.start()
        self.backup_worker.start_scheduled_backups()

        # Connect signals
        self.backup_worker.backup_completed.connect(self._on_backup_completed)
        self.backup_worker.backup_failed.connect(self._on_backup_failed)

        # Worker pool for general tasks
        self.worker_pool = WorkerPool(num_workers=4, logger=self.logger)
        self.worker_pool.start()

        self.logger.info("All workers initialized")

    def _setup_ui(self):
        """Setup UI"""
        # ... UI setup code ...
        pass

    # ========================================
    # Notification Handling
    # ========================================

    def handle_notification(self, content: str):
        """
        Handle incoming notification

        This is called from HTTP server thread.
        We offload processing to worker thread.
        """
        # Add to worker queue (non-blocking)
        self.notification_worker.process_notification(content)

    def _on_notification_parsed(self, parsed_notification):
        """
        Handle parsed notification (runs on UI thread)

        Args:
            parsed_notification: ParsedNotification object
        """
        # Update UI
        # This is safe because it runs on UI thread
        if hasattr(self, "bank_view"):
            self.bank_view.add_notification_to_ui(parsed_notification)

        # Show toast
        self.show_notification(
            f"Giao dịch mới: {parsed_notification.amount} từ {parsed_notification.source}",
            type="success",
        )

    # ========================================
    # Export Handling
    # ========================================

    def export_data_to_csv(self, data, filename, headers):
        """
        Export data to CSV (non-blocking)

        Args:
            data: List of dictionaries
            filename: Output filename
            headers: CSV headers
        """
        # Show loading indicator
        self.show_loading("Đang xuất dữ liệu...")

        # Add to worker queue
        self.export_worker.export_to_csv(data, filename, headers)

    def export_data_to_excel(self, data, filename):
        """
        Export data to Excel (non-blocking)

        Args:
            data: List of dictionaries
            filename: Output filename
        """
        # Show loading indicator
        self.show_loading("Đang xuất dữ liệu...")

        # Add to worker queue
        self.export_worker.export_to_excel(data, filename)

    def _on_export_progress(self, progress: int):
        """Handle export progress"""
        # Update progress bar
        if hasattr(self, "progress_bar"):
            self.progress_bar.setValue(progress)

    def _on_export_completed(self, file_path: str):
        """Handle export completion"""
        # Hide loading indicator
        self.hide_loading()

        # Show success message
        self.show_notification(f"Xuất dữ liệu thành công: {file_path}", type="success")

        # Open file location
        import os
        import subprocess

        if os.name == "nt":  # Windows
            subprocess.Popen(f'explorer /select,"{file_path}"')

    # ========================================
    # Backup Handling
    # ========================================

    def manual_backup(self):
        """Trigger manual backup"""
        self.show_notification("Đang sao lưu dữ liệu...", type="info")
        self.backup_worker.schedule_backup()

    def _on_backup_completed(self, backup_path: str):
        """Handle backup completion"""
        self.logger.info(f"Backup completed: {backup_path}")
        # Don't show notification for automatic backups
        # Only log it

    def _on_backup_failed(self, error_message: str):
        """Handle backup failure"""
        self.logger.error(f"Backup failed: {error_message}")
        self.show_notification(f"Sao lưu thất bại: {error_message}", type="error")

    # ========================================
    # General Task Execution
    # ========================================

    def execute_long_task(self, func, *args, **kwargs):
        """
        Execute long-running task in background

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
        """
        from workers.base_worker import TaskPriority

        task_id = f"task_{id(func)}"

        self.worker_pool.submit_task(
            task_id=task_id,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=TaskPriority.NORMAL,
            callback=self._on_task_completed,
            error_callback=self._on_task_error,
        )

    def _on_task_completed(self, result):
        """Handle task completion"""
        self.logger.debug(f"Task completed with result: {result}")

    def _on_task_error(self, error: Exception):
        """Handle task error"""
        self.logger.error(f"Task failed: {error}")
        self.show_notification(f"Lỗi: {str(error)}", type="error")

    # ========================================
    # Cleanup
    # ========================================

    def closeEvent(self, event):
        """Handle window close"""
        self.logger.info("Stopping workers...")

        # Stop all workers
        self.notification_worker.stop()
        self.export_worker.stop()
        self.backup_worker.stop_scheduled_backups()
        self.backup_worker.stop()
        self.worker_pool.stop()

        self.logger.info("All workers stopped")

        event.accept()

    # ========================================
    # UI Helper Methods
    # ========================================

    def show_loading(self, message: str):
        """Show loading indicator"""
        # TODO: Implement loading spinner
        pass

    def hide_loading(self):
        """Hide loading indicator"""
        # TODO: Hide loading spinner
        pass

    def show_notification(self, message: str, type: str = "info"):
        """Show notification toast"""
        # TODO: Implement toast notification
        pass
