"""Logging infrastructure with rotation and structured logging"""

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path


class LoggerFactory:
    """Factory for creating configured loggers"""

    @staticmethod
    def create(
        name: str,
        log_dir: Path,
        level: str = "INFO",
        rotation: str = "daily",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
    ) -> logging.Logger:
        """
        Create a configured logger with console and file handlers

        Args:
            name: Logger name
            log_dir: Directory for log files
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            rotation: Rotation strategy ('daily' or 'size')
            max_bytes: Maximum bytes per log file (for size rotation)
            backup_count: Number of backup files to keep

        Returns:
            Configured logger instance
        """

        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))

        # Prevent duplicate handlers
        if logger.handlers:
            return logger

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File handler
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{name}.log"

        if rotation == "size":
            file_handler = RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
        else:  # daily rotation
            file_handler = TimedRotatingFileHandler(
                log_file, when="midnight", interval=1, backupCount=backup_count
            )

        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        return logger
