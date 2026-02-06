"""
Enhanced domain models with validation.
Uses dataclasses with __post_init__ validation and Decimal for monetary values.
"""

import os
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

# Import custom exceptions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.exceptions import ValidationError


@dataclass
class Product:
    """Product domain model with validation"""

    id: Optional[int]
    name: str
    large_unit: str
    conversion: int
    unit_price: Decimal
    is_active: bool = True
    is_favorite: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        """Validate product data after initialization"""
        # Convert float to Decimal if needed
        if isinstance(self.unit_price, float):
            self.unit_price = Decimal(str(self.unit_price))

        self.validate()

    def validate(self) -> None:
        """Validate product data"""
        if not self.name or len(self.name.strip()) == 0:
            raise ValidationError("Product name cannot be empty", "name")

        if len(self.name) > 200:
            raise ValidationError("Product name too long (max 200 characters)", "name")

        if self.conversion <= 0:
            raise ValidationError("Conversion must be positive", "conversion")

        if self.unit_price < 0:
            raise ValidationError("Unit price cannot be negative", "unit_price")

        if not self.large_unit or len(self.large_unit.strip()) == 0:
            raise ValidationError("Large unit cannot be empty", "large_unit")

    @property
    def unit_char(self) -> str:
        """Get unit abbreviation"""
        mapping = {
            "Thùng": "t",
            "Vỉ": "v",
            "Gói": "g",
            "Két": "k",
            "Hộp": "h",
            "Chai": "c",
        }
        return mapping.get(
            self.large_unit, self.large_unit[0].lower() if self.large_unit else "u"
        )

    @classmethod
    def from_row(cls, row) -> "Product":
        """Create Product from sqlite3.Row"""
        return cls(
            id=row["id"],
            name=row["name"],
            large_unit=row["large_unit"],
            conversion=row["conversion"],
            unit_price=Decimal(str(row["unit_price"])),
            is_active=bool(row["is_active"]) if "is_active" in row.keys() else True,
            is_favorite=(
                bool(row["is_favorite"]) if "is_favorite" in row.keys() else False
            ),
            created_at=row["created_at"] if "created_at" in row.keys() else None,
            updated_at=row["updated_at"] if "updated_at" in row.keys() else None,
        )


@dataclass
class SessionData:
    """Session data with business rules and validation"""

    product: Product
    handover_qty: int = 0
    closing_qty: int = 0

    def __post_init__(self):
        """Validate session data after initialization"""
        self.validate()

    def validate(self) -> None:
        """Validate session data"""
        if self.handover_qty < 0:
            raise ValidationError(
                "Handover quantity cannot be negative", "handover_qty"
            )

        if self.closing_qty < 0:
            raise ValidationError("Closing quantity cannot be negative", "closing_qty")

        if self.closing_qty > self.handover_qty:
            raise ValidationError(
                "Closing quantity cannot exceed handover quantity", "closing_qty"
            )

    @property
    def used_qty(self) -> int:
        """Calculate used quantity"""
        return max(0, self.handover_qty - self.closing_qty)

    @property
    def amount(self) -> Decimal:
        """Calculate amount using Decimal for precision"""
        return Decimal(self.used_qty) * self.product.unit_price

    @classmethod
    def from_row(cls, row) -> "SessionData":
        """Create SessionData from sqlite3.Row (JOIN products and session_data)"""
        product = Product(
            id=row["id"],
            name=row["name"],
            large_unit=row["large_unit"],
            conversion=row["conversion"],
            unit_price=Decimal(str(row["unit_price"])),
            is_active=bool(row["is_active"]) if "is_active" in row.keys() else True,
            is_favorite=(
                bool(row["is_favorite"]) if "is_favorite" in row.keys() else False
            ),
        )
        return cls(
            product=product,
            handover_qty=row["handover_qty"],
            closing_qty=row["closing_qty"],
        )


@dataclass
class SessionHistoryItem:
    """Detail of a product in session history"""

    id: int
    history_id: int
    product_id: int
    product_name: str
    large_unit: str
    conversion: int
    unit_price: Decimal
    handover_qty: int
    closing_qty: int
    used_qty: int
    amount: Decimal

    def __post_init__(self):
        """Convert float to Decimal if needed"""
        if isinstance(self.unit_price, float):
            self.unit_price = Decimal(str(self.unit_price))
        if isinstance(self.amount, float):
            self.amount = Decimal(str(self.amount))

    @classmethod
    def from_row(cls, row) -> "SessionHistoryItem":
        return cls(
            id=row["id"],
            history_id=row["history_id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            large_unit=row["large_unit"],
            conversion=row["conversion"],
            unit_price=Decimal(str(row["unit_price"])),
            handover_qty=row["handover_qty"],
            closing_qty=row["closing_qty"],
            used_qty=row["used_qty"],
            amount=Decimal(str(row["amount"])),
        )


@dataclass
class SessionHistory:
    """History of a work session"""

    id: int
    session_date: date
    shift_name: Optional[str]
    total_amount: Decimal
    notes: Optional[str]
    created_at: Optional[datetime]
    items: List[SessionHistoryItem] = field(default_factory=list)

    def __post_init__(self):
        """Convert float to Decimal if needed"""
        if isinstance(self.total_amount, float):
            self.total_amount = Decimal(str(self.total_amount))

    @classmethod
    def from_row(cls, row) -> "SessionHistory":
        return cls(
            id=row["id"],
            session_date=row["session_date"],
            shift_name=row["shift_name"],
            total_amount=Decimal(str(row["total_amount"])),
            notes=row["notes"],
            created_at=row["created_at"],
        )


@dataclass
class QuickPrice:
    """Quick price entry"""

    id: int
    name: str
    price: Decimal

    def __post_init__(self):
        """Convert float to Decimal if needed"""
        if isinstance(self.price, float):
            self.price = Decimal(str(self.price))

    @classmethod
    def from_row(cls, row) -> "QuickPrice":
        return cls(id=row["id"], name=row["name"], price=Decimal(str(row["price"])))


@dataclass
class BankNotification:
    """Bank notification history"""

    id: int
    time_str: str
    source: str
    amount: str
    content: str
    sender_name: str
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> "BankNotification":
        return cls(
            id=row["id"],
            time_str=row["time_str"],
            source=row["source"],
            amount=row["amount"],
            content=row["content"],
            sender_name=row["sender_name"] if "sender_name" in row.keys() else "",
            created_at=row["created_at"],
        )


@dataclass
class StockChangeLog:
    """Stock quantity change history"""

    id: int
    product_id: int
    product_name: str
    old_qty: int
    new_qty: int
    change_type: str  # 'increase' or 'decrease'
    changed_at: datetime

    @classmethod
    def from_row(cls, row) -> "StockChangeLog":
        return cls(
            id=row["id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            old_qty=row["old_qty"],
            new_qty=row["new_qty"],
            change_type=row["change_type"],
            changed_at=row["changed_at"],
        )
