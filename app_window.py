"""
Main Application - Phần mềm Quản lý Xuất kho & Dịch vụ
PyQt6 Version - Modern Premium Design
"""

import html
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from PyQt6.QtCore import QEvent, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon
from PyQt6.QtWidgets import (QApplication, QFrame, QHBoxLayout, QLabel,
                             QMainWindow, QPushButton, QStackedWidget,
                             QTabWidget, QVBoxLayout, QWidget)

from database.connection import init_db
from database.repositories import BankRepository

init_db()

from datetime import datetime

from PyQt6.QtWidgets import QHeaderView, QTableWidget, QTableWidgetItem

from config import (APP_NAME, APP_VERSION, BASE_DIR, WINDOW_HEIGHT,
                    WINDOW_MIN_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_WIDTH)
from ui.qt_theme import AppColors, AppTheme
from ui.qt_views.calculation_view import CalculationView
from ui.qt_views.history_view import HistoryView
from ui.qt_views.product_view import ProductView
from ui.qt_views.settings_view import SettingsView
from ui.qt_views.stock_view import StockView


class BankView(QWidget):
    """View hiển thị lịch sử thông báo ngân hàng với sub-tabs"""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        header_layout = QHBoxLayout()
        header = QLabel("🏦 Quản lý Giao dịch Điện thoại")
        header.setStyleSheet(
            f"font-size: 20px; font-weight: 800; color: {AppColors.TEXT};"
        )
        header_layout.addWidget(header)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Sub-tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background: white;
            }
            QTabBar::tab {
                padding: 10px 20px;
                margin-right: 4px;
                background: #f5f5f5;
                border: 1px solid #e0e0e0;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background: white;
                border-bottom: 2px solid #2196F3;
            }
            QTabBar::tab:hover {
                background: #e8f5e9;
            }
        """)

        # Tab 1: Bank Transactions
        self.transactions_widget = QWidget()
        trans_layout = QVBoxLayout(self.transactions_widget)
        trans_layout.setContentsMargins(10, 10, 10, 10)

        # Filter and clear button row
        filter_layout = QHBoxLayout()

        # Source filter
        filter_label = QLabel("Lọc theo nguồn:")
        filter_label.setStyleSheet("font-weight: bold;")
        filter_layout.addWidget(filter_label)

        from PyQt6.QtWidgets import QComboBox

        self.source_filter = QComboBox()
        self.source_filter.addItems(
            [
                "Tất cả",
                "MoMo",
                "VietinBank",
                "Vietcombank",
                "MB Bank",
                "BIDV",
                "ACB",
                "TPBank",
                "Techcombank",
                "VNPay",
            ]
        )
        self.source_filter.setFixedWidth(150)
        self.source_filter.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.source_filter)

        filter_layout.addStretch()

        self.clear_trans_btn = QPushButton("🗑️ Xóa lịch sử")
        self.clear_trans_btn.setObjectName("secondary")
        self.clear_trans_btn.setFixedWidth(150)
        self.clear_trans_btn.setStyleSheet(
            f"color: {AppColors.ERROR}; border-color: {AppColors.ERROR};"
        )
        self.clear_trans_btn.clicked.connect(self.clear_history)
        filter_layout.addWidget(self.clear_trans_btn)
        trans_layout.addLayout(filter_layout)

        # Transactions table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Giờ", "Nguồn", "Số tiền", "Người chuyển", "Chi tiết", ""]
        )

        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 70)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 150)
        self.table.setColumnWidth(5, 50)

        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        trans_layout.addWidget(self.table)

        # Tab 2: Raw Logs
        self.logs_widget = QWidget()
        logs_layout = QVBoxLayout(self.logs_widget)
        logs_layout.setContentsMargins(10, 10, 10, 10)

        # Clear button for logs
        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch()
        self.clear_logs_btn = QPushButton("🗑️ Xóa logs")
        self.clear_logs_btn.setObjectName("secondary")
        self.clear_logs_btn.setFixedWidth(150)
        self.clear_logs_btn.setStyleSheet(
            f"color: {AppColors.ERROR}; border-color: {AppColors.ERROR};"
        )
        self.clear_logs_btn.clicked.connect(self.clear_logs)
        log_btn_layout.addWidget(self.clear_logs_btn)
        logs_layout.addLayout(log_btn_layout)

        # Logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(3)
        self.logs_table.setHorizontalHeaderLabels(
            ["Thời gian", "Package", "Raw Message"]
        )

        lh = self.logs_table.horizontalHeader()
        lh.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        lh.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        lh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        self.logs_table.setColumnWidth(0, 150)
        self.logs_table.setColumnWidth(1, 200)

        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.verticalHeader().setVisible(False)
        self.logs_table.verticalHeader().setDefaultSectionSize(40)
        logs_layout.addWidget(self.logs_table)

        # Add tabs
        self.tabs.addTab(self.transactions_widget, "💰 Giao dịch")
        self.tabs.addTab(self.logs_widget, "📋 Raw Logs")

        layout.addWidget(self.tabs)

        self.load_history()

    def load_history(self):
        """Tải lại lịch sử từ database"""
        notifs = BankRepository.get_all()
        for n in reversed(notifs):
            self._add_row_ui(
                n.id, n.time_str, n.source, n.amount, n.sender_name or "", n.content
            )

    def apply_filter(self):
        """Apply source filter to transactions table"""
        filter_text = self.source_filter.currentText()

        for row in range(self.table.rowCount()):
            source_item = self.table.item(row, 1)
            if source_item:
                source = source_item.text()
                if filter_text == "Tất cả" or source == filter_text:
                    self.table.setRowHidden(row, False)
                else:
                    self.table.setRowHidden(row, True)

    def add_notif(self, time_str, source, amount, sender_name, raw_message):
        try:
            # 1. Lưu vào database trước
            new_id = BankRepository.add(
                time_str, source, amount, raw_message, sender_name
            )

            # 2. Hiển thị lên UI (transactions tab)
            self._add_row_ui(new_id, time_str, source, amount, sender_name, raw_message)
        except Exception as e:
            # Log error silently
            import logging

            logging.error(f"Error in add_notif: {e}")

    def add_raw_log(self, time_str, package, raw_message):
        """Add to raw logs tab only"""
        self._add_log_row(time_str, package, raw_message)

    def _add_log_row(self, time_str, package, raw_message):
        """Thêm raw log vào logs table"""
        row = 0
        self.logs_table.insertRow(row)

        # Timestamp
        time_item = QTableWidgetItem(time_str)
        time_item.setFont(QFont("Roboto", 9))
        self.logs_table.setItem(row, 0, time_item)

        # Package name
        pkg_item = QTableWidgetItem(package)
        pkg_item.setFont(QFont("Roboto", 9))
        pkg_item.setForeground(QColor("#666"))
        self.logs_table.setItem(row, 1, pkg_item)

        # Raw message
        msg_item = QTableWidgetItem(raw_message)
        msg_item.setFont(QFont("Courier New", 8))
        msg_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
        self.logs_table.setItem(row, 2, msg_item)

        # Limit logs to 100 rows
        if self.logs_table.rowCount() > 100:
            self.logs_table.removeRow(100)

    def clear_logs(self):
        """Xóa tất cả raw logs"""
        self.logs_table.setRowCount(0)

    def _add_row_ui(self, db_id, time_str, source, amount, sender_name, raw_message):
        row = 0
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(time_str))

        src_item = QTableWidgetItem(source)
        src_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, src_item)

        amt_item = QTableWidgetItem(amount if amount else "---")

        # Set color based on transaction type (+ green, - red)
        if amount and amount.startswith("+"):
            amt_item.setForeground(QColor(AppColors.SUCCESS))  # Green for incoming
        elif amount and amount.startswith("-"):
            amt_item.setForeground(QColor(AppColors.ERROR))  # Red for outgoing
        else:
            amt_item.setForeground(QColor(AppColors.SUCCESS))  # Default green

        amt_item.setFont(QFont("Roboto", 9, QFont.Weight.Bold))
        amt_item.setTextAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )
        self.table.setItem(row, 2, amt_item)

        # Cột người chuyển
        sender_item = QTableWidgetItem(sender_name if sender_name else "---")
        sender_item.setFont(QFont("Roboto", 9))
        self.table.setItem(row, 3, sender_item)

        # Cột chi tiết - font nhỏ hơn
        detail_item = QTableWidgetItem(raw_message)
        detail_item.setFont(QFont("Roboto", 8))
        detail_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
        self.table.setItem(row, 4, detail_item)

        # Nút xóa từng dòng (Centered Layout & Force Style)
        del_container = QWidget()
        del_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        del_layout = QHBoxLayout(del_container)
        del_layout.setContentsMargins(0, 0, 0, 0)
        del_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(30, 30)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Force style mạnh mẽ
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                font-size: 16px; 
                margin: 0px; 
                padding: 0px;
                color: #ef4444; 
            }
            QPushButton:hover {
                background-color: #fef2f2;
                border: 1px solid #ef4444;
                border-radius: 4px;
            }
        """)
        del_btn.clicked.connect(lambda: self._delete_row(db_id))

        del_layout.addWidget(del_btn)
        self.table.setCellWidget(row, 5, del_container)

        # Lưu ID vào item ẩn để tham chiếu nếu cần
        self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, db_id)

    def _delete_row(self, db_id):  # Xóa row_index khỏi tham số vì không cần thiết
        """Xóa một dòng cụ thể dựa trên ID database"""
        # Tìm row index hiện tại (vì nó có thể thay đổi sau khi xóa row khác)
        target_row = -1
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item.data(Qt.ItemDataRole.UserRole) == db_id:
                target_row = r
                break

        if target_row != -1:
            BankRepository.delete(db_id)
            self.table.removeRow(target_row)

    def clear_history(self):
        """Xóa sạch bảng lịch sử"""
        BankRepository.clear_all()
        self.table.setRowCount(0)


