from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QDialog, QFileDialog, QFormLayout, QFrame,
                             QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                             QMessageBox, QPushButton, QSizePolicy,
                             QTableWidget, QTableWidgetItem, QTextEdit,
                             QVBoxLayout, QWidget)

from database import HistoryRepository, ProductRepository, SessionRepository
from database.connection import get_connection
from services import CalculatorService, ReportService
from ui.qt_theme import AppColors
from ui.qt_views.product_dialog import ProductDialog


class DragDropTableWidget(QTableWidget):
    """Custom QTableWidget with drag & drop support"""

    def __init__(self, parent=None, on_drop_callback=None):
        super().__init__(parent)
        self.on_drop_callback = on_drop_callback

    def dropEvent(self, event):
        """Handle drop event to save new order"""
        super().dropEvent(event)
        if self.on_drop_callback:
            self.on_drop_callback()


class SaveSessionDialog(QDialog):
    """Dialog lưu phiên"""

    def __init__(self, total_amount: float, parent=None):
        super().__init__(parent)
        self.total_amount = total_amount
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
        self.setWindowTitle("Lưu phiên làm việc")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(28, 24, 28, 24)

        # Total
        total_label = QLabel(f"💰 Tổng cộng: {self.total_amount:,.0f} VNĐ")
        total_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 700;
            color: white;
            padding: 16px;
            background: {AppColors.SUCCESS};
            border-radius: 10px;
        """)
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(total_label)

        # Form
        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.shift_input = QLineEdit()
        self.shift_input.setPlaceholderText("VD: Ca sáng, Ca chiều...")
        form.addRow("Tên ca:", self.shift_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Ghi chú (tuỳ chọn)")
        self.notes_input.setFixedHeight(80)
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
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _save(self):
        self.result_data = {
            "shift_name": self.shift_input.text().strip() or "Phiên làm việc",
            "notes": self.notes_input.toPlainText().strip(),
        }
        self.accept()


class CalculationView(QWidget):
    """View bảng tính kèm quản lý danh mục sản phẩm"""

    def __init__(self, container=None, on_refresh_stock=None):
        super().__init__()
        # Inject services from container
        self.container = container
        if container:
            self.calc_service = container.get("calculator")
            self.report_service = container.get("report_service") or ReportService()
            self.product_repo = container.get("product_repo")
            self.session_repo = container.get("session_repo")
            self.history_repo = container.get("history_repo")
            self.logger = container.get("logger")
            # Get error handler from container
            from utils.error_handler import ErrorHandler

            self.error_handler = ErrorHandler(self.logger)
        else:
            # Fallback to direct instantiation
            self.calc_service = CalculatorService()
            self.report_service = ReportService()
            self.product_repo = ProductRepository
            self.session_repo = SessionRepository
            self.history_repo = HistoryRepository
            self.logger = None
            self.error_handler = None

        self.on_refresh_stock = on_refresh_stock
        self._next_focus = None
        self._widget_height = 28  # Chiều cao mặc định

        # Loading state flags to prevent duplicate actions
        self._is_loading = False
        self._is_saving = False
        self._last_report_data = {}  # Store HTML report data for sidebar re-renders

        self._setup_ui()
        self.refresh_table()
        self.refresh_product_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Setup calc tab directly (no sub-tabs)
        self._setup_calc_tab_direct(layout)

        # Setup prod tab separately (will be used by parent)
        self.prod_tab = QWidget()
        self._setup_prod_tab()

    def _setup_calc_tab(self):
        layout = QVBoxLayout(self.calc_tab)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

    def _setup_calc_tab_direct(self, parent_layout):
        layout = parent_layout
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        # Toolbar Area
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)

        # Action group left
        import_btn = QPushButton("📄 Nhập từ HTML")
        import_btn.setObjectName("secondary")
        import_btn.setFixedWidth(160)
        import_btn.clicked.connect(self._import_html)
        toolbar.addWidget(import_btn)

        toolbar.addStretch()

        # Primary Action
        save_btn = QPushButton("💾 Lưu toàn bộ phiên")
        save_btn.setObjectName("primary")
        save_btn.setFixedWidth(220)
        save_btn.clicked.connect(self._save_session)
        toolbar.addWidget(save_btn)

        layout.addLayout(toolbar)

        # Content Layout (Table + Report)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        # Table
        self.table = QTableWidget()
        self._setup_calc_table()
        content_layout.addWidget(self.table, 1)

        # Report frame (Clean Sidebar surface)
        self.report_frame = QFrame()
        self.report_frame.setFixedWidth(290)
        self.report_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {AppColors.BG_SECONDARY};
                border-radius: 12px;
            }}
        """)
        content_layout.addWidget(self.report_frame)
        self._show_report({})

        layout.addLayout(content_layout, 1)

        # Footer
        footer = QHBoxLayout()
        footer.setSpacing(16)

        info = QLabel("💡 Định dạng: 3t4 = 3 thùng 4 lon")
        info.setObjectName("subtitle")
        footer.addWidget(info)

        footer.addStretch()

        self.total_label = QLabel("TỔNG TIỀN: 0 VNĐ")
        self.total_label.setStyleSheet(f"""
            color: white;
            font-size: 18px;
            font-weight: 800;
            padding: 10px 32px;
            background: {AppColors.SUCCESS};
            border-radius: 10px;
        """)
        footer.addWidget(self.total_label)

        layout.addLayout(footer)

    def _setup_prod_tab(self):
        layout = QVBoxLayout(self.prod_tab)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(16)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm sản phẩm theo tên...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.refresh_product_list)
        toolbar.addWidget(self.search_input)

        toolbar.addStretch()

        # Import/Export buttons
        import_btn = QPushButton("📥 Nhập CSV")
        import_btn.setObjectName("secondary")
        import_btn.setFixedWidth(140)
        import_btn.clicked.connect(self._import_products)
        toolbar.addWidget(import_btn)

        export_btn = QPushButton("📤 Xuất CSV")
        export_btn.setObjectName("secondary")
        export_btn.setFixedWidth(140)
        export_btn.clicked.connect(self._export_products)
        toolbar.addWidget(export_btn)

        add_btn = QPushButton("➕ Thêm sản phẩm")
        add_btn.setObjectName("primary")
        add_btn.setFixedWidth(180)
        add_btn.clicked.connect(self._add_product)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        self.prod_table = DragDropTableWidget(on_drop_callback=self._save_product_order)
        self._setup_prod_table()
        layout.addWidget(self.prod_table, 1)

    def _setup_calc_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            [
                "Tên sản phẩm",
                "Giao ca",
                "Chốt ca",
                "Đã dùng",
                "Đơn giá",
                "Thành tiền",
            ]
        )

        header = self.table.horizontalHeader()
        # "Tên sản phẩm" stretches to fill, but is also interactive
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        # Numerical columns: Interactive (Excel-like) with min-width
        for i in [1, 2, 3, 4, 5]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
            header.setMinimumSectionSize(80)

        # Initial default widths
        self.table.setColumnWidth(1, 100)  # Giao ca
        self.table.setColumnWidth(2, 100)  # Chốt ca
        self.table.setColumnWidth(3, 90)  # Đã dùng
        self.table.setColumnWidth(4, 110)  # Đơn giá
        self.table.setColumnWidth(5, 120)  # Thành tiền

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(70)

        # Allow double-click to auto-fit (Qt default for Interactive)
        header.setSectionsClickable(True)
        header.setSectionsMovable(True)

    def _setup_prod_table(self):
        self.prod_table.setColumnCount(6)
        self.prod_table.setHorizontalHeaderLabels(
            ["STT", "Tên sản phẩm", "Đơn vị", "Quy đổi", "Đơn giá", "Thao tác"]
        )

        header = self.prod_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in [2, 3, 4, 5]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)

        self.prod_table.setColumnWidth(0, 40)
        self.prod_table.setColumnWidth(2, 75)
        self.prod_table.setColumnWidth(3, 75)
        self.prod_table.setColumnWidth(4, 110)
        self.prod_table.setColumnWidth(5, 200)

        self.prod_table.setAlternatingRowColors(True)
        self.prod_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.prod_table.verticalHeader().setVisible(False)
        self.prod_table.verticalHeader().setDefaultSectionSize(64)

        # Enable drag & drop
        self.prod_table.setDragEnabled(True)
        self.prod_table.setAcceptDrops(True)
        self.prod_table.setDragDropMode(QTableWidget.DragDropMode.InternalMove)
        self.prod_table.setDefaultDropAction(Qt.DropAction.MoveAction)

    def refresh_table(self, force=False):
        # Prevent duplicate refresh operations
        if self._is_loading and not force:
            return

        self._is_loading = True
        try:
            # Optimize table rendering by disabling updates during batch operations
            self.table.setUpdatesEnabled(False)

            # Use repository interface instead of direct access
            if self.container:
                sessions = self.session_repo.get_all()
            else:
                sessions = SessionRepository.get_all()

            self.table.setRowCount(len(sessions))
            total = 0
            for row, s in enumerate(sessions):
                p = s.product
                handover_disp = self.calc_service.format_to_display(
                    s.handover_qty, p.conversion, p.unit_char
                )
                closing_disp = self.calc_service.format_to_display(
                    s.closing_qty, p.conversion, p.unit_char
                )
                total += s.amount

                # Col 0: Product name (with unit hint)
                name_text = f"{p.name}"
                name_item = QTableWidgetItem(name_text)
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                name_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                font = name_item.font()
                font.setBold(True)
                name_item.setFont(font)
                name_item.setForeground(QColor(AppColors.TEXT))
                self.table.setItem(row, 0, name_item)

                # Col 1: Giao ca (editable)
                handover_container = QWidget()
                handover_layout = QVBoxLayout(handover_container)
                handover_layout.setContentsMargins(4, 4, 4, 4)
                handover_layout.setSpacing(0)

                handover_edit = QLineEdit(handover_disp if s.handover_qty > 0 else "0")
                handover_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                handover_edit.setMinimumHeight(self._widget_height)
                # Ensure it expands to fill column width
                handover_edit.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                handover_edit.setStyleSheet(f"""
                    QLineEdit {{
                        border: 2px solid {AppColors.BORDER};
                        border-radius: 5px;
                        padding: 0px;
                        font-weight: 700;
                        font-size: 13px;
                        background: white;
                    }}
                    QLineEdit:focus {{
                        border-color: {AppColors.PRIMARY};
                    }}
                """)
                handover_edit.setProperty("product_id", p.id)
                handover_edit.setProperty("conversion", p.conversion)
                handover_edit.setProperty("row", row)
                handover_edit.setProperty("col", 1)
                handover_edit.editingFinished.connect(self._on_handover_change)
                handover_edit.returnPressed.connect(self._on_return_pressed)
                handover_layout.addWidget(handover_edit)
                self.table.setCellWidget(row, 1, handover_container)

                # Col 2: Chốt ca (editable)
                closing_container = QWidget()
                closing_layout = QVBoxLayout(closing_container)
                closing_layout.setContentsMargins(4, 4, 4, 4)
                closing_layout.setSpacing(0)

                closing_edit = QLineEdit(closing_disp if s.closing_qty > 0 else "0")
                closing_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
                closing_edit.setMinimumHeight(self._widget_height)
                # Ensure it expands to fill column width
                closing_edit.setSizePolicy(
                    QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
                )
                closing_edit.setStyleSheet(f"""
                    QLineEdit {{
                        border: 2px solid {AppColors.BORDER};
                        border-radius: 5px;
                        padding: 0px;
                        font-weight: 700;
                        font-size: 13px;
                        background: white;
                    }}
                    QLineEdit:focus {{
                        border-color: {AppColors.PRIMARY};
                    }}
                """)
                closing_edit.setProperty("product_id", p.id)
                closing_edit.setProperty("conversion", p.conversion)
                closing_edit.setProperty("row", row)
                closing_edit.setProperty("col", 2)
                closing_edit.editingFinished.connect(self._on_closing_change)
                closing_edit.returnPressed.connect(self._on_return_pressed)
                closing_layout.addWidget(closing_edit)
                self.table.setCellWidget(row, 2, closing_container)

                # Col 3: Used Column - Highlight non-zero as a badge
                if s.used_qty > 0:
                    self._set_cell_helper(
                        self.table,
                        row,
                        3,
                        str(s.used_qty),
                        right=True,
                        fg="white",
                        bold=True,
                        bg=AppColors.ERROR,
                    )
                else:
                    self._set_cell_helper(
                        self.table,
                        row,
                        3,
                        "0",
                        right=True,
                        fg=AppColors.TEXT_SECONDARY,
                        bg=None,
                    )

                # Col 4: Unit Price
                self._set_cell_helper(
                    self.table,
                    row,
                    4,
                    f"{p.unit_price:,.0f}",
                    right=True,
                    fg=AppColors.TEXT,
                    bg=None,
                )

                # Col 5: Amount - Highlight non-zero with Primary badge
                if s.amount > 0:
                    self._set_cell_helper(
                        self.table,
                        row,
                        5,
                        f"{s.amount:,.0f}",
                        right=True,
                        fg="white",
                        bold=True,
                        bg=AppColors.PRIMARY,
                    )
                else:
                    self._set_cell_helper(
                        self.table,
                        row,
                        5,
                        "0",
                        right=True,
                        fg=AppColors.TEXT_SECONDARY,
                        bg=None,
                    )

            self.total_label.setText(f"TỔNG TIỀN: {total:,.0f} VNĐ")
            if self._next_focus:
                row, col = self._next_focus
                self._next_focus = None
                if row < self.table.rowCount():
                    wc = self.table.cellWidget(row, col)
                    if wc:
                        e = wc.findChild(QLineEdit)
                        if e:
                            e.setFocus()
                            e.selectAll()
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error refreshing calculation table: {str(e)}", exc_info=True
                )
            if self.error_handler:
                self.error_handler.handle(e, self)
        finally:
            # Re-enable table updates after batch operations
            self.table.setUpdatesEnabled(True)
            self._is_loading = False

    def refresh_product_list(self):
        # Prevent duplicate refresh operations
        if self._is_loading:
            return

        try:
            query = self.search_input.text().lower().strip()
            # Use repository interface
            if self.container:
                products = self.product_repo.get_all()
            else:
                products = ProductRepository.get_all()

            if query:
                products = [p for p in products if query in p.name.lower()]

            # Optimize table rendering by disabling updates during batch operations
            self.prod_table.setUpdatesEnabled(False)
            self.prod_table.setRowCount(len(products))
            for row, p in enumerate(products):
                self._set_cell_helper(
                    self.prod_table, row, 0, str(row + 1), center=True
                )
                name_item = QTableWidgetItem(p.name)
                name_item.setData(Qt.ItemDataRole.UserRole, p.id)  # Store ID
                name_item.setTextAlignment(
                    Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
                )
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                f = name_item.font()
                f.setBold(True)
                name_item.setFont(f)
                self.prod_table.setItem(row, 1, name_item)
                self._set_cell_helper(
                    self.prod_table,
                    row,
                    2,
                    p.large_unit,
                    center=True,
                    fg=AppColors.PRIMARY,
                )
                self._set_cell_helper(
                    self.prod_table,
                    row,
                    3,
                    str(p.conversion),
                    center=True,
                    fg=AppColors.TEXT,
                )
                self._set_cell_helper(
                    self.prod_table,
                    row,
                    4,
                    f"{p.unit_price:,.0f}",
                    center=True,
                    fg=AppColors.SUCCESS,
                    bold=True,
                )
                # Force layout - Dùng VBoxLayout để căn giữa
                actions = QWidget()
                actions.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

                actions_v_layout = QVBoxLayout(actions)
                actions_v_layout.setContentsMargins(0, 6, 0, 6)  # Tăng margin vertical
                actions_v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                actions_h_widget = QWidget()
                al = QHBoxLayout(actions_h_widget)
                al.setContentsMargins(10, 0, 10, 0)
                al.setAlignment(Qt.AlignmentFlag.AlignCenter)
                al.setSpacing(10)

                # Action Button Style
                btn_style = """
                    QPushButton {
                        border: 1px solid #cbd5e1;
                        border-radius: 4px;
                        background-color: white;
                        color: #334155;
                        font-size: 12px;
                        font-weight: 600;
                        padding: 0px;
                        margin: 0px;
                    }
                    QPushButton:hover { background-color: #f1f5f9; border-color: #94a3b8; }
                """
                del_style = """
                    QPushButton {
                        border: 1px solid #ef4444;
                        border-radius: 4px;
                        background-color: white;
                        color: #ef4444;
                        font-size: 12px;
                        font-weight: 600;
                        padding: 0px;
                        margin: 0px;
                    }
                    QPushButton:hover { background-color: #fef2f2; }
                """

                eb = QPushButton("Sửa")
                eb.setFixedSize(62, self._widget_height + 2)  # Buttons cao hơn 2px
                eb.setStyleSheet(btn_style)
                eb.setCursor(Qt.CursorShape.PointingHandCursor)
                eb.clicked.connect(lambda _, pid=p.id: self._edit_product(pid))
                al.addWidget(eb)

                db = QPushButton("Xóa")
                db.setFixedSize(62, self._widget_height + 2)  # Buttons cao hơn 2px
                db.setStyleSheet(del_style)
                db.setCursor(Qt.CursorShape.PointingHandCursor)
                db.clicked.connect(
                    lambda _, pid=p.id, name=p.name: self._delete_product(pid, name)
                )
                al.addWidget(db)

                actions_v_layout.addWidget(actions_h_widget)
                self.prod_table.setCellWidget(row, 5, actions)

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error refreshing product list: {str(e)}", exc_info=True
                )
        finally:
            # Re-enable table updates after batch operations
            self.prod_table.setUpdatesEnabled(True)

    def _on_return_pressed(self):
        w = self.sender()
        self._next_focus = (w.property("row") + 1, w.property("col"))

    def _on_handover_change(self):
        w = self.sender()
        self._update_qty(w, w.property("product_id"), w.property("conversion"), True)

    def _on_closing_change(self):
        w = self.sender()
        self._update_qty(w, w.property("product_id"), w.property("conversion"), False)

    def _update_qty(self, w, pid, conv, is_h):
        new = self.calc_service.parse_to_small_units(w.text(), conv)
        # Use repository interface
        if self.container:
            sessions = self.session_repo.get_all()
        else:
            sessions = SessionRepository.get_all()

        curr = next((s for s in sessions if s.product.id == pid), None)
        if not curr:
            return
        h = new if is_h else curr.handover_qty
        c = curr.closing_qty if is_h else new

        # Validate closing quantity
        if not is_h and c > h:
            # Show warning when closing exceeds handover
            product_name = curr.product.name
            handover_display = self.calc_service.format_to_display(
                h, conv, curr.product.unit_char
            )
            closing_display = self.calc_service.format_to_display(
                c, conv, curr.product.unit_char
            )

            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("⚠️ Cảnh báo: Chốt ca > Giao ca")
            msg.setText(f"<b style='font-size:14px;'>{product_name}</b>")
            msg.setInformativeText(
                f"<b>Chốt ca:</b> {closing_display}<br>"
                f"<b>Giao ca:</b> {handover_display}<br><br>"
                f"<span style='color:#dc2626;'>❌ Chốt ca không thể lớn hơn Giao ca!</span>"
            )
            msg.setDetailedText(
                "Nguyên nhân có thể:\n\n"
                "1. Tính toán sai số lượng chốt ca\n"
                "2. Sai số lượng giao ca (nhập thiếu)\n"
                "3. Sai tồn kho từ ca trước\n"
                "4. Nhập nhầm đơn vị (thùng/lon)\n"
                "5. Có nhập thêm hàng trong ca\n\n"
                "→ Vui lòng kiểm tra lại số liệu!"
            )
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec()

            c = h  # Auto-adjust to handover

        if is_h:
            c = h

        # Use repository interface
        if self.container:
            self.session_repo.update_qty(pid, h, c)
        else:
            SessionRepository.update_qty(pid, h, c)

        self.refresh_table()
        self._show_report(getattr(self, "_last_report_data", {}))
        if self.on_refresh_stock:
            self.on_refresh_stock()

    def _set_cell_helper(
        self,
        table,
        row,
        col,
        text,
        center=True,
        right=False,
        bold=False,
        bg=None,
        fg=None,
    ):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        # Alignment
        align = Qt.AlignmentFlag.AlignVCenter
        if right:
            align |= Qt.AlignmentFlag.AlignRight
        elif center:
            align |= Qt.AlignmentFlag.AlignCenter
        else:
            align |= Qt.AlignmentFlag.AlignLeft
        item.setTextAlignment(align)

        if bold:
            f = item.font()
            f.setBold(True)
            item.setFont(f)

        # Style - Use real labels for badges to guarantee visibility and style
        if bg and fg == "white":
            container = QWidget()
            l = QHBoxLayout(container)
            l.setContentsMargins(4, 6, 4, 6)
            l.setAlignment(align)

            badge = QLabel(text)
            badge.setStyleSheet(f"""
                QLabel {{
                    background-color: {bg};
                    color: white;
                    border-radius: 12px;
                    padding: 2px 12px;
                    font-weight: {"bold" if bold else "normal"};
                    font-size: 13px;
                }}
            """)
            l.addWidget(badge)
            table.setCellWidget(row, col, container)
            # Item remains for sorting but text is hidden behind widget
            item.setForeground(QColor("transparent"))
            table.setItem(row, col, item)
        else:
            if bg:
                item.setBackground(QColor(bg))
            if fg:
                item.setForeground(QColor(fg))
            table.setItem(row, col, item)

    def _add_product(self):
        try:
            dialog = ProductDialog(parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
                d = dialog.result_data
                # Use repository interface
                if self.container:
                    self.product_repo.add(
                        d["name"], d["large_unit"], d["conversion"], d["unit_price"]
                    )
                else:
                    ProductRepository.add(
                        d["name"], d["large_unit"], d["conversion"], d["unit_price"]
                    )

                self.refresh_product_list()
                self.refresh_table()
                if self.on_refresh_stock:
                    self.on_refresh_stock()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error adding product: {str(e)}", exc_info=True)
            if self.error_handler:
                self.error_handler.handle(e, self)

    def _edit_product(self, pid):
        try:
            # Use repository interface
            if self.container:
                product = self.product_repo.get_by_id(pid)
            else:
                product = ProductRepository.get_by_id(pid)

            if not product:
                return
            dialog = ProductDialog(product=product, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
                d = dialog.result_data
                # Use repository interface
                if self.container:
                    self.product_repo.update(
                        pid,
                        d["name"],
                        d["large_unit"],
                        d["conversion"],
                        d["unit_price"],
                    )
                else:
                    ProductRepository.update(
                        pid,
                        d["name"],
                        d["large_unit"],
                        d["conversion"],
                        d["unit_price"],
                    )

                self.refresh_product_list()
                self.refresh_table()
                if self.on_refresh_stock:
                    self.on_refresh_stock()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error editing product: {str(e)}", exc_info=True)
            if self.error_handler:
                self.error_handler.handle(e, self)

    def _delete_product(self, pid, name):
        try:
            reply = QMessageBox.question(
                self,
                "Xác nhận",
                f"Xóa sản phẩm '{name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                # Use repository interface
                if self.container:
                    self.product_repo.delete(pid)
                else:
                    ProductRepository.delete(pid)

                self.refresh_product_list()
                self.refresh_table()
                if self.on_refresh_stock:
                    self.on_refresh_stock()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error deleting product: {str(e)}", exc_info=True)
            if self.error_handler:
                self.error_handler.handle(e, self)

    def _import_html(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file HTML", "", "HTML Files (*.html *.htm)"
        )
        if not path:
            return
        res = self.report_service.parse_html_report(path)
        if res["success"]:
            self._last_report_data = res
            self._show_report(res)
        else:
            QMessageBox.warning(self, "Lỗi", f"Không thể đọc file: {res['error']}")

    def _show_report(self, data: dict):
        """
        Render the shift summary sidebar.

        Design principles:
        - Max 3 info blocks: revenue → warning (conditional) → detail (collapsed)
        - 3 colors only: MUTED (gray), ACCENT (soft green), WARN (soft orange)
        - No icons, no colored borders, whitespace > decoration
        - Readable in 3 seconds by fatigued operator
        """
        # --- Palette (2 colors) ---
        CLR_MUTED = AppColors.TEXT_SECONDARY  # #6B7280
        CLR_ACCENT = "#16a34a"  # soft green (revenue)

        # --- Computation (separated from rendering) ---
        summary = self._compute_shift_summary(data)

        # --- Clear previous layout ---
        if self.report_frame.layout():
            layout = self.report_frame.layout()
            while layout.count():
                item = layout.takeAt(0)
                w = item.widget()
                if w:
                    w.deleteLater()
                elif item.layout():
                    sub = item.layout()
                    while sub.count():
                        si = sub.takeAt(0)
                        if si.widget():
                            si.widget().deleteLater()
        else:
            layout = QVBoxLayout(self.report_frame)

        layout.setContentsMargins(20, 24, 20, 24)
        layout.setSpacing(0)

        # ── Block 1: Header + Revenue ──
        title = QLabel("Tổng hợp ca")
        title.setStyleSheet(
            f"font-size: 11px; font-weight: 600; color: {CLR_MUTED};"
            " letter-spacing: 0.5px; text-transform: uppercase;"
            " background: transparent; border: none;"
        )
        layout.addWidget(title)
        layout.addSpacing(10)

        revenue_val = summary["total_amount"]
        revenue_lbl = QLabel(f"{revenue_val:,.0f} đ" if revenue_val > 0 else "0 đ")
        revenue_lbl.setStyleSheet(
            f"font-size: 22px; font-weight: 800; color: {CLR_ACCENT};"
            " background: transparent; border: none;"
        )
        layout.addWidget(revenue_lbl)

        # Subtitle: product count (only if there's usage)
        used_count = summary["used_product_count"]
        total_count = summary["total_product_count"]
        if used_count > 0:
            subtitle = QLabel(f"{used_count} / {total_count} sản phẩm đã dùng")
            subtitle.setStyleSheet(
                f"font-size: 11px; color: {CLR_MUTED};"
                " background: transparent; border: none; margin-top: 2px;"
            )
            layout.addWidget(subtitle)

        # ── Block 2: HTML report data (only when imported) ──
        html_total = summary.get("html_actual_total", 0)
        count_50k = summary.get("html_count_50k", 0)

        if html_total > 0 or count_50k > 0:
            layout.addSpacing(16)

            sep = QLabel("Báo cáo HTML")
            sep.setStyleSheet(
                f"font-size: 10px; font-weight: 600; color: {CLR_MUTED};"
                " letter-spacing: 0.5px; text-transform: uppercase;"
                " background: transparent; border: none;"
            )
            layout.addWidget(sep)
            layout.addSpacing(6)

            if html_total > 0:
                row_html = QHBoxLayout()
                row_html.setContentsMargins(0, 0, 0, 0)
                lbl_actual = QLabel("Doanh thu thực tế")
                lbl_actual.setStyleSheet(
                    f"font-size: 11px; color: {AppColors.TEXT};"
                    " background: transparent; border: none;"
                )
                row_html.addWidget(lbl_actual)
                row_html.addStretch()
                val_actual = QLabel(f"{html_total:,.0f} đ")
                val_actual.setStyleSheet(
                    f"font-size: 13px; font-weight: 700; color: {CLR_ACCENT};"
                    " background: transparent; border: none;"
                )
                row_html.addWidget(val_actual)
                layout.addLayout(row_html)

            if count_50k > 0:
                layout.addSpacing(4)
                row_50k = QHBoxLayout()
                row_50k.setContentsMargins(0, 0, 0, 0)
                lbl_50k = QLabel("Lượt quay 50K")
                lbl_50k.setStyleSheet(
                    f"font-size: 11px; color: {AppColors.TEXT};"
                    " background: transparent; border: none;"
                )
                row_50k.addWidget(lbl_50k)
                row_50k.addStretch()
                val_50k = QLabel(f"{count_50k} lượt")
                val_50k.setStyleSheet(
                    f"font-size: 13px; font-weight: 700; color: {AppColors.TEXT};"
                    " background: transparent; border: none;"
                )
                row_50k.addWidget(val_50k)
                layout.addLayout(row_50k)

        # ── Block 3: Product detail (collapsible, default collapsed) ──
        products = summary["used_products"]
        if products:
            layout.addSpacing(16)

            toggle_btn = QPushButton(f"Chi tiết  ({len(products)} SP)")
            toggle_btn.setStyleSheet(
                f"font-size: 11px; font-weight: 600; color: {CLR_MUTED};"
                " background: transparent; border: none; text-align: left;"
                " padding: 0;"
            )
            toggle_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(toggle_btn)

            detail_container = QWidget()
            detail_container.setVisible(False)  # collapsed by default
            detail_layout = QVBoxLayout(detail_container)
            detail_layout.setContentsMargins(0, 8, 0, 0)
            detail_layout.setSpacing(6)

            for item in products:
                row = QHBoxLayout()
                row.setContentsMargins(0, 0, 0, 0)

                name_lbl = QLabel(item["name"])
                name_lbl.setStyleSheet(
                    f"font-size: 11px; color: {AppColors.TEXT};"
                    " font-weight: 500; background: transparent; border: none;"
                )
                name_lbl.setWordWrap(True)
                row.addWidget(name_lbl, 1)

                amt_lbl = QLabel(f"{item['amount']:,.0f}")
                amt_lbl.setStyleSheet(
                    f"font-size: 11px; font-weight: 700; color: {AppColors.TEXT};"
                    " background: transparent; border: none;"
                )
                amt_lbl.setAlignment(
                    Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                )
                row.addWidget(amt_lbl)

                detail_layout.addLayout(row)

            layout.addWidget(detail_container)

            # Toggle behavior
            def _toggle(_checked=False, container=detail_container, btn=toggle_btn):
                visible = not container.isVisible()
                container.setVisible(visible)
                arrow = "▾" if visible else "▸"
                btn.setText(f"{arrow} Chi tiết  ({len(products)} SP)")

            toggle_btn.setText(f"▸ Chi tiết  ({len(products)} SP)")
            toggle_btn.clicked.connect(_toggle)

        elif revenue_val == 0:
            # Empty state — single muted line
            layout.addSpacing(24)
            empty = QLabel("Chưa có dữ liệu ca")
            empty.setStyleSheet(
                f"font-size: 11px; color: {CLR_MUTED};"
                " background: transparent; border: none;"
            )
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(empty)

        layout.addStretch()
        self.report_frame.show()

    # ── Computation (separated from rendering) ──

    def _compute_shift_summary(self, html_data: dict) -> dict:
        """
        Pure computation for shift summary. No UI, no logging of financial values.

        Returns dict with keys:
            total_amount, used_product_count, total_product_count,
            html_actual_total, html_count_50k, used_products
        """
        try:
            if self.container:
                sessions = self.session_repo.get_all()
            else:
                sessions = SessionRepository.get_all()
        except Exception:
            sessions = []

        total_amount = sum(s.amount for s in sessions)
        used = [s for s in sessions if s.used_qty > 0]

        return {
            "total_amount": total_amount,
            "used_product_count": len(used),
            "total_product_count": len(sessions),
            "html_actual_total": html_data.get("actual_total", 0) if html_data else 0,
            "html_count_50k": html_data.get("count_50k", 0) if html_data else 0,
            "used_products": [
                {"name": s.product.name, "amount": s.amount} for s in used
            ],
        }

    def _hex_to_rgb(self, h):
        h = h.lstrip("#")
        return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"

    def _save_session(self):
        # Prevent duplicate save operations
        if self._is_saving:
            return

        self._is_saving = True
        try:
            # Disable save button during operation
            save_btn = self.sender()
            if save_btn:
                save_btn.setEnabled(False)
                save_btn.setText("⏳ Đang lưu...")

            # Use repository interface
            if self.container:
                total = self.session_repo.get_total_amount()
            else:
                total = SessionRepository.get_total_amount()

            dialog = SaveSessionDialog(total, self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
                # Use repository interface
                if self.container:
                    self.history_repo.save_current_session(
                        shift_name=dialog.result_data["shift_name"],
                        notes=dialog.result_data["notes"],
                    )
                    self.session_repo.reset_all()
                else:
                    HistoryRepository.save_current_session(
                        shift_name=dialog.result_data["shift_name"],
                        notes=dialog.result_data["notes"],
                    )
                    SessionRepository.reset_all()

                self.refresh_table()
                self._last_report_data = {}  # Clear report data on shift reset
                self._show_report({})  # Refresh sidebar with empty data
                if self.on_refresh_stock:
                    self.on_refresh_stock()
                QMessageBox.information(self, "Thành công", "Đã lưu phiên làm việc!")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error saving session: {str(e)}", exc_info=True)
            if self.error_handler:
                self.error_handler.handle(e, self)
        finally:
            self._is_saving = False
            # Re-enable save button
            save_btn = self.sender()
            if save_btn:
                save_btn.setEnabled(True)
                save_btn.setText("💾 Lưu toàn bộ phiên")

    def _import_products(self):
        """Import products from CSV"""
        try:
            path, _ = QFileDialog.getOpenFileName(
                self, "Chọn file CSV để nhập", "", "CSV Files (*.csv);;All Files (*.*)"
            )
            if not path:
                return

            import csv

            # Read CSV file
            with open(path, "r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)

                # Validate columns
                required_cols = ["Tên sản phẩm", "Đơn vị", "Quy đổi", "Đơn giá"]
                if not all(col in reader.fieldnames for col in required_cols):
                    QMessageBox.warning(
                        self,
                        "Lỗi",
                        f"File CSV phải có các cột: {', '.join(required_cols)}",
                    )
                    return

                # Import products
                imported = 0
                for row in reader:
                    try:
                        name = str(row["Tên sản phẩm"]).strip()
                        large_unit = str(row["Đơn vị"]).strip()
                        conversion = int(row["Quy đổi"])
                        unit_price = float(row["Đơn giá"])

                        if name and large_unit and conversion > 0 and unit_price >= 0:
                            if self.container:
                                self.product_repo.add(
                                    name, large_unit, conversion, unit_price
                                )
                            else:
                                ProductRepository.add(
                                    name, large_unit, conversion, unit_price
                                )
                            imported += 1
                    except Exception as e:
                        if self.logger:
                            self.logger.warning(f"Skip row: {e}")
                        continue

            self.refresh_product_list()
            self.refresh_table()
            if self.on_refresh_stock:
                self.on_refresh_stock()

            QMessageBox.information(self, "Thành công", f"Đã nhập {imported} sản phẩm!")

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error importing products: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", f"Không thể nhập file: {str(e)}")

    def _export_products(self):
        """Export products to CSV"""
        try:
            path, _ = QFileDialog.getSaveFileName(
                self, "Lưu file CSV", "danh_sach_san_pham.csv", "CSV Files (*.csv)"
            )
            if not path:
                return

            import csv

            # Get all products
            if self.container:
                products = self.product_repo.get_all()
            else:
                products = ProductRepository.get_all()

            # Write CSV file
            with open(path, "w", encoding="utf-8-sig", newline="") as f:
                fieldnames = ["STT", "Tên sản phẩm", "Đơn vị", "Quy đổi", "Đơn giá"]
                writer = csv.DictWriter(f, fieldnames=fieldnames)

                writer.writeheader()
                for idx, p in enumerate(products, 1):
                    writer.writerow(
                        {
                            "STT": idx,
                            "Tên sản phẩm": p.name,
                            "Đơn vị": p.large_unit,
                            "Quy đổi": p.conversion,
                            "Đơn giá": p.unit_price,
                        }
                    )

            QMessageBox.information(
                self, "Thành công", f"Đã xuất {len(products)} sản phẩm!"
            )

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error exporting products: {str(e)}", exc_info=True)
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất file: {str(e)}")

    def _save_product_order(self):
        """Save product order after drag & drop"""
        try:
            # Get all products
            if self.container:
                self.product_repo.get_all()
            else:
                ProductRepository.get_all()

            # Update display_order in database based on current table order
            with get_connection() as conn:
                cursor = conn.cursor()
                for idx in range(self.prod_table.rowCount()):
                    name_item = self.prod_table.item(idx, 1)
                    if name_item:
                        product_id = name_item.data(Qt.ItemDataRole.UserRole)
                        if product_id:
                            cursor.execute(
                                "UPDATE products SET display_order = ? WHERE id = ?",
                                (idx, product_id),
                            )
                conn.commit()

            # Refresh all tables to reflect new order
            self.refresh_product_list()  # Refresh product list table
            self.refresh_table()  # Refresh calculation table
            if self.on_refresh_stock:
                self.on_refresh_stock()  # Refresh stock view

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error saving product order: {str(e)}", exc_info=True
                )
