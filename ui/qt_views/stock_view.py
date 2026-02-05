from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from ui.qt_theme import AppColors
from database import SessionRepository
from services import CalculatorService


class StockView(QWidget):
    """View kho hàng - Tối ưu nhập liệu bằng QLineEdit thay vì QSpinBox"""
    
    def __init__(self, on_refresh_calc=None):
        super().__init__()
        self.on_refresh_calc = on_refresh_calc
        self.calc_service = CalculatorService()
        self._setup_ui()
        self.refresh_list()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)
        
        # Toolbar
        self.toolbar = QFrame()
        self.toolbar.setStyleSheet("background: transparent;")
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)
        
        refresh_btn = QPushButton("🔄 Làm mới dữ liệu")
        refresh_btn.setObjectName("secondary")
        refresh_btn.setFixedWidth(200) # Đủ rộng cho text và icon
        refresh_btn.clicked.connect(self.refresh_list)
        toolbar_layout.addWidget(refresh_btn)
        
        toolbar_layout.addStretch()
        
        layout.addWidget(self.toolbar)
        
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
        
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 75)
        self.table.setColumnWidth(3, 75)
        self.table.setColumnWidth(4, 160) # Rộng hơn cho container nhập liệu
        self.table.setColumnWidth(5, 160)
        self.table.setColumnWidth(6, 110)
        
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(64) # Độ cao thoải mái cho container
    
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
    
    def refresh_list(self):
        sessions = SessionRepository.get_all()
        self.table.setRowCount(len(sessions))
        
        for row, s in enumerate(sessions):
            p = s.product
            l_qty = s.closing_qty // p.conversion
            s_qty = s.closing_qty % p.conversion
            
            has_data = s.closing_qty > 0
            row_bg = "rgba(37, 99, 235, 0.05)" if has_data else None
            
            self._set_cell(row, 0, str(row + 1), center=True, fg=AppColors.TEXT, bg=row_bg)
            self._set_cell(row, 1, p.name, bold=True, fg=AppColors.TEXT, bg=row_bg)
            
            # Unit
            u_item = QTableWidgetItem(p.large_unit)
            u_item.setFlags(u_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            u_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            u_item.setBackground(QColor(row_bg if has_data else "transparent"))
            u_item.setForeground(QColor(AppColors.PRIMARY))
            font = u_item.font()
            font.setBold(True)
            u_item.setFont(font)
            self.table.setItem(row, 2, u_item)
            
            self._set_cell(row, 3, str(p.conversion), center=True, fg=AppColors.TEXT, bg=row_bg)
            
            # Styles for inputs
            input_css = f"""
                QLineEdit {{
                    border: 1px solid {AppColors.BORDER};
                    border-radius: 4px;
                    padding: 2px;
                    font-weight: 700;
                    font-size: 13px;
                    background: white;
                    color: {AppColors.TEXT};
                }}
                QLineEdit:focus {{ border: 2px solid {AppColors.PRIMARY}; }}
            """
            
            # Large qty controls
            l_container = QFrame()
            l_layout = QHBoxLayout(l_container)
            l_layout.setContentsMargins(4, 0, 4, 0)
            l_layout.setSpacing(6)
            
            btn_m_l = QPushButton("➖")
            btn_m_l.setObjectName("iconBtn")
            btn_m_l.setFixedSize(36, 36)
            btn_m_l.clicked.connect(lambda _, pid=p.id, c=p.conversion, sq=s_qty: 
                                  self._adjust_qty(pid, c, sq, -1, True))
            
            edit_l = QLineEdit(str(l_qty))
            edit_l.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_l.setFixedHeight(34)
            edit_l.setStyleSheet(input_css)
            edit_l.editingFinished.connect(lambda w=edit_l, sq=s_qty, c=p.conversion, pid=p.id: 
                                         self._on_direct_change(pid, w.text(), str(sq), c))
            
            btn_p_l = QPushButton("➕")
            btn_p_l.setObjectName("iconBtn")
            btn_p_l.setFixedSize(36, 36)
            btn_p_l.clicked.connect(lambda _, pid=p.id, c=p.conversion, sq=s_qty: 
                                  self._adjust_qty(pid, c, sq, 1, True))
            
            l_layout.addWidget(btn_m_l)
            l_layout.addWidget(edit_l, 1)
            l_layout.addWidget(btn_p_l)
            self.table.setCellWidget(row, 4, l_container)
            
            # Small qty controls
            s_container = QFrame()
            s_layout = QHBoxLayout(s_container)
            s_layout.setContentsMargins(4, 0, 4, 0)
            s_layout.setSpacing(6)
            
            btn_m_s = QPushButton("➖")
            btn_m_s.setObjectName("iconBtn")
            btn_m_s.setFixedSize(36, 36)
            btn_m_s.clicked.connect(lambda _, pid=p.id, c=p.conversion, lq=l_qty: 
                                  self._adjust_qty(pid, c, lq, -1, False))
            
            edit_s = QLineEdit(str(s_qty))
            edit_s.setAlignment(Qt.AlignmentFlag.AlignCenter)
            edit_s.setFixedHeight(34)
            edit_s.setStyleSheet(input_css)
            edit_s.editingFinished.connect(lambda w=edit_s, lq=l_qty, c=p.conversion, pid=p.id: 
                                         self._on_direct_change(pid, str(lq), w.text(), c))
            
            btn_p_s = QPushButton("➕")
            btn_p_s.setObjectName("iconBtn")
            btn_p_s.setFixedSize(36, 36)
            btn_p_s.clicked.connect(lambda _, pid=p.id, c=p.conversion, lq=l_qty: 
                                  self._adjust_qty(pid, c, lq, 1, False))
            
            s_layout.addWidget(btn_m_s)
            s_layout.addWidget(edit_s, 1)
            s_layout.addWidget(btn_p_s)
            self.table.setCellWidget(row, 5, s_container)
            
            # Total - Tăng tương phản
            t_text = str(s.closing_qty)
            fg = "white" if has_data else AppColors.TEXT
            bg = AppColors.PRIMARY if has_data else "#e2e8f0"
            self._set_cell(row, 6, t_text, center=True, bold=True, fg=fg, bg=bg)
        
    def _adjust_qty(self, pid, conv, o_qty, delta, is_l):
        sessions = SessionRepository.get_all()
        sess = next((s for s in sessions if s.product.id == pid), None)
        if not sess: return
        cur_l = sess.closing_qty // conv
        cur_s = sess.closing_qty % conv
        if is_l:
            new_l = max(0, cur_l + delta)
            new_c = new_l * conv + cur_s
        else:
            new_s = max(0, min(conv - 1, cur_s + delta))
            new_c = cur_l * conv + new_s
        new_c = min(new_c, sess.handover_qty)
        SessionRepository.update_qty(pid, sess.handover_qty, new_c)
        self.refresh_list()
        if self.on_refresh_calc: self.on_refresh_calc()

    def _on_direct_change(self, pid, l_str, s_str, conv):
        sessions = SessionRepository.get_all()
        sess = next((s for s in sessions if s.product.id == pid), None)
        if not sess: return
        try:
            l = int(l_str) if l_str else 0
            s = int(s_str) if s_str else 0
        except ValueError:
            self.refresh_list()
            return
        new_c = min(l * conv + s, sess.handover_qty)
        SessionRepository.update_qty(pid, sess.handover_qty, new_c)
        self.refresh_list()
        if self.on_refresh_calc: self.on_refresh_calc()