from urllib.parse import parse_qs, urlparse


class NotificationHandler(BaseHTTPRequestHandler):
    """Server xử lý thông báo từ app Android - Filter tại PC"""

    # Danh sách package name của các app ngân hàng Việt Nam + test packages
    BANK_PACKAGES = {
        "com.vnpay.wallet",  # VNPay
        "com.vietcombank.mobile",  # Vietcombank
        "com.techcombank.bb.app",  # Techcombank
        "com.mbmobile",  # MB Bank
        "com.vnpay.bidv",  # BIDV
        "com.acb.acbmobile",  # ACB
        "com.tpb.mb.gprsandroid",  # TPBank
        "com.msb.mbanking",  # MSB
        "com.vietinbank.ipay",  # VietinBank
        "com.agribank.mobilebanking",  # Agribank
        "com.sacombank.mbanking",  # Sacombank
        "com.hdbank.mobilebanking",  # HDBank
        "com.vpbank.mobilebanking",  # VPBank
        "com.ocb.mobilebanking",  # OCB
        "com.shb.mobilebanking",  # SHB
        "com.scb.mobilebanking",  # SCB
        "com.seabank.mobilebanking",  # SeaBank
        "com.vib.mobilebanking",  # VIB
        "com.lienvietpostbank.mobilebanking",  # LienVietPostBank
        "com.bvbank.mobilebanking",  # BaoVietBank
        "com.pvcombank.mobilebanking",  # PVcomBank
        "com.mservice.momotransfer",  # MoMo
        # Test packages ONLY for adb testing - remove in production
        "android",  # For adb test notifications
        "com.android.shell",  # For adb test notifications
    }

    def handle_request(self):
        try:
            msg = None
            # Log incoming request
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.info(
                    f"=== Received {self.command} request to {self.path} ==="
                )
                self.server.logger.info(f"Headers: {dict(self.headers)}")

            # 1. Thử lấy từ URL Query (?content=...)
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.info(f"Query params: {query_params}")

            if "content" in query_params:
                msg = query_params["content"][0]
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.info(f"Found content in query: {msg}")

            # 2. Nếu URL không có, thử lấy từ Body
            if not msg:
                content_length = self.headers.get("Content-Length")
                content_type = self.headers.get("Content-Type", "")
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.info(
                        f"Content-Length: {content_length}, Content-Type: {content_type}"
                    )

                if content_length and int(content_length) > 0:
                    post_data = self.rfile.read(int(content_length)).decode("utf-8")
                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.info(f"Received body: {post_data}")

                    # Try JSON first
                    try:
                        data = json.loads(post_data)
                        msg = data.get("content", post_data)
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.info(f"Parsed JSON, content: {msg}")
                    except json.JSONDecodeError:
                        # Try form data (application/x-www-form-urlencoded)
                        if "application/x-www-form-urlencoded" in content_type:
                            form_params = parse_qs(post_data)
                            if "content" in form_params:
                                msg = form_params["content"][0]
                                if (
                                    hasattr(self.server, "logger")
                                    and self.server.logger
                                ):
                                    self.server.logger.info(
                                        f"Parsed form data, content: {msg}"
                                    )
                            else:
                                msg = post_data
                        else:
                            msg = post_data
                            if hasattr(self.server, "logger") and self.server.logger:
                                self.server.logger.info(
                                    f"Not JSON/form, using raw body: {msg}"
                                )

            # Luôn phản hồi success để Android biết đã nhận
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            if msg:
                # Try to parse as JSON to get package info
                package_name = None
                content = msg
                try:
                    data = json.loads(msg)
                    if isinstance(data, dict):
                        package_name = data.get("package")
                        # Get content - might be nested JSON string
                        raw_content = data.get("content", msg)

                        # Try to parse content if it's a JSON string
                        try:
                            content_data = json.loads(raw_content)
                            if isinstance(content_data, dict):
                                # Extract actual content from nested structure
                                content = content_data.get("content", raw_content)
                            else:
                                content = raw_content
                        except (json.JSONDecodeError, TypeError):
                            content = raw_content
                except (json.JSONDecodeError, TypeError):
                    pass

                # Filter by package name (PC-side filtering)
                if package_name:
                    if package_name not in self.BANK_PACKAGES:
                        if hasattr(self.server, "logger") and self.server.logger:
                            self.server.logger.debug(
                                f"Filtered out notification from: {package_name}"
                            )
                        self.wfile.write(b'{"status":"success","message":"filtered"}')
                        return

                    if hasattr(self.server, "logger") and self.server.logger:
                        self.server.logger.info(
                            f"Accepted notification from: {package_name}"
                        )

                self.wfile.write(b'{"status":"success","message":"received"}')
                # Đẩy lên giao diện
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.info(
                        f"Processing notification: {content[:100]}..."
                    )
                if hasattr(self.server, "signal"):
                    self.server.signal.emit(str(content))
            else:
                self.wfile.write(b'{"status":"success","message":"no content found"}')
                if hasattr(self.server, "logger") and self.server.logger:
                    self.server.logger.warning("No content found in request")

        except Exception as e:
            if hasattr(self.server, "logger") and self.server.logger:
                self.server.logger.error(f"Error handling request: {e}", exc_info=True)
            try:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(f'{{"status":"error","message":"{str(e)}"}}'.encode())
            except:
                pass

    def do_POST(self):
        self.handle_request()

    def do_GET(self):
        self.handle_request()

    def log_message(self, format, *args):
        # Allow logging for debugging purposes if needed, but keep it clean
        # print(f"[HTTP] {format % args}")
        return


