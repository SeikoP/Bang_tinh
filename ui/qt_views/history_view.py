"""
History View - Lịch sử phiên làm việc
Modern Premium Design
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QDialog,
    QTextEdit,
    QMessageBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.qt_theme import AppColors
from database import HistoryRepository


class HistoryDetailDialog(QDialog):
    """Dialog chi tiết phiên"""

    def __init__(self, history, parent=None):
        super().__init__(parent)
        self.history = history
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle(f"Chi tiết: {self.history.shift_name or 'Phiên làm việc'}")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)

        # Info
        info = QHBoxLayout()
        info.setSpacing(20)

        info.addWidget(QLabel(f"📅 Ngày: <b>{self.history.session_date}</b>"))
        info.addWidget(QLabel(f"⏰ Ca: <b>{self.history.shift_name or 'N/A'}</b>"))

        total = QLabel(f"💰 Tổng: <b>{self.history.total_amount:,.0f} VNĐ</b>")
        total.setStyleSheet(
            f"""
            color: white;
            font-size: 15px;
            font-weight: 700;
            padding: 8px 16px;
            background: {AppColors.SUCCESS};
            border-radius: 6px;
        """
        )
        info.addWidget(total)

        info.addStretch()
        layout.addLayout(info)

        # Items table
        if self.history.items:
            table = QTableWidget()
            table.setColumnCount(5)
            table.setHorizontalHeaderLabels(
                ["Sản phẩm", "Giao ca", "Chốt ca", "Đã dùng", "Thành tiền"]
            )
            table.setRowCount(len(self.history.items))

            header = table.horizontalHeader()
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            for i in range(1, 5):
                header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
                table.setColumnWidth(i, 80)

            table.verticalHeader().setVisible(False)
            table.setAlternatingRowColors(True)

            for row, item in enumerate(self.history.items):
                table.setItem(row, 0, QTableWidgetItem(item.product_name))
                for col, val in enumerate(
                    [item.handover_qty, item.closing_qty, item.used_qty], 1
                ):
                    cell = QTableWidgetItem(str(val))
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    table.setItem(row, col, cell)

                amount = QTableWidgetItem(f"{item.amount:,.0f}")
                amount.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                amount.setForeground(QColor(AppColors.SUCCESS))
                table.setItem(row, 4, amount)

            layout.addWidget(table, 1)

        # Notes
        if self.history.notes:
            notes = QTextEdit()
            notes.setPlainText(self.history.notes)
            notes.setReadOnly(True)
            notes.setMaximumHeight(60)
            layout.addWidget(notes)

        # Close
        close_btn = QPushButton("Đóng")
        close_btn.setObjectName("secondary")
        close_btn.setMaximumWidth(120)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)


class HistoryView(QWidget):
    """View lịch sử"""

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)

        refresh_btn = QPushButton("🔄 Làm mới danh sách")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedWidth(180)
        refresh_btn.clicked.connect(self.refresh_list)
        toolbar.addWidget(refresh_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Table
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)

    def _setup_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["STT", "Ngày", "Ca", "Tổng tiền", "Ghi chú", "Thao tác"]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(5, 110)  # Tăng lên 110px cho 2 icon buttons

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)  # Tăng lên 56px

    def refresh_list(self):
        histories = HistoryRepository.get_all()
        self.table.setRowCount(len(histories))

        for row, h in enumerate(histories):
            self._set_cell(row, 0, str(row + 1), center=True)
            self._set_cell(row, 1, str(h.session_date), center=True)
            self._set_cell(row, 2, h.shift_name or "Không tên", bold=True)
            self._set_cell(
                row,
                3,
                f"{h.total_amount:,.0f}",
                center=True,
                fg=AppColors.SUCCESS,
                bold=True,
            )

            notes_text = (
                h.notes[:25] + "..."
                if h.notes and len(h.notes) > 25
                else (h.notes or "—")
            )
            self._set_cell(row, 4, notes_text, fg=AppColors.TEXT_SECONDARY)

            actions = QWidget()

            actions_v_layout = QVBoxLayout(actions)
            actions_v_layout.setContentsMargins(0, 0, 0, 0)
            actions_v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            actions_h_widget = QWidget()
            actions_layout = QHBoxLayout(actions_h_widget)
            actions_layout.setContentsMargins(8, 0, 8, 0)
            actions_layout.setSpacing(8)

            view_btn = QPushButton("⊙")
            view_btn.setObjectName("iconBtn")
            view_btn.setFixedSize(28, 28)  # Thu nhỏ xuống
            view_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            view_btn.clicked.connect(lambda _, hid=h.id: self._view_detail(hid))
            actions_layout.addWidget(view_btn)

            del_btn = QPushButton("×")
            del_btn.setObjectName("iconBtn")
            del_btn.setFixedSize(28, 28)  # Thu nhỏ xuống
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, hid=h.id: self._delete_history(hid))
            actions_layout.addWidget(del_btn)

            actions_v_layout.addWidget(actions_h_widget)
            self.table.setCellWidget(row, 5, actions)

    def _set_cell(self, row, col, text, center=False, bold=False, bg=None, fg=None):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if center:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
        else:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            )
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        if bg:
            item.setBackground(QColor(bg))
        if fg:
            item.setForeground(QColor(fg))
        self.table.setItem(row, col, item)

    def _view_detail(self, history_id):
        history = HistoryRepository.get_by_id(history_id)
        if history:
            dialog = HistoryDetailDialog(history, self)
            dialog.exec()

    def _delete_history(self, history_id):
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Xóa phiên làm việc này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            HistoryRepository.delete(history_id)
            self.refresh_list()
