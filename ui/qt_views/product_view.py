from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QDoubleSpinBox,
    QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.qt_theme import AppColors
from database import QuickPriceRepository


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
        if self.item: self.name_input.setText(self.item.name)
        form.addRow("Tên:", self.name_input)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 1000000)
        self.price_spin.setDecimals(0)
        self.price_spin.setSuffix(" đ")
        if self.item: self.price_spin.setValue(self.item.price)
        form.addRow("Giá:", self.price_spin)
        
        layout.addLayout(form)
        
        btns = QHBoxLayout()
        save = QPushButton("Lưu")
        save.clicked.connect(self._save)
        btns.addWidget(save)
        layout.addLayout(btns)
        
    def _save(self):
        if not self.name_input.text().strip(): return
        self.result_data = {
            'name': self.name_input.text().strip(),
            'price': self.price_spin.value()
        }
        self.accept()


class ProductView(QWidget):
    """View theo dõi giá nhanh (Quick Price)"""
    
    def __init__(self, on_refresh_calc=None):
        super().__init__()
        self.on_refresh_calc = on_refresh_calc
        self._setup_ui()
        self.refresh_list()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)
        
        # Header/Title
        header = QLabel("📍 Bảng Giá Dịch Vụ Nhanh")
        header.setStyleSheet(f"font-size: 18px; font-weight: 800; color: {AppColors.TEXT};")
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
        self.table.setHorizontalHeaderLabels(["STT", "Tên dịch vụ", "Đơn giá", "Thao tác"])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 120)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(50)
    
    def refresh_list(self):
        query = self.search_input.text().lower().strip()
        items = QuickPriceRepository.get_all()
        if query:
            items = [i for i in items if query in i.name.lower()]
            
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            self._set_cell(row, 0, str(row + 1), center=True)
            self._set_cell(row, 1, item.name, bold=True)
            self._set_cell(row, 2, f"{item.price:,.0f} đ", center=True, fg=AppColors.PRIMARY, bold=True)
            
            actions = QFrame()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            actions_layout.setSpacing(10)
            
            edit_btn = QPushButton("Sửa")
            edit_btn.setObjectName("secondary")
            edit_btn.setMinimumWidth(80)
            edit_btn.setFixedHeight(32)
            edit_btn.clicked.connect(lambda _, it=item: self._edit_quick_price(it))
            actions_layout.addWidget(edit_btn)
            
            del_btn = QPushButton("Xóa")
            del_btn.setObjectName("iconBtn")
            del_btn.setMinimumWidth(80)
            del_btn.setFixedHeight(32)
            del_btn.setStyleSheet(f"color: {AppColors.ERROR}; border-color: {AppColors.ERROR};")
            del_btn.clicked.connect(lambda _, i_id=item.id: self._delete_quick_price(i_id))
            actions_layout.addWidget(del_btn)
            self.table.setCellWidget(row, 3, actions)
            
    def _add_quick_price(self):
        dialog = QuickPriceDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            QuickPriceRepository.add(d['name'], d['price'])
            self.refresh_list()
            if self.on_refresh_calc: self.on_refresh_calc()
            
    def _edit_quick_price(self, item):
        dialog = QuickPriceDialog(item=item, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            QuickPriceRepository.update(item.id, d['name'], d['price'])
            self.refresh_list()
            if self.on_refresh_calc: self.on_refresh_calc()
            
    def _delete_quick_price(self, item_id):
        QuickPriceRepository.delete(item_id)
        self.refresh_list()
        if self.on_refresh_calc: self.on_refresh_calc()

    def _set_cell(self, row, col, text, center=False, bold=False, bg=None, fg=None):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if center:
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        else:
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if bold:
            font = item.font()
            font.setBold(True)
            item.setFont(font)
        if bg: item.setBackground(QColor(bg))
        if fg: item.setForeground(QColor(fg))
        self.table.setItem(row, col, item)
