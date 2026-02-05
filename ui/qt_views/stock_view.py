"""
Stock View - Quản lý kho hàng
Clean Minimal Design
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpinBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.qt_theme import AppColors
from database import SessionRepository
from services import CalculatorService


class StockView(QWidget):
    """View kho hàng"""
    
    def __init__(self, on_refresh_calc=None):
        super().__init__()
        self.on_refresh_calc = on_refresh_calc
        self.calc_service = CalculatorService()
        self._setup_ui()
        self.refresh_list()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        
        title = QLabel("Chốt ca Kho hàng")
        title.setObjectName("title")
        header.addWidget(title)
        
        header.addStretch()
        
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
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "STT", "Tên sản phẩm", "Đơn vị", "Quy đổi", "SL Lớn", "SL Lẻ", "Tổng"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in [2, 3, 4, 5, 6]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(2, 70)
        self.table.setColumnWidth(3, 70)
        self.table.setColumnWidth(4, 80)
        self.table.setColumnWidth(5, 80)
        self.table.setColumnWidth(6, 70)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
    
    def refresh_list(self):
        sessions = SessionRepository.get_all()
        self.table.setRowCount(len(sessions))
        
        for row, s in enumerate(sessions):
            p = s.product
            large_qty = s.closing_qty // p.conversion
            small_qty = s.closing_qty % p.conversion
            
            # STT
            self._set_cell(row, 0, str(row + 1), center=True)
            
            # Name
            self._set_cell(row, 1, p.name, bold=True)
            
            # Unit
            self._set_cell(row, 2, p.large_unit, center=True, bg=AppColors.PRIMARY, fg="white")
            
            # Conversion
            self._set_cell(row, 3, str(p.conversion), center=True, fg=AppColors.TEXT_SECONDARY)
            
            # Large qty spinner
            large_spin = self._create_spinner(large_qty, 0, 999)
            large_spin.valueChanged.connect(
                lambda v, pr=p, ss=s, sq=small_qty: self._on_large_change(pr, ss, v, sq)
            )
            self.table.setCellWidget(row, 4, large_spin)
            
            # Small qty spinner
            small_spin = self._create_spinner(small_qty, 0, p.conversion - 1)
            small_spin.valueChanged.connect(
                lambda v, pr=p, ss=s, lq=large_qty: self._on_small_change(pr, ss, lq, v)
            )
            self.table.setCellWidget(row, 5, small_spin)
            
            # Total
            self._set_cell(row, 6, str(s.closing_qty), center=True, bold=True, fg=AppColors.PRIMARY)
    
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
    
    def _create_spinner(self, value, min_val, max_val):
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(value)
        spin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spin.setButtonSymbols(QSpinBox.ButtonSymbols.PlusMinus)
        spin.setStyleSheet("border: none; background: transparent; font-weight: 500;")
        return spin
    
    def _on_large_change(self, product, session, new_large, small_qty):
        new_closing = min(new_large * product.conversion + small_qty, session.handover_qty)
        new_closing = max(0, new_closing)
        SessionRepository.update_qty(product.id, session.handover_qty, new_closing)
        self.refresh_list()
        if self.on_refresh_calc:
            self.on_refresh_calc()
    
    def _on_small_change(self, product, session, large_qty, new_small):
        new_closing = min(large_qty * product.conversion + new_small, session.handover_qty)
        new_closing = max(0, new_closing)
        SessionRepository.update_qty(product.id, session.handover_qty, new_closing)
        self.refresh_list()
        if self.on_refresh_calc:
            self.on_refresh_calc()
