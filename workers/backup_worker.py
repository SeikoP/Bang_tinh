"""
Backup Worker - Automatic database backups
"""

import logging
import shutil
from datetime import datetime, timedelta
from pathlib import Path

from PyQt6.QtCore import QTimer, pyqtSignal

from workers.base_worker import BaseWorker, TaskPriority


class BackupWorker(BaseWorker):
    """
    Worker for automatic database backups

    Features:
    - Scheduled backups
    - Retention policy
    - Compression
    - Integrity verification
    """

    # Signals
    backup_completed = pyqtSignal(str)  # backup_path
    backup_failed = pyqtSignal(str)  # error_message

    def __init__(
        self,
        logger: logging.Logger,
        db_path: Path,
        backup_dir: Path,
        interval_hours: int = 24,
        retention_days: int = 30,
    ):
        super().__init__("BackupWorker", logger)

        self.db_path = db_path
        self.backup_dir = backup_dir
        self.interval_hours = interval_hours
        self.retention_days = retention_days

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Timer for scheduled backups
        self.timer = QTimer()
        self.timer.timeout.connect(self.schedule_backup)

        # Connect signals
        self.signals.finished.connect(self._on_backup_finished)
        self.signals.error.connect(self._on_backup_error)

    def start_scheduled_backups(self):
        """Start automatic scheduled backups"""
        # Do initial backup
        self.schedule_backup()

        # Start timer
        interval_ms = self.interval_hours * 60 * 60 * 1000
        self.timer.start(interval_ms)

        self.logger.info(
            f"Scheduled backups started (every {self.interval_hours} hours)"
        )

    def stop_scheduled_backups(self):
        """Stop scheduled backups"""
        self.timer.stop()
        self.logger.info("Scheduled backups stopped")

    def schedule_backup(self):
        """Schedule a backup task"""
        task_id = f"backup_{datetime.now().timestamp()}"

        self.add_task(
            task_id=task_id,
            func=self._backup_task,
            priority=TaskPriority.LOW,  # Low priority, don't interrupt user
        )

    def _backup_task(self) -> str:
        """
        Perform backup (runs on worker thread)

        Returns:
            Path to backup file
        """
        # Generate backup filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_filename

        try:
            # Copy database file
            shutil.copy2(self.db_path, backup_path)

            # Verify backup
            if not self._verify_backup(backup_path):
                raise Exception("Backup verification failed")

            # Compress backup (optional)
            compressed_path = self._compress_backup(backup_path)

            # Clean old backups
            self._cleanup_old_backups()

            self.logger.info(f"Backup completed: {compressed_path}")
            return str(compressed_path)

        except Exception as e:
            self.logger.error(f"Backup failed: {e}", exc_info=True)
            # Clean up failed backup
            if backup_path.exists():
                backup_path.unlink()
            raise

    def _verify_backup(self, backup_path: Path) -> bool:
        """
        Verify backup integrity

        Args:
            backup_path: Path to backup file

        Returns:
            True if backup is valid
        """
        try:
            import sqlite3

            # Try to open and query backup
            conn = sqlite3.connect(str(backup_path))
            cursor = conn.cursor()

            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()

            conn.close()

            return result[0] == "ok"

        except Exception as e:
            self.logger.error(f"Backup verification failed: {e}")
            return False

    def _compress_backup(self, backup_path: Path) -> Path:
        """
        Compress backup file

        Args:
            backup_path: Path to backup file

        Returns:
            Path to compressed file
        """
        import gzip

        compressed_path = backup_path.with_suffix(".db.gz")

        try:
            with open(backup_path, "rb") as f_in:
                with gzip.open(compressed_path, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Remove uncompressed backup
            backup_path.unlink()

            return compressed_path

        except Exception as e:
            self.logger.error(f"Compression failed: {e}")
            # Return uncompressed if compression fails
            return backup_path

    def _cleanup_old_backups(self):
        """Remove backups older than retention period"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for backup_file in self.backup_dir.glob("backup_*.db*"):
            try:
                # Extract timestamp from filename
                timestamp_str = backup_file.stem.split("_", 1)[1]
                if timestamp_str.endswith(".db"):
                    timestamp_str = timestamp_str[:-3]

                backup_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")

                # Delete if too old
                if backup_date < cutoff_date:
                    backup_file.unlink()
                    self.logger.info(f"Deleted old backup: {backup_file.name}")

            except Exception as e:
                self.logger.warning(f"Could not process backup file {backup_file}: {e}")

    def restore_backup(self, backup_path: Path) -> bool:
        """
        Restore database from backup

        Args:
            backup_path: Path to backup file

        Returns:
            True if restore successful
        """
        try:
            # Decompress if needed
            if backup_path.suffix == ".gz":
                import gzip

                temp_path = backup_path.with_suffix("")

                with gzip.open(backup_path, "rb") as f_in:
                    with open(temp_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)

                backup_path = temp_path

            # Verify backup before restoring
            if not self._verify_backup(backup_path):
                raise Exception("Backup file is corrupted")

            # Create backup of current database
            current_backup = self.db_path.with_suffix(".db.before_restore")
            shutil.copy2(self.db_path, current_backup)

            # Restore backup
            shutil.copy2(backup_path, self.db_path)

            self.logger.info(f"Database restored from {backup_path}")
            return True

        except Exception as e:
            self.logger.error(f"Restore failed: {e}", exc_info=True)
            return False

    def _on_backup_finished(self, task_id: str, backup_path: str):
        """Handle backup completion (runs on UI thread)"""
        self.backup_completed.emit(backup_path)

    def _on_backup_error(self, task_id: str, error: Exception):
        """Handle backup error (runs on UI thread)"""
        self.backup_failed.emit(str(error))
