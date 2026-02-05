"""Dependency injection container"""

from typing import Any, Dict, Optional
from core.config import Config
import logging


class Container:
    """Dependency injection container for managing application services"""

    def __init__(self, config: Config):
        self._config = config
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._register_services()

    def _register_services(self):
        """Register all application services"""
        from database.repositories import (
            ProductRepository,
            SessionRepository,
            HistoryRepository,
            QuickPriceRepository,
        )
        from services.calculator import CalculatorService
        from services.exporter import ExportService
        from services.notification_service import NotificationService
        from utils.logging import LoggerFactory

        # Store config as singleton
        self._singletons["config"] = self._config

        # Logger (singleton)
        logger = LoggerFactory.create(
            name="app",
            log_dir=self._config.log_dir,
            level=self._config.log_level,
            rotation=self._config.log_rotation,
        )
        self._singletons["logger"] = logger

        # Repositories (singletons)
        self._singletons["product_repo"] = ProductRepository()
        self._singletons["session_repo"] = SessionRepository()
        self._singletons["history_repo"] = HistoryRepository()
        self._singletons["quick_price_repo"] = QuickPriceRepository()

        # Services (singletons with dependencies)
        self._singletons["calculator"] = CalculatorService(
            session_repository=self.get("session_repo")
        )
        self._singletons["exporter"] = ExportService(
            export_dir=self._config.export_dir, logger=logger
        )
        self._singletons["notification"] = NotificationService(
            host=self._config.notification_host,
            port=self._config.notification_port,
            logger=logger,
        )

    def register_singleton(self, name: str, instance: Any) -> None:
        """Register a singleton service instance"""
        self._singletons[name] = instance

    def register_factory(self, name: str, factory: callable) -> None:
        """Register a factory function for creating service instances"""
        self._services[name] = factory

    def get(self, service_name: str) -> Optional[Any]:
        """Get a service by name"""
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]

        # Check factories
        if service_name in self._services:
            factory = self._services[service_name]
            instance = factory(self)
            return instance

        return None

    def has(self, service_name: str) -> bool:
        """Check if a service is registered"""
        return service_name in self._singletons or service_name in self._services
