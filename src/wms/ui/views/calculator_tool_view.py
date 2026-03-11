"""
Standard Calculator Tool View - Professional Windows-style Full Feature Set
Includes Money Counter for all Vietnamese currency denominations.
"""

from datetime import datetime

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QScrollArea,
                             QTabWidget, QVBoxLayout, QWidget)

from ..theme import AppColors
from ...database.repositories import BankRepository


class CalculatorToolView(QWidget):
    """Máy tính Standard Full tính năng (Windows Style) với phím tắt nâng cao"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_value = "0"
        self.expression = ""
        self.expression_parts = []
        self.pending_op = None
        self.last_val = None
        self.new_num = True  # Flag: Start entering a new number?

        # Accept keyboard focus so keyPressEvent fires without needing a click
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._setup_ui()
        
        # Timer to update bank total periodically
        self._bank_timer = QTimer()
        self._bank_timer.timeout.connect(self._update_bank_total)
        self._bank_timer.start(5000)  # Update every 5 seconds
        
        # Initial update
        QTimer.singleShot(500, self._update_bank_total)

    def showEvent(self, event):
        """Auto-grab keyboard focus whenever this tab becomes visible."""
        super().showEvent(event)
        self.setFocus()

    def _setup_ui(self):
        # Background main
        self.setStyleSheet(f"background-color: {AppColors.BG_SECONDARY};")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(0)

        # --- Sub-tab widget ---
        self.sub_tabs = QTabWidget()
        self.sub_tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar {{
                background: transparent;
            }}
            QTabBar::tab {{
                background: rgba(255, 255, 255, 0.6);
                color: {AppColors.TEXT_SECONDARY};
                font-size: 12px;
                font-weight: 700;
                padding: 10px 24px;
                margin-right: 6px;
                border: 1px solid {AppColors.BORDER};
                border-bottom: none;
                border-radius: 10px 10px 0 0;
            }}
            QTabBar::tab:selected {{
                background: white;
                color: {AppColors.PRIMARY};
                border-color: {AppColors.BORDER};
                border-bottom: 2px solid white;
            }}
            QTabBar::tab:hover:!selected {{
                background: rgba(255, 255, 255, 0.85);
                color: {AppColors.TEXT};
            }}
        """)
        outer.addWidget(self.sub_tabs)

        # ===== TAB 1: Calculator + History =====
        calc_page = QWidget()
        calc_page.setStyleSheet("background: transparent;")
        calc_h_layout = QHBoxLayout(calc_page)
        calc_h_layout.setContentsMargins(0, 12, 0, 0)
        calc_h_layout.setSpacing(16)

        # --- LEFT: CALCULATOR ---
        calc_container = QFrame()
        calc_container.setFixedWidth(390)
        calc_container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                border: 1px solid {AppColors.BORDER};
            }}
        """)

        calc_layout = QVBoxLayout(calc_container)
        calc_layout.setContentsMargins(18, 18, 18, 18)
        calc_layout.setSpacing(12)

        # Header info
        header_info = QLabel("STANDARD CALCULATOR")
        header_info.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-weight: 700; font-size: 9px; letter-spacing: 2.5px; padding-bottom: 2px;"
        )
        calc_layout.addWidget(header_info)

        # Display area with subtle gradient background
        display_frame = QFrame()
        display_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f8fafc, stop:1 #f1f5f9);
                border-radius: 12px;
                border: 1px solid {AppColors.BORDER};
                padding: 8px 12px;
            }}
        """)
        display_layout = QVBoxLayout(display_frame)
        display_layout.setContentsMargins(8, 4, 8, 4)
        display_layout.setSpacing(0)

        # Result Display (Top Line: Previous expression)
        self.prev_display = QLabel("")
        self.prev_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.prev_display.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 13px; min-height: 1.6em; background: transparent;"
        )
        display_layout.addWidget(self.prev_display)

        # Main Entry Display (Bottom Line)
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setMinimumHeight(50)
        self.display.setText("0")
        self.display.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background: transparent;
                color: {AppColors.TEXT};
                font-size: 34px;
                font-weight: 800;
                padding-right: 4px;
                letter-spacing: -0.5px;
            }}
        """)
        display_layout.addWidget(self.display)
        calc_layout.addWidget(display_frame)

        # --- SPECIAL ACTION PANEL ---
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        actions = [("Copy Kết quả", "#2563eb")]

        for text, fg in actions:
            btn = QPushButton(text)
            btn.setMinimumHeight(36)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: white;
                    color: {fg};
                    border-radius: 6px;
                    border: 1px solid {AppColors.BORDER};
                    font-size: 11px;
                    font-weight: 700;
                    padding: 0 12px;
                }}
                QPushButton:hover {{ background-color: #f8fafc; border-color: {fg}; }}
            """)
            btn.clicked.connect(lambda ch, t=text: self._on_special_action(t))
            action_layout.addWidget(btn)

        calc_layout.addLayout(action_layout)

        # Button grid (5 rows, 4 columns) — basic +-×÷ layout
        grid = QGridLayout()
        grid.setSpacing(8)

        buttons = [
            ("CE", 0, 0),
            ("C", 0, 1),
            ("⌫", 0, 2),
            ("÷", 0, 3),
            ("7", 1, 0),
            ("8", 1, 1),
            ("9", 1, 2),
            ("×", 1, 3),
            ("4", 2, 0),
            ("5", 2, 1),
            ("6", 2, 2),
            ("−", 2, 3),
            ("1", 3, 0),
            ("2", 3, 1),
            ("3", 3, 2),
            ("+", 3, 3),
            ("±", 4, 0),
            ("0", 4, 1),
            (".", 4, 2),
            ("=", 4, 3),
        ]

        for text, r, c in buttons:
            real_op = text  # For display vs logic mapping
            if text == "÷":
                real_op = "/"
            elif text == "×":
                real_op = "*"
            elif text == "−":
                real_op = "-"

            btn = QPushButton(text)
            btn.setMinimumSize(82, 56)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            is_digit = text.isdigit() or text == "."
            is_op = text in ["÷", "×", "−", "+"]

            # Ultra-clean modern style with press feedback
            if text == "=":
                st = f"background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {AppColors.PRIMARY_LIGHT}, stop:1 {AppColors.PRIMARY}); color: white; border-radius: 12px; font-weight: 700; font-size: 24px; border: none;"
                hover = f"background: {AppColors.PRIMARY_HOVER};"
                pressed = f"background: {AppColors.PRIMARY_DARK}; padding-top: 2px;"
            elif is_op:
                st = f"background: #F1F5F9; color: {AppColors.PRIMARY}; border-radius: 12px; font-weight: 600; font-size: 24px; border: none;"
                hover = f"background: #E2E8F0; color: {AppColors.PRIMARY_DARK};"
                pressed = f"background: #CBD5E1; padding-top: 2px;"
            elif is_digit:
                st = f"background: white; color: {AppColors.TEXT}; border-radius: 12px; font-weight: 600; font-size: 22px; border: 1px solid #F1F5F9;"
                hover = f"background: #F8FAFC; border-color: {AppColors.BORDER_HOVER};"
                pressed = f"background: #F1F5F9; border-color: {AppColors.PRIMARY}; padding-top: 2px;"
            else:  # Function keys (CE, C, etc)
                st = f"background: white; color: {AppColors.ERROR if text in ['C', 'CE'] else AppColors.TEXT_SECONDARY}; border-radius: 12px; font-weight: 600; font-size: 16px; border: 1px solid #F1F5F9;"
                hover = (
                    f"background: #FEF2F2; color: {AppColors.ERROR}; border-color: #FECACA;"
                    if text in ["C", "CE"]
                    else f"background: #F8FAFC; color: {AppColors.TEXT};"
                )
                pressed = f"background: #F1F5F9; padding-top: 2px;"

            btn.setStyleSheet(f"""
                QPushButton {{ {st} }}
                QPushButton:hover {{ {hover} }}
                QPushButton:pressed {{ {pressed} }}
            """)
            btn.clicked.connect(lambda ch, t=real_op: self._on_btn(t))
            grid.addWidget(btn, r, c)

        calc_layout.addLayout(grid)
        calc_h_layout.addWidget(calc_container)

        # --- Spacer between calc and history ---
        calc_h_layout.addStretch(1)

        # --- RIGHT: HISTORY ---
        history_side = QFrame()
        history_side.setFixedWidth(300)
        history_side.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                border: 1px solid {AppColors.BORDER};
            }}
        """)

        hist_layout = QVBoxLayout(history_side)
        hist_layout.setContentsMargins(14, 18, 14, 14)
        hist_layout.setSpacing(8)

        hist_label = QLabel("LỊCH SỬ")
        hist_label.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-weight: 700; font-size: 9px; letter-spacing: 2.5px; margin-bottom: 10px;"
        )
        hist_layout.addWidget(hist_label)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll.setStyleSheet("background: transparent;")

        self.hist_container = QWidget()
        self.hist_v_layout = QVBoxLayout(self.hist_container)
        self.hist_v_layout.setSpacing(10)
        self.hist_v_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.hist_empty = QLabel("Chưa có lịch sử tính")
        self.hist_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hist_empty.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px; font-weight: 600; padding: 24px 8px;"
        )
        self.hist_v_layout.addWidget(self.hist_empty)

        self.scroll.setWidget(self.hist_container)
        hist_layout.addWidget(self.scroll)

        clear_btn = QPushButton("Xóa lịch sử")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: #94a3b8; font-size: 11px; font-weight: 600; border: none; padding: 10px; }} QPushButton:hover {{ color: {AppColors.ERROR}; }}"
        )
        clear_btn.clicked.connect(self._clear_history)
        hist_layout.addWidget(clear_btn)

        calc_h_layout.addWidget(history_side)

        self.sub_tabs.addTab(calc_page, "Máy tính")

        # ===== TAB 2: Money Counter =====
        money_page = QWidget()
        money_page.setStyleSheet("background: transparent;")
        self._build_money_counter(money_page)
        self.sub_tabs.addTab(money_page, "Đếm tiền")

    # ================================================================
    # MONEY COUNTER
    # ================================================================

    # Vietnamese currency denominations (polymer notes only, ≥ 1.000₫)
    VND_DENOMINATIONS = [
        500_000, 200_000, 100_000, 50_000, 20_000,
        10_000, 5_000, 2_000, 1_000,
    ]

    # Color coding by denomination tier
    _DENOM_COLORS = {
        500_000: "#dc2626", 200_000: "#ea580c", 100_000: "#d97706",
        50_000:  "#16a34a", 20_000: "#2563eb", 10_000: "#7c3aed",
        5_000:   "#0d9488", 2_000:  "#64748b", 1_000:  "#64748b",
    }

    def _build_money_counter(self, parent_widget):
        """Build full-width money counter as its own tab with proper table alignment."""
        page_layout = QVBoxLayout(parent_widget)
        page_layout.setContentsMargins(0, 12, 0, 0)
        page_layout.setSpacing(12)

        # Main card
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame#money_card {{
                background-color: white;
                border-radius: 16px;
                border: 1px solid {AppColors.BORDER};
            }}
        """)
        card.setObjectName("money_card")

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(28, 20, 28, 18)
        card_layout.setSpacing(14)

        # Header row with decorative underline
        header_row = QHBoxLayout()
        header_label = QLabel("ĐẾM TIỀN VIỆT NAM")
        header_label.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-weight: 700; "
            f"font-size: 9px; letter-spacing: 2.5px;"
        )
        header_row.addWidget(header_label)
        header_row.addStretch()
        card_layout.addLayout(header_row)

        # --- Table header ---
        self._money_inputs: dict[int, QLineEdit] = {}
        self._money_subtotals: dict[int, QLabel] = {}

        table_grid = QGridLayout()
        table_grid.setHorizontalSpacing(16)
        table_grid.setVerticalSpacing(6)
        table_grid.setContentsMargins(0, 0, 0, 0)

        # Column headers for both sides
        col_headers = ["Mệnh giá", "Số lượng", "Thành tiền"]
        for group in range(2):  # 2 groups side-by-side
            base_col = group * 4  # 0 or 4 (col 3 and 7 are spacers)
            for i, hdr_text in enumerate(col_headers):
                hdr = QLabel(hdr_text)
                align = Qt.AlignmentFlag.AlignRight if i == 2 else Qt.AlignmentFlag.AlignLeft
                hdr.setAlignment(align)
                hdr.setStyleSheet(
                    f"color: {AppColors.TEXT_SECONDARY}; font-size: 9px; "
                    f"font-weight: 700; letter-spacing: 1.5px; padding-bottom: 6px;"
                    f"border-bottom: 2px solid {AppColors.BORDER};"
                )
                table_grid.addWidget(hdr, 0, base_col + i)

        # Spacer column between groups
        spacer = QLabel()
        spacer.setFixedWidth(32)
        table_grid.addWidget(spacer, 0, 3)

        # --- Denomination rows: 5 rows × 2 groups ---
        for idx, denom in enumerate(self.VND_DENOMINATIONS):
            group = idx // 5       # 0 = left group, 1 = right group
            row_num = (idx % 5) + 1  # rows 1..5 (row 0 is header)
            base_col = group * 4

            color = self._DENOM_COLORS.get(denom, "#64748b")

            # Column 0: Denomination label with color dot
            denom_widget = QWidget()
            # Alternate row background for zebra-stripe effect
            row_bg = "#f8fafc" if (row_num % 2 == 0) else "transparent"
            denom_widget.setStyleSheet(f"background: {row_bg}; border-radius: 6px;")
            denom_h = QHBoxLayout(denom_widget)
            denom_h.setContentsMargins(6, 4, 0, 4)
            denom_h.setSpacing(10)

            dot = QLabel()
            dot.setFixedSize(10, 10)
            dot.setStyleSheet(f"background: {color}; border-radius: 5px;")
            denom_h.addWidget(dot)

            if denom >= 1000:
                text = f"{denom:,}"
            else:
                text = str(denom)
            lbl = QLabel(text)
            lbl.setFixedWidth(75)
            lbl.setStyleSheet(
                f"color: {AppColors.TEXT}; font-weight: 700; font-size: 13px; background: transparent;"
            )
            denom_h.addWidget(lbl)
            denom_h.addStretch()
            table_grid.addWidget(denom_widget, row_num, base_col + 0)

            # Column 1: Quantity input
            qty_input = QLineEdit()
            qty_input.setPlaceholderText("0")
            qty_input.setValidator(QIntValidator(0, 99999))
            qty_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
            qty_input.setFixedWidth(80)
            qty_input.setMinimumHeight(34)
            qty_input.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {AppColors.BORDER};
                    border-radius: 8px;
                    background: white;
                    color: {AppColors.TEXT};
                    font-size: 13px;
                    font-weight: 600;
                    padding: 0 8px;
                }}
                QLineEdit:focus {{
                    border: 2px solid {AppColors.PRIMARY};
                    background: #f0fdf4;
                }}
                QLineEdit:hover {{
                    border-color: {AppColors.BORDER_HOVER};
                }}
            """)
            qty_input.textChanged.connect(lambda _: self._update_money_totals())
            table_grid.addWidget(qty_input, row_num, base_col + 1)
            self._money_inputs[denom] = qty_input

            # Enter key → jump to next denomination input
            qty_input.returnPressed.connect(
                lambda cur_idx=idx: self._focus_next_money_input(cur_idx)
            )

            # Column 2: Subtotal
            sub = QLabel("0 ₫")
            sub.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            sub.setFixedWidth(130)
            sub.setStyleSheet(
                f"color: {AppColors.TEXT_SECONDARY}; font-size: 13px; font-weight: 600;"
            )
            table_grid.addWidget(sub, row_num, base_col + 2)
            self._money_subtotals[denom] = sub

        card_layout.addLayout(table_grid)

        # Separator with gradient
        sep = QFrame()
        sep.setFixedHeight(2)
        sep.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {AppColors.PRIMARY}, stop:0.5 {AppColors.BORDER}, stop:1 transparent);
            border-radius: 1px;
        """)
        card_layout.addWidget(sep)

        # Grand total row - prominent
        total_row = QHBoxLayout()
        total_row.setContentsMargins(0, 6, 0, 2)
        total_label = QLabel("TỔNG CỘNG:")
        total_label.setStyleSheet(
            f"color: {AppColors.TEXT}; font-weight: 800; font-size: 14px; letter-spacing: 0.5px;"
        )
        self._money_total_label = QLabel("0 ₫")
        self._money_total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self._money_total_label.setStyleSheet(
            f"color: {AppColors.PRIMARY}; font-weight: 900; font-size: 24px; letter-spacing: -0.5px;"
        )
        total_row.addWidget(total_label)
        total_row.addWidget(self._money_total_label)
        card_layout.addLayout(total_row)

        # Count summary
        self._money_count_label = QLabel("Tổng: 0 tờ")
        self._money_count_label.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px;"
        )
        card_layout.addWidget(self._money_count_label)

        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        copy_btn = QPushButton("Copy kết quả")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.setMinimumHeight(38)
        copy_btn.setStyleSheet(f"""
            QPushButton {{
                background: white; color: {AppColors.PRIMARY};
                border-radius: 10px; border: 1.5px solid {AppColors.BORDER};
                font-size: 12px; font-weight: 700; padding: 0 20px;
            }}
            QPushButton:hover {{ background: #f0fdf4; border-color: {AppColors.PRIMARY}; }}
            QPushButton:pressed {{ background: #ecfdf5; }}
        """)
        copy_btn.clicked.connect(self._copy_money_total)
        btn_row.addWidget(copy_btn)

        send_btn = QPushButton("Gửi sang Máy tính")
        send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        send_btn.setMinimumHeight(38)
        send_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {AppColors.PRIMARY_LIGHT}, stop:1 {AppColors.PRIMARY});
                color: white;
                border-radius: 10px; border: none;
                font-size: 12px; font-weight: 700; padding: 0 20px;
            }}
            QPushButton:hover {{ background: {AppColors.PRIMARY_HOVER}; }}
            QPushButton:pressed {{ background: {AppColors.PRIMARY_DARK}; }}
        """)
        send_btn.clicked.connect(self._send_money_to_calc)
        btn_row.addWidget(send_btn)

        reset_btn = QPushButton("Xóa tất cả")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.setMinimumHeight(38)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background: white; color: {AppColors.ERROR};
                border-radius: 10px; border: 1.5px solid {AppColors.BORDER};
                font-size: 12px; font-weight: 700; padding: 0 20px;
            }}
            QPushButton:hover {{ background: #fef2f2; border-color: {AppColors.ERROR}; }}
            QPushButton:pressed {{ background: #fee2e2; }}
        """)
        reset_btn.clicked.connect(self._reset_money_counter)
        btn_row.addWidget(reset_btn)

        btn_row.addStretch()
        card_layout.addLayout(btn_row)

        # Push card to top
        page_layout.addWidget(card)
        
        # Bank Total Card
        bank_card = QFrame()
        bank_card.setStyleSheet(f"""
            QFrame#bank_card {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(16, 185, 129, 0.08), stop:1 rgba(59, 130, 246, 0.08));
                border-radius: 16px;
                border: 1px solid rgba(16, 185, 129, 0.2);
            }}
        """)
        bank_card.setObjectName("bank_card")
        bank_card.setMaximumHeight(120)
        
        bank_layout = QVBoxLayout(bank_card)
        bank_layout.setContentsMargins(24, 16, 24, 16)
        bank_layout.setSpacing(8)
        
        bank_header = QLabel("💰 TỔNG TIỀN NGÂN HÀNG")
        bank_header.setStyleSheet(f"""
            color: {AppColors.TEXT_SECONDARY};
            font-weight: 700;
            font-size: 11px;
            letter-spacing: 2px;
        """)
        bank_layout.addWidget(bank_header)
        
        self.bank_total_label = QLabel("0 VND")
        self.bank_total_label.setStyleSheet(f"""
            color: {AppColors.SUCCESS};
            font-weight: 800;
            font-size: 32px;
            letter-spacing: -0.5px;
        """)
        bank_layout.addWidget(self.bank_total_label)
        
        page_layout.addWidget(bank_card)
        page_layout.addStretch()
    def _focus_next_money_input(self, current_idx: int):
        """Move focus to the next denomination input field."""
        next_idx = current_idx + 1
        if next_idx < len(self.VND_DENOMINATIONS):
            next_denom = self.VND_DENOMINATIONS[next_idx]
            self._money_inputs[next_denom].setFocus()
        else:
            # Wrap to first or just stay
            first_denom = self.VND_DENOMINATIONS[0]
            self._money_inputs[first_denom].setFocus()

    def _update_money_totals(self):
        """Recalculate all subtotals and grand total."""
        grand_total = 0
        total_count = 0

        for denom, inp in self._money_inputs.items():
            txt = inp.text().strip()
            qty = int(txt) if txt.isdigit() else 0
            sub = denom * qty
            grand_total += sub
            total_count += qty

            lbl = self._money_subtotals[denom]
            if qty > 0:
                lbl.setText(f"{sub:,.0f} ₫")
                lbl.setStyleSheet(
                    f"color: {AppColors.TEXT}; font-size: 13px; font-weight: 700;"
                )
            else:
                lbl.setText("0 ₫")
                lbl.setStyleSheet(
                    f"color: {AppColors.TEXT_SECONDARY}; font-size: 13px; font-weight: 600;"
                )

        self._money_total_label.setText(f"{grand_total:,.0f} ₫")
        self._money_count_label.setText(f"Tổng: {total_count:,} tờ")

    def _copy_money_total(self):
        """Copy the grand total to clipboard."""
        text = self._money_total_label.text().replace(" ₫", "").replace(",", "")
        QApplication.clipboard().setText(text)

    def _send_money_to_calc(self):
        """Send the money counter total into the calculator display."""
        text = self._money_total_label.text().replace(" ₫", "").replace(",", "")
        if text and text != "0":
            self.current_value = text
            self._update_display()
            self.new_num = True

    def _reset_money_counter(self):
        """Clear all denomination inputs."""
        for inp in self._money_inputs.values():
            inp.clear()
        self._update_money_totals()

    def _on_btn(self, t):
        if t.isdigit():
            if self.new_num:
                self.current_value = t
                self.new_num = False
            else:
                if self.current_value == "0":
                    self.current_value = t
                else:
                    self.current_value += t
            self._update_display()

        elif t == ".":
            if self.new_num:
                self.current_value = "0."
                self.new_num = False
            elif "." not in self.current_value:
                self.current_value += "."
            self._update_display()

        elif t in ["/", "*", "-", "+"]:
            self._handle_op(t)

        elif t == "=":
            self._calculate_final()

        elif t == "C":
            self.current_value = "0"
            self.expression = ""
            self.expression_parts = []
            self.pending_op = None
            self.last_val = None
            self.new_num = True
            self.prev_display.setText("")
            self._update_display()

        elif t == "CE":
            self.current_value = "0"
            self.new_num = True
            self._update_display()

        elif t == "⌫":
            if not self.new_num:
                self.current_value = self.current_value[:-1]
                if not self.current_value:
                    self.current_value = "0"
                    self.new_num = True
                self._update_display()

        elif t == "±":
            if self.current_value != "0":
                if self.current_value.startswith("-"):
                    self.current_value = self.current_value[1:]
                else:
                    self.current_value = "-" + self.current_value
                self._update_display()

        # (Advanced buttons %, √x, x², 1/x removed — basic calculator only)

    def _update_display(self):
        try:
            val = float(self.current_value)
            # Format: No decimals if int, max 8 decimals if float
            if val.is_integer():
                formatted = f"{int(val):,}"
            else:
                formatted = f"{val:,.8f}".rstrip("0").rstrip(".")
            self.display.setText(formatted)
        except:
            self.display.setText(self.current_value)

    def _handle_op(self, next_op):
        val = float(self.current_value)
        display_op = self._display_op(next_op)
        display_ops = {"+", "-", "×", "÷"}

        if self.new_num and self.expression_parts:
            self.expression_parts[-1] = display_op
            self.expression = " ".join(self.expression_parts)
            self.prev_display.setText(self.expression)
            self.pending_op = next_op
            return

        if not self.expression_parts:
            self.expression_parts.append(self._fmt(val))
        elif self.expression_parts[-1] in display_ops:
            self.expression_parts.append(self._fmt(val))
        self.expression_parts.append(display_op)

        if self.last_val is None:
            self.last_val = val
        elif self.pending_op and not self.new_num:
            # Chain calculation: 100 + 50 + -> results in 150
            self.last_val = self._do_math(self.last_val, val, self.pending_op)
            self.current_value = str(self.last_val)
            self._update_display()

        self.pending_op = next_op
        self.expression = " ".join(self.expression_parts)
        self.prev_display.setText(self.expression)
        self.new_num = True

    def _calculate_final(self):
        if self.pending_op is None:
            return

        val = float(self.current_value)
        res = self._do_math(self.last_val, val, self.pending_op)

        self.expression_parts.append(self._fmt(val))
        full_expr = " ".join(self.expression_parts) + " ="
        self.prev_display.setText(full_expr)

        self.current_value = str(res)
        self._update_display()

        # Add to history
        self._add_to_history(full_expr, self.display.text())

        self.expression_parts = []
        self.last_val = None
        self.pending_op = None
        self.new_num = True

    def _do_math(self, v1, v2, op):
        if op == "+":
            return v1 + v2
        if op == "-":
            return v1 - v2
        if op == "*":
            return v1 * v2
        if op == "/":
            return v1 / v2 if v2 != 0 else 0
        return v2

    def _fmt(self, val):
        if val is None:
            return ""
        if val.is_integer():
            return f"{int(val):,}"
        return f"{val:,.4f}".rstrip("0").rstrip(".")

    def _display_op(self, op):
        return {"*": "×", "/": "÷", "-": "-", "+": "+"}.get(op, op)

    def _add_to_history(self, expr, res):
        if self.hist_empty and self.hist_empty.parent() is not None:
            self.hist_empty.setParent(None)

        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fafbfc, stop:1 #f1f5f9);
                border-radius: 10px;
                padding: 8px;
                border: 1px solid #e2e8f0;
            }}
            QFrame:hover {{
                border-color: {AppColors.PRIMARY};
                background: #f0fdf4;
            }}
        """)

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(10, 8, 10, 8)

        # Timestamp
        ts = QLabel(datetime.now().strftime("%H:%M:%S"))
        ts.setStyleSheet(
            "color: #94a3b8; font-size: 10px; font-weight: 600; background: transparent;"
        )
        ts.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(ts)

        eq = QLabel(expr)
        eq.setStyleSheet("color: #475569; font-size: 13px; font-weight: 600; background: transparent;")
        eq.setWordWrap(True)

        rs = QLabel(res)
        rs.setStyleSheet(f"color: {AppColors.TEXT}; font-weight: 800; font-size: 18px; background: transparent;")
        rs.setAlignment(Qt.AlignmentFlag.AlignRight)

        layout.addWidget(eq)
        layout.addWidget(rs)

        frame.setCursor(Qt.CursorShape.PointingHandCursor)
        # Reuse result on click
        frame.mousePressEvent = lambda e, v=res.replace(",", ""): self._reuse(v)

        self.hist_v_layout.insertWidget(0, frame)

    def _reuse(self, val):
        self.current_value = val
        self._update_display()
        self.new_num = True

    def _clear_history(self):
        while self.hist_v_layout.count():
            w = self.hist_v_layout.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.hist_empty = QLabel("Chưa có lịch sử tính")
        self.hist_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hist_empty.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px; font-weight: 600; padding: 24px 8px;"
        )
        self.hist_v_layout.addWidget(self.hist_empty)

    def _on_special_action(self, action):
        try:
            curr = float(self.current_value)
            if "VAT 10%" in action:
                res = curr * 1.1
            elif "VAT 8%" in action:
                res = curr * 1.08
            elif "Copy" in action:
                QApplication.clipboard().setText(self.display.text().replace(",", ""))
                return

            self.prev_display.setText(f"{self._fmt(curr)} + {action}")
            self.current_value = str(res)
            self._update_display()
            self.new_num = True
        except:
            pass

    def keyPressEvent(self, event):
        key = event.key()
        text = event.text()

        # If money counter tab is active, let its inputs handle events
        if self.sub_tabs.currentIndex() == 1:
            super().keyPressEvent(event)
            return

        # Handle number keys (both top row and numpad)
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            self._on_btn(text if text else chr(key))
            return

        # Handle operators
        if text in "+-*/.":
            self._on_btn(text)
            return

        # Handle Enter
        if key in [Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Equal]:
            self._on_btn("=")
            return

        # Handle editing keys
        if key == Qt.Key.Key_Backspace:
            self._on_btn("⌫")
        elif key == Qt.Key.Key_Escape:
            self._on_btn("C")
        elif key == Qt.Key.Key_Delete:
            self._on_btn("CE")

        # Handle copy shortcut
        elif (
            event.modifiers() == Qt.KeyboardModifier.ControlModifier
            and key == Qt.Key.Key_C
        ):
            self._on_special_action("Copy Kết quả")

        super().keyPressEvent(event)

    def _update_bank_total(self):
        """Update bank total from database"""
        try:
            if not hasattr(self, 'bank_total_label'):
                return
                
            # Get all transactions from database
            notifs = BankRepository.get_all()
            total = 0.0
            
            for n in notifs:
                if n.amount:
                    amt_text = n.amount.strip()
                    if amt_text and amt_text != "---":
                        try:
                            # Parse amount: "+5,000,000 VND" -> 5000000
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
            self.bank_total_label.setText(f"{formatted} VND")
            
            # Change color based on positive/negative
            if total >= 0:
                self.bank_total_label.setStyleSheet(f"""
                    color: {AppColors.SUCCESS};
                    font-weight: 800;
                    font-size: 32px;
                    letter-spacing: -0.5px;
                """)
            else:
                self.bank_total_label.setStyleSheet(f"""
                    color: {AppColors.ERROR};
                    font-weight: 800;
                    font-size: 32px;
                    letter-spacing: -0.5px;
                """)
        except Exception as e:
            # Silently fail if database not ready
            pass
