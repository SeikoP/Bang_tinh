"""
Task View - Quản lý ghi chú công việc
"""

import re

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDialog,
                             QFormLayout, QFrame, QHBoxLayout, QHeaderView,
                             QLabel, QLineEdit, QMessageBox, QPushButton,
                             QScrollArea, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget, QSpinBox)

from ...database.task_repository import TaskRepository
from ...database.repositories import ProductRepository
from ..theme import AppColors


def _eval_expression(text: str) -> float:
    """Tính biểu thức số học: '12 + 14', '10k + 5k', '35 + 50' (nghìn đồng)"""
    text = text.strip().lower()
    if not text:
        return 0.0
    # Expand shorthand: 10k -> 10000, 1m -> 1000000
    text = re.sub(r'(\d+(?:\.\d+)?)k', lambda m: str(float(m.group(1)) * 1000), text)
    text = re.sub(r'(\d+(?:\.\d+)?)m', lambda m: str(float(m.group(1)) * 1_000_000), text)
    # Only allow safe characters
    if re.fullmatch(r'[\d\s\+\-\*\/\(\)\.]+', text):
        try:
            result = float(eval(text))  # noqa: S307
            # Auto-convert to full amount if result is small (< 1000 = nghìn đồng)
            if result < 1000:
                result *= 1000
            return result
        except Exception:
            pass
    # Fallback: plain number
    try:
        val = float(text)
        # Auto-convert small numbers to thousands
        if val < 1000:
            val *= 1000
        return val
    except ValueError:
        return 0.0


