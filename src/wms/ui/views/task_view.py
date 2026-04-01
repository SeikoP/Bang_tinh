"""
Task View - Quản lý ghi chú công việc
"""

import json
import re
import urllib.request
import urllib.parse
from pathlib import Path

from PyQt6.QtCore import Qt, QTimer, QByteArray
from PyQt6.QtGui import QColor, QPixmap
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
    """Dialog thêm/sửa công việc - đơn giản hóa"""

    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.result_data = None
        self._picked_items = []
        if task and task.notes:
            self._picked_items = self._parse_notes_items(task.notes)
        self._item_rows = []
        self._setup_ui()

    def _parse_notes_items(self, notes: str):
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
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not event.modifiers() or event.modifiers() == Qt.KeyboardModifier.KeypadModifier:
                self._save()
                return
        super().keyPressEvent(event)

    def _setup_ui(self):
        self.setWindowTitle("Sửa công việc" if self.task else "Thêm công việc")
        self.setMinimumWidth(520)
        self.setMaximumWidth(600)
        self.setStyleSheet(f"""
            QDialog {{ background: {AppColors.SURFACE}; }}
            QLabel {{ background: transparent; color: {AppColors.TEXT}; }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 20, 24, 20)

        # --- Type (hidden, always "Chưa thanh toán") ---
        self.type_combo = QComboBox()
        self.type_combo.addItem("Chưa thanh toán", "unpaid")
        if self.task and self.task.task_type != "unpaid":
            type_map = {"uncollected": "Chưa thu tiền", "undelivered": "Chưa giao đồ",
                        "unreceived": "Chưa lấy đồ", "other": "Khác"}
            display = type_map.get(self.task.task_type, self.task.task_type)
            self.type_combo.addItem(display, self.task.task_type)
            self.type_combo.setCurrentIndex(1)
            type_lbl = QLabel("Loại")
            type_lbl.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
            layout.addWidget(type_lbl)
            layout.addWidget(self.type_combo)

        # --- Customer ---
        cust_lbl = QLabel("Khách hàng / Máy")
        cust_lbl.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
        layout.addWidget(cust_lbl)
        self.customer_input = QLineEdit()
        self.customer_input.setMinimumHeight(38)
        self.customer_input.setPlaceholderText("VD: MAY-1, tên khách...")
        self.customer_input.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {AppColors.BORDER}; border-radius: 8px;
                padding: 0 12px; font-size: 13px; background: white;
            }}
            QLineEdit:focus {{ border-color: {AppColors.PRIMARY}; }}
        """)
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
        layout.addWidget(self.customer_input)

        # --- Product rows header ---
        prod_header = QHBoxLayout()
        prod_lbl = QLabel("Sản phẩm")
        prod_lbl.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px; font-weight: 600;")
        prod_header.addWidget(prod_lbl)
        prod_header.addStretch()

        add_row_btn = QPushButton("+ Thêm dòng")
        add_row_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_row_btn.setFixedHeight(28)
        add_row_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {AppColors.PRIMARY};
                border: 1px solid {AppColors.PRIMARY}; border-radius: 5px;
                font-size: 11px; font-weight: 600; padding: 0 10px;
            }}
            QPushButton:hover {{ background: rgba(16, 185, 129, 0.08); }}
        """)
        add_row_btn.clicked.connect(lambda: self._add_item_row())
        prod_header.addWidget(add_row_btn)
        layout.addLayout(prod_header)

        # --- Column labels ---
        col_labels = QHBoxLayout()
        col_labels.setContentsMargins(8, 0, 8, 0)
        col_labels.setSpacing(8)
        for text, stretch, width in [("Tên", 3, 0), ("SL", 0, 65), ("Giá (K)", 0, 85), ("", 0, 30)]:
            lbl = QLabel(text)
            lbl.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 10px; background: transparent;")
            if stretch:
                col_labels.addWidget(lbl, stretch)
            elif width:
                lbl.setFixedWidth(width)
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                col_labels.addWidget(lbl)
            else:
                col_labels.addWidget(lbl)
        layout.addLayout(col_labels)

        # --- Items container ---
        self._items_container = QWidget()
        self._items_container.setStyleSheet(f"background: {AppColors.BG_SECONDARY};")
        self._items_layout = QVBoxLayout(self._items_container)
        self._items_layout.setContentsMargins(0, 4, 0, 4)
        self._items_layout.setSpacing(6)

        self._items_scroll = QScrollArea()
        self._items_scroll.setWidgetResizable(True)
        self._items_scroll.setMinimumHeight(50)
        self._items_scroll.setMaximumHeight(400)
        self._items_scroll.setStyleSheet(f"""
            QScrollArea {{ border: 1px solid {AppColors.BORDER}; border-radius: 8px; background: {AppColors.BG_SECONDARY}; }}
            QScrollBar:vertical {{ width: 6px; background: transparent; }}
            QScrollBar::handle:vertical {{ background: {AppColors.BORDER}; border-radius: 3px; min-height: 20px; }}
        """)
        self._items_scroll.setWidget(self._items_container)
        layout.addWidget(self._items_scroll)

        # --- Total display (created before _add_item_row) ---
        self._total_label = QLabel("Thành tiền: 0")
        self._total_label.setStyleSheet(f"""
            font-size: 15px; font-weight: 800; color: {AppColors.SUCCESS};
            padding: 6px 0; background: transparent;
        """)
        self._total_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Pre-populate
        for it in self._picked_items:
            self._add_item_row(it["name"], it["qty"], it["unit_price"])
        if not self._picked_items:
            self._add_item_row()

        layout.addWidget(self._total_label)

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

    def _add_item_row(self, name="", qty=0, price=0.0):
        """Add a product input row: [name] [qty] [price] [x]"""
        row_widget = QWidget()
        row_widget.setStyleSheet(f"background: {AppColors.BG_SECONDARY};")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(8, 4, 8, 4)
        row_layout.setSpacing(8)

        INPUT_STYLE = f"""
            QLineEdit, QSpinBox {{
                border: 1.5px solid {AppColors.BORDER}; border-radius: 6px;
                padding: 0 8px; font-size: 13px; background: white;
                color: {AppColors.TEXT};
            }}
            QLineEdit:focus, QSpinBox:focus {{ border-color: {AppColors.PRIMARY}; }}
        """

        name_input = QLineEdit(name)
        name_input.setPlaceholderText("Tên SP")
        name_input.setMinimumHeight(34)
        name_input.setStyleSheet(INPUT_STYLE)
        row_layout.addWidget(name_input, 3)

        qty_input = QSpinBox()
        qty_input.setRange(1, 999)
        qty_input.setValue(qty if qty > 0 else 1)
        qty_input.setFixedWidth(65)
        qty_input.setMinimumHeight(34)
        qty_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qty_input.setStyleSheet(INPUT_STYLE)
        qty_input.valueChanged.connect(self._recalc_total)
        row_layout.addWidget(qty_input)

        price_input = QLineEdit(str(int(price // 1000)) if price > 0 else "")
        price_input.setPlaceholderText("VD: 40")
        price_input.setFixedWidth(85)
        price_input.setMinimumHeight(34)
        price_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_input.setStyleSheet(INPUT_STYLE)
        price_input.textChanged.connect(self._recalc_total)
        row_layout.addWidget(price_input)

        del_btn = QPushButton("✕")
        del_btn.setFixedSize(30, 30)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        del_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {AppColors.TEXT_SECONDARY};
                border: 1px solid {AppColors.BORDER}; border-radius: 15px;
                font-size: 12px; font-weight: 700;
            }}
            QPushButton:hover {{ background: {AppColors.ERROR}; color: white; border-color: {AppColors.ERROR}; }}
        """)
        del_btn.clicked.connect(lambda: self._remove_item_row(row_widget))
        row_layout.addWidget(del_btn)

        self._item_rows.append({"widget": row_widget, "name": name_input, "qty": qty_input, "price": price_input})
        self._items_layout.addWidget(row_widget)
        self._recalc_total()
        self._auto_resize()

    def _remove_item_row(self, widget):
        self._item_rows = [r for r in self._item_rows if r["widget"] != widget]
        widget.deleteLater()
        if not self._item_rows:
            self._add_item_row()
        self._recalc_total()
        QTimer.singleShot(50, self._auto_resize)

    def _auto_resize(self):
        """Expand dialog to fit item rows (up to screen limit)."""
        row_h = 46  # approx height per row
        count = len(self._item_rows)
        need = max(50, count * row_h + 12)
        cap = 400
        self._items_scroll.setMinimumHeight(min(need, cap))
        self.adjustSize()

    def _recalc_total(self):
        total = 0
        for r in self._item_rows:
            qty = r["qty"].value()
            price = _eval_expression(r["price"].text()) if r["price"].text().strip() else 0
            total += qty * price
        if total > 0:
            self._total_label.setText(f"Thành tiền: {int(total):,} đ  ({int(total // 1000):,}K)")
        else:
            self._total_label.setText("Thành tiền: 0")

    def _save(self):
        customer = self.customer_input.text().strip()
        task_type = self.type_combo.currentData()

        # Collect items
        items = []
        total = 0
        for r in self._item_rows:
            name = r["name"].text().strip()
            qty = r["qty"].value()
            price_text = r["price"].text().strip()
            price = _eval_expression(price_text) if price_text else 0
            if name and qty > 0 and price > 0:
                items.append({"name": name, "qty": qty, "unit_price": price})
                total += qty * price

        desc = f"{customer} - {self.type_combo.currentText()}" if customer else self.type_combo.currentText()

        notes = "\n".join(f"{it['name']} x {it['qty']} @ {it['unit_price']}" for it in items) if items else ""

        self.result_data = {
            "task_type": task_type,
            "description": desc,
            "customer_name": customer,
            "amount": total,
            "notes": notes,
        }
        self.accept()


