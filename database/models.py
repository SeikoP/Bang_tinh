"""
Data models - Dataclasses đại diện cho các entity trong database
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List


@dataclass
class Product:
    """Đại diện cho một sản phẩm"""

    id: int
    name: str
    large_unit: str
    conversion: int
    unit_price: float
    is_active: bool = True
    is_favorite: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def unit_char(self) -> str:
        """Lấy ký tự viết tắt của đơn vị"""
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
        """Tạo Product từ sqlite3.Row"""
        return cls(
            id=row["id"],
            name=row["name"],
            large_unit=row["large_unit"],
            conversion=row["conversion"],
            unit_price=row["unit_price"],
            is_active=bool(row["is_active"]) if "is_active" in row.keys() else True,
            is_favorite=(
                bool(row["is_favorite"]) if "is_favorite" in row.keys() else False
            ),
            created_at=row["created_at"] if "created_at" in row.keys() else None,
            updated_at=row["updated_at"] if "updated_at" in row.keys() else None,
        )


@dataclass
class SessionData:
    """Dữ liệu phiên làm việc hiện tại cho một sản phẩm"""

    product: Product
    handover_qty: int = 0
    closing_qty: int = 0

    @property
    def used_qty(self) -> int:
        """Số lượng đã sử dụng"""
        return max(0, self.handover_qty - self.closing_qty)

    @property
    def amount(self) -> float:
        """Thành tiền"""
        return self.used_qty * self.product.unit_price

    @classmethod
    def from_row(cls, row) -> "SessionData":
        """Tạo SessionData từ sqlite3.Row (JOIN products và session_data)"""
        product = Product(
            id=row["id"],
            name=row["name"],
            large_unit=row["large_unit"],
            conversion=row["conversion"],
            unit_price=row["unit_price"],
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
    """Chi tiết một sản phẩm trong lịch sử phiên"""

    id: int
    history_id: int
    product_id: int
    product_name: str
    large_unit: str
    conversion: int
    unit_price: float
    handover_qty: int
    closing_qty: int
    used_qty: int
    amount: float

    @classmethod
    def from_row(cls, row) -> "SessionHistoryItem":
        return cls(
            id=row["id"],
            history_id=row["history_id"],
            product_id=row["product_id"],
            product_name=row["product_name"],
            large_unit=row["large_unit"],
            conversion=row["conversion"],
            unit_price=row["unit_price"],
            handover_qty=row["handover_qty"],
            closing_qty=row["closing_qty"],
            used_qty=row["used_qty"],
            amount=row["amount"],
        )


@dataclass
class SessionHistory:
    """Lịch sử một phiên làm việc"""

    id: int
    session_date: date
    shift_name: Optional[str]
    total_amount: float
    notes: Optional[str]
    created_at: Optional[datetime]
    items: List[SessionHistoryItem] = field(default_factory=list)

    @classmethod
    def from_row(cls, row) -> "SessionHistory":
        return cls(
            id=row["id"],
            session_date=row["session_date"],
            shift_name=row["shift_name"],
            total_amount=row["total_amount"],
            notes=row["notes"],
            created_at=row["created_at"],
        )


@dataclass
class QuickPrice:
    """Đại diện cho một mục trong bảng giá nhanh"""

    id: int
    name: str
    price: float

    @classmethod
    def from_row(cls, row) -> "QuickPrice":
        return cls(id=row["id"], name=row["name"], price=row["price"])


@dataclass
class BankNotification:
    """Lịch sử thông báo ngân hàng"""

    id: int
    time_str: str
    source: str
    amount: str
    content: str
    created_at: datetime

    @classmethod
    def from_row(cls, row) -> "BankNotification":
        return cls(
            id=row["id"],
            time_str=row["time_str"],
            source=row["source"],
            amount=row["amount"],
            content=row["content"],
            created_at=row["created_at"],
        )


@dataclass
class StockChangeLog:
    """Lịch sử thay đổi số lượng kho"""

    id: int
    product_id: int
    product_name: str
    old_qty: int
    new_qty: int
    change_type: str  # 'increase' hoặc 'decrease'
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
