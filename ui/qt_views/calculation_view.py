"""
Calculation View - Màn hình bảng tính dịch vụ
Clean Minimal Design
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QFileDialog, QMessageBox, QDialog, QFormLayout,
    QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.qt_theme import AppColors, AppTheme
from database import SessionRepository, HistoryRepository
from services import CalculatorService, ReportService


class SaveSessionDialog(QDialog):
    """Dialog lưu phiên"""
    
    def __init__(self, total_amount: float, parent=None):
        super().__init__(parent)
        self.total_amount = total_amount
        self.result_data = None
        self._setup_ui()
    
    def _setup_ui(self):
        self.setWindowTitle("Lưu phiên làm việc")
        self.setFixedWidth(380)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 20, 24, 20)
        
        # Total
        total_label = QLabel(f"Tổng cộng: {self.total_amount:,.0f} VNĐ")
        total_label.setStyleSheet(f"font-size: 16px; font-weight: 600; color: {AppColors.SUCCESS};")
        total_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(total_label)
        
        # Form
        form = QFormLayout()
        form.setSpacing(12)
        
        self.shift_input = QLineEdit()
        self.shift_input.setPlaceholderText("VD: Ca sáng, Ca chiều...")
        form.addRow("Tên ca:", self.shift_input)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Ghi chú (tuỳ chọn)")
        self.notes_input.setFixedHeight(60)
        form.addRow("Ghi chú:", self.notes_input)
        
        layout.addLayout(form)
        
        # Buttons
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
        self.result_data = {
            'shift_name': self.shift_input.text().strip() or "Phiên làm việc",
            'notes': self.notes_input.toPlainText().strip()
        }
        self.accept()


class CalculationView(QWidget):
    """View bảng tính"""
    
    def __init__(self):
        super().__init__()
        self.calc_service = CalculatorService()
        self.report_service = ReportService()
        self._setup_ui()
        self.refresh_table()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 16)
        layout.setSpacing(12)
        
        # Header
        header = QHBoxLayout()
        header.setSpacing(12)
        
        title = QLabel("Kê khai Dịch vụ")
        title.setObjectName("title")
        header.addWidget(title)
        
        header.addStretch()
        
        import_btn = QPushButton("Nhập HTML")
        import_btn.setObjectName("secondary")
        import_btn.clicked.connect(self._import_html)
        header.addWidget(import_btn)
        
        refresh_btn = QPushButton("Làm mới")
        refresh_btn.setObjectName("secondary")
        refresh_btn.clicked.connect(self.refresh_table)
        header.addWidget(refresh_btn)
        
        save_btn = QPushButton("Lưu phiên")
        save_btn.clicked.connect(self._save_session)
        header.addWidget(save_btn)
        
        layout.addLayout(header)
        
        # Report frame (hidden)
        self.report_frame = QFrame()
        self.report_frame.setObjectName("card")
        self.report_frame.hide()
        layout.addWidget(self.report_frame)
        
        # Table
        self.table = QTableWidget()
        self._setup_table()
        layout.addWidget(self.table, 1)
        
        # Footer
        footer = QHBoxLayout()
        
        info = QLabel("Định dạng: 3t4 = 3 thùng 4 lon")
        info.setObjectName("subtitle")
        footer.addWidget(info)
        
        footer.addStretch()
        
        self.total_label = QLabel("Tổng: 0 VNĐ")
        self.total_label.setStyleSheet(f"""
            color: {AppColors.SUCCESS};
            font-size: 15px;
            font-weight: 600;
            padding: 8px 14px;
            background-color: rgba(52, 168, 83, 0.1);
            border-radius: 4px;
        """)
        footer.addWidget(self.total_label)
        
        layout.addLayout(footer)
    
    def _setup_table(self):
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Đ.Vị", "Tên sản phẩm", "Giao ca", "Chốt ca",
            "Quy đổi", "Đã dùng", "Đơn giá", "Thành tiền"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for i in [2, 3, 4, 5, 6, 7]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 55)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 70)
        self.table.setColumnWidth(5, 70)
        self.table.setColumnWidth(6, 95)
        self.table.setColumnWidth(7, 110)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(42)
    
    def refresh_table(self):
        sessions = SessionRepository.get_all()
        self.table.setRowCount(len(sessions))
        
        total = 0
        
        for row, s in enumerate(sessions):
            p = s.product
            
            handover_disp = self.calc_service.format_to_display(s.handover_qty, p.conversion, p.unit_char)
            closing_disp = self.calc_service.format_to_display(s.closing_qty, p.conversion, p.unit_char)
            
            total += s.amount
            
            # Unit
            self._set_cell(row, 0, p.large_unit, center=True, bg=AppColors.PRIMARY, fg="white")
            
            # Name
            self._set_cell(row, 1, p.name, bold=True)
            
            # Handover input
            handover_edit = QLineEdit(handover_disp if s.handover_qty > 0 else "0")
            handover_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            handover_edit.setStyleSheet("border: none; background: transparent;")
            handover_edit.editingFinished.connect(
                lambda r=row, pid=p.id, conv=p.conversion: self._on_qty_change(r, pid, conv, True)
            )
            self.table.setCellWidget(row, 2, handover_edit)
            
            # Closing input
            closing_edit = QLineEdit(closing_disp if s.closing_qty > 0 else "0")
            closing_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            closing_edit.setStyleSheet("border: none; background: transparent;")
            closing_edit.editingFinished.connect(
                lambda r=row, pid=p.id, conv=p.conversion: self._on_qty_change(r, pid, conv, False)
            )
            self.table.setCellWidget(row, 3, closing_edit)
            
            # Conversion
            self._set_cell(row, 4, str(p.conversion), center=True, fg=AppColors.TEXT_SECONDARY)
            
            # Used
            if s.used_qty > 0:
                self._set_cell(row, 5, str(s.used_qty), center=True, bg=AppColors.WARNING, fg="#333")
            else:
                self._set_cell(row, 5, "0", center=True)
            
            # Price
            self._set_cell(row, 6, f"{p.unit_price:,.0f}", center=True)
            
            # Amount
            self._set_cell(row, 7, f"{s.amount:,.0f}", center=True, fg=AppColors.SUCCESS, bold=True)
        
        self.total_label.setText(f"Tổng: {total:,.0f} VNĐ")
    
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
    
    def _on_qty_change(self, row, product_id, conversion, is_handover):
        col = 2 if is_handover else 3
        widget = self.table.cellWidget(row, col)
        if not widget:
            return
        
        new_qty = self.calc_service.parse_to_small_units(widget.text(), conversion)
        sessions = SessionRepository.get_all()
        current = next((s for s in sessions if s.product.id == product_id), None)
        if not current:
            return
        
        h_qty = new_qty if is_handover else current.handover_qty
        c_qty = current.closing_qty if is_handover else new_qty
        
        if is_handover:
            c_qty = h_qty
        if c_qty > h_qty:
            c_qty = h_qty
        
        SessionRepository.update_qty(product_id, h_qty, c_qty)
        self.refresh_table()
    
    def _import_html(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Chọn file HTML", "", "HTML Files (*.html *.htm)"
        )
        if not file_path:
            return
        
        result = self.report_service.parse_html_report(file_path)
        if result["success"]:
            self._show_report(result)
        else:
            QMessageBox.warning(self, "Lỗi", f"Không thể đọc file: {result['error']}")
    
    def _show_report(self, data: dict):
        old_layout = self.report_frame.layout()
        if old_layout:
            while old_layout.count():
                item = old_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
            QWidget().setLayout(old_layout)
        
        layout = QHBoxLayout(self.report_frame)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(16)
        
        layout.addWidget(self._stat_label("Thực tế", f"{data['actual_total']:,.0f}đ", AppColors.PRIMARY))
        layout.addWidget(self._stat_label("Thực thu", f"{data['received_total']:,.0f}đ", AppColors.SUCCESS))
        layout.addWidget(self._stat_label("Lượt 50K", str(data['count_50k']), AppColors.WARNING))
        
        layout.addStretch()
        
        close_btn = QPushButton("×")
        close_btn.setObjectName("iconBtn")
        close_btn.clicked.connect(lambda: self.report_frame.hide())
        layout.addWidget(close_btn)
        
        self.report_frame.show()
    
    def _stat_label(self, label: str, value: str, color: str) -> QLabel:
        lbl = QLabel(f"{label}: <b>{value}</b>")
        lbl.setStyleSheet(f"color: {color};")
        return lbl
    
    def _save_session(self):
        total = SessionRepository.get_total_amount()
        dialog = SaveSessionDialog(total, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            HistoryRepository.save_current_session(
                shift_name=dialog.result_data['shift_name'],
                notes=dialog.result_data['notes']
            )
            SessionRepository.reset_all()
            self.refresh_table()
            QMessageBox.information(self, "Thành công", "Đã lưu phiên làm việc!")
