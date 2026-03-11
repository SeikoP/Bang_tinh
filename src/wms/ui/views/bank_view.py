"""
Bank View - Transaction history and raw logs
"""

import html
import logging
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QComboBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem,
    QTabWidget, QVBoxLayout, QWidget
)

from ...database.repositories import BankRepository
from ..theme import AppColors


class BankView(QWidget):
    """View hiển thị lịch sử thông báo ngân hàng với sub-tabs"""

    def __init__(self):
        super().__init__()
        self._data_loaded = False
        self._setup_ui()

    def showEvent(self, event):
        """Lazy-load history on first show"""
        super().showEvent(event)
        if not self._data_loaded:
            self._data_loaded = True
            self.load_history()

    def _setup_ui(self):
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
        
        # Total amount display
        self.total_label = QLabel("Tổng: 0 VND")
        self.total_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: {AppColors.SUCCESS};
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(16, 185, 129, 0.1), stop:1 rgba(16, 185, 129, 0.05));
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid rgba(16, 185, 129, 0.2);
        """)
        header_layout.addWidget(self.total_label)
        
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
        self._setup_transactions_tab()

        # Tab 2: Raw Logs
        self._setup_logs_tab()

        # Add tabs
        self.tabs.addTab(self.transactions_widget, "Giao dịch")
        self.tabs.addTab(self.logs_widget, "Raw Logs")

        layout.addWidget(self.tabs)

    def _setup_transactions_tab(self):
        self.transactions_widget = QWidget()
        trans_layout = QVBoxLayout(self.transactions_widget)
        trans_layout.setContentsMargins(10, 10, 10, 10)

        # Filter and clear button row
        filter_layout = QHBoxLayout()

        # Source filter
        filter_label = QLabel("Lọc theo nguồn:")
        filter_label.setStyleSheet("font-weight: bold;")
        filter_layout.addWidget(filter_label)

        self.source_filter = QComboBox()
        self.source_filter.addItems([
            "Tất cả", "MoMo", "VietinBank", "Vietcombank", "MB Bank",
            "BIDV", "ACB", "TPBank", "Techcombank", "VNPay",
        ])
        self.source_filter.setFixedWidth(150)
        self.source_filter.currentTextChanged.connect(self.apply_filter)
        filter_layout.addWidget(self.source_filter)

        filter_layout.addStretch()

        self.clear_trans_btn = QPushButton("Xóa lịch sử")
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
        self.table.setColumnWidth(3, 180)
        self.table.setColumnWidth(5, 50)

        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45)
        self.table.verticalHeader().setMinimumSectionSize(35)
        trans_layout.addWidget(self.table)

    def _setup_logs_tab(self):
        self.logs_widget = QWidget()
        logs_layout = QVBoxLayout(self.logs_widget)
        logs_layout.setContentsMargins(10, 10, 10, 10)

        # Clear button for logs
        log_btn_layout = QHBoxLayout()
        log_btn_layout.addStretch()
        self.clear_logs_btn = QPushButton("Xóa logs")
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
        self.logs_table.verticalHeader().setMinimumSectionSize(30)
        logs_layout.addWidget(self.logs_table)

    def load_history(self):
        """Tải lại lịch sử từ database"""
        notifs = BankRepository.get_all()
        for n in reversed(notifs):
            self._add_row_ui(
                n.id, n.time_str, n.source, n.amount, n.sender_name or "", n.content
            )
        self._update_total()
    
    def _update_total(self):
        """Cập nhật tổng tiền từ tất cả giao dịch"""
        total = 0.0
        for row in range(self.table.rowCount()):
            # Skip hidden rows (filtered out)
            if self.table.isRowHidden(row):
                continue
                
            amt_item = self.table.item(row, 2)
            if amt_item:
                amt_text = amt_item.text().strip()
                if amt_text and amt_text != "---":
                    # Parse amount: "+5,000,000 VND" -> 5000000
                    try:
                        # Remove +/-, VND, spaces, commas
                        clean = amt_text.replace("+", "").replace("-", "").replace("VND", "").replace(",", "").replace(" ", "").strip()
                        value = float(clean)
                        # Add or subtract based on sign
                        if amt_text.startswith("-"):
                            total -= value
                        else:
                            total += value
                    except:
                        pass
        
        # Format total with thousand separators
        formatted = f"{total:,.0f}".replace(",", ".")
        self.total_label.setText(f"Tổng: {formatted} VND")
        
        # Change color based on positive/negative
        if total >= 0:
            self.total_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: 700;
                color: {AppColors.SUCCESS};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(16, 185, 129, 0.1), stop:1 rgba(16, 185, 129, 0.05));
                padding: 8px 16px;
                border-radius: 8px;
                border: 1px solid rgba(16, 185, 129, 0.2);
            """)
        else:
            self.total_label.setStyleSheet(f"""
                font-size: 18px;
                font-weight: 700;
                color: {AppColors.ERROR};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(239, 68, 68, 0.1), stop:1 rgba(239, 68, 68, 0.05));
                padding: 8px 16px;
                border-radius: 8px;
                border: 1px solid rgba(239, 68, 68, 0.2);
            """)

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
        
        # Update total after filter
        self._update_total()

    def add_notif(self, time_str, source, amount, sender_name, raw_message):
        try:
            # 1. Lưu vào database trước
            new_id = BankRepository.add(
                time_str, source, amount, raw_message, sender_name
            )

            # 2. Hiển thị lên UI (chỉ khi view đã được load lần đầu)
            if self._data_loaded:
                self._add_row_ui(new_id, time_str, source, amount, sender_name, raw_message)
                self._update_total()
        except Exception as e:
            # Log error silently
            logging.error(f"Error in add_notif: {e}")

    def add_raw_log(self, time_str, package, raw_message):
        """Add to raw logs tab only"""
        self._add_log_row(time_str, package, raw_message)

    def add_system_log(self, message):
        """Add system log (Ping/Connection status) to raw logs"""
        from datetime import datetime
        time_str = datetime.now().strftime("%H:%M:%S")
        
        row = 0
        self.logs_table.insertRow(row)

        # Timestamp
        time_item = QTableWidgetItem(time_str)
        time_item.setFont(QFont("Roboto", 9))
        self.logs_table.setItem(row, 0, time_item)

        # System Label
        pkg_item = QTableWidgetItem("System")
        pkg_item.setFont(QFont("Roboto", 9, QFont.Weight.Bold))
        pkg_item.setForeground(QColor(AppColors.INFO))
        self.logs_table.setItem(row, 1, pkg_item)

        # Message
        msg_item = QTableWidgetItem(message)
        msg_item.setFont(QFont("Segoe UI", 9))
        msg_item.setForeground(QColor(AppColors.TEXT))
        self.logs_table.setItem(row, 2, msg_item)
        
        # Limit logs
        while self.logs_table.rowCount() > 100:
            self.logs_table.removeRow(self.logs_table.rowCount() - 1)

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
            amt_item.setForeground(QColor(AppColors.SUCCESS))
        elif amount and amount.startswith("-"):
            amt_item.setForeground(QColor(AppColors.ERROR))
        else:
            amt_item.setForeground(QColor(AppColors.SUCCESS))

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

        # Nút xóa từng dòng
        del_container = QWidget()
        del_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        del_layout = QHBoxLayout(del_container)
        del_layout.setContentsMargins(0, 0, 0, 0)
        del_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        del_btn = QPushButton("X")
        del_btn.setFixedSize(30, 30)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
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

    def _delete_row(self, db_id):
        """Xóa một dòng cụ thể dựa trên ID database"""
        # Tìm row index hiện tại
        target_row = -1
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item.data(Qt.ItemDataRole.UserRole) == db_id:
                target_row = r
                break

        if target_row != -1:
            BankRepository.delete(db_id)
            self.table.removeRow(target_row)
            self._update_total()

    def clear_history(self):
        """Xóa sạch bảng lịch sử"""
        BankRepository.clear_all()
        self.table.setRowCount(0)
        self._update_total()

    def cleanup(self):
        """Cleanup resources to prevent memory leaks"""
        # Clear tables
        self.table.setRowCount(0)
        self.logs_table.setRowCount(0)
        
        # Disconnect signals
        try:
            self.source_filter.currentTextChanged.disconnect()
            self.clear_trans_btn.clicked.disconnect()
            self.clear_logs_btn.clicked.disconnect()
        except:
            pass
