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

import logging
import sys
from typing import Optional

from PyQt6.QtWidgets import QApplication, QMessageBox

from core.config import Config
from core.container import Container
from core.exceptions import ConfigurationError
from core.license import LicenseManager, LicenseValidator
from database.connection import init_db
from runtime.crash_handler import CrashHandler
from utils.logging import LoggerFactory


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
        self.profiler: Optional['ApplicationProfiler'] = None
        self.watchdog: Optional['ApplicationWatchdog'] = None
        self.health_check: Optional['HealthCheckSystem'] = None
        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize the application.

        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            # Step 1: Load configuration
            config_metric = None
            self._load_configuration()

            # Step 2: Initialize logging
            self._initialize_logging()
            
            # Step 3: Initialize profiler
            self._initialize_profiler()
            
            config_metric = self.profiler.start_metric("configuration_load")

            self.logger.info("=" * 70)
            self.logger.info(
                f"Starting {self.config.app_name} v{self.config.app_version}"
            )
            self.logger.info(f"Environment: {self.config.environment}")
            self.logger.info("=" * 70)
            
            if config_metric:
                self.profiler.end_metric(config_metric)

            # Step 4: Initialize database
            db_metric = self.profiler.start_metric("database_init")
            self._initialize_database()
            self.profiler.end_metric(db_metric)

            # Step 5: Initialize dependency injection container
            container_metric = self.profiler.start_metric("container_init")
            self._initialize_container()
            self.profiler.end_metric(container_metric)

            # Step 6: Set up global exception handling
            self._setup_exception_handling()
            
            # Step 7: Initialize watchdog
            self._initialize_watchdog()
            
            # Step 8: Initialize health check system
            self._initialize_health_check()

            # Step 9: Check license (if in production)
            self._check_license()

            # Step 10: Initialize Qt Application
            qt_metric = self.profiler.start_metric("qt_init")
            self._initialize_qt_application()
            self.profiler.end_metric(qt_metric)
            
            # Step 11: Run initial health checks
            self._run_initial_health_checks()

            self._initialized = True
            self.logger.info("Application bootstrap completed successfully")
            
            # Log system metrics
            if self.profiler:
                self.profiler.log_system_metrics()
            
            return True

        except ConfigurationError as e:
            self._show_error_dialog(
                "Configuration Error", f"Failed to load configuration:\n{e.message}"
            )
            return False

        except Exception as e:
            self._show_error_dialog(
                "Initialization Error", f"Failed to initialize application:\n{str(e)}"
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
                "Configuration validation failed:\n"
                + "\n".join(f"  - {e}" for e in errors)
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
            rotation=self.config.log_rotation,
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

            # Run migrations
            from database.migrations import MigrationManager

            migration_manager = MigrationManager(self.config.db_path)
            migration_manager.migrate(logger=self.logger)

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

        # Create crash handler with auto-restart option
        auto_restart = self.config.environment in ["production", "prod"]
        self.crash_handler = CrashHandler(
            logger=self.logger, 
            config=self.config,
            auto_restart=auto_restart
        )

        # Install exception hook
        sys.excepthook = self.crash_handler.handle_exception

        self.logger.info("Global exception handling configured")
    
    def _initialize_profiler(self):
        """Initialize performance profiler"""
        from runtime.profiler import ApplicationProfiler
        
        # Enable profiler in dev/staging, optional in production
        enabled = self.config.environment in ["dev", "development", "staging"]
        self.profiler = ApplicationProfiler(self.logger, enabled=enabled)
        
        self.logger.info(f"Profiler initialized (enabled: {enabled})")
    
    def _initialize_watchdog(self):
        """Initialize application watchdog"""
        from runtime.watchdog import ApplicationWatchdog
        
        # Enable watchdog in all environments
        self.watchdog = ApplicationWatchdog(
            logger=self.logger,
            check_interval=60,  # Check every minute
            enabled=True
        )
        
        # Start watchdog
        self.watchdog.start()
        
        # Store in container
        self.container._services['watchdog'] = self.watchdog
        
        self.logger.info("Watchdog initialized and started")
    
    def _initialize_health_check(self):
        """Initialize health check system"""
        from runtime.healthcheck import HealthCheckSystem
        
        self.health_check = HealthCheckSystem(
            logger=self.logger,
            config=self.config
        )
        
        # Store in container
        self.container._services['health_check'] = self.health_check
        
        self.logger.info("Health check system initialized")
    
    def _run_initial_health_checks(self):
        """Run initial health checks"""
        if not self.health_check:
            return
        
        self.logger.info("Running initial health checks...")
        
        try:
            checks = self.health_check.run_all_checks()
            
            # Log any critical issues
            critical_checks = [c for c in checks if c.status.value == "critical"]
            if critical_checks:
                self.logger.warning(f"Found {len(critical_checks)} critical health issues")
                for check in critical_checks:
                    self.logger.warning(f"  - {check.name}: {check.message}")
        
        except Exception as e:
            self.logger.error(f"Initial health check failed: {e}")

    def _check_license(self):
        """Check license key validation"""
        self.logger.info("Checking license...")

        # Skip license validation for dev/local environments
        if self.config.environment in ["dev", "development", "local"]:
            self.logger.info("License validation skipped (development environment)")
            return

        try:
            # Create license validator
            validator = LicenseValidator(logger=self.logger)

            # Create license manager
            license_manager = LicenseManager(validator=validator, logger=self.logger)

            # Validate license at startup
            is_valid = license_manager.validate_startup_license(
                license_key=self.config.license_key, environment=self.config.environment
            )

            if not is_valid:
                self.logger.warning("License validation failed. Running in trial mode.")
                return

            # Store license manager in container for later use
            self.container._services["license_manager"] = license_manager

            self.logger.info("License validation completed successfully")

        except Exception as e:
            self.logger.warning(f"License validation error: {e}")
            self.logger.info("Continuing without license validation")

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
        try:
            from app.core.paths import ASSETS
            icon_path = ASSETS / "icon.png"
        except ImportError:
            icon_path = self.config.base_dir / "assets" / "icon.png"
            
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
            raise RuntimeError(
                "Qt application not initialized. Call initialize() first."
            )
        return self.qt_app
    
    def get_profiler(self) -> 'ApplicationProfiler':
        """Get the profiler instance"""
        if not self.profiler:
            raise RuntimeError("Profiler not initialized. Call initialize() first.")
        return self.profiler
    
    def get_watchdog(self) -> 'ApplicationWatchdog':
        """Get the watchdog instance"""
        if not self.watchdog:
            raise RuntimeError("Watchdog not initialized. Call initialize() first.")
        return self.watchdog
    
    def get_health_check(self) -> 'HealthCheckSystem':
        """Get the health check system"""
        if not self.health_check:
            raise RuntimeError("Health check not initialized. Call initialize() first.")
        return self.health_check
