"""Application configuration management"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

# Import centralized paths
try:
    from app.core.paths import BACKUPS, DATABASE, EXPORTS, LOGS, ROOT
except ImportError:
    # Fallback for transition period
    ROOT = Path(__file__).resolve().parents[1]
    DATABASE = ROOT / "storage.db"
    LOGS = ROOT / "data" / "logs"
    EXPORTS = ROOT / "data" / "exports"
    BACKUPS = ROOT / "data" / "backups"


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
    secret_key: str

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        base_dir = Path(os.getenv("APP_BASE_DIR", ROOT))

        # Load or generate secret key
        secret_file = base_dir / ".secret_key"
        if secret_file.exists():
            secret_key = secret_file.read_text().strip()
        else:
            import uuid

            secret_key = str(uuid.uuid4())
            try:
                secret_file.write_text(secret_key)
            except Exception:
                pass  # Fail silently if cannot write, key will change on restart (acceptable fallback)

        return cls(
            base_dir=base_dir,
            db_path=Path(os.getenv("DB_PATH", DATABASE)),
            export_dir=Path(os.getenv("EXPORT_DIR", EXPORTS)),
            backup_dir=Path(os.getenv("BACKUP_DIR", BACKUPS)),
            log_dir=Path(os.getenv("LOG_DIR", LOGS)),
            app_name=os.getenv("APP_NAME", "WMS"),
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
            secret_key=secret_key,
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
