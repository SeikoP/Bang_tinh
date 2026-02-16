"""
Quick Bank Peek Widget - Fast transaction preview
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QHeaderView, QLabel,
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QVBoxLayout)

from ui.qt_theme import AppColors


class QuickBankPeek(QFrame):
    """Cửa sổ hiện nhanh lịch sử giao dịch khi nhấn giữ nút Ngân hàng"""

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip)
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
        self.table.verticalHeader().setDefaultSectionSize(40)
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

    def cleanup(self):
        """Cleanup resources"""
        self.table.setRowCount(0)
