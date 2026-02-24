"""
Base ViewModel — QObject subclass with PySide6 QML integration helpers.

All ViewModels inherit from this to get:
- Signal/Slot/Property shortcuts
- Container access for services 
- Standard error handling pattern
"""

import logging
from typing import Any, Optional

from PySide6.QtCore import QObject, Signal, Slot, Property


class BaseViewModel(QObject):
    """
    Base class for all ViewModels.
    
    Subclasses should:
    1. Define Signal attributes for notifications to QML
    2. Define @Slot methods for QML to call
    3. Use _notify() to emit property change signals
    4. Access services via self._container.get("service_name")
    """

    # Generic error signal — all VMs can emit this
    errorOccurred = Signal(str)

    def __init__(self, container=None, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._container = container
        self._logger = logging.getLogger(self.__class__.__name__)

    # ---- Helpers ----

    def _get_service(self, name: str) -> Any:
        """Get a service from the DI container."""
        if self._container is None:
            self._logger.warning(f"No container — cannot resolve '{name}'")
            return None
        svc = self._container.get(name)
        if svc is None:
            self._logger.warning(f"Service '{name}' not registered")
        return svc

    def _safe_call(self, func, *args, error_msg: str = "Operation failed", **kwargs):
        """
        Execute func inside a try/except; emit errorOccurred on failure.
        Returns the result or None.
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            msg = f"{error_msg}: {e}"
            self._logger.exception(msg)
            self.errorOccurred.emit(msg)
            return None