class NotificationServer(QThread):
    """Luồng chạy server lắng nghe thông báo"""

    msg_received = pyqtSignal(str)

    def __init__(self, host="0.0.0.0", port=5005, logger=None):
        super().__init__()
        self.host = host
        self.port = port
        self.logger = logger

    def run(self):
        try:
            # Sử dụng ThreadingHTTPServer để xử lý đa luồng
            server = ThreadingHTTPServer((self.host, self.port), NotificationHandler)
            server.allow_reuse_address = True
            server.timeout = 5
            server.signal = self.msg_received
            server.logger = self.logger  # Pass logger to handler
            if self.logger:
                self.logger.info(
                    f"Notification Server started on {self.host}:{self.port}"
                )
            server.serve_forever()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Could not start server: {e}")


class QuickBankPeek(QFrame):
    """Cửa sổ hiện nhanh lịch sử giao dịch khi nhấn giữ nút Ngân hàng"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)  # Hiển thị trên cùng
        self.setObjectName("card")
        self.setFixedWidth(350)
        self.setFixedHeight(400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # Tiêu đề và nút đóng
        header_layout = QHBoxLayout()
        title = QLabel("⚡ Xem nhanh giao dịch")
        title.setStyleSheet(f"font-weight: 800; color: {AppColors.PRIMARY};")
        header_layout.addWidget(title)

        header_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(
            f"background: transparent; color: {AppColors.TEXT_SECONDARY}; border: none; font-weight: bold;"
        )
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)

        # Bảng thu nhỏ
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Giờ", "Tiền", "Nội dung"])
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("font-size: 11px;")
        self.table.verticalHeader().setDefaultSectionSize(
            40
        )  # Chiều cao hàng xem nhanh
        layout.addWidget(self.table)

        hint = QLabel("Nhấn vào nút Ngân hàng để xem đầy đủ")
        hint.setStyleSheet(
            f"color: {AppColors.TEXT_DISABLED}; font-size: 10px; font-style: italic;"
        )
        layout.addWidget(hint)

    def update_data(self, bank_view_table):
        """Đồng bộ dữ liệu từ bảng chính sang bảng xem nhanh"""
        rows = min(bank_view_table.rowCount(), 15)
        self.table.setRowCount(rows)
        for r in range(rows):
            self.table.setItem(
                r, 0, QTableWidgetItem(bank_view_table.item(r, 0).text())
            )

            # Copy màu sắc số tiền based on +/-
            amt_text = bank_view_table.item(r, 2).text()
            amt_item = QTableWidgetItem(amt_text)

            if amt_text.startswith("+"):
                amt_item.setForeground(QColor(AppColors.SUCCESS))
            elif amt_text.startswith("-"):
                amt_item.setForeground(QColor(AppColors.ERROR))
            else:
                amt_item.setForeground(QColor(AppColors.SUCCESS))

            amt_item.setFont(QFont("Roboto", 8, QFont.Weight.Bold))
            self.table.setItem(r, 1, amt_item)

            self.table.setItem(
                r, 2, QTableWidgetItem(bank_view_table.item(r, 3).text())
            )


class MainWindow(QMainWindow):
    """Main window - modern premium design"""

    # Signal for cross-thread notification
    notification_received = pyqtSignal(str)

    def __init__(self, container=None):
        super().__init__()
        # Inject dependency container
        from core.config import Config
        from core.container import Container

        if container is None:
            # Fallback: create default container if not provided
            config = Config.from_env()
            container = Container(config)

        self.container = container
        self.logger = container.get("logger")
        self.config = container.get("config")
        self.error_handler = None  # Will be initialized in _setup_ui

        # Production mode checks
        if self.config and self.config.environment == "production":
            self.logger.info("Running in PRODUCTION mode")
            # Disable debug features in production
            self._production_mode = True
        else:
            self._production_mode = False
            if self.config:
                self.logger.info(f"Running in {self.config.environment.upper()} mode")

        self._setup_window()
        self._setup_ui()
        self._apply_theme()

        # Connect notification signal
        self.notification_received.connect(self._do_show_notification)

        self._start_notification_server()

        # Timer để ẩn Quick Peek có độ trễ nhỏ (tránh flickering)
        self._peek_timer = QTimer()
        self._peek_timer.setSingleShot(True)
        self._peek_timer.timeout.connect(self._hide_peek_safe)

    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        icon_path = BASE_DIR / "assets" / "icon.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                self.setWindowIcon(icon)

        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - WINDOW_WIDTH) // 2
        y = (screen.height() - WINDOW_HEIGHT) // 2
        self.move(x, y)

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(150)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet(
            f"background-color: {AppColors.SIDEBAR_BG}; border: none;"
        )

        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 24, 12, 24)
        sidebar_layout.setSpacing(8)

        logo = QLabel("BANGLA")
        logo.setStyleSheet(
            "color: white; font-weight: 950; font-size: 18px; padding: 0 4px 16px 4px;"
        )
        sidebar_layout.addWidget(logo)

        self.nav_btns = []
        self._add_nav_btn(sidebar_layout, "🧮 Bảng tính", 0)
        self._add_nav_btn(sidebar_layout, "📦 Kho hàng", 1)
        self._add_nav_btn(sidebar_layout, "🏷️ Sản phẩm", 2)
        self._add_nav_btn(sidebar_layout, "🏦 Ngân hàng", 3)
        self._add_nav_btn(sidebar_layout, "📜 Lịch sử", 4)
        self._add_nav_btn(sidebar_layout, "⚙️ Cài đặt", 5)

        sidebar_layout.addStretch()
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(
            f"color: {AppColors.SIDEBAR_TEXT}; font-size: 11px; padding: 10px;"
        )
        sidebar_layout.addWidget(version)

        main_layout.addWidget(self.sidebar)

        # Content
        self.content_stack = QStackedWidget()
        self._create_views()
        self.content_stack.addWidget(self.calc_view)
        self.content_stack.addWidget(self.stock_view)
        self.content_stack.addWidget(self.product_view)
        self.content_stack.addWidget(self.bank_view)
        self.content_stack.addWidget(self.history_view)
        self.content_stack.addWidget(self.settings_view)

        main_content = QWidget()
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Global Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(
            f"background-color: white; border-bottom: 1px solid {AppColors.BORDER};"
        )
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)

        self.breadcrumb = QLabel("Trang chủ > Bảng tính")
        self.breadcrumb.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-weight: 500;"
        )
        header_layout.addWidget(self.breadcrumb)

        header_layout.addStretch()

        # Notification Widget (Toast-like in header)
        self.notif_box = QFrame()
        self.notif_box.setFixedHeight(46)
        self.notif_box.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_box.setStyleSheet(f"""
            QFrame {{
                background: {AppColors.SUCCESS};
                border-radius: 23px;
                padding: 0 4px;
            }}
            QFrame:hover {{
                background: #059669;
            }}
        """)
        # Tính năng Nhấn và Rê chuột (Hover) cho Thông báo
        self.notif_box.mousePressEvent = lambda e: self._switch_view(3)
        self.notif_box.installEventFilter(self)

        notif_layout = QHBoxLayout(self.notif_box)
        notif_layout.setContentsMargins(15, 0, 5, 0)
        notif_layout.setSpacing(10)

        self.notif_label = QLabel("🔔 Chưa có thông báo mới")
        self.notif_label.setStyleSheet(
            "color: white; font-weight: 600; font-size: 13px; background: transparent;"
        )
        notif_layout.addWidget(self.notif_label)

        # Nút đóng thông báo (X)
        self.notif_close_btn = QPushButton("✕")
        self.notif_close_btn.setFixedSize(32, 32)
        self.notif_close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        self.notif_close_btn.clicked.connect(self.notif_box.hide)
        notif_layout.addWidget(self.notif_close_btn)

        self.notif_box.hide()  # Ẩn mặc định
        header_layout.addWidget(self.notif_box)

        content_layout.addWidget(header)
        content_layout.addWidget(self.content_stack)
        main_layout.addWidget(main_content)

        self._switch_view(0)

    def _add_nav_btn(self, layout, text, index):
        btn = QPushButton(text)
        btn.setObjectName("navItem")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._switch_view(index))

        # Nhấn giữ nút bên trái vẫn dùng hold
        if index == 3:
            self.bank_btn = btn
            btn.pressed.connect(self._start_bank_hold)
            btn.released.connect(self._stop_bank_hold)
            self._hold_timer = QTimer()
            self._hold_timer.setSingleShot(True)
            self._hold_timer.timeout.connect(self._on_bank_hold_success)

        layout.addWidget(btn)
        self.nav_btns.append(btn)

    def eventFilter(self, source, event):
        """Xử lý sự kiện di chuyển chuột (Hover)"""
        if source == self.notif_box:
            if event.type() == QEvent.Type.Enter:
                self._show_peek_under_notif()
            elif event.type() == QEvent.Type.Leave:
                # Đợi một chút rồi mới ẩn để người dùng có thể di chuyển chuột vào bảng
                self._peek_timer.start(200)

        if hasattr(self, "quick_peek") and source == self.quick_peek:
            if event.type() == QEvent.Type.Enter:
                self._peek_timer.stop()  # Hủy lệnh ẩn nếu chuột đi vào bảng
            elif event.type() == QEvent.Type.Leave:
                self._peek_timer.start(200)

        return super().eventFilter(source, event)

    def _show_peek_under_notif(self):
        """Hiện danh sách nhanh dưới thanh thông báo"""
        if not hasattr(self, "quick_peek"):
            self.quick_peek = QuickBankPeek(self)
            self.quick_peek.installEventFilter(self)

        self.quick_peek.update_data(self.bank_view.table)
        pos = self.notif_box.mapToGlobal(self.notif_box.rect().bottomLeft())
        self.quick_peek.move(pos.x(), pos.y() + 5)
        self.quick_peek.show()
        self._peek_timer.stop()

    def _hide_peek_safe(self):
        if hasattr(self, "quick_peek"):
            self.quick_peek.hide()

    def _start_bank_hold(self):
        self._hold_timer.start(500)  # Nhấn giữ 0.5 giây

    def _stop_bank_hold(self):
        self._hold_timer.stop()

    def _on_bank_hold_success(self):
        """Khi nhấn giữ nút Sidebar -> Hiện danh sách nhanh"""
        if not hasattr(self, "quick_peek"):
            self.quick_peek = QuickBankPeek(self)
            self.quick_peek.installEventFilter(self)

        self.quick_peek.update_data(self.bank_view.table)
        btn_pos = self.bank_btn.mapToGlobal(self.bank_btn.rect().topRight())
        self.quick_peek.move(btn_pos.x() + 10, btn_pos.y())
        self.quick_peek.show()
        self._peek_timer.stop()

    def _on_bank_hold_success(self):
        """Khi nhấn giữ đủ lâu, hiện cửa sổ xem nhanh"""
        if not hasattr(self, "quick_peek"):
            self.quick_peek = QuickBankPeek(self)

        self.quick_peek.update_data(self.bank_view.table)

        # Tính toán vị trí hiển thị ngay cạnh sidebar
        btn_pos = self.bank_btn.mapToGlobal(self.bank_btn.rect().topRight())
        self.quick_peek.move(btn_pos.x() + 10, btn_pos.y())
        self.quick_peek.show()

    def _switch_view(self, index):
        self.content_stack.setCurrentIndex(index)
        names = ["Bảng tính", "Kho hàng", "Sản phẩm", "Ngân hàng", "Lịch sử", "Cài đặt"]
        self.breadcrumb.setText(f"Trang chủ > {names[index]}")
        for i, btn in enumerate(self.nav_btns):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def _create_views(self):
        # Initialize error handler
        from utils.error_handler import ErrorHandler

        self.error_handler = ErrorHandler(self.logger)

        # Pass container to views
        self.calc_view = CalculationView(
            container=self.container, on_refresh_stock=self._refresh_stock
        )
        self.stock_view = StockView(on_refresh_calc=self._refresh_calc)
        self.product_view = ProductView(
            container=self.container, on_refresh_calc=self._refresh_calc
        )
        self.bank_view = BankView()  # View mới cho Ngân hàng
        self.history_view = HistoryView()
        self.settings_view = SettingsView(container=self.container)

        # Kết nối signals từ settings để cập nhật UI real-time
        self.settings_view.row_height_changed.connect(self._on_row_height_changed)
        self.settings_view.widget_height_changed.connect(self._on_widget_height_changed)

    def _start_notification_server(self):
        """Khởi chạy server ngầm để nhận thông báo"""
        # Get notification service from container
        notification_service = self.container.get("notification")
        if notification_service:
            notification_service.register_handler(self._show_notification)
            notification_service.start_server()
            self.logger.info("Notification server started successfully")
        else:
            # Fallback to old implementation if service not available
            config = self.container.get("config")
            if config:
                self.notif_thread = NotificationServer(
                    host=config.notification_host,
                    port=config.notification_port,
                    logger=self.logger,
                )
            else:
                self.notif_thread = NotificationServer(logger=self.logger)
            self.notif_thread.msg_received.connect(self._show_notification)
            self.notif_thread.start()

    def _show_notification(self, message):
        """Hiển thị thông báo an toàn (Safe UI Thread)"""
        # Emit signal to handle in main thread
        self.notification_received.emit(message)

    def _do_show_notification(self, message):
        now = datetime.now()
        if hasattr(self, "_last_msg_content") and self._last_msg_content == message:
            if (now - self._last_msg_time).total_seconds() < 2:
                return

        self._last_msg_content = message
        self._last_msg_time = now

        # Try to parse as JSON first (structured notification from Android)
        package_name = None
        content = message

        try:
            data = json.loads(message)
            if isinstance(data, dict):
                # Get package name from top level
                package_name = data.get("package", "")

                # Debug logging
                if hasattr(self, "logger"):
                    self.logger.info(f"Parsed JSON - package: {package_name}")

                # Get content - could be string or nested dict
                raw_content = data.get("content", message)

                # If content is a string, use it directly
                if isinstance(raw_content, str):
                    content = raw_content
                # If content is a dict, try to extract meaningful text
                elif isinstance(raw_content, dict):
                    content = raw_content.get("content", str(raw_content))
                else:
                    content = str(raw_content)
        except (json.JSONDecodeError, TypeError) as e:
            # Plain text message
            if hasattr(self, "logger"):
                self.logger.debug(f"Not JSON: {e}")
            pass

        # Determine source from package name
        source = (
            self._get_source_from_package(package_name) if package_name else "Phone"
        )

        # Debug logging
        if hasattr(self, "logger"):
            self.logger.info(
                f"Source determined: {source} (from package: {package_name})"
            )

        # Extract amount and transaction type, sender name
        amount, trans_type = self._extract_amount(content)
        sender_name = self._extract_sender_name(content)
        timestamp = now.strftime("%H:%M:%S")

        # Only show topbar notification if it has amount (real transaction)
        if amount:
            # HTML Escape để tránh lỗi ký tự đặc biệt phá hỏng giao diện
            safe_sender = html.escape(sender_name[:30]) if sender_name else ""
            safe_source = html.escape(source)
            safe_amount = html.escape(amount)

            # Format: Giờ | Tiền | Người chuyển
            if safe_sender:
                rich_text = f"<b style='font-size:15px; color:white;'>{timestamp}</b> | <b style='font-size:15px; color:white;'>{safe_amount}</b> | <span style='font-size:12px; color:#e1f5fe;'>{safe_sender}</span>"
            else:
                rich_text = f"<b style='font-size:15px; color:white;'>{timestamp}</b> | <b style='font-size:15px; color:white;'>{safe_amount}</b> | <span style='font-size:11px; color:#e1f5fe;'>{safe_source}</span>"

            self.notif_label.setText(rich_text)
            self.notif_box.show()

        if hasattr(self, "bank_view"):
            # Always add to raw logs
            self.bank_view.add_raw_log(timestamp, source, content)

            # Only add to transactions if it has amount (real bank transaction)
            if amount:
                self.bank_view.add_notif(
                    timestamp, source, amount, sender_name, content
                )
        else:
            if hasattr(self, "logger"):
                self.logger.warning(
                    "bank_view not initialized yet, notification not saved"
                )

    def _extract_amount(self, text):
        """Extract amount and detect transaction type (in/out)"""
        pattern = r"(?:\+|\-)?\d{1,3}(?:[.,]\d{3})+(?:\s?[đVNDvmd₫])?"
        matches = re.findall(pattern, text)
        if not matches:
            return None, None

        amount = matches[0]

        # Detect transaction type from keywords
        text_lower = text.lower()

        # Keywords for incoming money (tiền vào)
        incoming_keywords = [
            "nhận tiền",
            "nhan tien",
            "cộng tiền",
            "cong tien",
            "tiền vào",
            "tien vao",
            "+",
            "nạp tiền",
            "nap tien",
            "hoàn tiền",
            "hoan tien",
        ]

        # Keywords for outgoing money (tiền ra)
        outgoing_keywords = [
            "trừ tiền",
            "tru tien",
            "tiền ra",
            "tien ra",
            "chi tiêu",
            "chi tieu",
            "thanh toán",
            "thanh toan",
            "chuyển tiền",
            "chuyen tien",
            "rút tiền",
            "rut tien",
            "giao dịch: -",
            "giao dich: -",
            "-",
        ]

        # Check for explicit +/- in amount
        if amount.startswith("+"):
            return amount, "in"
        elif amount.startswith("-"):
            return amount, "out"

        # Check keywords
        for keyword in incoming_keywords:
            if keyword in text_lower:
                return f"+{amount}", "in"

        for keyword in outgoing_keywords:
            if keyword in text_lower:
                return f"-{amount}", "out"

        # Default: if no clear indicator, assume incoming (safer assumption)
        return f"+{amount}", "in"

    def _get_source_from_package(self, package_name):
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

    def _extract_sender_name(self, text):
        """Extract sender name from bank notification message"""
        # Clean text first: remove escape characters and normalize
        cleaned_text = text.replace("\\n", "\n").replace("\\", "").replace("\n", " ")

        # Common patterns for Vietnamese bank notifications
        # Use greedy matching [A-Z\s]+ to capture full names, then stop at boundaries
        patterns = [
            # Format: "ND Chuyen tien tu TEN" or "ND Nhan tien tu TEN"
            r"ND\s+Chuyen\s+tien\s+tu\s+([A-Z][A-Z\s]+?)(?:\s+\d|\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
            r"ND\s+Nhan\s+tien\s+tu\s+([A-Z][A-Z\s]+?)(?:\s+\d|\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
            # Format: "Chuyen tien tu TEN" or "Nhan tien tu TEN" (without ND prefix, with/without diacritics)
            r"Chuyen\s+tien\s+tu\s+([A-Z][A-Z\s]+?)(?:\s+\d|\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
            r"Nhan\s+tien\s+tu\s+([A-Z][A-Z\s]+?)(?:\s+\d|\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
            r"Nhận\s+tiền\s+từ\s+([A-Z][A-Z\s]+?)(?:\s+\d|\s*\.|,|\s+Ref|\s+MBVCB|\s+FT\d+|$)",
            # Format: "ND: TEN chuyen tien" or "ND: TEN nhan tien" (name comes first, then action)
            r"ND[:\s]+([A-Z][A-Z\s]+?)(?:\s+chuyen|\s+nhan|\s+Ref|\s+MBVCB|\s+FT\d+|\s*\.|,|\s+\d|$)",
            # Format: "Nhận tiền chuyển khoản từ TEN" (MoMo style)
            r"Nhận\s+tiền\s+chuyển\s+khoản\s+từ\s+([A-Z][A-Z\s]+?)(?:\s*:|,|\s+Số\s+tiền|$)",
            # Format: "CT DI:xxxxx TEN Chuyen tien" (VietinBank style)
            r"CT\s+DI:\d+\s+([A-Z][A-Z\s]+?)(?:\s+Chuyen|\s+chuyen|\s*;|$)",
        ]

        for pattern in patterns:
            match = re.search(pattern, cleaned_text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up: remove trailing reference codes only
                name = re.sub(r"\s*(Ref|MBVCB|FT\d+).*$", "", name, flags=re.IGNORECASE)
                # Remove trailing action words only if they appear at the end
                name = re.sub(
                    r"\s+(chuyen\s+tien|nhan\s+tien|chuyen\s+khoan|nhan\s+khoan)$",
                    "",
                    name,
                    flags=re.IGNORECASE,
                )
                # Remove trailing punctuation and whitespace
                name = re.sub(r"[,.\s]+$", "", name)
                name = name.strip()
                # Valid name should be at least 3 chars (to filter out "A", "AB")
                if len(name) >= 3:
                    return name[:50]  # Limit length

        return ""

    def _refresh_calc(self):
        if hasattr(self, "calc_view"):
            self.calc_view.refresh_table()

    def _refresh_stock(self):
        if hasattr(self, "stock_view"):
            self.stock_view.refresh_list()

    def _on_row_height_changed(self, height: int):
        """Cập nhật chiều cao row cho tất cả tables"""
        # Calculation view
        if hasattr(self, "calc_view"):
            self.calc_view.table.verticalHeader().setDefaultSectionSize(height)
            self.calc_view.prod_table.verticalHeader().setDefaultSectionSize(height)

        # Stock view
        if hasattr(self, "stock_view"):
            self.stock_view.table.verticalHeader().setDefaultSectionSize(height)

        # Product view
        if hasattr(self, "product_view"):
            self.product_view.table.verticalHeader().setDefaultSectionSize(height)

        # History view
        if hasattr(self, "history_view"):
            self.history_view.table.verticalHeader().setDefaultSectionSize(height)

        # Bank view
        if hasattr(self, "bank_view"):
            self.bank_view.table.verticalHeader().setDefaultSectionSize(height)

    def _on_widget_height_changed(self, height: int):
        """Cập nhật chiều cao widget - cần refresh lại views"""
        # Lưu giá trị mới
        if hasattr(self, "calc_view"):
            self.calc_view._widget_height = height
            self.calc_view.refresh_table()

        if hasattr(self, "stock_view"):
            self.stock_view._widget_height = height
            self.stock_view.refresh_list()

        if hasattr(self, "product_view"):
            self.product_view._widget_height = height
            self.product_view.refresh_list()

    def _apply_theme(self):
        self.setStyleSheet(AppTheme.get_stylesheet())


def main():
    import ctypes

    # Performance optimization for Windows
    try:
        myappid = "bangtinh.warehouse.app.2.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

        # Set process priority to above normal for better responsiveness
        import psutil

        p = psutil.Process()
        p.nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
    except:
        pass

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)

    # Load custom fonts from assets
    from PyQt6.QtGui import QFontDatabase

    fonts_dir = BASE_DIR / "assets" / "fonts"

    # Load Roboto fonts
    roboto_dir = fonts_dir / "Roboto"
    if roboto_dir.exists():
        for font_file in roboto_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))

    # Load Cabin fonts
    cabin_dir = fonts_dir / "Cabin-master" / "fonts" / "TTF"
    if cabin_dir.exists():
        for font_file in cabin_dir.glob("*.ttf"):
            QFontDatabase.addApplicationFont(str(font_file))

    # Set default application font to Roboto
    app.setFont(QFont("Roboto", 11))
    app.setApplicationVersion(APP_VERSION)

    icon_path = BASE_DIR / "assets" / "icon.png"
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        if not icon.isNull():
            app.setWindowIcon(icon)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # Initialize container with configuration
    from PyQt6.QtWidgets import QMessageBox

    from core.config import Config
    from core.container import Container
    from core.license import LicenseManager, LicenseValidator

    config = Config.from_env()

    # Validate configuration
    config_errors = config.validate()
    if config_errors:
        error_msg = "Configuration errors:\n" + "\n".join(config_errors)
        QMessageBox.critical(None, "Configuration Error", error_msg)
        sys.exit(1)

    container = Container(config)
    logger = container.get("logger")

    # Validate license at startup
    try:
        validator = LicenseValidator(logger=logger)
        license_manager = LicenseManager(validator, logger)

        if not license_manager.validate_startup_license(
            config.license_key, config.environment
        ):
            QMessageBox.critical(
                None,
                "License Error",
                "Invalid or expired license key.\n\n"
                "Please contact support to obtain a valid license.",
            )
            logger.error("Application startup blocked: Invalid license")
            sys.exit(1)

        # Store license manager in container for later use
        container.register_singleton("license_manager", license_manager)

    except Exception as e:
        logger.error(f"License validation error: {e}")
        if config.environment == "production":
            QMessageBox.critical(
                None, "License Error", f"Failed to validate license: {str(e)}"
            )
            sys.exit(1)

    # Create main window with injected container
    window = MainWindow(container=container)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
