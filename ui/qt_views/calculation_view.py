from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QFrame,
    QLineEdit, QFileDialog, QMessageBox, QDialog, QFormLayout,
    QTextEdit, QTabWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.qt_theme import AppColors
from database import SessionRepository, HistoryRepository, ProductRepository
from services import CalculatorService, ReportService
from ui.qt_views.product_dialog import ProductDialog


class SaveSessionDialog(QDialog):
    """Dialog lưu phiên"""
    
    def __init__(self, total_amount: float, parent=None):
        super().__init__(parent)
        self.total_amount = total_amount
        self.result_data = None
        self._setup_ui()
    
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
            'shift_name': self.shift_input.text().strip() or "Phiên làm việc",
            'notes': self.notes_input.toPlainText().strip()
        }
        self.accept()


class CalculationView(QWidget):
    """View bảng tính kèm quản lý danh mục sản phẩm"""
    
    def __init__(self, on_refresh_stock=None):
        super().__init__()
        self.calc_service = CalculatorService()
        self.report_service = ReportService()
        self.on_refresh_stock = on_refresh_stock
        self._next_focus = None
        self._widget_height = 28  # Chiều cao mặc định
        self._setup_ui()
        self.refresh_table()
        self.refresh_product_list()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Sub Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: transparent;
            }}
            QTabBar::tab {{
                padding: 12px 28px;
                font-weight: 600;
                font-size: 13px;
                background: transparent;
                color: {AppColors.TEXT_SECONDARY};
                border-bottom: 2px solid transparent;
            }}
            QTabBar::tab:selected {{
                color: {AppColors.PRIMARY};
                border-bottom: 2px solid {AppColors.PRIMARY};
                background: rgba(37, 99, 235, 0.05);
            }}
            QTabBar::tab:hover:!selected {{
                color: {AppColors.TEXT};
                background: rgba(15, 23, 42, 0.05);
            }}
        """)
        
        # 1. Calculation Tab
        self.calc_tab = QWidget()
        self._setup_calc_tab()
        self.tabs.addTab(self.calc_tab, "🧮 Máy tính")
        
        # 2. Product Management Tab (Moved from Product View)
        self.prod_tab = QWidget()
        self._setup_prod_tab()
        self.tabs.addTab(self.prod_tab, "📦 Danh sách sản phẩm")
        
        layout.addWidget(self.tabs)

    def _setup_calc_tab(self):
        layout = QVBoxLayout(self.calc_tab)
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
        
        # Report frame (visible by default)
        self.report_frame = QFrame()
        self.report_frame.setObjectName("card")
        self.report_frame.setFixedWidth(280)
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
        
        add_btn = QPushButton("➕ Thêm sản phẩm")
        add_btn.setObjectName("primary")
        add_btn.setFixedWidth(180)
        add_btn.clicked.connect(self._add_product)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)
        
        self.prod_table = QTableWidget()
        self._setup_prod_table()
        layout.addWidget(self.prod_table, 1)

    def _setup_calc_table(self):
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Đ.Vị", "Quy đổi", "Tên sản phẩm", "Giao ca", "Chốt ca",
            "Đã dùng", "Đơn giá", "Thành tiền"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        for i in [3, 4, 5, 6, 7]:
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 65)
        self.table.setColumnWidth(3, 110)
        self.table.setColumnWidth(4, 110)
        self.table.setColumnWidth(5, 75)
        self.table.setColumnWidth(6, 95)
        self.table.setColumnWidth(7, 110)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(70)

    def _setup_prod_table(self):
        self.prod_table.setColumnCount(6)
        self.prod_table.setHorizontalHeaderLabels(["STT", "Tên sản phẩm", "Đơn vị", "Quy đổi", "Đơn giá", "Thao tác"])
        
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

    def refresh_table(self):
        sessions = SessionRepository.get_all()
        self.table.setRowCount(len(sessions))
        total = 0
        for row, s in enumerate(sessions):
            p = s.product
            handover_disp = self.calc_service.format_to_display(s.handover_qty, p.conversion, p.unit_char)
            closing_disp = self.calc_service.format_to_display(s.closing_qty, p.conversion, p.unit_char)
            total += s.amount
            has_data = s.used_qty > 0
            row_bg = "rgba(37, 99, 235, 0.05)" if has_data else None
            unit_item = QTableWidgetItem(p.large_unit)
            unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            unit_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            unit_item.setBackground(QColor(row_bg if has_data else "#f1f5f9"))
            unit_item.setForeground(QColor(AppColors.PRIMARY))
            font = unit_item.font()
            font.setBold(True)
            unit_item.setFont(font)
            self.table.setItem(row, 0, unit_item)
            self._set_cell_helper(self.table, row, 1, str(p.conversion), right=True, fg=AppColors.TEXT, bg=row_bg)
            self._set_cell_helper(self.table, row, 2, p.name, bold=True, fg=AppColors.TEXT, bg=row_bg)
            handover_container = QWidget()
            handover_layout = QVBoxLayout(handover_container)
            handover_layout.setContentsMargins(10, 8, 10, 8)  # Tăng margin để widget không bị overflow
            handover_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            handover_edit = QLineEdit(handover_disp if s.handover_qty > 0 else "0")
            handover_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            handover_edit.setFixedHeight(self._widget_height)
            # Set stylesheet trực tiếp với specificity cao
            handover_edit.setStyleSheet(f"""
                QLineEdit {{
                    border: 2px solid {AppColors.BORDER};
                    border-radius: 5px;
                    padding: 2px 6px;
                    font-weight: 700;
                    font-size: 13px;
                    background: white;
                }}
            """)
            handover_edit.setProperty("product_id", p.id)
            handover_edit.setProperty("conversion", p.conversion)
            handover_edit.setProperty("row", row)
            handover_edit.setProperty("col", 3)
            handover_edit.editingFinished.connect(self._on_handover_change)
            handover_edit.returnPressed.connect(self._on_return_pressed)
            handover_layout.addWidget(handover_edit)
            self.table.setCellWidget(row, 3, handover_container)
            closing_container = QWidget()
            closing_layout = QVBoxLayout(closing_container)
            closing_layout.setContentsMargins(10, 8, 10, 8)  # Tăng margin để widget không bị overflow
            closing_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            closing_edit = QLineEdit(closing_disp if s.closing_qty > 0 else "0")
            closing_edit.setAlignment(Qt.AlignmentFlag.AlignCenter)
            closing_edit.setFixedHeight(self._widget_height)
            # Set stylesheet trực tiếp với specificity cao
            closing_edit.setStyleSheet(f"""
                QLineEdit {{
                    border: 2px solid {AppColors.BORDER};
                    border-radius: 5px;
                    padding: 2px 6px;
                    font-weight: 700;
                    font-size: 13px;
                    background: white;
                }}
            """)
            closing_edit.setProperty("product_id", p.id)
            closing_edit.setProperty("conversion", p.conversion)
            closing_edit.setProperty("row", row)
            closing_edit.setProperty("col", 4)
            closing_edit.editingFinished.connect(self._on_closing_change)
            closing_edit.returnPressed.connect(self._on_return_pressed)
            closing_layout.addWidget(closing_edit)
            self.table.setCellWidget(row, 4, closing_container)
            if s.used_qty > 0:
                used_item = QTableWidgetItem(str(s.used_qty))
                used_item.setFlags(used_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                used_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                used_item.setBackground(QColor(AppColors.WARNING))
                used_item.setForeground(QColor("white"))
                font = used_item.font()
                font.setBold(True)
                used_item.setFont(font)
                self.table.setItem(row, 5, used_item)
            else:
                self._set_cell_helper(self.table, row, 5, "0", right=True, fg=AppColors.TEXT, bg=row_bg)
            self._set_cell_helper(self.table, row, 6, f"{p.unit_price:,.0f}", right=True, fg=AppColors.TEXT, bg=row_bg)
            self._set_cell_helper(self.table, row, 7, f"{s.amount:,.0f}", right=True, fg=AppColors.SUCCESS, bold=True, bg=row_bg)
        self.total_label.setText(f"💰 TỔNG TIỀN: {total:,.0f} VNĐ")
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

    def refresh_product_list(self):
        query = self.search_input.text().lower().strip()
        products = ProductRepository.get_all()
        if query:
            products = [p for p in products if query in p.name.lower()]
        self.prod_table.setRowCount(len(products))
        for row, p in enumerate(products):
            self._set_cell_helper(self.prod_table, row, 0, str(row + 1), center=True)
            self._set_cell_helper(self.prod_table, row, 1, p.name, bold=True)
            self._set_cell_helper(self.prod_table, row, 2, p.large_unit, center=True, fg=AppColors.PRIMARY)
            self._set_cell_helper(self.prod_table, row, 3, str(p.conversion), center=True, fg=AppColors.TEXT)
            self._set_cell_helper(self.prod_table, row, 4, f"{p.unit_price:,.0f}", center=True, fg=AppColors.SUCCESS, bold=True)
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
            db.clicked.connect(lambda _, pid=p.id, name=p.name: self._delete_product(pid, name))
            al.addWidget(db)
            
            actions_v_layout.addWidget(actions_h_widget)
            self.prod_table.setCellWidget(row, 5, actions)

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
        sessions = SessionRepository.get_all()
        curr = next((s for s in sessions if s.product.id == pid), None)
        if not curr: return
        h = new if is_h else curr.handover_qty
        c = curr.closing_qty if is_h else new
        if is_h: c = h
        if c > h: c = h
        SessionRepository.update_qty(pid, h, c)
        self.refresh_table()
        if self.on_refresh_stock: self.on_refresh_stock()
    
    def _set_cell_helper(self, table, row, col, text, center=False, right=False, bold=False, bg=None, fg=None):
        item = QTableWidgetItem(text)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        if center: item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        elif right: item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        else: item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        if bold:
            f = item.font()
            f.setBold(True)
            item.setFont(f)
        if bg: item.setBackground(QColor(bg))
        if fg: item.setForeground(QColor(fg))
        table.setItem(row, col, item)

    def _add_product(self):
        dialog = ProductDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            ProductRepository.add(d['name'], d['large_unit'], d['conversion'], d['unit_price'])
            self.refresh_product_list()
            self.refresh_table()
            if self.on_refresh_stock: self.on_refresh_stock()
    
    def _edit_product(self, pid):
        product = ProductRepository.get_by_id(pid)
        if not product: return
        dialog = ProductDialog(product=product, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            d = dialog.result_data
            ProductRepository.update(pid, d['name'], d['large_unit'], d['conversion'], d['unit_price'])
            self.refresh_product_list()
            self.refresh_table()
            if self.on_refresh_stock: self.on_refresh_stock()
    
    def _delete_product(self, pid, name):
        reply = QMessageBox.question(self, "Xác nhận", f"Xóa sản phẩm '{name}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            ProductRepository.delete(pid)
            self.refresh_product_list()
            self.refresh_table()
            if self.on_refresh_stock: self.on_refresh_stock()
    
    def _import_html(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file HTML", "", "HTML Files (*.html *.htm)")
        if not path: return
        res = self.report_service.parse_html_report(path)
        if res["success"]: self._show_report(res)
        else: QMessageBox.warning(self, "Lỗi", f"Không thể đọc file: {res['error']}")
    
    def _show_report(self, data: dict):
        if self.report_frame.layout():
            l = self.report_frame.layout()
            while l.count():
                i = l.takeAt(0)
                if i.widget(): i.widget().deleteLater()
                elif i.layout():
                    s = i.layout()
                    while s.count():
                        si = s.takeAt(0)
                        if si.widget(): si.widget().deleteLater()
        else:
            l = QVBoxLayout(self.report_frame)
            l.setContentsMargins(16, 20, 16, 20)
            l.setSpacing(16)
        h = QHBoxLayout()
        h.setContentsMargins(0, 0, 0, 10)
        t = QLabel("📄 Bảng Tổng Hợp")
        t.setStyleSheet(f"font-weight: 800; font-size: 18px; color: {AppColors.PRIMARY};")
        h.addWidget(t)
        h.addStretch()
        if data:
            cb = QPushButton("×")
            cb.setObjectName("iconBtn")
            cb.setFixedSize(32, 32)
            cb.clicked.connect(lambda: self._show_report({}))
            h.addWidget(cb)
        l.addLayout(h)
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet(f"background-color: {AppColors.BORDER}; max-height: 1px;")
        l.addWidget(line)
        ac = self._create_stat_card("💰 Tiền thực tế", f"{data.get('actual_total', 0):,.0f} đ", AppColors.PRIMARY)
        l.addWidget(ac)
        cc = self._create_stat_card("🎰 Lượt 50K", f"{data.get('count_50k', 0)} lượt", AppColors.WARNING)
        l.addWidget(cc)
        l.addStretch()
        self.report_frame.show()
    
    def _create_stat_card(self, label, value, color):
        card = QFrame()
        card.setStyleSheet(f"QFrame {{ background-color: rgba({self._hex_to_rgb(color)}, 0.1); border-left: 4px solid {color}; border-radius: 6px; padding: 8px 12px; }}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(8, 6, 8, 6)
        cl.setSpacing(4)
        lw = QLabel(label)
        lw.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-size: 12px; font-weight: 500;")
        cl.addWidget(lw)
        vw = QLabel(value)
        vw.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: 700;")
        cl.addWidget(vw)
        return card
    
    def _hex_to_rgb(self, h):
        h = h.lstrip('#')
        return f"{int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)}"
    
    def _save_session(self):
        total = SessionRepository.get_total_amount()
        dialog = SaveSessionDialog(total, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.result_data:
            HistoryRepository.save_current_session(shift_name=dialog.result_data['shift_name'], notes=dialog.result_data['notes'])
            SessionRepository.reset_all()
            self.refresh_table()
            if self.on_refresh_stock: self.on_refresh_stock()
            QMessageBox.information(self, "Thành công", "Đã lưu phiên làm việc!")
