"""
Task View - Quản lý ghi chú công việc
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QCheckBox, QDialog, QFormLayout,
    QLineEdit, QTextEdit, QMessageBox, QHeaderView, QCompleter
)
from PySide6.QtGui import QColor

from database.task_repository import TaskRepository
from ui.qt_theme import AppColors


class TaskDialog(QDialog):
    """Dialog thêm/sửa công việc"""

    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.task = task
        self.result_data = None
        self._setup_ui()

    def keyPressEvent(self, event):
        """Handle Enter key to submit dialog"""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if (
                not event.modifiers()
                or event.modifiers() == Qt.KeyboardModifier.KeypadModifier
            ):
                self._save()
                return
        super().keyPressEvent(event)

    def _setup_ui(self):
        self.setWindowTitle("Sửa công việc" if self.task else "Thêm công việc")
        self.setFixedWidth(500)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Form
        form = QFormLayout()
        form.setSpacing(12)

        # Task type
        self.type_combo = QComboBox()
        self.type_combo.addItem("💰 Chưa thanh toán", "unpaid")
        self.type_combo.addItem("💵 Chưa thu tiền", "uncollected")
        self.type_combo.addItem("📦 Chưa giao đồ", "undelivered")
        self.type_combo.addItem("📥 Chưa lấy đồ", "unreceived")
        self.type_combo.addItem("📝 Khác", "other")

        if self.task:
            index = self.type_combo.findData(self.task.task_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)

        form.addRow("Loại:", self.type_combo)

        # Customer name - QLineEdit with QCompleter for autocomplete
        self.customer_input = QLineEdit()
        self.customer_input.setPlaceholderText(
            "Nhập tên máy (VD: MAY-1) hoặc tên khách"
        )

        # Get machine count from settings (default 46)
        machine_count = 46
        if self.parent():
            try:
                main_window = self.parent()
                while main_window.parent():
                    main_window = main_window.parent()
                if hasattr(main_window, "settings_view"):
                    machine_count = main_window.settings_view.current_machine_count
            except:
                pass

        # Create machine list for autocomplete
        machines = [f"MAY-{i}" for i in range(1, machine_count + 1)]

        # Setup QCompleter for autocomplete
        completer = QCompleter(machines, self)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        completer.setMaxVisibleItems(10)
        self.customer_input.setCompleter(completer)

        if self.task and self.task.customer_name:
            self.customer_input.setText(self.task.customer_name)

        form.addRow("Khách hàng:", self.customer_input)

        # Amount
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("0")
        if self.task:
            self.amount_input.setText(str(int(self.task.amount)))
        form.addRow("Số tiền:", self.amount_input)

        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Ghi chú thêm (tuỳ chọn)")
        self.notes_input.setFixedHeight(80)
        if self.task:
            self.notes_input.setPlainText(self.task.notes)
        form.addRow("Ghi chú:", self.notes_input)

        layout.addLayout(form)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)

        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("💾 Lưu")
        save_btn.setObjectName("primary")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        # Auto-generate description from customer name and type
        customer = self.customer_input.text().strip()
        task_type = self.type_combo.currentText()

        # Generate description
        if customer:
            desc = f"{customer} - {task_type}"
        else:
            desc = task_type

        # Parse amount with shorthand support (10k, 1m, etc.)
        amount_text = self.amount_input.text().strip().lower()
        amount = 0
        if amount_text:
            try:
                if amount_text.endswith("k"):
                    amount = float(amount_text.replace("k", "")) * 1000
                elif amount_text.endswith("m"):
                    amount = float(amount_text.replace("m", "")) * 1000000
                else:
                    amount = float(amount_text)
            except ValueError:
                amount = 0

        self.result_data = {
            "task_type": self.type_combo.currentData(),
            "description": desc,
            "customer_name": customer,
            "amount": amount,
            "notes": self.notes_input.toPlainText().strip(),
        }
        self.accept()


class TaskView(QWidget):
    """View quản lý công việc"""

    def __init__(self, container=None):
        super().__init__()
        self.container = container
        self.logger = container.get("logger") if container else None

        # Initialize repository
        TaskRepository.create_table()

        # Timer for periodic reminder
        self._reminder_timer = QTimer()
        self._reminder_timer.timeout.connect(self._check_pending_tasks)
        self._reminder_timer.start(300000)  # Check every 5 minutes

        self._setup_ui()
        self.refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        # Header
        header = QLabel("📋 Ghi chú / Công việc")
        header.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {AppColors.TEXT};"
        )
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        # Filter by type
        self.type_filter = QComboBox()
        self.type_filter.addItem("Tất cả", "all")
        self.type_filter.addItem("💰 Chưa thanh toán", "unpaid")
        self.type_filter.addItem("💵 Chưa thu tiền", "uncollected")
        self.type_filter.addItem("📦 Chưa giao đồ", "undelivered")
        self.type_filter.addItem("📥 Chưa lấy đồ", "unreceived")
        self.type_filter.addItem("📝 Khác", "other")
        self.type_filter.currentIndexChanged.connect(self.refresh_list)
        toolbar.addWidget(QLabel("Lọc:"))
        toolbar.addWidget(self.type_filter)

        # Show completed checkbox
        self.show_completed = QCheckBox("Hiện việc đã xong")
        self.show_completed.stateChanged.connect(self.refresh_list)
        toolbar.addWidget(self.show_completed)

        toolbar.addStretch()

        # Add button
        add_btn = QPushButton("➕ Thêm công việc")
        add_btn.setObjectName("primary")
        add_btn.setFixedWidth(180)
        add_btn.clicked.connect(self._add_task)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        # Stats
        self.stats_label = QLabel()
        self.stats_label.setStyleSheet(
            f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px;"
        )
        layout.addWidget(self.stats_label)

        # Table
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)

    def _setup_table(self):
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Loại",
                "Mô tả",
                "Khách hàng",
                "Số tiền",
                "Thời gian",
                "Ghi chú",
                "Thao tác",
            ]
        )

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 150)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 100)
        self.table.setColumnWidth(4, 120)
        self.table.setColumnWidth(5, 100)
        self.table.setColumnWidth(6, 180)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(60)

    def refresh_list(self):
        """Refresh task list"""
        try:
            # Get filter
            task_type = self.type_filter.currentData()
            include_completed = self.show_completed.isChecked()

            # Get tasks
            if task_type == "all":
                tasks = TaskRepository.get_all(include_completed)
            else:
                tasks = TaskRepository.get_by_type(task_type, include_completed)

            # Update stats
            pending_count = TaskRepository.count_pending()
            self.stats_label.setText(
                f"Tổng: {len(tasks)} việc | Chưa xong: {pending_count} việc"
            )

            # Check and update pending task notification
            self._check_pending_tasks()

            # Update table
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
                customer_item.setFlags(
                    customer_item.flags() & ~Qt.ItemFlag.ItemIsEditable
                )
                customer_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if task.completed:
                    customer_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                self.table.setItem(row, 2, customer_item)

                # Amount: Use true badge widget for visibility
                amount_text = f"{task.amount:,.0f}" if task.amount > 0 else "-"
                amount_item = QTableWidgetItem(amount_text)
                amount_item.setFlags(amount_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                amount_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                if task.completed:
                    amount_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                elif task.amount > 0:
                    self.table.setCellWidget(
                        row, 3, self._create_badge(amount_text, AppColors.PRIMARY)
                    )
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
                notes_text = (
                    task.notes[:20] + "..."
                    if len(task.notes) > 20
                    else task.notes or "-"
                )
                notes_item = QTableWidgetItem(notes_text)
                notes_item.setFlags(notes_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                notes_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if task.completed:
                    notes_item.setForeground(QColor(AppColors.TEXT_SECONDARY))
                self.table.setItem(row, 5, notes_item)

                # Actions
                actions = QWidget()
                actions_layout = QHBoxLayout(actions)
                actions_layout.setContentsMargins(4, 8, 4, 8)
                actions_layout.setSpacing(6)

                if not task.completed:
                    # Complete button
                    complete_btn = QPushButton("✅")
                    complete_btn.setFixedSize(40, 44)
                    complete_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: {AppColors.SUCCESS};
                            color: white;
                            border: none;
                            border-radius: 6px;
                            font-size: 18px;
                        }}
                        QPushButton:hover {{ background: #059669; }}
                    """)
                    complete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                    complete_btn.clicked.connect(
                        lambda _, tid=task.id: self._complete_task(tid)
                    )
                    actions_layout.addWidget(complete_btn)

                # Edit button
                edit_btn = QPushButton("✏️")
                edit_btn.setFixedSize(40, 44)
                edit_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {AppColors.PRIMARY};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 16px;
                    }}
                    QPushButton:hover {{ background: {AppColors.PRIMARY_HOVER}; }}
                """)
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.clicked.connect(lambda _, tid=task.id: self._edit_task(tid))
                actions_layout.addWidget(edit_btn)

                # Delete button
                del_btn = QPushButton("🗑️")
                del_btn.setFixedSize(40, 44)
                del_btn.setStyleSheet(f"""
                    QPushButton {{
                        background: {AppColors.ERROR};
                        color: white;
                        border: none;
                        border-radius: 6px;
                        font-size: 16px;
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

    def _add_task(self):
        """Add new task"""
        dialog = TaskDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            TaskRepository.add(
                d["task_type"],
                d["description"],
                d["customer_name"],
                d["amount"],
                d["notes"],
            )
            self.refresh_list()

    def _edit_task(self, task_id: int):
        """Edit task"""
        task = TaskRepository.get_by_id(task_id)
        if not task:
            return

        dialog = TaskDialog(task=task, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            TaskRepository.update(
                task_id,
                d["task_type"],
                d["description"],
                d["customer_name"],
                d["amount"],
                d["notes"],
            )
            self.refresh_list()

    def _complete_task(self, task_id: int):
        """Mark task as completed"""
        TaskRepository.mark_completed(task_id)
        self.refresh_list()

    def _delete_task(self, task_id: int):
        """Delete task"""
        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Xóa công việc này?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            TaskRepository.delete(task_id)
            self.refresh_list()

    def _check_pending_tasks(self):
        """Check and show reminder for pending tasks"""
        try:
            pending_count = TaskRepository.count_pending()
            if pending_count > 0:
                # Show notification in parent window if available
                parent = self.parent()
                if parent:
                    # Find main window
                    main_window = parent
                    while main_window.parent():
                        main_window = main_window.parent()

                    # Update task notification
                    if hasattr(main_window, "task_notif_label") and hasattr(
                        main_window, "task_notif_box"
                    ):
                        main_window.task_notif_label.setText(
                            f"⚠️ Còn {pending_count} việc chưa xong!"
                        )
                        main_window.task_notif_box.show()
                        if self.logger:
                            self.logger.info(
                                f"Task notification shown: {pending_count} pending tasks"
                            )
            else:
                # Hide notification if no pending tasks
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
                padding: 2px 12px;
                font-weight: bold;
                font-size: 13px;
            }}
        """)
        l.addWidget(badge)
        return container
