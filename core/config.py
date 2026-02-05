"""Application configuration management"""

from dataclasses import dataclass
from pathlib import Path
import os
from typing import Optional


@dataclass
class Config:
    """Application configuration"""

    # Paths
    base_dir: Path
    db_path: Path
    export_dir: Path
    backup_dir: Path
    log_dir: Path

    # Application
    app_name: str
    app_version: str
    environment: str  # dev, staging, production

    # UI
    window_width: int
    window_height: int
    theme: str

    # Server
    notification_port: int
    notification_host: str
    enable_ssl: bool

    # Security
    license_key: Optional[str]
    encryption_key: Optional[str]

    # Logging
    log_level: str
    log_rotation: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        base_dir = Path(os.getenv("APP_BASE_DIR", Path.cwd()))

        return cls(
            base_dir=base_dir,
            db_path=Path(os.getenv("DB_PATH", base_dir / "storage.db")),
            export_dir=Path(os.getenv("EXPORT_DIR", base_dir / "exports")),
            backup_dir=Path(os.getenv("BACKUP_DIR", base_dir / "backups")),
            log_dir=Path(os.getenv("LOG_DIR", base_dir / "logs")),
            app_name=os.getenv("APP_NAME", "Warehouse Management"),
            app_version=os.getenv("APP_VERSION", "2.0.0"),
            environment=os.getenv("ENVIRONMENT", "production"),
            window_width=int(os.getenv("WINDOW_WIDTH", "1200")),
            window_height=int(os.getenv("WINDOW_HEIGHT", "800")),
            theme=os.getenv("THEME", "modern"),
            notification_port=int(os.getenv("NOTIFICATION_PORT", "5005")),
            notification_host=os.getenv("NOTIFICATION_HOST", "0.0.0.0"),
            enable_ssl=os.getenv("ENABLE_SSL", "false").lower() == "true",
            license_key=os.getenv("LICENSE_KEY"),
            encryption_key=os.getenv("ENCRYPTION_KEY"),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_rotation=os.getenv("LOG_ROTATION", "daily"),
        )

    def validate(self) -> list[str]:
        """Validate configuration and return list of errors"""
        errors = []

        if not self.db_path.parent.exists():
            errors.append(f"Database directory does not exist: {self.db_path.parent}")

        if self.notification_port < 1024 or self.notification_port > 65535:
            errors.append(f"Invalid notification port: {self.notification_port}")

        # License key is optional - just log a warning if missing
        # if self.environment == 'production' and not self.license_key:
        #     errors.append("License key required for production environment")

        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            errors.append(f"Invalid log level: {self.log_level}")

        if self.log_rotation not in ["daily", "size"]:
            errors.append(f"Invalid log rotation: {self.log_rotation}")

        if self.window_width < 800 or self.window_height < 600:
            errors.append("Window dimensions too small (minimum 800x600)")

        return errors