class TaskCompletionPopup(QDialog):
    """Popup hiển thị khi ghi chú được tự động hoàn thành bởi thông báo ngân hàng.

    Shows: task info, product notes, and VietQR (if available).
    """

    def __init__(self, task, amount_text: str = "", parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle(f"✅ Hoàn thành — {task.note_code}")
        self.setFixedWidth(440)
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setStyleSheet(f"""
            QDialog {{
                background: {AppColors.SURFACE};
                border-radius: 12px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(20, 20, 20, 20)

        # ── Success banner ─────────────────────────────────────
        banner = QFrame()
        banner.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #10b981);
                border-radius: 10px;
                border: none;
            }
        """)
        b_lay = QHBoxLayout(banner)
        b_lay.setContentsMargins(16, 10, 16, 10)
        b_lay.setSpacing(10)

        check_icon = QLabel("✅")
        check_icon.setStyleSheet("font-size: 18px; background: transparent; border: none;")
        b_lay.addWidget(check_icon)

        b_text = QLabel(
            f"<span style='color:white; font-size:14px; font-weight:800;'>"
            f"{task.note_code} — ĐÃ THANH TOÁN</span>"
        )
        b_text.setStyleSheet("background: transparent; border: none;")
        b_text.setTextFormat(Qt.TextFormat.RichText)
        b_lay.addWidget(b_text, 1)

        if amount_text:
            amt_badge = QLabel(amount_text)
            amt_badge.setStyleSheet("""
                background: rgba(255,255,255,0.25); color: white;
                font-size: 12px; font-weight: 800; padding: 4px 12px;
                border-radius: 10px; border: none;
            """)
            b_lay.addWidget(amt_badge)

        root.addWidget(banner)

        # ── Task info ──────────────────────────────────────────
        info_frame = QFrame()
        info_frame.setStyleSheet(f"""
            QFrame {{
                background: {AppColors.BG_SECONDARY};
                border: 1px solid {AppColors.BORDER};
                border-radius: 8px;
            }}
        """)
        info_lay = QVBoxLayout(info_frame)
        info_lay.setContentsMargins(14, 10, 14, 10)
        info_lay.setSpacing(6)

        # Customer
        if task.customer_name:
            cust = QLabel(f"👤 {task.customer_name}")
            cust.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {AppColors.TEXT}; background: transparent; border: none;")
            info_lay.addWidget(cust)

        # Description
        if task.description:
            desc_lbl = QLabel(task.description)
            desc_lbl.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT_SECONDARY}; background: transparent; border: none;")
            desc_lbl.setWordWrap(True)
            info_lay.addWidget(desc_lbl)

        # Amount
        if task.amount:
            amt_lbl = QLabel(f"💰 {int(task.amount):,} đ")
            amt_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {AppColors.SUCCESS}; background: transparent; border: none;")
            info_lay.addWidget(amt_lbl)

        root.addWidget(info_frame)

        # ── Notes (product list) ───────────────────────────────
        notes_text = getattr(task, "notes", "") or ""
        if notes_text.strip():
            notes_frame = QFrame()
            notes_frame.setStyleSheet(f"""
                QFrame {{
                    background: {AppColors.SURFACE};
                    border: 1px solid {AppColors.BORDER};
                    border-radius: 8px;
                }}
            """)
            notes_lay = QVBoxLayout(notes_frame)
            notes_lay.setContentsMargins(14, 10, 14, 10)
            notes_lay.setSpacing(4)

            notes_title = QLabel("📋 Ghi chú sản phẩm")
            notes_title.setStyleSheet(f"""
                font-size: 10px; font-weight: 700; letter-spacing: 0.05em;
                color: {AppColors.TEXT_SECONDARY}; text-transform: uppercase;
                background: transparent; border: none;
            """)
            notes_lay.addWidget(notes_title)

            for line in notes_text.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                item_lbl = QLabel(f"  • {line}")
                item_lbl.setStyleSheet(f"font-size: 11px; color: {AppColors.TEXT}; background: transparent; border: none;")
                item_lbl.setWordWrap(True)
                notes_lay.addWidget(item_lbl)

            root.addWidget(notes_frame)

        # ── VietQR image ───────────────────────────────────────
        qr_url = getattr(task, "vietqr_url", "") or ""
        if qr_url:
            self._qr_label = QLabel("⏳ Đang tải QR...")
            self._qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._qr_label.setFixedHeight(180)
            self._qr_label.setStyleSheet(f"""
                border: 1px solid {AppColors.BORDER}; border-radius: 8px;
                background: {AppColors.BG_SECONDARY}; color: {AppColors.TEXT_SECONDARY};
            """)
            root.addWidget(self._qr_label)
            QTimer.singleShot(50, lambda: self._load_qr(qr_url))

        # ── Close button ───────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        close_btn = QPushButton("Đóng")
        close_btn.setFixedHeight(36)
        close_btn.setFixedWidth(100)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {AppColors.PRIMARY}; color: white; border: none;
                border-radius: 8px; font-weight: 700; font-size: 12px;
            }}
            QPushButton:hover {{ background: {AppColors.PRIMARY_HOVER}; }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        root.addLayout(btn_row)

    def _load_qr(self, url: str):
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read()
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(data))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    170, 170,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._qr_label.setPixmap(pixmap)
                self._qr_label.setText("")
            else:
                self._qr_label.setText("Không tải được QR")
        except Exception:
            self._qr_label.setText("Lỗi tải QR")


