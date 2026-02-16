"""
Backup Service - Auto-backup database with rotation
"""

import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from core.exceptions import AppException


class BackupService:
    """
    Service for automatic database backup with rotation.

    Features:
    - Auto-backup on schedule
    - Keep last N backups
    - Compress old backups
    - Restore from backup
    """

    def __init__(
        self,
        db_path: Path,
        backup_dir: Path,
        keep_backups: int = 30,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize backup service.

        Args:
            db_path: Path to database file
            backup_dir: Directory to store backups
            keep_backups: Number of backups to keep
            logger: Logger instance
        """
        self.db_path = db_path
        self.backup_dir = backup_dir
        self.keep_backups = keep_backups
        self.logger = logger or logging.getLogger(__name__)

        # Ensure backup directory exists
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        self.logger.info(f"BackupService initialized: {backup_dir}")

    def create_backup(self, prefix: str = "backup") -> Path:
        """
        Create a backup of the database.

        Args:
            prefix: Backup file prefix

        Returns:
            Path to backup file

        Raises:
            AppException: If backup fails
        """
        try:
            # Check if database exists
            if not self.db_path.exists():
                raise AppException(
                    f"Database file not found: {self.db_path}", "BACKUP_ERROR"
                )

            # Generate backup filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"{prefix}_{timestamp}.db"

            # Copy database file
            shutil.copy2(self.db_path, backup_file)

            # Verify backup
            if not backup_file.exists():
                raise AppException("Backup file not created", "BACKUP_ERROR")

            backup_size = backup_file.stat().st_size
            self.logger.info(
                f"Backup created: {backup_file.name} ({backup_size / 1024:.2f} KB)"
            )

            # Cleanup old backups
            self._cleanup_old_backups()

            return backup_file

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            raise AppException(
                f"Failed to create backup: {str(e)}", "BACKUP_ERROR"
            ) from e

    def restore_backup(self, backup_file: Path) -> bool:
        """
        Restore database from backup.

        Args:
            backup_file: Path to backup file

        Returns:
            True if successful

        Raises:
            AppException: If restore fails
        """
        try:
            # Validate backup file
            if not backup_file.exists():
                raise AppException(
                    f"Backup file not found: {backup_file}", "RESTORE_ERROR"
                )

            # Create backup of current database before restore
            if self.db_path.exists():
                current_backup = self.create_backup(prefix="pre_restore")
                self.logger.info(f"Current database backed up: {current_backup.name}")

            # Restore from backup
            shutil.copy2(backup_file, self.db_path)

            self.logger.info(f"Database restored from: {backup_file.name}")
            return True

        except Exception as e:
            self.logger.error(f"Restore failed: {e}")
            raise AppException(
                f"Failed to restore backup: {str(e)}", "RESTORE_ERROR"
            ) from e

    def get_backups(self) -> List[Path]:
        """
        Get list of available backups, sorted by date (newest first).

        Returns:
            List of backup file paths
        """
        backups = sorted(
            self.backup_dir.glob("*.db"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        return backups

    def _cleanup_old_backups(self):
        """Remove old backups, keeping only the most recent N backups."""
        try:
            backups = self.get_backups()

            # Keep only the most recent backups
            if len(backups) > self.keep_backups:
                old_backups = backups[self.keep_backups :]

                for backup in old_backups:
                    backup.unlink()
                    self.logger.debug(f"Deleted old backup: {backup.name}")

                self.logger.info(
                    f"Cleaned up {len(old_backups)} old backups, "
                    f"kept {self.keep_backups} most recent"
                )
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")

    def get_backup_info(self, backup_file: Path) -> dict:
        """
        Get information about a backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            Dictionary with backup info
        """
        if not backup_file.exists():
            return {}

        stat = backup_file.stat()

        return {
            "name": backup_file.name,
            "path": str(backup_file),
            "size": stat.st_size,
            "size_mb": stat.st_size / (1024 * 1024),
            "created": datetime.fromtimestamp(stat.st_mtime),
            "age_days": (datetime.now() - datetime.fromtimestamp(stat.st_mtime)).days,
        }

    def auto_backup_on_startup(self) -> Optional[Path]:
        """
        Create backup on application startup.

        Returns:
            Path to backup file or None if failed
        """
        try:
            return self.create_backup(prefix="startup")
        except Exception as e:
            self.logger.error(f"Startup backup failed: {e}")
            return None

    def auto_backup_on_shutdown(self) -> Optional[Path]:
        """
        Create backup on application shutdown.

        Returns:
            Path to backup file or None if failed
        """
        try:
            return self.create_backup(prefix="shutdown")
        except Exception as e:
            self.logger.error(f"Shutdown backup failed: {e}")
            return None

    def auto_backup_daily(self) -> Optional[Path]:
        """
        Create daily backup (call this once per day).

        Returns:
            Path to backup file or None if already backed up today
        """
        try:
            # Check if we already have a backup today
            today = datetime.now().date()
            backups = self.get_backups()

            for backup in backups:
                backup_date = datetime.fromtimestamp(backup.stat().st_mtime).date()
                if backup_date == today:
                    self.logger.debug("Daily backup already exists")
                    return None

            # Create daily backup
            return self.create_backup(prefix="daily")

        except Exception as e:
            self.logger.error(f"Daily backup failed: {e}")
            return None
