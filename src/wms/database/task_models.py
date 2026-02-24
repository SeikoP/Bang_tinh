"""
Task models for work notes
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class TaskType(Enum):
    """Task types"""

    UNPAID = "unpaid"  # Chưa thanh toán
    UNCOLLECTED = "uncollected"  # Chưa thu tiền
    UNDELIVERED = "undelivered"  # Chưa giao đồ
    UNRECEIVED = "unreceived"  # Chưa lấy đồ
    OTHER = "other"  # Khác


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
