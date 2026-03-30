"""
Notification Processor Worker - Process notifications in background
"""

import json
from datetime import datetime

from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal

from ..services.bank_parser import BankStatementParser
from ..core.constants import BANK_PACKAGES, ALL_BANK_PACKAGES


class NotificationProcessor(QObject):
    """Worker để xử lý thông báo trong background thread"""

    # Signals
    notification_processed = pyqtSignal(dict)  # Emit processed notification data
    error_occurred = pyqtSignal(str)  # Emit error message

    def __init__(self, logger=None):
        super().__init__()
        self.logger = logger
        self._last_msg_content = None
        self._last_msg_time = None

    def process_notification(self, message: str):
        """
        Process raw notification message using advanced parser

        Args:
            message: Raw notification message from Android
        """
        try:
            now = datetime.now()

            # --- SPECIAL COMMANDS ---
            try:
                data = json.loads(message)
                if isinstance(data, dict):
                    # Connection Test from Android
                    if data.get("content") == "Ping":
                        processed_data = {
                            "timestamp": now.strftime("%H:%M:%S"),
                            "source": "System",
                            "amount": "",
                            "sender_name": "Android App",
                            "content": "Kết nối OK! App điện thoại đã liên kết thành công.",
                            "has_command": True,
                            "command": "PING_SUCCESS",
                            "has_amount": False,
                            "datetime": now,
                        }
                        self.notification_processed.emit(processed_data)
                        return

                    # Session Update Callback (If triggered by NotificationService)
                    if data.get("command") == "SESSION_UPDATED":
                        processed_data = {
                            "timestamp": now.strftime("%H:%M:%S"),
                            "source": "Remote",
                            "amount": "",
                            "sender_name": "App Di Động",
                            "content": f"Đã cập nhật chốt ca: {data.get('count', 0)} mặt hàng",
                            "has_command": True,
                            "command": "REFRESH_SESSION",
                            "has_amount": False,
                            "datetime": now,
                        }
                        self.notification_processed.emit(processed_data)
                        return
            except:
                pass

            # --- REGULAR NOTIFICATION ---
            # Extract content text and package from JSON wrapper (if any)
            package_name = None
            content_text = message
            try:
                data = json.loads(message)
                if isinstance(data, dict):
                    package_name = data.get("package")
                    # Extract actual notification text — this is what the bank sent
                    content_text = data.get("content", message)
            except (json.JSONDecodeError, ValueError):
                pass

            if self.logger:
                safe_preview = (content_text or "")[:120].replace("\n", " ")
                self.logger.info(
                    f"[NOTIF PIPELINE] Step 1 - raw_len={len(message)}, "
                    f"package={package_name}, content_preview={safe_preview}"
                )

            # Parse ONLY the notification text, not the full JSON wrapper
            parsed = BankStatementParser.parse(content_text)

            if self.logger:
                self.logger.info(
                    f"[NOTIF PIPELINE] Step 2 - amount={parsed.get('amount')!r}, "
                    f"source={parsed.get('source')!r}, sender={parsed.get('sender_name')!r}"
                )

            # Determine source (Package Map -> Parser detection -> Default)
            source = (
                self._get_source_from_package(package_name) if package_name else None
            )
            if not source or source == "Phone":
                source = parsed.get("source", "Phone")

            # Use parsed data
            sender_name = parsed["sender_name"]
            amount = parsed["amount"]
            timestamp = now.strftime("%H:%M:%S")

            # Detect whether this is from a known bank/fintech/SMS package
            is_bank = bool(package_name and package_name in ALL_BANK_PACKAGES)

            if self.logger:
                self.logger.info(
                    f"[NOTIF PIPELINE] Step 3 - has_amount={bool(amount)}, "
                    f"is_bank={is_bank}, source={source}, emitting signal"
                )

            # Build processed data
            processed_data = {
                "timestamp": timestamp,
                "source": source,
                "amount": amount,
                "trans_type": "in" if amount and amount.startswith("+") else "out",
                "sender_name": sender_name,
                "content": parsed["content"],
                "package": package_name,
                "has_amount": bool(amount),
                "is_bank": is_bank,
                "datetime": parsed["datetime"],
            }

            # Emit processed notification
            self.notification_processed.emit(processed_data)

        except Exception as e:
            error_msg = f"Error processing notification: {e}"
            if self.logger:
                self.logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)

    def _get_source_from_package(self, package_name: str) -> Optional[str]:
        """Map package name to bank/app name"""
        if not package_name:
            return None

        from ..core.constants import BANK_PACKAGE_MAP

        return BANK_PACKAGE_MAP.get(package_name)
