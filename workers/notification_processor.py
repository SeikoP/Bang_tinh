"""
Notification Processor Worker - Process notifications in background
"""

from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal

from services.bank_parser import BankStatementParser


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
                import json

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
            # Parse message using advanced parser
            parsed = BankStatementParser.parse(message)

            # Extract package name if JSON
            package_name = None
            parsed["raw_content"]

            try:
                data = json.loads(message)
                if isinstance(data, dict):
                    package_name = data.get("package")
                    data.get("content", message)
            except:
                pass

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
                "datetime": parsed["datetime"],
            }

            # Emit processed notification
            self.notification_processed.emit(processed_data)

        except Exception as e:
            error_msg = f"Error processing notification: {e}"
            if self.logger:
                self.logger.error(error_msg, exc_info=True)
            self.error_occurred.emit(error_msg)

    def _get_source_from_package(self, package_name: str) -> str:
        """Map package name to bank/app name"""
        if not package_name:
            return None

        package_map = {
            "com.mservice.momotransfer": "MoMo",
            "com.vnpay.wallet": "VNPay",
            "com.vietcombank.mobile": "Vietcombank",
            "com.vietinbank.ipay": "VietinBank",
            "com.techcombank.bb.app": "Techcombank",
            "com.mbmobile": "MB Bank",
            "com.vnpay.bidv": "BIDV",
            "com.acb.acbmobile": "ACB",
            "com.tpb.mb.gprsandroid": "TPBank",
            "com.msb.mbanking": "MSB",
            "com.agribank.mobilebanking": "Agribank",
            "com.sacombank.mbanking": "Sacombank",
            "com.hdbank.mobilebanking": "HDBank",
            "com.vpbank.mobilebanking": "VPBank",
            "com.ocb.mobilebanking": "OCB",
            "com.shb.mobilebanking": "SHB",
            "com.scb.mobilebanking": "SCB",
            "com.seabank.mobilebanking": "SeaBank",
            "com.vib.mobilebanking": "VIB",
            "com.lienvietpostbank.mobilebanking": "LienVietPostBank",
            "com.bvbank.mobilebanking": "BaoVietBank",
            "com.pvcombank.mobilebanking": "PVcomBank",
        }

        return package_map.get(package_name)
