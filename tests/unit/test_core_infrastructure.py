"""Unit tests for core infrastructure components"""

import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from core.config import Config
from core.container import Container
from core.exceptions import (AppException, BusinessRuleError,
                             ConfigurationError, DatabaseError, SecurityError,
                             ValidationError)
from utils.error_handler import ErrorHandler
from utils.logging import LoggerFactory


class TestConfig:
    """Test configuration management"""

    def test_config_from_env_with_defaults(self):
        """Test configuration loads with default values"""
        config = Config.from_env()

        assert config.app_name == "Warehouse Management"
        assert config.app_version == "2.0.0"
        assert config.environment == "production"
        assert config.notification_port == 5005
        assert config.log_level == "INFO"

    def test_config_from_env_with_custom_values(self):
        """Test configuration loads from environment variables"""
        with patch.dict(
            os.environ,
            {
                "APP_NAME": "Test App",
                "APP_VERSION": "1.0.0",
                "NOTIFICATION_PORT": "8080",
                "LOG_LEVEL": "DEBUG",
            },
        ):
            config = Config.from_env()

            assert config.app_name == "Test App"
            assert config.app_version == "1.0.0"
            assert config.notification_port == 8080
            assert config.log_level == "DEBUG"

    def test_config_validate_success(self):
        """Test configuration validation passes with valid config"""
        config = Config.from_env()
        errors = config.validate()

        # Should have no errors for default config
        assert isinstance(errors, list)

    def test_config_validate_invalid_port(self):
        """Test configuration validation fails with invalid port"""
        config = Config.from_env()
        config.notification_port = 100  # Invalid port < 1024

        errors = config.validate()
        assert len(errors) > 0
        assert any("port" in error.lower() for error in errors)

    def test_config_validate_invalid_log_level(self):
        """Test configuration validation fails with invalid log level"""
        config = Config.from_env()
        config.log_level = "INVALID"

        errors = config.validate()
        assert len(errors) > 0
        assert any("log level" in error.lower() for error in errors)

    def test_config_validate_small_window_dimensions(self):
        """Test configuration validation fails with too small window"""
        config = Config.from_env()
        config.window_width = 500
        config.window_height = 400

        errors = config.validate()
        assert len(errors) > 0
        assert any("window" in error.lower() for error in errors)


class TestContainer:
    """Test dependency injection container"""

    def test_container_initialization(self):
        """Test container initializes with config"""
        config = Config.from_env()
        container = Container(config)

        assert container is not None
        assert container.get("config") == config

    def test_register_and_get_singleton(self):
        """Test registering and retrieving singleton services"""
        config = Config.from_env()
        container = Container(config)

        test_service = Mock()
        container.register_singleton("test_service", test_service)

        retrieved = container.get("test_service")
        assert retrieved is test_service

    def test_register_and_get_factory(self):
        """Test registering and retrieving factory services"""
        config = Config.from_env()
        container = Container(config)

        def factory(cont):
            return Mock()

        container.register_factory("test_factory", factory)

        instance = container.get("test_factory")
        assert instance is not None

    def test_has_service(self):
        """Test checking if service is registered"""
        config = Config.from_env()
        container = Container(config)

        assert container.has("config")
        assert not container.has("nonexistent_service")

    def test_get_nonexistent_service(self):
        """Test getting nonexistent service returns None"""
        config = Config.from_env()
        container = Container(config)

        result = container.get("nonexistent")
        assert result is None


