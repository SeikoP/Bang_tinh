"""
Product View - Quản lý sản phẩm
Clean Minimal Design
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QComboBox, QDoubleSpinBox,
    QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.qt_theme import AppColors
from database import ProductRepository
from config import DEFAULT_UNITS


class ProductDialog(QDialog):
    """Dialog thêm/sửa sản phẩm"""
    
    def __init__(self, product=None, parent=None):
        super().__init__(parent)
        self.product = product
        self.result_data = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Thêm sản phẩm" if not self.product else "Sửa sản phẩm")
        self.setFixedWidth(380)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("VD: Bia Tiger...")
        if self.product:
            self.name_input.setText(self.product.name)
        form.addRow("Tên:", self.name_input)
        
        self.unit_combo = QComboBox()
        for unit in DEFAULT_UNITS:
            self.unit_combo.addItem(unit["name"])
        if self.product:
            idx = self.unit_combo.findText(self.product.large_unit)
            if idx >= 0:
                self.unit_combo.setCurrentIndex(idx)
        form.addRow("Đơn vị:", self.unit_combo)
        
        self.conversion_spin = QSpinBox()
        self.conversion_spin.setRange(1, 100)
        self.conversion_spin.setValue(self.product.conversion if self.product else 24)
        form.addRow("Quy đổi:", self.conversion_spin)
        
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0, 10000000)
        self.price_spin.setDecimals(0)
        self.price_spin.setSingleStep(1000)
        self.price_spin.setSuffix(" VNĐ")
        self.price_spin.setValue(self.product.unit_price if self.product else 5000)
        form.addRow("Đơn giá:", self.price_spin)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        
        cancel_btn = QPushButton("Hủy")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Lưu")
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)
    
    def _save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên!")
            return
        
        self.result_data = {
            'name': name,
            'large_unit': self.unit_combo.currentText(),
            'conversion': self.conversion_spin.value(),
            'unit_price': self.price_spin.value()
        }
        self.accept()


class ProductView(QWidget):
    """View sản phẩm"""
    
    def __init__(self, on_refresh_calc=None):
        super().__init__()
        self.on_refresh_calc = on_refresh_calc
        self._setup_ui()
        self.refresh_list()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Quản lý Sản phẩm")
        title.setObjectName("title")
        header.addWidget(title)
        
        header.addStretch()
        
        add_btn = QPushButton("+ Thêm")
        add_btn.clicked.connect(self._add_product)
        header.addWidget(add_btn)
        
        refresh_btn = QPushButton("Làm mới")
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh_list)
        header.addWidget(refresh_btn)
        
        layout.addLayout(header)
        
        # Table
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)
    
    def _setup_table(self):
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "STT", "Tên sản phẩm", "Đơn vị", "Quy đổi", "Đơn giá", "Thao tác"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in [2, 3, 4, 5]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 100)
        self.table.setColumnWidth(5, 90)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
    
    def refresh_list(self):
        products = ProductRepository.get_all()
        self.table.setRowCount(len(products))
        
        for row, p in enumerate(products):
            self._set_cell(row, 0, str(row + 1), center=True)
            self._set_cell(row, 1, p.name, bold=True)
            self._set_cell(row, 2, p.large_unit, center=True, bg=AppColors.PRIMARY, fg="white")
            self._set_cell(row, 3, str(p.conversion), center=True, fg=AppColors.TEXT_SECONDARY)
            self._set_cell(row, 4, f"{p.unit_price:,.0f}", center=True, fg=AppColors.SUCCESS, bold=True)
            
            actions = QWidget()
            actions_layout = QHBoxLayout(actions)
            actions_layout.setContentsMargins(4, 2, 4, 2)
            actions_layout.setSpacing(4)
            
            edit_btn = QPushButton("✎")
            edit_btn.setObjectName("iconBtn")
            edit_btn.clicked.connect(lambda _, pid=p.id: self._edit_product(pid))
            actions_layout.addWidget(edit_btn)
            
            del_btn = QPushButton("×")
            del_btn.setObjectName("iconBtn")
            del_btn.clicked.connect(lambda _, pid=p.id, name=p.name: self._delete_product(pid, name))
            actions_layout.addWidget(del_btn)
            
            self.table.setCellWidget(row, 5, actions)
    
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
        if bg:
            item.setBackground(QColor(bg))
        if fg:
            item.setForeground(QColor(fg))
        self.table.setItem(row, col, item)
    
    def _add_product(self):
        dialog = ProductDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            ProductRepository.create(d['name'], d['large_unit'], d['conversion'], d['unit_price'])
            self.refresh_list()
            if self.on_refresh_calc:
                self.on_refresh_calc()
    
    def _edit_product(self, product_id):
        product = ProductRepository.get_by_id(product_id)
        if not product:
            return
        
        dialog = ProductDialog(product=product, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            ProductRepository.update(product_id, d['name'], d['large_unit'], d['conversion'], d['unit_price'])
            self.refresh_list()
            if self.on_refresh_calc:
                self.on_refresh_calc()
    
    def _delete_product(self, product_id, name):
        reply = QMessageBox.question(
            self, "Xác nhận", f"Xóa sản phẩm '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            ProductRepository.delete(product_id)
            self.refresh_list()
            if self.on_refresh_calc:
                self.on_refresh_calc()
