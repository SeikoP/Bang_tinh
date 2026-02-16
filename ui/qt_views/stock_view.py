"""
Stock View - Quản lý kho hàng
Modern Premium Design with Real-time History
"""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QScrollArea,
                             QTableWidget, QTableWidgetItem, QVBoxLayout,
                             QWidget)

from database import SessionRepository, StockChangeLogRepository
from services import CalculatorService
from ui.qt_theme import AppColors


class StockStepper(QFrame):
    """Modern Stepper Component for adjusting quantities"""

    value_changed = pyqtSignal(int)

    def __init__(self, value: int, label: str = "", parent=None):
        super().__init__(parent)
        self.value = value
        self.label = label
        self._setup_ui()

    def _setup_ui(self):
        self.setFixedHeight(42)
        self.setObjectName("stepper")
        self.setStyleSheet(f"""
            QFrame#stepper {{
                background: white;
                border: 2px solid {AppColors.BORDER};
                border-radius: 8px;
            }}
            QFrame#stepper:hover {{
                border-color: {AppColors.PRIMARY};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Minus button
        self.minus_btn = QPushButton("−")
        self.minus_btn.setFixedSize(38, 38)
        self.minus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.minus_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-right: 1px solid {AppColors.BORDER};
                background: #F8FAFC;
                color: {AppColors.ERROR};
                font-size: 20px;
                font-weight: bold;
                border-top-left-radius: 6px;
                border-bottom-left-radius: 6px;
            }}
            QPushButton:hover {{ background: #FEE2E2; }}
            QPushButton:pressed {{ background: {AppColors.ERROR}; color: white; }}
        """)
        self.minus_btn.clicked.connect(lambda: self.adjust_value(-1))
        layout.addWidget(self.minus_btn)

        # Value display
        self.display = QLabel(str(self.value))
        self.display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.display.setStyleSheet(f"""
            font-weight: 800;
            font-size: 15px;
            color: {AppColors.TEXT};
            min-width: 45px;
            background: transparent;
        """)
        layout.addWidget(self.display, 1)

        # Plus button
        self.plus_btn = QPushButton("+")
        self.plus_btn.setFixedSize(38, 38)
        self.plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.plus_btn.setStyleSheet(f"""
            QPushButton {{
                border: none;
                border-left: 1px solid {AppColors.BORDER};
                background: #F8FAFC;
                color: {AppColors.SUCCESS};
                font-size: 18px;
                font-weight: bold;
                border-top-right-radius: 6px;
                border-bottom-right-radius: 6px;
            }}
            QPushButton:hover {{ background: #DCFCE7; }}
            QPushButton:pressed {{ background: {AppColors.SUCCESS}; color: white; }}
        """)
        self.plus_btn.clicked.connect(lambda: self.adjust_value(1))
        layout.addWidget(self.plus_btn)

    def adjust_value(self, delta: int):
        self.value += delta
        self.display.setText(str(self.value))
        self.value_changed.emit(self.value)

    def set_value(self, val: int):
        self.value = val
        self.display.setText(str(self.value))


