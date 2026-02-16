"""
Notification Worker - Process notifications in background
"""

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import pyqtSignal

from workers.base_worker import BaseWorker, TaskPriority


@dataclass
class ParsedNotification:
    """Parsed notification data"""

    source: str
    amount: str
    sender_name: Optional[str]
    content: str
    time_str: str


class NotificationParser:
    """Parse bank notification messages"""

    # Patterns for different banks
    PATTERNS = {
        "momo": {
            "source": "MoMo",
            "amount": re.compile(
                r"[\+\-]?\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?)\s*(?:VND|đ|d)?",
                re.IGNORECASE,
            ),
            "sender": re.compile(r"(?:từ|from|tu)\s+([A-Za-z0-9\s]+)", re.IGNORECASE),
        },
        "vietinbank": {
            "source": "VietinBank",
            "amount": re.compile(
                r"[\+\-]?\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?)\s*(?:VND|đ|d)?",
                re.IGNORECASE,
            ),
            "sender": re.compile(
                r"(?:TK|tai khoan|account)\s+([A-Za-z0-9\s]+)", re.IGNORECASE
            ),
        },
        "vietcombank": {
            "source": "Vietcombank",
            "amount": re.compile(
                r"[\+\-]?\s*(\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?)\s*(?:VND|đ|d)?",
                re.IGNORECASE,
            ),
            "sender": re.compile(r"(?:tu|from)\s+([A-Za-z0-9\s]+)", re.IGNORECASE),
        },
        # Add more banks...
    }

    @classmethod
    def parse(cls, content: str) -> ParsedNotification:
        """
        Parse notification content

        Args:
            content: Raw notification content

        Returns:
            ParsedNotification object
        """
        # Detect bank
        source = cls._detect_bank(content)

        # Extract amount
        amount = cls._extract_amount(content, source)

        # Extract sender
        sender_name = cls._extract_sender(content, source)

        # Generate timestamp
        time_str = datetime.now().strftime("%H:%M")

        return ParsedNotification(
            source=source,
            amount=amount,
            sender_name=sender_name,
            content=content,
            time_str=time_str,
        )

    @classmethod
    def _detect_bank(cls, content: str) -> str:
        """Detect bank from content"""
        content_lower = content.lower()

        if "momo" in content_lower:
            return "MoMo"
        elif "vietinbank" in content_lower or "viettinbank" in content_lower:
            return "VietinBank"
        elif "vietcombank" in content_lower or "vcb" in content_lower:
            return "Vietcombank"
        elif "mbbank" in content_lower or "mb bank" in content_lower:
            return "MB Bank"
        elif "bidv" in content_lower:
            return "BIDV"
        elif "acb" in content_lower:
            return "ACB"
        elif "techcombank" in content_lower or "tcb" in content_lower:
            return "Techcombank"
        elif "tpbank" in content_lower:
            return "TPBank"
        elif "vnpay" in content_lower:
            return "VNPay"
        else:
            return "Unknown"

    @classmethod
    def _extract_amount(cls, content: str, source: str) -> str:
        """Extract amount from content"""
        # Try bank-specific pattern
        bank_key = source.lower().replace(" ", "")
        if bank_key in cls.PATTERNS:
            pattern = cls.PATTERNS[bank_key]["amount"]
            match = pattern.search(content)
            if match:
                amount = match.group(1)
                # Determine if incoming or outgoing
                if (
                    "+" in content
                    or "nhận" in content.lower()
                    or "nhan" in content.lower()
                ):
                    return f"+{amount}"
                elif (
                    "-" in content
                    or "chuyển" in content.lower()
                    or "chuyen" in content.lower()
                ):
                    return f"-{amount}"
                else:
                    return amount

        # Fallback: generic amount pattern
        pattern = re.compile(r"(\d{1,3}(?:[,\.]\d{3})*(?:\.\d{2})?)")
        match = pattern.search(content)
        if match:
            return match.group(1)

        return "---"

    @classmethod
    def _extract_sender(cls, content: str, source: str) -> Optional[str]:
        """Extract sender name from content"""
        bank_key = source.lower().replace(" ", "")
        if bank_key in cls.PATTERNS:
            pattern = cls.PATTERNS[bank_key]["sender"]
            match = pattern.search(content)
            if match:
                return match.group(1).strip()

        return None


class NotificationWorker(BaseWorker):
    """
    Worker for processing notifications in background

    Responsibilities:
    - Parse notification content
    - Save to database
    - Emit signal for UI update
    """

    # Signal for UI update
    notification_parsed = pyqtSignal(object)  # ParsedNotification

    def __init__(self, logger: logging.Logger, repository):
        super().__init__("NotificationWorker", logger)
        self.repository = repository

        # Connect signal
        self.signals.finished.connect(self._on_task_finished)

    def process_notification(self, content: str):
        """
        Add notification processing task

        Args:
            content: Raw notification content
        """
        task_id = f"notif_{datetime.now().timestamp()}"

        self.add_task(
            task_id=task_id,
            func=self._process_notification_task,
            args=(content,),
            priority=TaskPriority.HIGH,  # Notifications are high priority
        )

    def _process_notification_task(self, content: str) -> ParsedNotification:
        """
        Process notification (runs on worker thread)

        Args:
            content: Raw notification content

        Returns:
            ParsedNotification object
        """
        # Parse notification
        parsed = NotificationParser.parse(content)

        # Save to database
        try:
            self.repository.add(
                time_str=parsed.time_str,
                source=parsed.source,
                amount=parsed.amount,
                content=parsed.content,
                sender_name=parsed.sender_name,
            )
        except Exception as e:
            self.logger.error(f"Failed to save notification: {e}")
            # Don't fail the task, just log error

        return parsed

    def _on_task_finished(self, task_id: str, result: ParsedNotification):
        """Handle task completion (runs on UI thread)"""
        # Emit signal for UI update
        self.notification_parsed.emit(result)
