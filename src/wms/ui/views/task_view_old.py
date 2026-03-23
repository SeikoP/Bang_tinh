"""
Task View - Quản lý ghi chú công việc
"""

import re

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QCheckBox, QComboBox, QCompleter, QDialog,
                             QFormLayout, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QMessageBox, QPushButton, QTableWidget,
                             QTableWidgetItem, QVBoxLayout, QWidget, QSpinBox)

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
    """Dialog chọn sản phẩm"""

    def __init__(self, selected_items=None, parent=None):
        super().__init__(parent)
        self._selected = {item["product_id"]: item.copy() for item in (selected_items or [])}
        self.result_items = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Chọn sản phẩm")
        self.setMinimumWidth(500)
        self.setMinimumHeight(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍 Tìm sản phẩm...")
        self._search.textChanged.connect(self._filter_products)
        layout.addWidget(self._search)

        # Product list
        self._product_table = QTableWidget()
        self._product_table.setColumnCount(4)
        self._product_table.setHorizontalHeaderLabels(["Sản phẩm", "Giá", "SL", "Tổng"])
        header = self._product_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._product_table.setColumnWidth(1, 80)
        self._product_table.setColumnWidth(2, 80)
        self._product_table.setColumnWidth(3, 90)
        self._product_table.verticalHeader().setVisible(False)
        self._product_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        layout.addWidget(self._product_table, 1)

        # Total
        total_row = QHBoxLayout()
        total_row.addStretch()
        self._total_label = QLabel("Tổng: 0")
        self._total_label.setStyleSheet(f"font-size: 16px; font-weight: 700; color: {AppColors.PRIMARY};")
        total_row.addWidget(self._total_label)
        layout.addLayout(total_row)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        cancel = QPushButton("Hủy")
        cancel.setObjectName("secondary")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        btn_row.addStretch()
        ok = QPushButton("Xác nhận")
        ok.setObjectName("primary")
        ok.clicked.connect(self._confirm)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

        self._load_products()

    def _load_products(self, keyword=""):
        try:
            from ...database.connection import get_connection
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
            # Name
            name_item = QTableWidgetItem(p.name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self._product_table.setItem(row, 0, name_item)

            # Unit price
            price_item = QTableWidgetItem(f"{int(p.unit_price // 1000):,}")
            price_item.setFlags(price_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._product_table.setItem(row, 1, price_item)

            # Qty spinner
            spin = QSpinBox()
            spin.setRange(0, 9999)
            spin.setValue(self._selected.get(p.id, {}).get("qty", 0))
            spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
            spin.valueChanged.connect(lambda val, pid=p.id, pname=p.name, price=p.unit_price, r=row: self._on_qty_changed(pid, pname, price, val, r))
            self._product_table.setCellWidget(row, 2, spin)

            # Subtotal
            qty = self._selected.get(p.id, {}).get("qty", 0)
            sub = qty * p.unit_price
            sub_item = QTableWidgetItem(f"{int(sub // 1000):,}" if sub > 0 else "-")
            sub_item.setFlags(sub_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._product_table.setItem(row, 3, sub_item)

        self._update_total()

    def _filter_products(self, text):
        self._load_products(text.strip())

    def _on_qty_changed(self, product_id, product_name, unit_price, qty, row):
        if qty > 0:
            self._selected[product_id] = {
                "product_id": product_id,
                "name": product_name,
                "unit_price": unit_price,
                "qty": qty,
            }
        else:
            self._selected.pop(product_id, None)

        # Update subtotal
        sub = qty * unit_price
        sub_item = QTableWidgetItem(f"{int(sub // 1000):,}" if sub > 0 else "-")
        sub_item.setFlags(sub_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        sub_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self._product_table.setItem(row, 3, sub_item)
        self._update_total()

    def _update_total(self):
        total = sum(v["qty"] * v["unit_price"] for v in self._selected.values())
        self._total_label.setText(f"Tổng: {int(total // 1000):,}")

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
        self.setFixedWidth(520)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        form.setSpacing(12)

        # Task type
        self.type_combo = QComboBox()
        self.type_combo.addItem("Chưa thanh toán", "unpaid")
        self.type_combo.addItem("Chưa thu tiền", "uncollected")
        self.type_combo.addItem("Chưa giao đồ", "undelivered")
        self.type_combo.addItem("Chưa lấy đồ", "unreceived")
        self.type_combo.addItem("Khác", "other")
        if self.task:
            index = self.type_combo.findData(self.task.task_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
        form.addRow("Loại:", self.type_combo)

        # Customer
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText("Nhập tên máy (VD: MAY-1) hoặc tên khách")
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
        form.addRow("Khách hàng:", self.customer_input)

        # Amount - auto-convert nghìn đồng
        amount_row = QHBoxLayout()
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("35 (nghìn) hoặc 35 + 50")
        if self.task:
            # Display in thousands
            self.amount_input.setText(str(int(self.task.amount // 1000)) if self.task.amount else "")
        self.amount_input.editingFinished.connect(self._eval_amount)
        amount_row.addWidget(self.amount_input)

        # Product picker
        pick_btn = QPushButton("🛒")
        pick_btn.setFixedWidth(50)
        pick_btn.setToolTip("Chọn sản phẩm")
        pick_btn.clicked.connect(self._open_product_picker)
        amount_row.addWidget(pick_btn)
        form.addRow("Số tiền:", amount_row)

        # Picked products summary
        self._items_label = QLabel()
        self._items_label.setWordWrap(True)
        self._items_label.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 11px;")
        self._refresh_items_label()
        form.addRow("Sản phẩm:", self._items_label)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        save_btn = QPushButton("Lưu")
        save_btn.setObjectName("primary")
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
        if not self._picked_items:
            self._items_label.setText("— chưa chọn —")
            return
        lines = [f"• {it['name']} x{it['qty']} = {int(it['qty'] * it['unit_price'] // 1000):,}"
                 for it in self._picked_items]
        self._items_label.setText("\n".join(lines))

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

        add_btn = QPushButton("➕ Thêm")
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

        self.table.setColumnWidth(0, 130)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 140)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(56)

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
                    notes_text = f"🛒 {len(lines)}"
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
                actions_layout.setContentsMargins(4, 6, 4, 6)
                actions_layout.setSpacing(4)

                if not task.completed:
                    done_btn = QPushButton("✓")
                    done_btn.setFixedSize(36, 44)
                    done_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {AppColors.SUCCESS};
                            color: white;
                            border: none;
                            border-radius: 6px;
                            font-size: 16px;
                        }}
                        QPushButton:hover {{ background: #059669; }}
                    """)
                    done_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    done_btn.clicked.connect(lambda _, tid=task.id: self._complete_task(tid))
                    actions_layout.addWidget(done_btn)

                edit_btn = QPushButton("✏")
                edit_btn.setFixedSize(36, 44)
                edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {AppColors.PRIMARY};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 14px;
                    }}
                    QPushButton:hover {{ background: {AppColors.PRIMARY_HOVER}; }}
                """)
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.clicked.connect(lambda _, tid=task.id: self._edit_task(tid))
                actions_layout.addWidget(edit_btn)

                del_btn = QPushButton("×")
                del_btn.setFixedSize(36, 44)
                del_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {AppColors.ERROR};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 20px;
                    }}
                    QPushButton:hover {{ background: #B91C1C; }}
                """)
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.clicked.connect(lambda _, tid=task.id: self._delete_task(tid))
                actions_layout.addWidget(del_btn)

                actions_layout.addStretch()
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