class PaymentLinkDialog(QDialog):
    """Dialog hiển thị QR VietQR và quản lý thanh toán"""

    def __init__(self, task, parent=None):
        super().__init__(parent)
        self.task = task
        self.setWindowTitle(f"Thanh Toán - {task.note_code}")
        self.setMinimumWidth(420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title row
        title = QLabel(f"<b>{task.note_code}</b> — {task.description}")
        title.setStyleSheet("font-size: 14px;")
        layout.addWidget(title)

        # Customer + Amount
        info = QLabel(
            f"Khách: <b>{task.customer_name or '—'}</b>  |  "
            f"Số tiền: <b>{int(task.amount):,} đ</b>"
        )
        info.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(info)

        # Transfer content row
        content_row = QHBoxLayout()
        tc_label = QLabel("Nội dung CK:")
        tc_label.setStyleSheet("font-size: 12px;")
        self._tc_value = QLineEdit(task.transfer_content or task.note_code)
        self._tc_value.setReadOnly(True)
        self._tc_value.setStyleSheet(
            "font-weight: bold; font-size: 13px; background:#1e293b; color:#38bdf8; border-radius:5px;"
        )
        copy_btn = QPushButton("Copy")
        copy_btn.setFixedWidth(60)
        copy_btn.setFixedHeight(32)
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self._copy_content)
        content_row.addWidget(tc_label)
        content_row.addWidget(self._tc_value, 1)
        content_row.addWidget(copy_btn)
        layout.addLayout(content_row)

        # QR image placeholder
        self._qr_label = QLabel("⏳ Đang tải QR...")
        self._qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._qr_label.setFixedHeight(220)
        self._qr_label.setStyleSheet(
            "border: 1px solid #334155; border-radius: 8px; background: #0f172a; color: #94a3b8;"
        )
        layout.addWidget(self._qr_label)

        # Payment status badge
        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet("font-size: 13px; font-weight: bold; padding: 4px;")
        self._refresh_status()
        layout.addWidget(self._status_label)

        # URL row
        self._url_edit = QLineEdit(task.vietqr_url or "")
        self._url_edit.setReadOnly(True)
        self._url_edit.setPlaceholderText("Chưa tạo link QR (cấu hình tài khoản ngân hàng trong Cài đặt)")
        self._url_edit.setStyleSheet("font-size: 10px; color:#64748b;")
        layout.addWidget(self._url_edit)

        # Button row
        btn_row = QHBoxLayout()

        self._gen_btn = QPushButton("Tạo / Làm mới QR")
        self._gen_btn.setFixedHeight(36)
        self._gen_btn.setObjectName("primary")
        self._gen_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._gen_btn.clicked.connect(self._generate_qr)
        btn_row.addWidget(self._gen_btn)

        self._copy_link_btn = QPushButton("Copy link QR")
        self._copy_link_btn.setFixedHeight(36)
        self._copy_link_btn.setStyleSheet(
            "background: #3b82f6; color: white; border: none; border-radius: 6px; font-weight: bold; padding: 0 12px;"
            "QPushButton:hover { background: #2563eb; }"
        )
        self._copy_link_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_link_btn.clicked.connect(self._copy_qr_link)
        btn_row.addWidget(self._copy_link_btn)

        self._copy_msg_btn = QPushButton("Copy tin nhan TT")
        self._copy_msg_btn.setFixedHeight(36)
        self._copy_msg_btn.setStyleSheet(
            "background: #2563eb; color: white; border: none; border-radius: 6px; font-weight: bold; padding: 0 12px;"
            "QPushButton:hover { background: #1d4ed8; }"
        )
        self._copy_msg_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_msg_btn.clicked.connect(self._copy_payment_message)
        btn_row.addWidget(self._copy_msg_btn)

        self._paid_btn = QPushButton("Da TT")
        self._paid_btn.setFixedHeight(36)
        self._paid_btn.setStyleSheet(
            "background: #059669; color: white; border: none; border-radius: 6px; font-weight: bold;"
            "QPushButton:hover { background: #047857; }"
        )
        self._paid_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._paid_btn.clicked.connect(self._mark_paid)
        btn_row.addWidget(self._paid_btn)

        close_btn = QPushButton("Đóng")
        close_btn.setFixedHeight(36)
        close_btn.setFixedWidth(80)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)

        layout.addLayout(btn_row)

        # Disable paid button if already completed
        if task.payment_status in ("completed", "matched"):
            self._paid_btn.setEnabled(False)

        # Auto-load QR image if URL present
        if task.vietqr_url:
            QTimer.singleShot(50, self._load_qr_image)

    def _refresh_status(self):
        status_map = {
            "none": ("Chưa tạo QR", "#64748b"),
            "pending": ("⏳ Chờ thanh toán", "#d97706"),
            "matched": ("🔵 Đã khớp / Đang xử lý", "#2563eb"),
            "completed": ("✅ Đã thanh toán", "#059669"),
            "failed": ("❌ Lỗi / Thất bại", "#dc2626"),
        }
        text, color = status_map.get(self.task.payment_status, ("—", "#64748b"))
        self._status_label.setText(text)
        self._status_label.setStyleSheet(
            f"font-size: 13px; font-weight: bold; padding: 4px; color: {color};"
        )

    def _copy_content(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._tc_value.text())
        self._tc_value.selectAll()

    def _build_payment_message(self) -> str:
        """Build chat-friendly payment text for one-tap copy."""
        amount = int(self.task.amount or 0)
        amount_text = f"{amount:,} đ" if amount > 0 else "theo hoa don"
        transfer_content = (self._tc_value.text() or self.task.note_code).strip()
        qr_url = (self._url_edit.text() or "").strip()
        customer = (self.task.customer_name or "Khach").strip()

        lines = [
            f"Ma CK: {transfer_content}",
            f"So tien: {amount_text}",
            f"Khach: {customer}",
        ]
        if qr_url:
            lines.append(f"QR: {qr_url}")
        return "\n".join(lines)

    def _copy_payment_message(self):
        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText(self._build_payment_message())
        self._copy_msg_btn.setText("Đã copy!")
        QTimer.singleShot(1500, lambda: self._copy_msg_btn.setText("Copy tin nhắn TT"))

    def _copy_qr_link(self):
        """Copy the VietQR image URL to clipboard"""
        from PyQt6.QtWidgets import QApplication
        url = self._url_edit.text().strip()
        if url:
            QApplication.clipboard().setText(url)
            self._copy_link_btn.setText("Đã copy!")
            QTimer.singleShot(1500, lambda: self._copy_link_btn.setText("Copy link QR"))

    def _generate_qr(self):
        """Build VietQR URL from bank settings and update task"""
        cfg_path = Path(__file__).parents[3] / "config" / "bank_settings.json"
        if not cfg_path.exists():
            QMessageBox.warning(self, "Thiếu cấu hình",
                "Chưa cấu hình tài khoản ngân hàng.\nVui lòng vào Cài đặt → Tài khoản NH để nhập thông tin.")
            return

        try:
            bank = json.loads(cfg_path.read_text(encoding="utf-8"))
        except Exception as e:
            QMessageBox.warning(self, "Lỗi", f"Không đọc được cấu hình ngân hàng: {e}")
            return

        bin_code = bank.get("bin", "")
        account = bank.get("account", "")
        holder = bank.get("holder", "")

        if not bin_code or not account:
            QMessageBox.warning(self, "Thiếu thông tin",
                "Cần nhập BIN ngân hàng và số tài khoản trong Cài đặt.")
            return

        # Build detailed transfer content: GC{id} + customer + product summary
        parts = [self.task.note_code]
        if self.task.customer_name:
            # Abbreviate customer name (first word only to save space)
            cust_short = self.task.customer_name.split()[0] if self.task.customer_name.strip() else ""
            if cust_short:
                parts.append(cust_short)

        # Summarize products from notes: count items
        notes_text = getattr(self.task, "notes", "") or ""
        product_lines = [l.strip() for l in notes_text.strip().split("\n") if l.strip()]
        if product_lines:
            total_qty = 0
            for line in product_lines:
                # Parse "Name x Qty @ Price" format
                import re as _re
                qty_match = _re.search(r'x\s*(\d+)', line)
                if qty_match:
                    total_qty += int(qty_match.group(1))
                else:
                    total_qty += 1
            parts.append(f"{len(product_lines)}SP")
            if total_qty > len(product_lines):
                parts.append(f"SL{total_qty}")

        amount_k = int(self.task.amount // 1000) if self.task.amount else 0
        if amount_k > 0:
            parts.append(f"{amount_k}K")
        tc = " ".join(parts)

        # VietQR addInfo limit is ~50 chars for most banks
        if len(tc) > 50:
            tc = tc[:47] + "..."

        amount = int(self.task.amount)
        url = (
            f"https://img.vietqr.io/image/{bin_code}-{account}-compact.png"
            f"?amount={amount}&addInfo={urllib.parse.quote(tc)}"
            f"&accountName={urllib.parse.quote(holder)}"
        )

        TaskRepository.update_payment(self.task.id, "pending", url, tc)
        TaskRepository.log_event(self.task.id, "qr_created", f"VietQR URL generated, amount={amount}")

        self.task.payment_status = "pending"
        self.task.vietqr_url = url
        self.task.transfer_content = tc
        self._url_edit.setText(url)
        self._tc_value.setText(tc)
        self._refresh_status()
        self._load_qr_image()

    def _load_qr_image(self):
        """Download and display QR image"""
        url = self.task.vietqr_url
        if not url:
            return
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                data = resp.read()
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(data))
            if not pixmap.isNull():
                pixmap = pixmap.scaled(
                    200, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._qr_label.setPixmap(pixmap)
                self._qr_label.setText("")
            else:
                self._qr_label.setText("Không tải được ảnh QR")
        except Exception as e:
            self._qr_label.setText(f"Lỗi tải QR: {e}")

    def _mark_paid(self):
        TaskRepository.complete_payment(self.task.id, source="Manual/Desktop")
        TaskRepository.log_event(self.task.id, "payment_completed", "Marked paid manually on desktop")
        self.task.payment_status = "completed"
        self._refresh_status()
        self._paid_btn.setEnabled(False)
        QMessageBox.information(self, "OK", f"{self.task.note_code} đã được đánh dấu là ĐÃ THANH TOÁN.")


class ManualReviewDialog(QDialog):
    """Review queue for payment events that require manual confirmation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manual Review - Chuyen khoan khong ma")
        self.setMinimumWidth(900)
        self.setMinimumHeight(500)
        self._setup_ui()
        self.refresh_events()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        hint = QLabel("Danh sach giao dich khong co ma GC/INV hoac khong tim thay ghi chu pending.")
        hint.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(hint)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Thời gian", "Nguồn", "Số tiền", "Nội dung CK", "Nội dung thông báo"])
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(1, 140)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 180)
        layout.addWidget(self.table, 1)

        row = QHBoxLayout()
        self._stats = QLabel("")
        self._stats.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px;")
        row.addWidget(self._stats)
        row.addStretch()

        refresh_btn = QPushButton("Lam moi")
        refresh_btn.clicked.connect(self.refresh_events)
        row.addWidget(refresh_btn)

        copy_btn = QPushButton("Copy dong da chon")
        copy_btn.clicked.connect(self._copy_selected)
        row.addWidget(copy_btn)

        resolve_btn = QPushButton("Danh dau da xu ly")
        resolve_btn.setObjectName("primary")
        resolve_btn.clicked.connect(self._resolve_selected)
        row.addWidget(resolve_btn)

        close_btn = QPushButton("Dong")
        close_btn.clicked.connect(self.accept)
        row.addWidget(close_btn)

        layout.addLayout(row)

    def refresh_events(self):
        events = TaskRepository.get_manual_review_events(limit=300)
        self.table.setRowCount(len(events))

        for row, ev in enumerate(events):
            metadata = {}
            if ev.metadata:
                try:
                    metadata = json.loads(ev.metadata)
                except Exception:
                    metadata = {}

            source = metadata.get("source") or metadata.get("package") or "unknown"
            amount = str(metadata.get("amount", ""))
            transfer_content = str(metadata.get("transfer_content", ""))
            content = str(metadata.get("content", ""))
            time_text = ev.created_at.strftime("%d/%m %H:%M:%S")

            cells = [time_text, source, amount, transfer_content, content]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    item.setData(Qt.ItemDataRole.UserRole, ev.id)
                self.table.setItem(row, col, item)

        self._stats.setText(f"Can manual review: {len(events)} giao dich")

    def _selected_event_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        cell = self.table.item(row, 0)
        if not cell:
            return None
        return cell.data(Qt.ItemDataRole.UserRole)

    def _copy_selected(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "Thông báo", "Hãy chọn 1 dòng để copy.")
            return

        parts = []
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            item = self.table.item(row, col)
            value = item.text() if item else ""
            parts.append(f"{header}: {value}")

        from PyQt6.QtWidgets import QApplication
        QApplication.clipboard().setText("\n".join(parts))
        QMessageBox.information(self, "Đã copy", "Đã copy thông tin giao dịch vào clipboard.")

    def _resolve_selected(self):
        event_id = self._selected_event_id()
        if not event_id:
            QMessageBox.information(self, "Thông báo", "Hãy chọn 1 dòng trước.")
            return

        TaskRepository.delete_event(int(event_id))
        self.refresh_events()


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
        self.type_filter.currentIndexChanged.connect(self.refresh_list)
        toolbar.addWidget(QLabel("Lọc:"))
        toolbar.addWidget(self.type_filter)

        self.show_completed = QCheckBox("Hiện việc đã xong")
        self.show_completed.stateChanged.connect(self.refresh_list)
        toolbar.addWidget(self.show_completed)

        self.manual_review_btn = QPushButton("Manual Review (0)")
        self.manual_review_btn.setFixedWidth(170)
        self.manual_review_btn.clicked.connect(self._open_manual_review)
        toolbar.addWidget(self.manual_review_btn)

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

    def _update_manual_review_badge(self):
        pending = TaskRepository.count_manual_review_events()
        self.manual_review_btn.setText(f"Manual Review ({pending})")
        if pending > 0:
            self.manual_review_btn.setStyleSheet(
                "background: #dc2626; color: white; border: none; border-radius: 6px; font-weight: bold; padding: 6px 10px;"
            )
        else:
            self.manual_review_btn.setStyleSheet("")

    def _open_manual_review(self):
        dlg = ManualReviewDialog(parent=self)
        dlg.exec()
        self._update_manual_review_badge()

    def _setup_table(self):
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Loại", "Khách", "Tiền", "Thanh toán", "Thao tác"])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 120)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 120)
        self.table.setColumnWidth(4, 220)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(44)

        # Connect row double-click to show details
        self.table.cellDoubleClicked.connect(self._on_cell_clicked)

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
            self._update_manual_review_badge()

            self._check_pending_tasks()

            self.table.setUpdatesEnabled(False)
            self.table.setRowCount(len(tasks))

            for row, task in enumerate(tasks):
                # Type (col 0)
                type_item = QTableWidgetItem(task.type_display)
                type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if task.completed:
                    type_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                self.table.setItem(row, 0, type_item)

                # Customer (col 1)
                cust_text = task.customer_name or "-"
                if task.completed:
                    customer_item = QTableWidgetItem(cust_text)
                    customer_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                    font = customer_item.font()
                    font.setStrikeOut(True)
                    customer_item.setFont(font)
                else:
                    customer_item = QTableWidgetItem(cust_text)
                    font = customer_item.font()
                    font.setBold(True)
                    customer_item.setFont(font)
                customer_item.setFlags(customer_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 1, customer_item)

                # Amount (col 2)
                amount_text = f"{int(task.amount // 1000):,}" if task.amount > 0 else "-"
                amount_item = QTableWidgetItem(amount_text)
                amount_item.setFlags(amount_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if task.completed:
                    amount_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                elif task.amount > 0:
                    self.table.setCellWidget(row, 2, self._create_badge(amount_text, AppColors.PRIMARY))
                    amount_item.setForeground(QColor("transparent"))
                else:
                    amount_item.setForeground(QColor(AppColors.TEXT_SECONDARY))

                self.table.setItem(row, 2, amount_item)

                # Payment status (col 3)
                payment_display = task.payment_status_display
                if payment_display or task.task_type == "unpaid":
                    pay_badge_text = payment_display or "Chưa TT"
                    pay_color_map = {
                        "none":      "#475569",
                        "pending":   "#d97706",
                        "matched":   "#2563eb",
                        "completed": "#059669",
                        "failed":    "#dc2626",
                    }
                    pay_color = pay_color_map.get(task.payment_status, "#475569")
                    self.table.setCellWidget(row, 3, self._create_badge(pay_badge_text, pay_color))
                else:
                    empty_pay = QTableWidgetItem("-")
                    empty_pay.setFlags(empty_pay.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    empty_pay.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setItem(row, 3, empty_pay)

                # Actions (col 4)
                actions = QWidget()
                actions_layout = QHBoxLayout(actions)
                actions_layout.setContentsMargins(2, 4, 2, 4)
                actions_layout.setSpacing(4)

                btn_style = """
                    QPushButton {{
                        background: {bg};
                        color: white;
                        border: none;
                        border-radius: 5px;
                        font-size: 11px;
                        font-weight: 700;
                        padding: 0 8px;
                    }}
                    QPushButton:hover {{ background: {hover}; }}
                """

                if not task.completed:
                    done_btn = QPushButton("Xong")
                    done_btn.setFixedHeight(30)
                    done_btn.setStyleSheet(btn_style.format(bg=AppColors.SUCCESS, hover="#059669"))
                    done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    done_btn.clicked.connect(lambda _, tid=task.id: self._complete_task(tid))
                    actions_layout.addWidget(done_btn)

                    if task.task_type == "unpaid":
                        qr_btn = QPushButton("QR")
                        qr_btn.setFixedHeight(30)
                        qr_btn.setStyleSheet(btn_style.format(bg="#7c3aed", hover="#6d28d9"))
                        qr_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                        qr_btn.clicked.connect(lambda _, t=task: self._open_payment_dialog(t))
                        actions_layout.addWidget(qr_btn)

                edit_btn = QPushButton("Sửa")
                edit_btn.setFixedHeight(30)
                edit_btn.setStyleSheet(btn_style.format(bg=AppColors.PRIMARY, hover=AppColors.PRIMARY_HOVER))
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.clicked.connect(lambda _, tid=task.id: self._edit_task(tid))
                actions_layout.addWidget(edit_btn)

                del_btn = QPushButton("Xóa")
                del_btn.setFixedHeight(30)
                del_btn.setStyleSheet(btn_style.format(bg=AppColors.ERROR, hover="#B91C1C"))
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.clicked.connect(lambda _, tid=task.id: self._delete_task(tid))
                actions_layout.addWidget(del_btn)

                self.table.setCellWidget(row, 4, actions)

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
        """Handle double-click to show task details"""
        try:
            task_type = self.type_filter.currentData()
            include_completed = self.show_completed.isChecked()

            if task_type == "all":
                tasks = TaskRepository.get_all(include_completed)
            else:
                tasks = TaskRepository.get_by_type(task_type, include_completed)

            if row >= len(tasks):
                return

            self._show_product_details(tasks[row])

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error showing details: {e}", exc_info=True)

    def _show_product_details(self, task):
        """Show dialog with full task details"""
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Chi tiết - {task.customer_name or task.note_code}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(350)

        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header info
        header = QLabel(f"<b>{task.type_display}</b> — {task.customer_name or 'Không rõ'}")
        header.setStyleSheet("font-size: 15px;")
        layout.addWidget(header)

        # Time + amount info
        info_parts = [f"Thời gian: {task.created_at.strftime('%d/%m/%Y %H:%M')}"]
        if task.amount > 0:
            info_parts.append(f"Số tiền: <b>{int(task.amount):,} đ</b>")
        if task.payment_status_display:
            info_parts.append(f"Thanh toán: {task.payment_status_display}")
        info_label = QLabel("  |  ".join(info_parts))
        info_label.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(info_label)

        # Separator
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {AppColors.BORDER};")
        layout.addWidget(sep)

        # Product table (if has product notes)
        has_products = task.notes and " x " in task.notes and " @ " in task.notes
        if has_products:
            table = QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["Sản phẩm", "SL", "Đơn giá", "Thành tiền"])
            h = table.horizontalHeader()
            h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
            h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
            h.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
            table.setColumnWidth(1, 60)
            table.setColumnWidth(2, 100)
            table.setColumnWidth(3, 110)
            table.verticalHeader().setVisible(False)
            table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
            table.setAlternatingRowColors(True)

            products = []
            for line in task.notes.splitlines():
                m = re.match(r'^(.+?) x (\d+) @ ([\d.]+)', line.strip())
                if m:
                    products.append({"name": m.group(1), "qty": int(m.group(2)), "price": float(m.group(3))})

            table.setRowCount(len(products))
            total = 0
            for r, prod in enumerate(products):
                name_item = QTableWidgetItem(prod["name"])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                table.setItem(r, 0, name_item)
                qty_item = QTableWidgetItem(str(prod["qty"]))
                qty_item.setFlags(qty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                qty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(r, 1, qty_item)
                price_item = QTableWidgetItem(f"{int(prod['price'] // 1000):,}")
                price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                table.setItem(r, 2, price_item)
                subtotal = prod["qty"] * prod["price"]
                total += subtotal
                sub_item = QTableWidgetItem(f"{int(subtotal // 1000):,}")
                sub_item.setFlags(sub_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                sub_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                sub_item.setForeground(QColor(AppColors.PRIMARY))
                font = sub_item.font()
                font.setBold(True)
                sub_item.setFont(font)
                table.setItem(r, 3, sub_item)

            layout.addWidget(table, 1)

            total_row = QHBoxLayout()
            total_row.addStretch()
            total_row.addWidget(QLabel("TỔNG:"))
            tv = QLabel(f"{int(total // 1000):,} (nghìn)")
            tv.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {AppColors.SUCCESS};")
            total_row.addWidget(tv)
            layout.addLayout(total_row)
        elif task.notes:
            notes_label = QLabel(task.notes)
            notes_label.setWordWrap(True)
            notes_label.setStyleSheet(f"color: {AppColors.TEXT}; font-size: 12px; padding: 8px; background: #f8fafc; border-radius: 6px;")
            layout.addWidget(notes_label)

        # Close button
        close_btn = QPushButton("Đóng")
        close_btn.setObjectName("primary")
        close_btn.setFixedHeight(36)
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

    def _open_payment_dialog(self, task):
        """Open payment QR dialog for a task"""
        dlg = PaymentLinkDialog(task, parent=self)
        dlg.exec()
        self.refresh_list()

    def notify_payment_matched(self, note_id: int, note_code: str, amount: str):
        """Called when a payment is auto-matched (from main_window signal)"""
        self.refresh_list()

    def _check_pending_tasks(self):
        """Check pending tasks and show reminder in bottom ticker bar"""
        try:
            pending_count = TaskRepository.count_pending()
            if pending_count > 0:
                # Walk up to main window
                parent = self.parent()
                if parent:
                    main_window = parent
                    while main_window.parent():
                        main_window = main_window.parent()
                    if hasattr(main_window, "task_banner"):
                        main_window.task_banner.show_message(
                            f"📋 Còn {pending_count} ghi chú chưa xong!",
                            duration=10000,
                        )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error checking pending tasks: {e}", exc_info=True)