class StockView(QWidget):
    """View Kho Hàng - Tối ưu cho việc kiểm kê nhanh"""

    def __init__(self, on_refresh_calc=None):
        super().__init__()
        self.on_refresh_calc = on_refresh_calc
        self.calc_service = CalculatorService()
        self._setup_ui()
        self.refresh_data()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 20)
        main_layout.setSpacing(20)

        # Header Section: Stats & Search
        header_panel = QHBoxLayout()

        # Stats summary
        stats_frame = QFrame()
        stats_frame.setObjectName("stats_card")
        stats_frame.setStyleSheet("""
            QFrame#stats_card {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #1E293B, stop:1 #334155);
                border-radius: 12px;
                min-width: 300px;
            }
        """)
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(20, 12, 20, 12)

        self.total_products_label = QLabel("📦 Sản phẩm: 0")
        self.total_products_label.setStyleSheet(
            "color: white; font-weight: 700; font-size: 14px;"
        )
        stats_layout.addWidget(self.total_products_label)

        stats_layout.addSpacing(20)

        self.total_stock_label = QLabel("📥 Tổng tồn: 0")
        self.total_stock_label.setStyleSheet(
            "color: #94A3B8; font-weight: 600; font-size: 14px;"
        )
        stats_layout.addWidget(self.total_stock_label)

        header_panel.addWidget(stats_frame)

        header_panel.addStretch()

        # Search & Refresh
        search_layout = QHBoxLayout()
        search_layout.setSpacing(10)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm sản phẩm...")
        self.search_input.setFixedWidth(250)
        self.search_input.setFixedHeight(42)
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid {AppColors.BORDER};
                border-radius: 10px;
                padding: 0 15px;
                background: white;
                font-size: 14px;
            }}
            QLineEdit:focus {{ border-color: {AppColors.PRIMARY}; }}
        """)
        self.search_input.textChanged.connect(self.filter_table)
        search_layout.addWidget(self.search_input)

        refresh_btn = QPushButton("🔄 Làm mới")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedHeight(42)
        refresh_btn.setFixedWidth(120)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.clicked.connect(self.refresh_data)
        search_layout.addWidget(refresh_btn)

        header_panel.addLayout(search_layout)

        main_layout.addLayout(header_panel)

        # Content Section: Table & History
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)

        # Left: Main Stock Table
        table_container = QWidget()
        table_v_layout = QVBoxLayout(table_container)
        table_v_layout.setContentsMargins(0, 0, 0, 0)

        self.table = QTableWidget()
        self._setup_main_table()
        table_v_layout.addWidget(self.table)

        content_layout.addWidget(table_container, 3)

        # Right: History panel
        history_panel = QFrame()
        history_panel.setObjectName("history_card")
        history_panel.setFixedWidth(320)
        history_panel.setStyleSheet(f"""
            QFrame#history_card {{
                background: #F8FAFC;
                border: 1px solid {AppColors.BORDER};
                border-radius: 12px;
            }}
        """)
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(16, 16, 16, 16)

        h_header = QHBoxLayout()
        h_title = QLabel("🕒 Lịch sử kiểm kho")
        h_title.setStyleSheet(
            f"font-weight: 800; font-size: 15px; color: {AppColors.TEXT};"
        )
        h_header.addWidget(h_title)
        h_header.addStretch()

        clear_btn = QPushButton("🗑️")
        clear_btn.setFixedSize(30, 30)
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setToolTip("Xóa trắng lịch sử")
        clear_btn.setStyleSheet("""
            QPushButton { border: none; background: transparent; font-size: 16px; border-radius: 15px; }
            QPushButton:hover { background: #fee2e2; }
        """)
        clear_btn.clicked.connect(self._clear_history)
        h_header.addWidget(clear_btn)
        history_layout.addLayout(h_header)

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.history_scroll.setStyleSheet("background: transparent;")

        self.history_content = QWidget()
        self.history_content.setStyleSheet("background: transparent;")
        self.history_list_layout = QVBoxLayout(self.history_content)
        self.history_list_layout.setContentsMargins(0, 5, 0, 5)
        self.history_list_layout.setSpacing(8)
        self.history_list_layout.addStretch()

        self.history_scroll.setWidget(self.history_content)
        history_layout.addWidget(self.history_scroll)

        content_layout.addWidget(history_panel, 1)

        main_layout.addLayout(content_layout)

    def _setup_main_table(self):
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "STT",
                "Sản phẩm",
                "Đơn vị",
                "Quy đổi",
                "SỐ LƯỢNG LỚN",
                "SỐ LƯỢNG LẺ",
                "TỔNG TỒN",
            ]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in [0, 2, 3, 4, 5, 6]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 160)
        self.table.setColumnWidth(5, 160)
        self.table.setColumnWidth(6, 120)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60)

        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {AppColors.BORDER};
                border-radius: 8px;
                gridline-color: rgba(0,0,0,0.05);
                font-size: 13px;
                background: white;
            }}
            QHeaderView::section {{
                background: #F1F5F9;
                color: {AppColors.TEXT_SECONDARY};
                font-weight: 700;
                font-size: 11px;
                padding: 10px;
                border: none;
                border-bottom: 2px solid {AppColors.BORDER};
            }}
        """)

    def refresh_data(self):
        self.refresh_list()
        self.refresh_history()

    def filter_table(self):
        query = self.search_input.text().lower().strip()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            if item:
                self.table.setRowHidden(row, query not in item.text().lower())

    def refresh_list(self):
        sessions = SessionRepository.get_all()
        self.table.setRowCount(len(sessions))

        total_qty = 0
        for row, s in enumerate(sessions):
            p = s.product
            total_qty += s.closing_qty
            l_qty = s.closing_qty // p.conversion
            s_qty = s.closing_qty % p.conversion

            # STT
            stt = QTableWidgetItem(str(row + 1))
            stt.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, stt)

            # Name
            name = QTableWidgetItem(p.name)
            name.setFont(QFont("", -1, QFont.Weight.Bold))
            self.table.setItem(row, 1, name)

            # Unit
            unit = QTableWidgetItem(p.large_unit)
            unit.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            unit.setForeground(QColor(AppColors.PRIMARY))
            self.table.setItem(row, 2, unit)

            # Conversion
            conv = QTableWidgetItem(str(p.conversion))
            conv.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 3, conv)

            # Stepper Large
            stepper_l = StockStepper(l_qty)
            stepper_l.value_changed.connect(
                lambda v, pid=p.id, c=p.conversion, sq=s_qty: self._on_qty_change(
                    pid, v, sq, c
                )
            )
            self.table.setCellWidget(row, 4, self._wrap_widget(stepper_l))

            # Stepper Small
            stepper_s = StockStepper(s_qty)
            stepper_s.value_changed.connect(
                lambda v, pid=p.id, lq=l_qty, c=p.conversion: self._on_qty_change(
                    pid, lq, v, c
                )
            )
            self.table.setCellWidget(row, 5, self._wrap_widget(stepper_s))

            # Total: Use true badge widget for visibility
            total = QTableWidgetItem(str(s.closing_qty))
            total.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if s.closing_qty > 0:
                self.table.setCellWidget(
                    row, 6, self._create_badge(str(s.closing_qty), AppColors.PRIMARY)
                )
                total.setForeground(QColor("transparent"))
            else:
                total.setForeground(QColor(AppColors.TEXT_SECONDARY))
            self.table.setItem(row, 6, total)

        self.total_products_label.setText(f"📦 Sản phẩm: {len(sessions)}")
        self.total_stock_label.setText(f"📥 Tổng tồn: {total_qty:,}")

    def _wrap_widget(self, widget):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(widget)
        return container

    def _on_qty_change(self, pid: int, large: int, small: int, conv: int):
        sessions = SessionRepository.get_all()
        s = next((x for x in sessions if x.product.id == pid), None)
        if not s:
            return

        old_val = s.closing_qty

        # Calculate new total value allowing for units borrowing
        raw_new_val = (large * conv) + small

        # Logic: If small went negative (-1), it's handled by (large*conv) - 1
        # BUT we must clamp the TOTAL to 0 and handover
        new_val = max(0, min(raw_new_val, s.handover_qty))

        if old_val != new_val:
            SessionRepository.update_qty(pid, s.handover_qty, new_val)
            StockChangeLogRepository.add_log(pid, s.product.name, old_val, new_val)
            self.refresh_data()
            if self.on_refresh_calc:
                self.on_refresh_calc()

    def refresh_history(self):
        """Build a modern scrollable history list"""
        # Clear existing logs
        while self.history_list_layout.count() > 1:
            item = self.history_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        logs = StockChangeLogRepository.get_all(30)
        for log in logs:
            card = QFrame()
            card.setStyleSheet(f"""
                QFrame {{
                    background: white;
                    border: 1px solid {AppColors.BORDER};
                    border-radius: 8px;
                    padding: 4px;
                }}
                QFrame:hover {{ border-color: {AppColors.PRIMARY}; }}
            """)
            l = QVBoxLayout(card)
            l.setSpacing(4)

            top = QHBoxLayout()
            name = QLabel(log.product_name)
            name.setStyleSheet("font-weight: 700; color: #334155; font-size: 13px;")
            top.addWidget(name)
            top.addStretch()

            diff = log.new_qty - log.old_qty
            diff_label = QLabel(f"{diff:+d}")
            color = AppColors.SUCCESS if diff > 0 else AppColors.ERROR
            diff_label.setStyleSheet(f"font-weight: 900; color: {color};")
            top.addWidget(diff_label)
            l.addLayout(top)

            bottom = QHBoxLayout()
            time_str = (
                log.changed_at.strftime("%H:%M:%S")
                if isinstance(log.changed_at, datetime)
                else str(log.changed_at)[-8:]
            )
            time_lbl = QLabel(time_str)
            time_lbl.setStyleSheet(
                f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px;"
            )
            bottom.addWidget(time_lbl)
            bottom.addStretch()

            l.addLayout(bottom)
            self.history_list_layout.insertWidget(0, card)

    def _create_badge(self, text, bg_color):
        container = QWidget()
        l = QHBoxLayout(container)
        l.setContentsMargins(4, 6, 4, 6)
        l.setAlignment(Qt.AlignmentFlag.AlignCenter)

        badge = QLabel(text)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                border-radius: 12px;
                padding: 2px 14px;
                font-weight: bold;
                font-size: 13px;
            }}
        """)
        l.addWidget(badge)
        return container

    def _clear_history(self):
        if (
            QMessageBox.question(
                self,
                "Xác nhận",
                "Xóa toàn bộ lịch sử?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            == QMessageBox.StandardButton.Yes
        ):
            StockChangeLogRepository.clear_all()
            self.refresh_history()
