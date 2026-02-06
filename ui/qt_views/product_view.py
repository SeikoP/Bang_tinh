from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (QDialog, QDoubleSpinBox, QFormLayout, QHBoxLayout,
                             QHeaderView, QLabel, QLineEdit, QPushButton,
                             QSizePolicy, QTableWidget, QTableWidgetItem,
                             QVBoxLayout, QWidget)

from database import QuickPriceRepository
from ui.qt_theme import AppColors


class QuickPriceDialog(QDialog):
    """Dialog thêm/sửa bảng giá nhanh"""

    def __init__(self, item=None, parent=None):
        super().__init__(parent)
        self.item = item
        self.result_data = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("Thêm giá nhanh" if not self.item else "Sửa giá nhanh")
        self.setFixedWidth(350)

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        form = QFormLayout()
        self.name_input = QLineEdit()
        if self.item:
            self.name_input.setText(self.item.name)
        form.addRow("Tên:", self.name_input)

        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 1000000)
        self.price_spin.setDecimals(0)
        self.price_spin.setSuffix(" đ")
        if self.item:
            self.price_spin.setValue(self.item.price)
        form.addRow("Giá:", self.price_spin)

        layout.addLayout(form)

        btns = QHBoxLayout()
        save = QPushButton("Lưu")
        save.clicked.connect(self._save)
        btns.addWidget(save)
        layout.addLayout(btns)

    def _save(self):
        if not self.name_input.text().strip():
            return
        self.result_data = {
            "name": self.name_input.text().strip(),
            "price": self.price_spin.value(),
        }
        self.accept()


