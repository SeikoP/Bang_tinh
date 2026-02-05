"""
Application Bootstrap System

Handles the initialization sequence for the application:
1. Load environment configuration
2. Initialize logging
3. Initialize database
4. Initialize dependency injection container
5. Set up global exception handling
6. Check license
7. Start the UI
"""

import sys
import logging
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import QApplication, QMessageBox

from core.config import Config
from core.container import Container
from core.exceptions import ConfigurationError, AppException
from core.license import LicenseValidator
from database.connection import init_db
from utils.logging import LoggerFactory
from runtime.crash_handler import CrashHandler


class ApplicationBootstrap:
    """
    Manages the application bootstrap process.
    
    This class orchestrates the initialization of all application components
    in the correct order, ensuring proper error handling and logging.
    """
    
    def __init__(self):
        self.config: Optional[Config] = None
        self.container: Optional[Container] = None
        self.logger: Optional[logging.Logger] = None
        self.qt_app: Optional[QApplication] = None
        self.crash_handler: Optional[CrashHandler] = None
        self._initialized = False
    
    def initialize(self) -> bool:
        """
        Initialize the application.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Step 1: Load configuration
            self._load_configuration()
            
            # Step 2: Initialize logging
            self._initialize_logging()
            
            self.logger.info("=" * 70)
            self.logger.info(f"Starting {self.config.app_name} v{self.config.app_version}")
            self.logger.info(f"Environment: {self.config.environment}")
            self.logger.info("=" * 70)
            
            # Step 3: Initialize database
            self._initialize_database()
            
            # Step 4: Initialize dependency injection container
            self._initialize_container()
            
            # Step 5: Set up global exception handling
            self._setup_exception_handling()
            
            # Step 6: Check license (if in production)
            self._check_license()
            
            # Step 7: Initialize Qt Application
            self._initialize_qt_application()
            
            self._initialized = True
            self.logger.info("Application bootstrap completed successfully")
            return True
            
        except ConfigurationError as e:
            self._show_error_dialog(
                "Configuration Error",
                f"Failed to load configuration:\n{e.message}"
            )
            return False
            
        except Exception as e:
            self._show_error_dialog(
                "Initialization Error",
                f"Failed to initialize application:\n{str(e)}"
            )
            if self.logger:
                self.logger.exception("Bootstrap failed")
            return False
    
    def _load_configuration(self):
        """Load and validate configuration from environment"""
        self.config = Config.from_env()
        
        # Validate configuration
        errors = self.config.validate()
        if errors:
            raise ConfigurationError(
                f"Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )
        
        # Ensure required directories exist
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        self.config.export_dir.mkdir(parents=True, exist_ok=True)
        self.config.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_logging(self):
        """Initialize logging system"""
        self.logger = LoggerFactory.create(
            name=self.config.app_name,
            log_dir=self.config.log_dir,
            level=self.config.log_level,
            rotation=self.config.log_rotation
        )
        
        self.logger.info("Logging system initialized")
        self.logger.debug(f"Log directory: {self.config.log_dir}")
        self.logger.debug(f"Log level: {self.config.log_level}")
    
    def _initialize_database(self):
        """Initialize database connection and schema"""
        self.logger.info("Initializing database...")
        
        try:
            # Initialize database schema
            init_db()
            
            self.logger.info(f"Database initialized: {self.config.db_path}")
            
            # Log database info
            if self.config.db_path.exists():
                size_mb = self.config.db_path.stat().st_size / (1024 * 1024)
                self.logger.debug(f"Database size: {size_mb:.2f} MB")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
    
    def _initialize_container(self):
        """Initialize dependency injection container"""
        self.logger.info("Initializing dependency injection container...")
        
        try:
            self.container = Container(self.config)
            self.logger.info("Dependency injection container initialized")
            
        except Exception as e:
            self.logger.error(f"Container initialization failed: {e}")
            raise
    
    def _setup_exception_handling(self):
        """Set up global exception handling"""
        self.logger.info("Setting up global exception handling...")
        
        # Create crash handler
        self.crash_handler = CrashHandler(
            logger=self.logger,
            config=self.config
        )
        
        # Install exception hook
        sys.excepthook = self.crash_handler.handle_exception
        
        self.logger.info("Global exception handling configured")
    
    def _check_license(self):
        """Check license key (stub for now)"""
        if self.config.environment == 'production':
            self.logger.info("Checking license...")
            
            if not self.config.license_key:
                self.logger.warning("No license key provided - running in trial mode")
                return
            
            try:
                # For now, just log that we would validate
                # In production, you would use LicenseValidator here
                self.logger.info("License validation skipped (stub)")
                
                # Example of how to use LicenseValidator:
                # validator = LicenseValidator(public_key_pem)
                # is_valid, license_data = validator.validate(self.config.license_key)
                # if not is_valid:
                #     raise ValidationError("Invalid license key")
                # self.logger.info(f"License valid for: {license_data.get('customer')}")
                
            except Exception as e:
                self.logger.error(f"License validation failed: {e}")
                raise
        else:
            self.logger.info(f"License check skipped (environment: {self.config.environment})")
    
    def _initialize_qt_application(self):
        """Initialize Qt Application"""
        self.logger.info("Initializing Qt application...")
        
        # Create QApplication if not already created
        if not QApplication.instance():
            self.qt_app = QApplication(sys.argv)
        else:
            self.qt_app = QApplication.instance()
        
        # Set application metadata
        self.qt_app.setApplicationName(self.config.app_name)
        self.qt_app.setApplicationVersion(self.config.app_version)
        self.qt_app.setOrganizationName("Bangla Team")
        
        # Set application icon if available
        icon_path = self.config.base_dir / 'assets' / 'icon.png'
        if icon_path.exists():
            from PyQt6.QtGui import QIcon
            self.qt_app.setWindowIcon(QIcon(str(icon_path)))
        
        self.logger.info("Qt application initialized")
    
    def _show_error_dialog(self, title: str, message: str):
        """Show error dialog to user"""
        # Try to create a minimal QApplication for the error dialog
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def get_container(self) -> Container:
        """Get the dependency injection container"""
        if not self._initialized:
            raise RuntimeError("Application not initialized. Call initialize() first.")
        return self.container
    
    def get_config(self) -> Config:
        """Get the application configuration"""
        if not self.config:
            raise RuntimeError("Configuration not loaded. Call initialize() first.")
        return self.config
    
    def get_qt_app(self) -> QApplication:
        """Get the Qt application instance"""
        if not self.qt_app:
            raise RuntimeError("Qt application not initialized. Call initialize() first.")
        return self.qt_app
