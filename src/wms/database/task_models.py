"""
Task models for work notes
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskType(Enum):
    """Task types"""

    UNPAID = "unpaid"  # Chưa thanh toán
    UNCOLLECTED = "uncollected"  # Chưa thu tiền
    UNDELIVERED = "undelivered"  # Chưa giao đồ
    UNRECEIVED = "unreceived"  # Chưa lấy đồ
    OTHER = "other"  # Khác


class PaymentStatus(Enum):
    """Payment status for unpaid tasks"""

    NONE = "none"  # Chưa tạo link thanh toán
    PENDING = "pending"  # Đã tạo link, chờ thanh toán
    MATCHED = "matched"  # Phát hiện giao dịch khớp
    COMPLETED = "completed"  # Đã hoàn thành thanh toán
    FAILED = "failed"  # Lỗi / quá hạn


@dataclass
class Task:
    """Task data model"""

    id: int
    task_type: str
    description: str
    customer_name: str
    amount: float
    created_at: datetime
    completed: bool = False
    completed_at: datetime = None
    notes: str = ""
    payment_status: str = "none"
    transfer_content: str = ""
    vietqr_url: str = ""

    @property
    def type_display(self) -> str:
        """Get display text for task type"""
        type_map = {
            "unpaid": "Chưa thanh toán",
            "uncollected": "Chưa thu tiền",
            "undelivered": "Chưa giao đồ",
            "unreceived": "Chưa lấy đồ",
            "other": "Khác",
        }
        return type_map.get(self.task_type, "Khác")

    @property
    def note_code(self) -> str:
        """Return GC{id} code for payment matching"""
        return f"GC{self.id}"

    @property
    def payment_status_display(self) -> str:
        status_map = {
            "none": "",
            "pending": "⏳ Chờ TT",
            "matched": "🔵 Đã khớp",
            "completed": "✅ Đã TT",
            "failed": "❌ Lỗi",
        }
        return status_map.get(self.payment_status, "")


@dataclass
class InvoiceItem:
    """A product line within a note/invoice"""

    note_id: int
    product_name: str
    qty: int
    unit_price: float
    line_total: float
    id: int = 0
    product_id: int = 0
    unit: str = ""
    item_note: str = ""


@dataclass
class NoteEvent:
    """Audit event log for a note"""

    note_id: int
    event_type: str
    id: int = 0
    message: str = ""
    metadata: str = ""
    created_at: datetime = field(default_factory=datetime.now)
