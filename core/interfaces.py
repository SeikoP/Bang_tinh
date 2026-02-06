"""
Core interfaces for repositories and services.
Defines abstract base classes for dependency injection and clean architecture.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from core.models import Product, SessionData, SessionHistory


class IProductRepository(ABC):
    """Interface for product data access"""

    @abstractmethod
    def get_all(self, include_inactive: bool = False) -> List["Product"]:
        """Get all products"""
        pass

    @abstractmethod
    def get_by_id(self, product_id: int) -> Optional["Product"]:
        """Get product by ID"""
        pass

    @abstractmethod
    def search(self, keyword: str) -> List["Product"]:
        """Search products by name"""
        pass

    @abstractmethod
    def add(
        self, name: str, large_unit: str, conversion: int, unit_price: float
    ) -> int:
        """Add new product, returns ID"""
        pass

    @abstractmethod
    def update(
        self,
        product_id: int,
        name: str,
        large_unit: str,
        conversion: int,
        unit_price: float,
    ) -> bool:
        """Update product"""
        pass

    @abstractmethod
    def delete(self, product_id: int, soft_delete: bool = True) -> bool:
        """Delete product (soft delete by default)"""
        pass

    @abstractmethod
    def toggle_favorite(self, product_id: int) -> bool:
        """Toggle favorite status"""
        pass


class ISessionRepository(ABC):
    """Interface for session data access (current work session)"""

    @abstractmethod
    def get_all(self) -> List["SessionData"]:
        """Get current session data for all active products"""
        pass

    @abstractmethod
    def update_qty(self, product_id: int, handover: int, closing: int) -> bool:
        """Update handover/closing quantities"""
        pass

    @abstractmethod
    def reset_all(self) -> bool:
        """Reset all quantities to 0"""
        pass

    @abstractmethod
    def get_total_amount(self) -> float:
        """Calculate total amount for current session"""
        pass


class IHistoryRepository(ABC):
    """Interface for session history access"""

    @abstractmethod
    def save_current_session(self, shift_name: str = None, notes: str = None) -> int:
        """Save current session to history"""
        pass

    @abstractmethod
    def get_all(self, limit: int = 50) -> List["SessionHistory"]:
        """Get list of session history"""
        pass

    @abstractmethod
    def get_by_id(self, history_id: int) -> Optional["SessionHistory"]:
        """Get details of a session history"""
        pass

    @abstractmethod
    def get_by_date_range(
        self, start_date: date, end_date: date
    ) -> List["SessionHistory"]:
        """Get history by date range"""
        pass

    @abstractmethod
    def delete(self, history_id: int) -> bool:
        """Delete a session history"""
        pass


class ICalculatorService(ABC):
    """Interface for calculation business logic"""

    @abstractmethod
    def parse_to_small_units(self, value_str: str, conversion: int) -> int:
        """Parse display string to small units"""
        pass

    @abstractmethod
    def format_to_display(
        self, total_small_units: int, conversion: int, unit_char: str
    ) -> str:
        """Format small units to display string"""
        pass

    @abstractmethod
    def calculate_session_total(self) -> float:
        """Calculate total amount for current session"""
        pass


class INotificationService(ABC):
    """Interface for notification handling"""

    @abstractmethod
    def start_server(self) -> None:
        """Start notification server"""
        pass

    @abstractmethod
    def stop_server(self) -> None:
        """Stop notification server"""
        pass

    @abstractmethod
    def register_handler(self, handler: callable) -> None:
        """Register notification handler callback"""
        pass


class IExportService(ABC):
    """Interface for export functionality"""

    @abstractmethod
    def export_to_excel(self, data: List, filename: str) -> bool:
        """Export data to Excel file"""
        pass

    @abstractmethod
    def export_session_history(self, history_id: int, filename: str) -> bool:
        """Export session history to file"""
        pass
