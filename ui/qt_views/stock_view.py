from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget)

from database import SessionRepository, StockChangeLogRepository
from services import CalculatorService
from ui.qt_theme import AppColors


class StockView(QWidget):
    """View kho hàng - Buttons tách riêng dễ nhấn"""

    def __init__(self, on_refresh_calc=None):
        super().__init__()
        self.on_refresh_calc = on_refresh_calc
        self.calc_service = CalculatorService()
        self._setup_ui()
        self.refresh_list()
        self.refresh_history()

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 20)
        main_layout.setSpacing(16)

        # Left: Table
        left_widget = QWidget()
        layout = QVBoxLayout(left_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        # Toolbar
        self.toolbar = QFrame()
        self.toolbar.setStyleSheet("background: transparent;")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        refresh_btn = QPushButton("🔄 Làm mới dữ liệu")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedWidth(200)
        refresh_btn.clicked.connect(self.refresh_list)
        toolbar_layout.addWidget(refresh_btn)

        toolbar_layout.addStretch()

        layout.addWidget(self.toolbar)

        # Table
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)

        main_layout.addWidget(left_widget, 3)

        # Right: History panel
        history_panel = QFrame()
        history_panel.setObjectName("card")
        history_panel.setFixedWidth(300)
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(16, 16, 16, 16)
        history_layout.setSpacing(12)

        # Header
        header_layout = QHBoxLayout()
        history_title = QLabel("📋 Lịch sử thay đổi")
        history_title.setStyleSheet(
            f"font-weight: 700; font-size: 15px; color: {AppColors.TEXT};"
        )
        header_layout.addWidget(history_title)
        header_layout.addStretch()

        clear_btn = QPushButton("🗑️")
        clear_btn.setObjectName("iconBtn")
        clear_btn.setFixedSize(28, 28)
        clear_btn.setToolTip("Xóa lịch sử")
        clear_btn.clicked.connect(self._clear_history)
        header_layout.addWidget(clear_btn)

        history_layout.addLayout(header_layout)

        # History list
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(4)
        self.history_table.setHorizontalHeaderLabels(
            ["Sản phẩm", "Thay đổi", "Thời gian", ""]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.history_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.history_table.setColumnWidth(1, 60)
        self.history_table.setColumnWidth(2, 60)
        self.history_table.setColumnWidth(3, 32)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.verticalHeader().setDefaultSectionSize(40)
        self.history_table.setStyleSheet("font-size: 11px;")
        history_layout.addWidget(self.history_table, 1)

        main_layout.addWidget(history_panel, 1)

    def _setup_table(self):
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["STT", "Tên sản phẩm", "Đơn vị", "Quy đổi", "SL Lớn", "SL Lẻ", "Tổng"]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in [2, 3, 4, 5, 6]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(2, 85)
        self.table.setColumnWidth(3, 85)
        self.table.setColumnWidth(4, 140)
        self.table.setColumnWidth(5, 140)
        self.table.setColumnWidth(6, 120)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(58)

    def _set_cell(self, row, col, text, center=True, bold=False, bg=None, fg=None):
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

    def refresh_list(self):
        sessions = SessionRepository.get_all()
        self.table.setRowCount(len(sessions))

        # Helper function - Buttons trong box, cao bằng box
        def create_stepper(value, max_val, on_change):
            wrapper = QWidget()
            w_layout = QHBoxLayout(wrapper)
            w_layout.setContentsMargins(0, 0, 0, 0)
            w_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            w_layout.setSpacing(0)

            # Container box
            container = QFrame()
            container.setFixedHeight(36)
            container.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid {AppColors.BORDER};
                    border-radius: 6px;
                    background: white;
                }}
            """)

            box_layout = QHBoxLayout(container)
            box_layout.setContentsMargins(0, 0, 0, 0)
            box_layout.setSpacing(0)

            # Nút Trừ
            btn_sub = QPushButton("▼")
            btn_sub.setFixedSize(40, 40)
            btn_sub.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_sub.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    border-right: 1px solid {AppColors.BORDER};
                    border-top-left-radius: 6px;
                    border-bottom-left-radius: 6px;
                    background: #fef2f2;
                    color: #dc2626;
                    font-weight: 700;
                    font-size: 16px;
                }}
                QPushButton:hover {{ 
                    background-color: #fee2e2; 
                    color: #b91c1c;
                }}
                QPushButton:pressed {{
                    background-color: #ef4444;
                    color: white;
                }}
            """)
            btn_sub.clicked.connect(lambda: on_change(value - 1))

            # Ô hiển thị số - Chỉ đọc
            display = QLineEdit(str(value))
            display.setReadOnly(True)
            display.setFixedWidth(60)
            display.setAlignment(Qt.AlignmentFlag.AlignCenter)
            display.setStyleSheet(f"""
                QLineEdit {{
                    border: none;
                    background: white;
                    color: {AppColors.TEXT};
                    font-weight: 700;
                    font-size: 16px;
                    font-family: 'Roboto', 'Segoe UI', sans-serif;
                }}
            """)

            # Nút Cộng
            btn_add = QPushButton("▲")
            btn_add.setFixedSize(40, 40)
            btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_add.setStyleSheet(f"""
                QPushButton {{
                    border: none;
                    border-left: 1px solid {AppColors.BORDER};
                    border-top-right-radius: 6px;
                    border-bottom-right-radius: 6px;
                    background: #f0fdf4;
                    color: #16a34a;
                    font-weight: 700;
                    font-size: 16px;
                }}
                QPushButton:hover {{ 
                    background-color: #dcfce7; 
                    color: #15803d;
                }}
                QPushButton:pressed {{
                    background-color: #10b981;
                    color: white;
                }}
            """)
            btn_add.clicked.connect(lambda: on_change(value + 1))

            box_layout.addWidget(btn_sub)
            box_layout.addWidget(display)
            box_layout.addWidget(btn_add)

            w_layout.addWidget(container)
            return wrapper

        for row, s in enumerate(sessions):
            p = s.product
            l_qty = s.closing_qty // p.conversion
            s_qty_val = s.closing_qty % p.conversion

            has_data = s.closing_qty > 0
            row_bg = "rgba(37, 99, 235, 0.05)" if has_data else None

            self._set_cell(row, 0, str(row + 1), fg=AppColors.TEXT, bg=row_bg)
            self._set_cell(
                row, 1, p.name, center=False, bold=True, fg=AppColors.TEXT, bg=row_bg
            )

            # Unit
            u_item = QTableWidgetItem(p.large_unit)
            u_item.setFlags(u_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            u_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            u_item.setBackground(QColor(row_bg if has_data else "transparent"))
            u_item.setForeground(QColor(AppColors.PRIMARY))
            font = u_item.font()
            font.setBold(True)
            u_item.setFont(font)
            self.table.setItem(row, 2, u_item)

            self._set_cell(row, 3, str(p.conversion), fg=AppColors.TEXT, bg=row_bg)

            # --- Cột SL Lớn ---
            max_large = s.handover_qty // p.conversion
            w_large = create_stepper(
                l_qty,
                max_large,
                lambda v, pid=p.id, c=p.conversion, sq=s_qty_val: self._on_large_change(
                    pid, v, c, sq
                ),
            )
            self.table.setCellWidget(row, 4, w_large)

            # --- Cột SL Lẻ ---
            max_small = p.conversion - 1
            w_small = create_stepper(
                s_qty_val,
                max_small,
                lambda v, pid=p.id, c=p.conversion, lq=l_qty: self._on_small_change(
                    pid, lq, v, c
                ),
            )
            self.table.setCellWidget(row, 5, w_small)

            # Total - Text màu nổi bật
            t_text = str(s.closing_qty)
            if has_data:
                fg = "white"
                bg = AppColors.PRIMARY
            else:
                fg = AppColors.PRIMARY  # Màu xanh primary để nổi bật
                bg = "#e0e7ff"  # Background xanh nhạt
            self._set_cell(row, 6, t_text, center=True, bold=True, fg=fg, bg=bg)

    def _on_large_change(self, pid, new_large, conv, old_small):
        sessions = SessionRepository.get_all()
        sess = next((s for s in sessions if s.product.id == pid), None)
        if not sess:
            return
        old_qty = sess.closing_qty
        
        # Đảm bảo new_large không âm
        new_large = max(0, new_large)
            
        new_c = new_large * conv + old_small
        
        # Đảm bảo không âm và không vượt quá handover_qty
        new_c = max(0, min(new_c, sess.handover_qty))
        SessionRepository.update_qty(pid, sess.handover_qty, new_c)

        # Log thay đổi
        if old_qty != new_c:
            StockChangeLogRepository.add_log(pid, sess.product.name, old_qty, new_c)

        self.refresh_list()
        self.refresh_history()
        if self.on_refresh_calc:
            self.on_refresh_calc()

    def _on_small_change(self, pid, old_large, new_small, conv):
        sessions = SessionRepository.get_all()
        sess = next((s for s in sessions if s.product.id == pid), None)
        if not sess:
            return
        old_qty = sess.closing_qty
        
        # Nếu giảm xuống dưới 0, tự động giảm SL Lớn
        if new_small < 0 and old_large > 0:
            new_large = old_large - 1
            new_small = conv - 1
            new_c = new_large * conv + new_small
        # Nếu tăng vượt quá max, tự động tăng SL Lớn
        elif new_small >= conv:
            new_large = old_large + 1
            new_small = 0
            new_c = new_large * conv + new_small
        else:
            new_c = old_large * conv + new_small
        
        # Đảm bảo không âm và không vượt quá handover_qty
        new_c = max(0, min(new_c, sess.handover_qty))
        SessionRepository.update_qty(pid, sess.handover_qty, new_c)

        # Log thay đổi
        if old_qty != new_c:
            StockChangeLogRepository.add_log(pid, sess.product.name, old_qty, new_c)

        self.refresh_list()
        self.refresh_history()
        if self.on_refresh_calc:
            self.on_refresh_calc()

    def refresh_history(self):
        """Refresh bảng lịch sử"""
        logs = StockChangeLogRepository.get_all(50)
        self.history_table.setRowCount(len(logs))

        for row, log in enumerate(logs):
            # Product name
            self._set_history_cell(row, 0, log.product_name)

            # Change
            change = log.new_qty - log.old_qty
            change_text = f"{change:+d}"
            change_color = AppColors.SUCCESS if change > 0 else AppColors.ERROR
            self._set_history_cell(
                row, 1, change_text, center=True, fg=change_color, bold=True
            )

            # Time
            time_str = (
                log.changed_at.strftime("%H:%M")
                if isinstance(log.changed_at, datetime)
                else str(log.changed_at)[-8:-3]
            )
            self._set_history_cell(
                row, 2, time_str, center=True, fg=AppColors.TEXT_SECONDARY
            )

            # Delete button
            del_btn = QPushButton("×")
            del_btn.setObjectName("iconBtn")
            del_btn.setFixedSize(24, 24)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    color: {AppColors.TEXT_SECONDARY};
                    border: none;
                    font-size: 18px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background: {AppColors.ERROR};
                    color: white;
                    border-radius: 4px;
                }}
            """)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.clicked.connect(lambda _, log_id=log.id: self._delete_log(log_id))

            # Container để căn giữa button
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(4, 0, 4, 0)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(del_btn)

            self.history_table.setCellWidget(row, 3, container)

    def _set_history_cell(self, row, col, text, center=False, bold=False, fg=None):
        from PyQt6.QtWidgets import QTableWidgetItem

        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if center:
            item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        if fg:
            item.setForeground(QColor(fg))
        self.history_table.setItem(row, col, item)

    def _delete_log(self, log_id: int):
        """Xóa một log cụ thể"""
        StockChangeLogRepository.delete(log_id)
        self.refresh_history()

    def _clear_history(self):

        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Xóa toàn bộ lịch sử thay đổi?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            StockChangeLogRepository.clear_all()
            self.refresh_history()