class ProductView(QWidget):
    """View theo dõi giá nhanh (Quick Price)"""

    def __init__(self, container=None, on_refresh_calc=None):
        super().__init__()
        # Inject repository from container
        self.container = container
        if container:
            self.quick_price_repo = container.get("quick_price_repo")
            self.logger = container.get("logger")
            # Get error handler
            from utils.error_handler import ErrorHandler

            self.error_handler = ErrorHandler(self.logger)
        else:
            # Fallback to direct access
            self.quick_price_repo = QuickPriceRepository
            self.logger = None
            self.error_handler = None

        # Loading state flag to prevent duplicate actions
        self._is_loading = False

        self.on_refresh_calc = on_refresh_calc
        self._setup_ui()
        self.refresh_list()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        # Header/Title
        header = QLabel("📍 Bảng Giá Dịch Vụ Nhanh")
        header.setStyleSheet(
            f"font-size: 18px; font-weight: 800; color: {AppColors.TEXT};"
        )
        layout.addWidget(header)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 0)
        toolbar.setSpacing(16)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Tìm giá nhanh...")
        self.search_input.setFixedWidth(300)
        self.search_input.textChanged.connect(self.refresh_list)
        toolbar.addWidget(self.search_input)

        toolbar.addStretch()

        add_btn = QPushButton("➕ Thêm giá nhanh")
        add_btn.setObjectName("secondary")
        add_btn.setFixedWidth(180)
        add_btn.clicked.connect(self._add_quick_price)
        toolbar.addWidget(add_btn)

        layout.addLayout(toolbar)

        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)

    def _setup_table(self):
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["STT", "Tên dịch vụ", "Đơn giá", "Thao tác"]
        )
        self.table.setShowGrid(False)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)

        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(2, 130)
        self.table.setColumnWidth(3, 170)

        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(68)

    def refresh_list(self):
        # Prevent duplicate refresh operations
        if self._is_loading:
            return

        self._is_loading = True
        try:
            # Optimize table rendering by disabling updates during batch operations
            self.table.setUpdatesEnabled(False)

            query = self.search_input.text().lower().strip()
            # Use repository interface
            if self.container:
                items = self.quick_price_repo.get_all()
            else:
                items = QuickPriceRepository.get_all()

            if query:
                items = [i for i in items if query in i.name.lower()]

            self.table.setRowCount(len(items))
            for row, item in enumerate(items):
                self._set_cell(row, 0, str(row + 1), center=True)
                self._set_cell(row, 1, item.name, center=False, bold=True)
                self._set_cell(
                    row,
                    2,
                    f"{item.price:,.0f} đ",
                    center=True,
                    fg=AppColors.PRIMARY,
                    bold=True,
                )

                # Container widget - Dùng VBoxLayout để căn giữa theo chiều dọc
                actions = QWidget()
                actions.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

                actions_v_layout = QVBoxLayout(actions)
                actions_v_layout.setContentsMargins(0, 0, 0, 0)
                actions_v_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

                # Inner HBox cho buttons
                actions_h_widget = QWidget()
                actions_layout = QHBoxLayout(actions_h_widget)
                actions_layout.setContentsMargins(10, 0, 10, 0)
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                actions_layout.setSpacing(10)

                # Action Button Style - Thay đổi màu sắc RÕ RỆT để user thấy
                btn_style = f"""
                    QPushButton {{
                        border: none;
                        border-radius: 4px;
                        background-color: {AppColors.PRIMARY}; 
                        color: white;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 4px 10px;
                    }}
                    QPushButton:hover {{ background-color: #1d4ed8; }}
                    QPushButton:pressed {{ background-color: #1e40af; }}
                """
                del_style = """
                    QPushButton {
                        border: none;
                        border-radius: 4px;
                        background-color: #fee2e2;
                        color: #ef4444;
                        font-size: 11px;
                        font-weight: 600;
                        padding: 4px 10px;
                    }
                    QPushButton:hover { background-color: #fecaca; }
                """

                edit_btn = QPushButton("Sửa")
                edit_btn.setStyleSheet(btn_style)
                edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                edit_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                edit_btn.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                edit_btn.setFixedSize(58, 30)  # Thu nhỏ xuống
                edit_btn.clicked.connect(lambda _, it=item: self._edit_quick_price(it))
                actions_layout.addWidget(edit_btn)

                del_btn = QPushButton("Xóa")
                del_btn.setStyleSheet(del_style)
                del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                del_btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                del_btn.setSizePolicy(
                    QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
                )
                del_btn.setFixedSize(58, 30)  # Thu nhỏ xuống
                del_btn.clicked.connect(
                    lambda _, i_id=item.id: self._delete_quick_price(i_id)
                )
                actions_layout.addWidget(del_btn)

                actions_v_layout.addWidget(actions_h_widget)
                self.table.setCellWidget(row, 3, actions)

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error refreshing quick price list: {str(e)}", exc_info=True
                )
        finally:
            # Re-enable table updates after batch operations
            self.table.setUpdatesEnabled(True)
            self._is_loading = False

    def _add_quick_price(self):
        try:
            dialog = QuickPriceDialog(parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
                d = dialog.result_data
                # Use repository interface
                if self.container:
                    self.quick_price_repo.add(d["name"], d["price"])
                else:
                    QuickPriceRepository.add(d["name"], d["price"])

                self.refresh_list()
                if self.on_refresh_calc:
                    self.on_refresh_calc()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error adding quick price: {str(e)}", exc_info=True)
            if self.error_handler:
                self.error_handler.handle(e, self)

    def _edit_quick_price(self, item):
        try:
            dialog = QuickPriceDialog(item=item, parent=self)
            if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
                d = dialog.result_data
                # Use repository interface
                if self.container:
                    self.quick_price_repo.update(item.id, d["name"], d["price"])
                else:
                    QuickPriceRepository.update(item.id, d["name"], d["price"])

                self.refresh_list()
                if self.on_refresh_calc:
                    self.on_refresh_calc()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error editing quick price: {str(e)}", exc_info=True)
            if self.error_handler:
                self.error_handler.handle(e, self)

    def _delete_quick_price(self, item_id):
        try:
            # Use repository interface
            if self.container:
                self.quick_price_repo.delete(item_id)
            else:
                QuickPriceRepository.delete(item_id)

            self.refresh_list()
            if self.on_refresh_calc:
                self.on_refresh_calc()
        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Error deleting quick price: {str(e)}", exc_info=True
                )
            if self.error_handler:
                self.error_handler.handle(e, self)

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