class ProductPickerDialog(QDialog):
    """Dialog chọn sản phẩm - nhanh, dễ dùng"""

    def __init__(self, selected_items=None, parent=None):
        super().__init__(parent)
        self._selected = {item["product_id"]: item.copy() for item in (selected_items or [])}
        self.result_items = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Chọn sản phẩm")
        self.setMinimumWidth(580)
        self.setMinimumHeight(600)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # === Combo đêm - prominent card ===
        combo_card = QFrame()
        combo_card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(16, 185, 129, 0.06), stop:1 rgba(59, 130, 246, 0.06));
                border-radius: 10px;
                border: 1px solid {AppColors.BORDER};
            }}
        """)
        combo_layout = QHBoxLayout(combo_card)
        combo_layout.setContentsMargins(14, 10, 14, 10)
        combo_layout.setSpacing(10)

        combo_label = QLabel("Combo đêm")
        combo_label.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {AppColors.TEXT};")
        combo_layout.addWidget(combo_label)

        # Minus button
        minus_btn = QPushButton("−")
        minus_btn.setFixedSize(32, 32)
        minus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        minus_btn.setStyleSheet(f"""
            QPushButton {{
                background: white; color: {AppColors.TEXT};
                border: 1px solid {AppColors.BORDER}; border-radius: 6px;
                font-size: 16px; font-weight: 700;
            }}
            QPushButton:hover {{ background: #f1f5f9; }}
        """)
        minus_btn.clicked.connect(lambda: self._combo_spin.setValue(max(0, self._combo_spin.value() - 1)))
        combo_layout.addWidget(minus_btn)

        self._combo_spin = QSpinBox()
        self._combo_spin.setRange(0, 99)
        self._combo_spin.setValue(0)
        self._combo_spin.setFixedSize(60, 32)
        self._combo_spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._combo_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self._combo_spin.setStyleSheet(f"""
            QSpinBox {{
                font-size: 14px; font-weight: 700; color: {AppColors.TEXT};
                border: 1.5px solid {AppColors.BORDER}; border-radius: 6px;
                background: white; padding: 0 4px;
            }}
            QSpinBox:focus {{ border-color: {AppColors.PRIMARY}; }}
        """)
        self._combo_spin.valueChanged.connect(self._on_combo_changed)
        combo_layout.addWidget(self._combo_spin)

        # Plus button
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(32, 32)
        plus_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        plus_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.PRIMARY}; color: white;
                border: none; border-radius: 6px;
                font-size: 16px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {AppColors.PRIMARY_HOVER}; }}
        """)
        plus_btn.clicked.connect(lambda: self._combo_spin.setValue(self._combo_spin.value() + 1))
        combo_layout.addWidget(plus_btn)

        combo_layout.addStretch()

        combo_price_label = QLabel("x 40k =")
        combo_price_label.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px;")
        combo_layout.addWidget(combo_price_label)

        self._combo_total_label = QLabel("0")
        self._combo_total_label.setStyleSheet(f"font-weight: 800; font-size: 14px; color: {AppColors.PRIMARY};")
        combo_layout.addWidget(self._combo_total_label)

        layout.addWidget(combo_card)

        # === Search ===
        self._search = QLineEdit()
        self._search.setMinimumHeight(36)
        self._search.setPlaceholderText("Tìm sản phẩm...")
        self._search.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {AppColors.BORDER}; border-radius: 8px;
                padding: 0 12px; font-size: 13px; background: white;
            }}
            QLineEdit:focus {{ border: 2px solid {AppColors.PRIMARY}; }}
        """)
        self._search.textChanged.connect(self._filter_products)
        layout.addWidget(self._search)

        # === Product table with 4 columns ===
        self._product_table = QTableWidget()
        self._product_table.setColumnCount(4)
        self._product_table.setHorizontalHeaderLabels(["Sản phẩm", "Giá", "Số lượng", "Tạm tính"])
        header = self._product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._product_table.setColumnWidth(1, 70)
        self._product_table.setColumnWidth(2, 110)
        self._product_table.setColumnWidth(3, 90)
        self._product_table.verticalHeader().setVisible(False)
        self._product_table.verticalHeader().setDefaultSectionSize(44)
        self._product_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._product_table.setAlternatingRowColors(True)
        layout.addWidget(self._product_table, 1)

        # === Total bar ===
        total_bar = QFrame()
        total_bar.setStyleSheet(f"""
            QFrame {{
                background: {AppColors.SUCCESS}; border-radius: 10px;
            }}
        """)
        total_bar_layout = QHBoxLayout(total_bar)
        total_bar_layout.setContentsMargins(16, 10, 16, 10)

        total_label = QLabel("TỔNG CỘNG:")
        total_label.setStyleSheet("color: white; font-size: 13px; font-weight: 700;")
        total_bar_layout.addWidget(total_label)

        total_bar_layout.addStretch()

        self._total_label = QLabel("0")
        self._total_label.setStyleSheet("color: white; font-size: 20px; font-weight: 900;")
        total_bar_layout.addWidget(self._total_label)

        layout.addWidget(total_bar)

        # === Buttons ===
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = QPushButton("Hủy")
        cancel.setObjectName("secondary")
        cancel.setMinimumHeight(40)
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        btn_row.addStretch()
        ok = QPushButton("Xác nhận chọn")
        ok.setObjectName("primary")
        ok.setMinimumHeight(40)
        ok.clicked.connect(self._confirm)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

        # Load combo value if exists
        combo_item = next((it for it in self._selected.values() if it["name"] == "Combo đêm"), None)
        if combo_item:
            self._combo_spin.setValue(combo_item["qty"])

        self._load_products()

    def _on_combo_changed(self, qty):
        """Handle combo đêm quantity change"""
        combo_price = 40000  # 40k
        if qty > 0:
            self._selected[-1] = {  # Use -1 as special ID for combo
                "product_id": -1,
                "name": "Combo đêm",
                "unit_price": combo_price,
                "qty": qty,
            }
        else:
            self._selected.pop(-1, None)
        
        combo_total = qty * combo_price
        self._combo_total_label.setText(f"{int(combo_total // 1000):,}")
        self._update_total()

    def _load_products(self, keyword=""):
        try:
            from ...database.repositories import ProductRepository
            products = ProductRepository.get_all()
            if keyword:
                keyword = keyword.lower()
                products = [p for p in products if keyword in p.name.lower()]
        except Exception:
            products = []

        self._products = products
        self._product_table.setRowCount(len(products))

        for row, p in enumerate(products):
            qty = self._selected.get(p.id, {}).get("qty", 0)
            has_qty = qty > 0

            # Name
            name_item = QTableWidgetItem(p.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            font = name_item.font()
            font.setPointSize(10)
            if has_qty:
                font.setBold(True)
            name_item.setFont(font)
            if has_qty:
                name_item.setForeground(QColor(AppColors.PRIMARY))
            self._product_table.setItem(row, 0, name_item)

            # Unit price
            price_item = QTableWidgetItem(f"{int(p.unit_price // 1000):,}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            price_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
            self._product_table.setItem(row, 1, price_item)

            # Qty spinner with +/- buttons
            spin_container = QWidget()
            spin_layout = QHBoxLayout(spin_container)
            spin_layout.setContentsMargins(4, 2, 4, 2)
            spin_layout.setSpacing(2)

            dec_btn = QPushButton("−")
            dec_btn.setFixedSize(26, 28)
            dec_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            dec_btn.setStyleSheet(f"""
                QPushButton {{
                    background: #f1f5f9; color: {AppColors.TEXT}; border: none;
                    border-radius: 4px; font-size: 14px; font-weight: 700;
                }}
                QPushButton:hover {{ background: #e2e8f0; }}
            """)
            spin_layout.addWidget(dec_btn)

            spin = QSpinBox()
            spin.setRange(0, 999)
            spin.setValue(qty)
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.setFixedHeight(28)
            spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
            spin.setStyleSheet(f"""
                QSpinBox {{
                    font-size: 13px; font-weight: 700;
                    border: 1px solid {AppColors.BORDER}; border-radius: 4px;
                    background: white; padding: 0 2px;
                }}
                QSpinBox:focus {{ border-color: {AppColors.PRIMARY}; }}
            """)
            spin.valueChanged.connect(lambda val, pid=p.id, pname=p.name, price=p.unit_price: self._on_qty_changed(pid, pname, price, val))
            spin_layout.addWidget(spin)

            inc_btn = QPushButton("+")
            inc_btn.setFixedSize(26, 28)
            inc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            inc_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {AppColors.PRIMARY}; color: white; border: none;
                    border-radius: 4px; font-size: 14px; font-weight: 700;
                }}
                QPushButton:hover {{ background: {AppColors.PRIMARY_HOVER}; }}
            """)
            spin_layout.addWidget(inc_btn)

            dec_btn.clicked.connect(lambda _, s=spin: s.setValue(max(0, s.value() - 1)))
            inc_btn.clicked.connect(lambda _, s=spin: s.setValue(s.value() + 1))

            self._product_table.setCellWidget(row, 2, spin_container)

            # Subtotal
            subtotal = qty * p.unit_price
            sub_item = QTableWidgetItem(f"{int(subtotal // 1000):,}" if subtotal > 0 else "")
            sub_item.setFlags(sub_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            if has_qty:
                sub_item.setForeground(QColor(AppColors.SUCCESS))
                font = sub_item.font()
                font.setBold(True)
                sub_item.setFont(font)
            self._product_table.setItem(row, 3, sub_item)

        self._update_total()

    def _filter_products(self, text):
        self._load_products(text.strip())

    def _on_qty_changed(self, product_id, product_name, unit_price, qty):
        if qty > 0:
            self._selected[product_id] = {
                "product_id": product_id,
                "name": product_name,
                "unit_price": unit_price,
                "qty": qty,
            }
        else:
            self._selected.pop(product_id, None)

        # Update subtotal cell and row highlight
        for row in range(self._product_table.rowCount()):
            name_item = self._product_table.item(row, 0)
            if name_item and name_item.text() == product_name:
                has_qty = qty > 0
                # Update name highlight
                font = name_item.font()
                font.setBold(has_qty)
                name_item.setFont(font)
                name_item.setForeground(QColor(AppColors.PRIMARY) if has_qty else QColor(AppColors.TEXT))
                # Update subtotal
                sub_item = self._product_table.item(row, 3)
                if sub_item:
                    subtotal = qty * unit_price
                    sub_item.setText(f"{int(subtotal // 1000):,}" if subtotal > 0 else "")
                    sub_font = sub_item.font()
                    sub_font.setBold(has_qty)
                    sub_item.setFont(sub_font)
                    sub_item.setForeground(QColor(AppColors.SUCCESS) if has_qty else QColor(AppColors.TEXT_SECONDARY))
                break

        self._update_total()

    def _update_total(self):
        total = sum(v["qty"] * v["unit_price"] for v in self._selected.values())
        self._total_label.setText(f"{int(total // 1000):,}")

    def _confirm(self):
        self.result_items = [v for v in self._selected.values() if v["qty"] > 0]
        self.accept()

    def get_total(self) -> float:
        if self.result_items is None:
            return 0.0
        return sum(v["qty"] * v["unit_price"] for v in self.result_items)



class TaskDialog(QDialog):
    """Dialog thêm/sửa công việc"""

    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.result_data = None
        self._picked_items = []
        if task and task.notes:
            self._picked_items = self._parse_notes_items(task.notes)
        self._setup_ui()

    def _parse_notes_items(self, notes: str):
        """Parse stored product list from notes"""
        items = []
        for line in notes.splitlines():
            m = re.match(r'^(.+?) x (\d+) @ ([\d.]+)$', line.strip())
            if m:
                items.append({
                    "product_id": -1,
                    "name": m.group(1),
                    "qty": int(m.group(2)),
                    "unit_price": float(m.group(3)),
                })
        return items

    def keyPressEvent(self, event):
        """Handle Enter key"""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not event.modifiers() or event.modifiers() == Qt.KeyboardModifier.KeypadModifier:
                self._save()
                return
        super().keyPressEvent(event)

    def _setup_ui(self):
        self.setWindowTitle("Sửa công việc" if self.task else "Thêm công việc")
        self.setMinimumWidth(480)
        self.setMinimumHeight(380)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        # --- Type + Customer row ---
        row1 = QHBoxLayout()
        row1.setSpacing(12)

        type_group = QVBoxLayout()
        type_lbl = QLabel("Loại")
        type_lbl.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
        type_group.addWidget(type_lbl)
        self.type_combo = QComboBox()
        self.type_combo.setMinimumHeight(36)
        self.type_combo.addItem("Chưa thanh toán", "unpaid")
        self.type_combo.addItem("Chưa thu tiền", "uncollected")
        self.type_combo.addItem("Chưa giao đồ", "undelivered")
        self.type_combo.addItem("Chưa lấy đồ", "unreceived")
        self.type_combo.addItem("Khác", "other")
        if self.task:
            index = self.type_combo.findData(self.task.task_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        type_group.addWidget(self.type_combo)
        row1.addLayout(type_group, 2)

        cust_group = QVBoxLayout()
        cust_lbl = QLabel("Khách hàng / Máy")
        cust_lbl.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
        cust_group.addWidget(cust_lbl)
        self.customer_input = QLineEdit()
        self.customer_input.setMinimumHeight(36)
        self.customer_input.setPlaceholderText("MAY-1, tên khách...")
        machine_count = 46
        if self.parent():
            try:
                main_window = self.parent()
                while main_window.parent():
                    main_window = main_window.parent()
                if hasattr(main_window, "settings_view"):
                    machine_count = main_window.settings_view.current_machine_count
            except Exception:
                pass
        machines = [f"MAY-{i}" for i in range(1, machine_count + 1)]
        completer = QCompleter(machines, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setMaxVisibleItems(10)
        self.customer_input.setCompleter(completer)
        if self.task and self.task.customer_name:
            self.customer_input.setText(self.task.customer_name)
        cust_group.addWidget(self.customer_input)
        row1.addLayout(cust_group, 3)
        layout.addLayout(row1)

        # --- Amount + Product picker row ---
        amt_group = QVBoxLayout()
        amt_lbl = QLabel("Số tiền (nghìn)")
        amt_lbl.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
        amt_group.addWidget(amt_lbl)

        amount_row = QHBoxLayout()
        amount_row.setSpacing(8)
        self.amount_input = QLineEdit()
        self.amount_input.setMinimumHeight(36)
        self.amount_input.setPlaceholderText("35 hoặc 35 + 50")
        if self.task:
            self.amount_input.setText(str(int(self.task.amount // 1000)) if self.task.amount else "")
        self.amount_input.editingFinished.connect(self._eval_amount)
        amount_row.addWidget(self.amount_input)

        pick_btn = QPushButton("Chọn SP")
        pick_btn.setMinimumHeight(36)
        pick_btn.setFixedWidth(90)
        pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        pick_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 12px;
                font-weight: 700;
            }}
            QPushButton:hover {{ background: {AppColors.PRIMARY_HOVER}; }}
        """)
        pick_btn.clicked.connect(self._open_product_picker)
        amount_row.addWidget(pick_btn)
        amt_group.addLayout(amount_row)
        layout.addLayout(amt_group)

        # --- Picked products summary (scrollable chips) ---
        items_group = QVBoxLayout()
        items_group.setSpacing(4)
        items_header = QLabel("Sản phẩm đã chọn")
        items_header.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
        items_group.addWidget(items_header)

        self._items_scroll = QScrollArea()
        self._items_scroll.setWidgetResizable(True)
        self._items_scroll.setMaximumHeight(140)
        self._items_scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid {AppColors.BORDER};
                border-radius: 6px;
                background: #f8fafc;
            }}
            QScrollBar:vertical {{
                width: 6px; background: transparent;
            }}
            QScrollBar::handle:vertical {{
                background: {AppColors.BORDER}; border-radius: 3px; min-height: 20px;
            }}
        """)
        self._items_container = QWidget()
        self._items_flow = QVBoxLayout(self._items_container)
        self._items_flow.setContentsMargins(8, 6, 8, 6)
        self._items_flow.setSpacing(4)
        self._items_scroll.setWidget(self._items_container)

        self._empty_label = QLabel("— chưa chọn sản phẩm —")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; padding: 12px 0;")

        items_group.addWidget(self._items_scroll)
        self._refresh_items_label()
        layout.addLayout(items_group)

        layout.addStretch()

        # --- Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("secondary")
        cancel_btn.setMinimumHeight(40)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Lưu")
        save_btn.setObjectName("primary")
        save_btn.setMinimumHeight(40)
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _eval_amount(self):
        """Auto-evaluate expression"""
        text = self.amount_input.text().strip()
        if not text:
            return
        # Evaluate if expression
        if any(op in text for op in ('+', '-', '*', '/')):
            result = _eval_expression(text)
            # Display in thousands
            self.amount_input.setText(f"{int(result // 1000)}")

    def _open_product_picker(self):
        dialog = ProductPickerDialog(selected_items=self._picked_items, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._picked_items = dialog.result_items or []
            total = dialog.get_total()
            if total > 0:
                # Display in thousands
                self.amount_input.setText(str(int(total // 1000)))
            self._refresh_items_label()

    def _refresh_items_label(self):
        # Clear existing chips
        while self._items_flow.count():
            child = self._items_flow.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self._picked_items:
            self._items_flow.addWidget(self._empty_label)
            self._empty_label.show()
            return

        self._empty_label.hide()
        for idx, it in enumerate(self._picked_items):
            chip = QWidget()
            chip.setStyleSheet(f"""
                QWidget {{
                    background: white;
                    border: 1px solid {AppColors.BORDER};
                    border-radius: 4px;
                }}
            """)
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(8, 4, 4, 4)
            chip_layout.setSpacing(6)

            name_lbl = QLabel(it["name"])
            name_lbl.setStyleSheet(f"border: none; color: {AppColors.TEXT}; font-size: 12px; font-weight: 600;")
            chip_layout.addWidget(name_lbl)

            qty_lbl = QLabel(f"x{it['qty']}")
            qty_lbl.setStyleSheet(f"border: none; color: {AppColors.TEXT_SECONDARY}; font-size: 11px;")
            chip_layout.addWidget(qty_lbl)

            chip_layout.addStretch()

            sub_val = int(it["qty"] * it["unit_price"] // 1000)
            sub_lbl = QLabel(f"{sub_val:,}")
            sub_lbl.setStyleSheet(f"border: none; color: {AppColors.SUCCESS}; font-size: 12px; font-weight: 700;")
            chip_layout.addWidget(sub_lbl)

            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(22, 22)
            remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            remove_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent; color: {AppColors.TEXT_SECONDARY};
                    border: none; border-radius: 11px; font-size: 12px; font-weight: 700;
                }}
                QPushButton:hover {{ background: {AppColors.ERROR}; color: white; }}
            """)
            remove_btn.clicked.connect(lambda _, i=idx: self._remove_item(i))
            chip_layout.addWidget(remove_btn)

            self._items_flow.addWidget(chip)

        self._items_flow.addStretch()

    def _remove_item(self, index):
        if 0 <= index < len(self._picked_items):
            self._picked_items.pop(index)
            total = sum(it["qty"] * it["unit_price"] for it in self._picked_items)
            if total > 0:
                self.amount_input.setText(str(int(total // 1000)))
            else:
                self.amount_input.clear()
            self._refresh_items_label()

    def _save(self):
        customer = self.customer_input.text().strip()
        task_type = self.type_combo.currentText()
        desc = f"{customer} - {task_type}" if customer else task_type

        # Parse amount - auto-convert from thousands
        amount = _eval_expression(self.amount_input.text())

        # Encode picked items
        if self._picked_items:
            notes = "\n".join(
                f"{it['name']} x {it['qty']} @ {it['unit_price']}"
                for it in self._picked_items
            )
        else:
            notes = ""

        self.result_data = {
            "task_type": self.type_combo.currentData(),
            "description": desc,
            "customer_name": customer,
            "amount": amount,
            "notes": notes,
        }
        self.accept()



class TaskView(QWidget):
    """View quản lý công việc"""

    def __init__(self, container=None):
        super().__init__()
        self.container = container
        self.logger = container.get("logger") if container else None

        TaskRepository.create_table()

        self._reminder_timer = QTimer()
        self._reminder_timer.timeout.connect(self._check_pending_tasks)
        self._reminder_timer.start(300000)  # 5 minutes

        self._data_loaded = False
        self._setup_ui()

    def showEvent(self, event):
        """Lazy-load data"""
        super().showEvent(event)
        if not self._data_loaded:
            self._data_loaded = True
            self.refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QLabel("Ghi chú / Công việc")
        header.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {AppColors.TEXT};")
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self.type_filter = QComboBox()
        self.type_filter.addItem("Tất cả", "all")
        self.type_filter.addItem("Chưa thanh toán", "unpaid")
        self.type_filter.addItem("Chưa thu tiền", "uncollected")
        self.type_filter.addItem("Chưa giao đồ", "undelivered")
        self.type_filter.addItem("Chưa lấy đồ", "unreceived")
        self.type_filter.addItem("Khác", "other")
        self.type_filter.currentIndexChanged.connect(self.refresh_list)
        toolbar.addWidget(QLabel("Lọc:"))
        toolbar.addWidget(self.type_filter)

        self.show_completed = QCheckBox("Hiện việc đã xong")
        self.show_completed.stateChanged.connect(self.refresh_list)
        toolbar.addWidget(self.show_completed)

        toolbar.addStretch()

        add_btn = QPushButton("Thêm")
        add_btn.setObjectName("primary")
        add_btn.setFixedWidth(120)
        add_btn.clicked.connect(self._add_task)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self.stats_label)

        # Table
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)

    def _setup_table(self):
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Loại", "Mô tả", "Khách", "Tiền", "Thời gian", "Ghi chú", "Thao tác"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 110)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 80)
        self.table.setColumnWidth(4, 95)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 160)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)
        
        # Connect cell click to show product details
        self.table.cellClicked.connect(self._on_cell_clicked)

    def refresh_list(self):
        """Refresh task list"""
        try:
            task_type = self.type_filter.currentData()
            include_completed = self.show_completed.isChecked()

            if task_type == "all":
                tasks = TaskRepository.get_all(include_completed)
            else:
                tasks = TaskRepository.get_by_type(task_type, include_completed)

            pending_count = TaskRepository.count_pending()
            self.stats_label.setText(f"Tổng: {len(tasks)} việc | Chưa xong: {pending_count} việc")

            self._check_pending_tasks()

            self.table.setUpdatesEnabled(False)
            self.table.setRowCount(len(tasks))

            for row, task in enumerate(tasks):
                # Type
                type_item = QTableWidgetItem(task.type_display)
                type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if task.completed:
                    type_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                self.table.setItem(row, 0, type_item)

                # Description
                desc_item = QTableWidgetItem(task.description)
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if task.completed:
                    desc_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                    font = desc_item.font()
                    font.setStrikeOut(True)
                    desc_item.setFont(font)
                else:
                    font = desc_item.font()
                    font.setBold(True)
                    desc_item.setFont(font)
                self.table.setItem(row, 1, desc_item)

                # Customer
                customer_item = QTableWidgetItem(task.customer_name or "-")
                customer_item.setFlags(customer_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                customer_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if task.completed:
                    customer_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                self.table.setItem(row, 2, customer_item)

                # Amount
                amount_text = f"{int(task.amount // 1000):,}" if task.amount > 0 else "-"
                amount_item = QTableWidgetItem(amount_text)
                amount_item.setFlags(amount_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if task.completed:
                    amount_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                elif task.amount > 0:
                    self.table.setCellWidget(row, 3, self._create_badge(amount_text, AppColors.PRIMARY))
                    amount_item.setForeground(QColor("transparent"))
                else:
                    amount_item.setForeground(QColor(AppColors.TEXT_SECONDARY))

                self.table.setItem(row, 3, amount_item)

                # Time
                time_text = task.created_at.strftime("%d/%m %H:%M")
                time_item = QTableWidgetItem(time_text)
                time_item.setFlags(time_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if task.completed:
                    time_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                self.table.setItem(row, 4, time_item)

                # Notes
                raw_notes = task.notes or ""
                if raw_notes and " x " in raw_notes and " @ " in raw_notes:
                    lines = [l for l in raw_notes.splitlines() if " x " in l and " @ " in l]
                    notes_text = f"{len(lines)} SP"
                else:
                    notes_text = (raw_notes[:15] + "..." if len(raw_notes) > 15 else raw_notes or "-")
                notes_item = QTableWidgetItem(notes_text)
                notes_item.setFlags(notes_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                notes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if task.completed:
                    notes_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                self.table.setItem(row, 5, notes_item)

                # Actions
                actions = QWidget()
                actions_layout = QHBoxLayout(actions)
                actions_layout.setContentsMargins(2, 4, 2, 4)
                actions_layout.setSpacing(3)

                btn_style = """
                    QPushButton {{
                        background: {bg};
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 11px;
                        font-weight: 700;
                        padding: 0 6px;
                    }}
                    QPushButton:hover {{ background: {hover}; }}
                """

                if not task.completed:
                    done_btn = QPushButton("Xong")
                    done_btn.setFixedHeight(32)
                    done_btn.setStyleSheet(btn_style.format(bg=AppColors.SUCCESS, hover="#059669"))
                    done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    done_btn.clicked.connect(lambda _, tid=task.id: self._complete_task(tid))
                    actions_layout.addWidget(done_btn)

                edit_btn = QPushButton("Sửa")
                edit_btn.setFixedHeight(32)
                edit_btn.setStyleSheet(btn_style.format(bg=AppColors.PRIMARY, hover=AppColors.PRIMARY_HOVER))
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.clicked.connect(lambda _, tid=task.id: self._edit_task(tid))
                actions_layout.addWidget(edit_btn)

                del_btn = QPushButton("Xóa")
                del_btn.setFixedHeight(32)
                del_btn.setStyleSheet(btn_style.format(bg=AppColors.ERROR, hover="#B91C1C"))
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.clicked.connect(lambda _, tid=task.id: self._delete_task(tid))
                actions_layout.addWidget(del_btn)

                self.table.setCellWidget(row, 6, actions)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error refreshing task list: {e}", exc_info=True)
        finally:
            self.table.setUpdatesEnabled(True)

    def _create_badge(self, text, bg_color):
        """Create badge widget"""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 6, 4, 6)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge = QLabel(text)
        badge.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                border-radius: 10px;
                padding: 2px 10px;
                font-weight: bold;
                font-size: 12px;
            }}
        """)
        layout.addWidget(badge)
        return container

    def _on_cell_clicked(self, row: int, col: int):
        """Handle cell click to show product details"""
        try:
            # Get all tasks
            task_type = self.type_filter.currentData()
            include_completed = self.show_completed.isChecked()
            
            if task_type == "all":
                tasks = TaskRepository.get_all(include_completed)
            else:
                tasks = TaskRepository.get_by_type(task_type, include_completed)
            
            if row >= len(tasks):
                return
                
            task = tasks[row]
            
            # Check if task has product notes
            if not task.notes or not (" x " in task.notes and " @ " in task.notes):
                return
            
            # Show product details dialog
            self._show_product_details(task)
            
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error showing product details: {e}", exc_info=True)

    def _show_product_details(self, task):
        """Show dialog with product details"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Chi tiết sản phẩm - {task.customer_name or 'Khách'}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header info
        header = QLabel(f"<b>{task.description}</b>")
        header.setStyleSheet("font-size: 14px;")
        layout.addWidget(header)
        
        time_label = QLabel(f"Thời gian: {task.created_at.strftime('%d/%m/%Y %H:%M')}")
        time_label.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(time_label)
        
        # Separator
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {AppColors.BORDER};")
        layout.addWidget(sep)
        
        # Product table
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["Sản phẩm", "Số lượng", "Đơn giá", "Thành tiền"])
        
        header = table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        table.setColumnWidth(1, 100)
        table.setColumnWidth(2, 100)
        table.setColumnWidth(3, 120)
        
        table.verticalHeader().setVisible(False)
        table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        table.setAlternatingRowColors(True)
        
        # Parse products from notes
        products = []
        for line in task.notes.splitlines():
            m = re.match(r'^(.+?) x (\d+) @ ([\d.]+)', line.strip())
            if m:
                products.append({
                    "name": m.group(1),
                    "qty": int(m.group(2)),
                    "price": float(m.group(3)),
                })
        
        table.setRowCount(len(products))
        total = 0
        
        for row, prod in enumerate(products):
            # Name
            name_item = QTableWidgetItem(prod["name"])
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            table.setItem(row, 0, name_item)
            
            # Quantity
            qty_item = QTableWidgetItem(str(prod["qty"]))
            qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            table.setItem(row, 1, qty_item)
            
            # Unit price
            price_item = QTableWidgetItem(f"{int(prod['price'] // 1000):,}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            table.setItem(row, 2, price_item)
            
            # Subtotal
            subtotal = prod["qty"] * prod["price"]
            total += subtotal
            subtotal_item = QTableWidgetItem(f"{int(subtotal // 1000):,}")
            subtotal_item.setFlags(subtotal_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            subtotal_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            subtotal_item.setForeground(QColor(AppColors.PRIMARY))
            font = subtotal_item.font()
            font.setBold(True)
            subtotal_item.setFont(font)
            table.setItem(row, 3, subtotal_item)
        
        layout.addWidget(table, 1)
        
        # Total row
        total_row = QHBoxLayout()
        total_row.addStretch()
        total_label = QLabel("TỔNG CỘNG:")
        total_label.setStyleSheet("font-size: 14px; font-weight: 700;")
        total_row.addWidget(total_label)
        
        total_value = QLabel(f"{int(total // 1000):,} (nghìn)")
        total_value.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {AppColors.SUCCESS};")
        total_row.addWidget(total_value)
        layout.addLayout(total_row)
        
        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setObjectName("primary")
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()

    def _add_task(self):
        """Add task"""
        dialog = TaskDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            TaskRepository.add(d["task_type"], d["description"], d["customer_name"], d["amount"], d["notes"])
            self.refresh_list()

    def _edit_task(self, task_id: int):
        """Edit task"""
        task = TaskRepository.get_by_id(task_id)
        if not task:
            return
        dialog = TaskDialog(task=task, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            TaskRepository.update(task_id, d["task_type"], d["description"], d["customer_name"], d["amount"], d["notes"])
            self.refresh_list()

    def _complete_task(self, task_id: int):
        """Complete task"""
        TaskRepository.mark_completed(task_id)
        self.refresh_list()

    def _delete_task(self, task_id: int):
        """Delete task"""
        reply = QMessageBox.question(
            self, "Xác nhận", "Xóa công việc này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            TaskRepository.delete(task_id)
            self.refresh_list()

    def _check_pending_tasks(self):
        """Check pending tasks"""
        try:
            pending_count = TaskRepository.count_pending()
            if pending_count > 0:
                parent = self.parent()
                if parent:
                    main_window = parent
                    while main_window.parent():
                        main_window = main_window.parent()
                    if hasattr(main_window, "task_notif_label") and hasattr(main_window, "task_notif_box"):
                        main_window.task_notif_label.setText(f"Còn {pending_count} việc chưa xong!")
                        main_window.task_notif_box.show()
            else:
                parent = self.parent()
                if parent:
                    main_window = parent
                    while main_window.parent():
                        main_window = main_window.parent()
                    if hasattr(main_window, "task_notif_box"):
                        main_window.task_notif_box.hide()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking pending tasks: {e}", exc_info=True)
