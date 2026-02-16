"""
Standard Calculator Tool View - Professional Windows-style Full Feature Set
"""

import math

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout,
                             QLabel, QLineEdit, QPushButton, QScrollArea,
                             QVBoxLayout, QWidget)

from ui.qt_theme import AppColors


class CalculatorToolView(QWidget):
    """Máy tính Standard Full tính năng (Windows Style) với phím tắt nâng cao"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_value = "0"
        self.expression = ""
        self.pending_op = None
        self.last_val = None
        self.new_num = True  # Flag: Start entering a new number?

        self._setup_ui()

    def _setup_ui(self):
        # Background main
        self.setStyleSheet(f"background-color: {AppColors.BG_SECONDARY};")

        main_h_layout = QHBoxLayout(self)
        main_h_layout.setContentsMargins(40, 40, 40, 40)
        main_h_layout.setSpacing(30)
        main_h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- LEFT: CALCULATOR ---
        calc_container = QFrame()
        calc_container.setFixedWidth(400)
        calc_container.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: 16px;
                border: 1px solid {AppColors.BORDER};
            }}
        """)

        calc_layout = QVBoxLayout(calc_container)
        calc_layout.setContentsMargins(15, 20, 15, 20)
        calc_layout.setSpacing(10)

        # Header info
        header_info = QLabel("STANDARD BUSINESS CALCULATOR")
        header_info.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-weight: 700; font-size: 10px; letter-spacing: 1.5px;"
        )
        calc_layout.addWidget(header_info)

        # Result Display (Top Line: Previous expression)
        self.prev_display = QLabel("")
        self.prev_display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.prev_display.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 14px; min-height: 24px;"
        )
        calc_layout.addWidget(self.prev_display)

        # Main Entry Display (Bottom Line)
        self.display = QLineEdit()
        self.display.setReadOnly(True)
        self.display.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.display.setFixedHeight(65)
        self.display.setText("0")
        self.display.setStyleSheet(f"""
            QLineEdit {{
                border: none;
                background: transparent;
                color: {AppColors.TEXT};
                font-size: 42px;
                font-weight: 800;
                padding-right: 5px;
            }}
        """)
        calc_layout.addWidget(self.display)

        # --- SPECIAL ACTION PANEL ---
        action_layout = QHBoxLayout()
        action_layout.setSpacing(8)

        actions = [("Copy Kết quả", "#2563eb")]

        for text, fg in actions:
            btn = QPushButton(text)
            btn.setFixedHeight(34)
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

        # Button grid (6 rows, 4 columns)
        grid = QGridLayout()
        grid.setSpacing(6)

        buttons = [
            ("%", 0, 0),
            ("CE", 0, 1),
            ("C", 0, 2),
            ("⌫", 0, 3),
            ("1/x", 1, 0),
            ("x²", 1, 1),
            ("√x", 1, 2),
            ("÷", 1, 3),
            ("7", 2, 0),
            ("8", 2, 1),
            ("9", 2, 2),
            ("×", 2, 3),
            ("4", 3, 0),
            ("5", 3, 1),
            ("6", 3, 2),
            ("−", 3, 3),
            ("1", 4, 0),
            ("2", 4, 1),
            ("3", 4, 2),
            ("+", 4, 3),
            ("±", 5, 0),
            ("0", 5, 1),
            (".", 5, 2),
            ("=", 5, 3),
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
            btn.setFixedSize(86, 60)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

            is_digit = text.isdigit() or text == "."
            is_op = text in ["÷", "×", "−", "+"]

            # Ultra-clean modern style
            if text == "=":
                st = f"background: {AppColors.PRIMARY}; color: white; border-radius: 12px; font-weight: 700; font-size: 24px; border: none;"
                hover = f"background: {AppColors.PRIMARY_HOVER}; margin-top: -2px;"
            elif is_op:
                st = f"background: #F1F5F9; color: {AppColors.PRIMARY}; border-radius: 12px; font-weight: 600; font-size: 24px; border: none;"
                hover = f"background: #E2E8F0; color: {AppColors.PRIMARY_DARK};"
            elif is_digit:
                st = f"background: white; color: {AppColors.TEXT}; border-radius: 12px; font-weight: 600; font-size: 22px; border: 1px solid #F1F5F9;"
                hover = f"background: #F8FAFC; border-color: {AppColors.BORDER_HOVER};"
            else:  # Function keys (CE, C, etc)
                st = f"background: white; color: {AppColors.ERROR if text in ['C', 'CE'] else AppColors.TEXT_SECONDARY}; border-radius: 12px; font-weight: 600; font-size: 16px; border: 1px solid #F1F5F9;"
                hover = (
                    f"background: #FEF2F2; color: {AppColors.ERROR}; border-color: #FECACA;"
                    if text in ["C", "CE"]
                    else f"background: #F8FAFC; color: {AppColors.TEXT};"
                )

            btn.setStyleSheet(f"""
                QPushButton {{ {st} }}
                QPushButton:hover {{ {hover} }}
                QPushButton:pressed {{ background: #E2E8F0; margin-top: 1px; }}
            """)
            btn.clicked.connect(lambda ch, t=real_op: self._on_btn(t))
            grid.addWidget(btn, r, c)

        calc_layout.addLayout(grid)
        main_h_layout.addWidget(calc_container)

        # --- RIGHT: HISTORY ---
        history_side = QFrame()
        history_side.setFixedWidth(260)
        history_side.setStyleSheet(
            f"background-color: white; border-radius: 16px; border: 1px solid {AppColors.BORDER};"
        )

        hist_layout = QVBoxLayout(history_side)
        hist_layout.setContentsMargins(15, 20, 15, 15)

        hist_label = QLabel("Dữ liệu Lịch sử")
        hist_label.setStyleSheet(
            f"color: {AppColors.TEXT}; font-weight: 800; font-size: 13px; margin-bottom: 8px;"
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

        self.scroll.setWidget(self.hist_container)
        hist_layout.addWidget(self.scroll)

        clear_btn = QPushButton("🗑️ Xóa sạch lịch sử")
        clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        clear_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: #94a3b8; font-size: 11px; font-weight: 600; border: none; padding: 10px; }} QPushButton:hover {{ color: {AppColors.ERROR}; }}"
        )
        clear_btn.clicked.connect(self._clear_history)
        hist_layout.addWidget(clear_btn)

        main_h_layout.addWidget(history_side)

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

        elif t == "%":
            try:
                val = float(self.current_value)
                if self.last_val is not None:
                    # Business style: 100 + 10% = 110
                    res = self.last_val * (val / 100)
                    self.current_value = str(res)
                else:
                    self.current_value = str(val / 100)
                self._update_display()
            except:
                pass

        elif t == "√x":
            try:
                self.current_value = str(math.sqrt(float(self.current_value)))
                self._update_display()
                self.new_num = True
            except:
                self.display.setText("Lỗi")

        elif t == "x²":
            try:
                self.current_value = str(float(self.current_value) ** 2)
                self._update_display()
                self.new_num = True
            except:
                pass

        elif t == "1/x":
            try:
                v = float(self.current_value)
                self.current_value = str(1 / v) if v != 0 else "0"
                self._update_display()
                self.new_num = True
            except:
                pass

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

        if self.last_val is None:
            self.last_val = val
        elif self.pending_op and not self.new_num:
            # Chain calculation: 100 + 50 + -> results in 150
            self.last_val = self._do_math(self.last_val, val, self.pending_op)
            self.current_value = str(self.last_val)
            self._update_display()

        self.pending_op = next_op
        self.expression = f"{self._fmt(self.last_val)} {next_op}"
        self.prev_display.setText(self.expression)
        self.new_num = True

    def _calculate_final(self):
        if self.pending_op is None:
            return

        val = float(self.current_value)
        res = self._do_math(self.last_val, val, self.pending_op)

        full_expr = f"{self._fmt(self.last_val)} {self.pending_op} {self._fmt(val)} ="
        self.prev_display.setText(full_expr)

        self.current_value = str(res)
        self._update_display()

        # Add to history
        self._add_to_history(full_expr, self.display.text())

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

    def _add_to_history(self, expr, res):
        frame = QFrame()
        frame.setStyleSheet(
            f"QFrame {{ background: #f8fafc; border-radius: 8px; padding: 8px; border: 1px solid #e2e8f0; }} QFrame:hover {{ border-color: {AppColors.PRIMARY}; }}"
        )

        layout = QVBoxLayout(frame)
        layout.setContentsMargins(8, 8, 8, 8)

        eq = QLabel(expr)
        eq.setStyleSheet("color: #64748b; font-size: 11px;")
        eq.setWordWrap(True)

        rs = QLabel(res)
        rs.setStyleSheet(f"color: {AppColors.TEXT}; font-weight: 800; font-size: 15px;")
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

        # Handle number keys (both top row and numpad)
        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            self._on_btn(text if text else chr(key))
            return

        # Handle operators
        if text in "+-*/%.":
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