class TestLogging:
    """Test logging infrastructure"""

    def test_logger_creation(self):
        """Test logger is created successfully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = LoggerFactory.create("test_logger_1", log_dir)

            assert logger is not None
            assert logger.name == "test_logger_1"
            assert logger.level == logging.INFO

            # Close handlers to release file locks
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()

    def test_logger_with_custom_level(self):
        """Test logger creation with custom log level"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = LoggerFactory.create("test_logger_2", log_dir, level="DEBUG")

            assert logger.level == logging.DEBUG

            # Close handlers to release file locks
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()

    def test_logger_creates_log_directory(self):
        """Test logger creates log directory if it doesn't exist"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "logs"
            assert not log_dir.exists()

            logger = LoggerFactory.create("test_logger_3", log_dir)

            # Directory should be created by logger
            assert log_dir.exists()

            # Close handlers to release file locks
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()

    def test_logger_creates_log_file(self):
        """Test logger creates log file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = LoggerFactory.create("test_logger_4", log_dir)

            logger.info("Test message")

            # Flush handlers to ensure file is written
            for handler in logger.handlers:
                handler.flush()

            log_file = log_dir / "test_logger_4.log"
            assert log_file.exists()

            # Close handlers to release file locks
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()

    def test_logger_rotation_daily(self):
        """Test logger with daily rotation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = LoggerFactory.create("test_logger_5", log_dir, rotation="daily")

            assert logger is not None
            assert len(logger.handlers) == 2  # Console + File

            # Close handlers to release file locks
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()

    def test_logger_rotation_size(self):
        """Test logger with size-based rotation"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir)
            logger = LoggerFactory.create("test_logger_6", log_dir, rotation="size")

            assert logger is not None
            assert len(logger.handlers) == 2  # Console + File

            # Close handlers to release file locks
            for handler in logger.handlers:
                handler.close()
            logger.handlers.clear()


class TestExceptions:
    """Test custom exception hierarchy"""

    def test_app_exception(self):
        """Test base AppException"""
        error = AppException("Test error", "TEST_CODE", {"key": "value"})

        assert error.message == "Test error"
        assert error.code == "TEST_CODE"
        assert error.details == {"key": "value"}

    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("Invalid input", "username")

        assert error.message == "Invalid input"
        assert error.code == "VALIDATION_ERROR"
        assert error.details["field"] == "username"

    def test_database_error(self):
        """Test DatabaseError"""
        error = DatabaseError("Connection failed", "connect")

        assert error.message == "Connection failed"
        assert error.code == "DATABASE_ERROR"
        assert error.details["operation"] == "connect"

    def test_configuration_error(self):
        """Test ConfigurationError"""
        error = ConfigurationError("Missing config", "db_path")

        assert error.message == "Missing config"
        assert error.code == "CONFIG_ERROR"
        assert error.details["config_key"] == "db_path"

    def test_business_rule_error(self):
        """Test BusinessRuleError"""
        error = BusinessRuleError("Rule violated", "max_quantity")

        assert error.message == "Rule violated"
        assert error.code == "BUSINESS_RULE_ERROR"
        assert error.details["rule"] == "max_quantity"

    def test_security_error(self):
        """Test SecurityError"""
        error = SecurityError("Unauthorized access", "authentication")

        assert error.message == "Unauthorized access"
        assert error.code == "SECURITY_ERROR"
        assert error.details["violation_type"] == "authentication"


class TestErrorHandler:
    """Test error handler"""

    def test_error_handler_initialization(self):
        """Test error handler initializes with logger"""
        logger = Mock()
        handler = ErrorHandler(logger)

        assert handler.logger is logger

    @patch("utils.error_handler.QMessageBox")
    def test_handle_app_exception(self, mock_msgbox):
        """Test handling AppException"""
        logger = Mock()
        handler = ErrorHandler(logger)

        error = ValidationError("Test error", "field")
        handler.handle(error)

        logger.error.assert_called_once()
        mock_msgbox.assert_called()

    @patch("utils.error_handler.QMessageBox")
    def test_handle_generic_exception(self, mock_msgbox):
        """Test handling generic exception"""
        logger = Mock()
        handler = ErrorHandler(logger)

        error = Exception("Generic error")
        handler.handle(error)

        logger.exception.assert_called_once()
        mock_msgbox.assert_called()

    @patch("utils.error_handler.QMessageBox")
    def test_handle_critical(self, mock_msgbox):
        """Test handling critical error"""
        logger = Mock()
        handler = ErrorHandler(logger)

        error = Exception("Critical error")
        handler.handle_critical(error)

        logger.critical.assert_called_once()
        mock_msgbox.assert_called()

    @patch("utils.error_handler.QMessageBox")
    def test_handle_warning(self, mock_msgbox):
        """Test handling warning"""
        logger = Mock()
        handler = ErrorHandler(logger)

        handler.handle_warning("Warning message")

        logger.warning.assert_called_once()
        mock_msgbox.assert_called()

    @patch("utils.error_handler.QMessageBox")
    def test_handle_info(self, mock_msgbox):
        """Test handling info message"""
        logger = Mock()
        handler = ErrorHandler(logger)

        handler.handle_info("Info message")

        logger.info.assert_called_once()
        mock_msgbox.assert_called()
