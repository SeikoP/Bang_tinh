"""
Main Application - Phần mềm Quản lý Xuất kho & Dịch vụ
PyQt6 Version - Modern Premium Design
"""
import sys
import json
import re
from pathlib import Path
from http.server import BaseHTTPRequestHandler, HTTPServer, ThreadingHTTPServer
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QTabWidget, QFrame, QLabel, QPushButton, QStackedWidget
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QEvent
import html
from PyQt6.QtGui import QFont, QIcon, QColor

from database.connection import init_db
from database.repositories import BankRepository
init_db()

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, BASE_DIR
from ui.qt_theme import AppTheme, AppColors
from datetime import datetime
from ui.qt_views.calculation_view import CalculationView
from ui.qt_views.stock_view import StockView
from ui.qt_views.product_view import ProductView
from ui.qt_views.history_view import HistoryView
from ui.qt_views.settings_view import SettingsView

from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView

class BankView(QWidget):
    """View hiển thị lịch sử thông báo ngân hàng chuyên nghiệp"""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        header_layout = QHBoxLayout()
        header = QLabel("🏦 Quản lý Giao dịch Điện thoại")
        header.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {AppColors.TEXT};")
        header_layout.addWidget(header)
        
        header_layout.addStretch()
        
        self.clear_btn = QPushButton("🗑️ Xóa lịch sử")
        self.clear_btn.setObjectName("secondary")
        self.clear_btn.setFixedWidth(150) # Tăng độ rộng để không mất chữ
        self.clear_btn.setStyleSheet(f"color: {AppColors.ERROR}; border-color: {AppColors.ERROR};")
        self.clear_btn.clicked.connect(self.clear_history)
        header_layout.addWidget(self.clear_btn)
        
        layout.addLayout(header_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Giờ", "Nguồn", "Số tiền", "Chi tiết tin nhắn", ""])
        
        h = self.table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        
        self.table.setColumnWidth(0, 80)
        self.table.setColumnWidth(1, 100)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(4, 50)
        
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(45) # Tăng chiều cao hàng để tránh mất chữ
        layout.addWidget(self.table)
        
        self.load_history()

    def load_history(self):
        """Tải lại lịch sử từ database"""
        notifs = BankRepository.get_all()
        for n in reversed(notifs): # Đảo ngược để thêm theo thứ tự cũ -> mới (vì add_row thêm lên đầu)
            self._add_row_ui(n.id, n.time_str, n.source, n.amount, n.content)
            
    def add_notif(self, time_str, source, amount, raw_message):
        # 1. Lưu vào database trước
        new_id = BankRepository.add(time_str, source, amount, raw_message)
        
        # 2. Hiển thị lên UI
        self._add_row_ui(new_id, time_str, source, amount, raw_message)

    def _add_row_ui(self, db_id, time_str, source, amount, raw_message):
        row = 0
        self.table.insertRow(row) # Thêm vào đầu bảng
        
        self.table.setItem(row, 0, QTableWidgetItem(time_str))
        
        src_item = QTableWidgetItem(source)
        src_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 1, src_item)
        
        amt_item = QTableWidgetItem(amount if amount else "---")
        amt_item.setForeground(QColor(AppColors.SUCCESS))
        amt_item.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        amt_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.table.setItem(row, 2, amt_item)
        
        self.table.setItem(row, 3, QTableWidgetItem(raw_message))
        
        # Nút xóa từng dòng (Centered Layout & Force Style)
        del_container = QWidget()
        del_container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        del_layout = QHBoxLayout(del_container)
        del_layout.setContentsMargins(0, 0, 0, 0)
        del_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        del_btn = QPushButton("🗑️")
        del_btn.setFixedSize(30, 30)
        del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        # Force style mạnh mẽ
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; 
                border: none; 
                font-size: 16px; 
                margin: 0px; 
                padding: 0px;
                color: #ef4444; 
            }
            QPushButton:hover {
                background-color: #fef2f2;
                border: 1px solid #ef4444;
                border-radius: 4px;
            }
        """)
        del_btn.clicked.connect(lambda: self._delete_row(db_id))
        
        del_layout.addWidget(del_btn)
        self.table.setCellWidget(row, 4, del_container)
        
        # Lưu ID vào item ẩn để tham chiếu nếu cần
        self.table.item(row, 0).setData(Qt.ItemDataRole.UserRole, db_id)

    def _delete_row(self, db_id): # Xóa row_index khỏi tham số vì không cần thiết
        """Xóa một dòng cụ thể dựa trên ID database"""
        # Tìm row index hiện tại (vì nó có thể thay đổi sau khi xóa row khác)
        target_row = -1
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item.data(Qt.ItemDataRole.UserRole) == db_id:
                target_row = r
                break
        
        if target_row != -1:
            BankRepository.delete(db_id)
            self.table.removeRow(target_row)

    def clear_history(self):
        """Xóa sạch bảng lịch sử"""
        BankRepository.clear_all()
        self.table.setRowCount(0)


from urllib.parse import urlparse, parse_qs

class NotificationHandler(BaseHTTPRequestHandler):
    """Server xử lý thông báo từ app Android linh hoạt hơn (POST/GET, Body/Query)"""
    
    def handle_request(self):
        try:
            msg = None
            # Log incoming request for debugging
            print(f"[Server] Received {self.command} request to {self.path}")
            
            # 1. Thử lấy từ URL Query (?content=...)
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            if 'content' in query_params:
                msg = query_params['content'][0]
                print(f"[Server] Found content in query: {msg}")
                
            # 2. Nếu URL không có, thử lấy từ Body
            if not msg:
                content_length = self.headers.get('Content-Length')
                if content_length and int(content_length) > 0:
                    post_data = self.rfile.read(int(content_length)).decode('utf-8')
                    print(f"[Server] Received body: {post_data}")
                    try:
                        data = json.loads(post_data)
                        msg = data.get('content', post_data)
                    except json.JSONDecodeError:
                        msg = post_data
            
            if msg:
                # Phản hồi cho client trước để giải phóng kết nối
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status":"success"}')
                
                # Sau đó mới đẩy lên giao diện
                print(f"[Server] Content: {msg}")
                if hasattr(self.server, 'signal'):
                    self.server.signal.emit(str(msg))
            else:
                self.send_response(400)
                self.end_headers()
        except Exception as e:
            # print(f"[Server] Error: {e}")
            try:
                self.send_response(500)
                self.end_headers()
            except: pass

    def do_POST(self):
        self.handle_request()
        
    def do_GET(self):
        self.handle_request()

    def log_message(self, format, *args):
        # Allow logging for debugging purposes if needed, but keep it clean
        # print(f"[HTTP] {format % args}")
        return

class NotificationServer(QThread):
    """Luồng chạy server lắng nghe thông báo"""
    msg_received = pyqtSignal(str)
    
    def run(self):
        try:
            # Sử dụng ThreadingHTTPServer để xử lý đa luồng
            server = ThreadingHTTPServer(('0.0.0.0', 5005), NotificationHandler)
            server.allow_reuse_address = True
            server.timeout = 5
            server.signal = self.msg_received
            print("\n>>> Notification Server OK (Port 5005) <<<")
            server.serve_forever()
        except Exception as e:
            print(f"Could not start server: {e}")


class QuickBankPeek(QFrame):
    """Cửa sổ hiện nhanh lịch sử giao dịch khi nhấn giữ nút Ngân hàng"""
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.ToolTip) # Hiển thị trên cùng
        self.setObjectName("card")
        self.setFixedWidth(350)
        self.setFixedHeight(400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # Tiêu đề và nút đóng
        header_layout = QHBoxLayout()
        title = QLabel("⚡ Xem nhanh giao dịch")
        title.setStyleSheet(f"font-weight: 800; color: {AppColors.PRIMARY};")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.setStyleSheet(f"background: transparent; color: {AppColors.TEXT_SECONDARY}; border: none; font-weight: bold;")
        close_btn.clicked.connect(self.hide)
        header_layout.addWidget(close_btn)
        layout.addLayout(header_layout)

        # Bảng thu nhỏ
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Giờ", "Tiền", "Nội dung"])
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 60)
        self.table.setColumnWidth(1, 90)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("font-size: 11px;")
        self.table.verticalHeader().setDefaultSectionSize(40) # Chiều cao hàng xem nhanh
        layout.addWidget(self.table)
        
        hint = QLabel("Nhấn vào nút Ngân hàng để xem đầy đủ")
        hint.setStyleSheet(f"color: {AppColors.TEXT_DISABLED}; font-size: 10px; font-style: italic;")
        layout.addWidget(hint)

    def update_data(self, bank_view_table):
        """Đồng bộ dữ liệu từ bảng chính sang bảng xem nhanh"""
        rows = min(bank_view_table.rowCount(), 15)
        self.table.setRowCount(rows)
        for r in range(rows):
            self.table.setItem(r, 0, QTableWidgetItem(bank_view_table.item(r, 0).text()))
            
            # Copy màu sắc số tiền
            amt_item = QTableWidgetItem(bank_view_table.item(r, 2).text())
            amt_item.setForeground(QColor(AppColors.SUCCESS))
            amt_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.table.setItem(r, 1, amt_item)
            
            self.table.setItem(r, 2, QTableWidgetItem(bank_view_table.item(r, 3).text()))

class MainWindow(QMainWindow):
    """Main window - modern premium design"""
    
    def __init__(self):
        super().__init__()
        self._setup_window()
        self._setup_ui()
        self._apply_theme()
        self._start_notification_server()
        
        # Timer để ẩn Quick Peek có độ trễ nhỏ (tránh flickering)
        self._peek_timer = QTimer()
        self._peek_timer.setSingleShot(True)
        self._peek_timer.timeout.connect(self._hide_peek_safe)
    
    def _setup_window(self):
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        icon_path = BASE_DIR / "assets" / "icon.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            if not icon.isNull():
                self.setWindowIcon(icon)
        
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - WINDOW_WIDTH) // 2
        y = (screen.height() - WINDOW_HEIGHT) // 2
        self.move(x, y)
    
    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Sidebar
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(150)
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setStyleSheet(f"background-color: {AppColors.SIDEBAR_BG}; border: none;")
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(12, 24, 12, 24)
        sidebar_layout.setSpacing(8)
        
        logo = QLabel("BANGLA")
        logo.setStyleSheet("color: white; font-weight: 950; font-size: 18px; padding: 0 4px 16px 4px;")
        sidebar_layout.addWidget(logo)
        
        self.nav_btns = []
        self._add_nav_btn(sidebar_layout, "🧮 Bảng tính", 0)
        self._add_nav_btn(sidebar_layout, "📦 Kho hàng", 1)
        self._add_nav_btn(sidebar_layout, "🏷️ Sản phẩm", 2)
        self._add_nav_btn(sidebar_layout, "🏦 Ngân hàng", 3)
        self._add_nav_btn(sidebar_layout, "📜 Lịch sử", 4)
        self._add_nav_btn(sidebar_layout, "⚙️ Cài đặt", 5)
        
        sidebar_layout.addStretch()
        version = QLabel(f"v{APP_VERSION}")
        version.setStyleSheet(f"color: {AppColors.SIDEBAR_TEXT}; font-size: 11px; padding: 10px;")
        sidebar_layout.addWidget(version)
        
        main_layout.addWidget(self.sidebar)
        
        # Content
        self.content_stack = QStackedWidget()
        self._create_views()
        self.content_stack.addWidget(self.calc_view)
        self.content_stack.addWidget(self.stock_view)
        self.content_stack.addWidget(self.product_view)
        self.content_stack.addWidget(self.bank_view)
        self.content_stack.addWidget(self.history_view)
        self.content_stack.addWidget(self.settings_view)
        
        main_content = QWidget()
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Global Header
        header = QFrame()
        header.setFixedHeight(64)
        header.setStyleSheet(f"background-color: white; border-bottom: 1px solid {AppColors.BORDER};")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(24, 0, 24, 0)
        
        self.breadcrumb = QLabel("Trang chủ > Bảng tính")
        self.breadcrumb.setStyleSheet(f"color: {AppColors.TEXT_SECONDARY}; font-weight: 500;")
        header_layout.addWidget(self.breadcrumb)
        
        header_layout.addStretch()
        
        # Notification Widget (Toast-like in header)
        self.notif_box = QFrame()
        self.notif_box.setFixedHeight(46)
        self.notif_box.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_box.setStyleSheet(f"""
            QFrame {{
                background: {AppColors.SUCCESS};
                border-radius: 23px;
                padding: 0 4px;
            }}
            QFrame:hover {{
                background: #059669;
            }}
        """)
        # Tính năng Nhấn và Rê chuột (Hover) cho Thông báo
        self.notif_box.mousePressEvent = lambda e: self._switch_view(3)
        self.notif_box.installEventFilter(self)
        
        notif_layout = QHBoxLayout(self.notif_box)
        notif_layout.setContentsMargins(15, 0, 5, 0)
        notif_layout.setSpacing(10)
        
        self.notif_label = QLabel("🔔 Chưa có thông báo mới")
        self.notif_label.setStyleSheet("color: white; font-weight: 600; font-size: 13px; background: transparent;")
        notif_layout.addWidget(self.notif_label)
        
        # Nút đóng thông báo (X)
        self.notif_close_btn = QPushButton("✕")
        self.notif_close_btn.setFixedSize(32, 32)
        self.notif_close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.notif_close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 16px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        self.notif_close_btn.clicked.connect(self.notif_box.hide)
        notif_layout.addWidget(self.notif_close_btn)
        
        self.notif_box.hide() # Ẩn mặc định
        header_layout.addWidget(self.notif_box)
        
        content_layout.addWidget(header)
        content_layout.addWidget(self.content_stack)
        main_layout.addWidget(main_content)
        
        self._switch_view(0)

    def _add_nav_btn(self, layout, text, index):
        btn = QPushButton(text)
        btn.setObjectName("navItem")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.clicked.connect(lambda: self._switch_view(index))
        
        # Nhấn giữ nút bên trái vẫn dùng hold
        if index == 3:
            self.bank_btn = btn
            btn.pressed.connect(self._start_bank_hold)
            btn.released.connect(self._stop_bank_hold)
            self._hold_timer = QTimer()
            self._hold_timer.setSingleShot(True)
            self._hold_timer.timeout.connect(self._on_bank_hold_success)
            
        layout.addWidget(btn)
        self.nav_btns.append(btn)

    def eventFilter(self, source, event):
        """Xử lý sự kiện di chuyển chuột (Hover)"""
        if source == self.notif_box:
            if event.type() == QEvent.Type.Enter:
                self._show_peek_under_notif()
            elif event.type() == QEvent.Type.Leave:
                # Đợi một chút rồi mới ẩn để người dùng có thể di chuyển chuột vào bảng
                self._peek_timer.start(200)
        
        if hasattr(self, 'quick_peek') and source == self.quick_peek:
            if event.type() == QEvent.Type.Enter:
                self._peek_timer.stop() # Hủy lệnh ẩn nếu chuột đi vào bảng
            elif event.type() == QEvent.Type.Leave:
                self._peek_timer.start(200)
                
        return super().eventFilter(source, event)

    def _show_peek_under_notif(self):
        """Hiện danh sách nhanh dưới thanh thông báo"""
        if not hasattr(self, 'quick_peek'):
            self.quick_peek = QuickBankPeek(self)
            self.quick_peek.installEventFilter(self)
        
        self.quick_peek.update_data(self.bank_view.table)
        pos = self.notif_box.mapToGlobal(self.notif_box.rect().bottomLeft())
        self.quick_peek.move(pos.x(), pos.y() + 5)
        self.quick_peek.show()
        self._peek_timer.stop()

    def _hide_peek_safe(self):
        if hasattr(self, 'quick_peek'):
            self.quick_peek.hide()

    def _start_bank_hold(self):
        self._hold_timer.start(500) # Nhấn giữ 0.5 giây
        
    def _stop_bank_hold(self):
        self._hold_timer.stop()
        
    def _on_bank_hold_success(self):
        """Khi nhấn giữ nút Sidebar -> Hiện danh sách nhanh"""
        if not hasattr(self, 'quick_peek'):
            self.quick_peek = QuickBankPeek(self)
            self.quick_peek.installEventFilter(self)
        
        self.quick_peek.update_data(self.bank_view.table)
        btn_pos = self.bank_btn.mapToGlobal(self.bank_btn.rect().topRight())
        self.quick_peek.move(btn_pos.x() + 10, btn_pos.y())
        self.quick_peek.show()
        self._peek_timer.stop()
        
    def _on_bank_hold_success(self):
        """Khi nhấn giữ đủ lâu, hiện cửa sổ xem nhanh"""
        if not hasattr(self, 'quick_peek'):
            self.quick_peek = QuickBankPeek(self)
        
        self.quick_peek.update_data(self.bank_view.table)
        
        # Tính toán vị trí hiển thị ngay cạnh sidebar
        btn_pos = self.bank_btn.mapToGlobal(self.bank_btn.rect().topRight())
        self.quick_peek.move(btn_pos.x() + 10, btn_pos.y())
        self.quick_peek.show()

    def _switch_view(self, index):
        self.content_stack.setCurrentIndex(index)
        names = ["Bảng tính", "Kho hàng", "Sản phẩm", "Ngân hàng", "Lịch sử", "Cài đặt"]
        self.breadcrumb.setText(f"Trang chủ > {names[index]}")
        for i, btn in enumerate(self.nav_btns):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
    
    def _create_views(self):
        self.calc_view = CalculationView(on_refresh_stock=self._refresh_stock)
        self.stock_view = StockView(on_refresh_calc=self._refresh_calc)
        self.product_view = ProductView(on_refresh_calc=self._refresh_calc)
        self.bank_view = BankView() # View mới cho Ngân hàng
        self.history_view = HistoryView()
        self.settings_view = SettingsView()
        
        # Kết nối signals từ settings để cập nhật UI real-time
        self.settings_view.row_height_changed.connect(self._on_row_height_changed)
        self.settings_view.widget_height_changed.connect(self._on_widget_height_changed)
    
    def _start_notification_server(self):
        """Khởi chạy server ngầm để nhận thông báo"""
        self.notif_thread = NotificationServer()
        self.notif_thread.msg_received.connect(self._show_notification)
        self.notif_thread.start()
        
    def _show_notification(self, message):
        """Hiển thị thông báo an toàn (Safe UI Thread)"""
        # Đưa việc cập nhật UI vào hàng đợi chính của Qt để tránh treo luồng
        QTimer.singleShot(0, lambda: self._do_show_notification(message))

    def _do_show_notification(self, message):
        now = datetime.now()
        if hasattr(self, '_last_msg_content') and self._last_msg_content == message:
             if (now - self._last_msg_time).total_seconds() < 2:
                return
        
        self._last_msg_content = message
        self._last_msg_time = now

        source = "Phone"
        msg_lower = message.lower()
        if "momo" in msg_lower: source = "MoMo"
        elif "vcb" in msg_lower or "vietcombank" in msg_lower: source = "VCB"
        elif "mb" in msg_lower or "mbbank" in msg_lower: source = "MB"
        elif "tpbank" in msg_lower: source = "TPBank"

        amount = self._extract_amount(message)
        timestamp = now.strftime("%H:%M:%S")

        # HTML Escape để tránh lỗi ký tự đặc biệt phá hỏng giao diện
        safe_msg = html.escape(message[:100])
        safe_source = html.escape(source)
        safe_amount = html.escape(amount) if amount else ""

        if amount:
            rich_text = f"<b style='font-size:15px; color:white;'>{safe_amount}</b><br><span style='font-size:11px; color:#e1f5fe;'>{safe_source}: {safe_msg}</span>"
        else:
            rich_text = f"<b>Tin nhắn mới</b><br><span style='font-size:11px;'>{safe_msg}</span>"

        self.notif_label.setText(rich_text)
        self.notif_box.show()
        
        if hasattr(self, 'bank_view'):
            self.bank_view.add_notif(timestamp, source, amount, message)

    def _extract_amount(self, text):
        pattern = r'(?:\+|\-)?\d{1,3}(?:[.,]\d{3})+(?:\s?[đVNDvmd])?'
        matches = re.findall(pattern, text)
        return matches[0] if matches else None

    def _refresh_calc(self):
        if hasattr(self, 'calc_view'):
            self.calc_view.refresh_table()
    
    def _refresh_stock(self):
        if hasattr(self, 'stock_view'):
            self.stock_view.refresh_list()
    
    def _on_row_height_changed(self, height: int):
        """Cập nhật chiều cao row cho tất cả tables"""
        # Calculation view
        if hasattr(self, 'calc_view'):
            self.calc_view.table.verticalHeader().setDefaultSectionSize(height)
            self.calc_view.prod_table.verticalHeader().setDefaultSectionSize(height)
        
        # Stock view
        if hasattr(self, 'stock_view'):
            self.stock_view.table.verticalHeader().setDefaultSectionSize(height)
        
        # Product view
        if hasattr(self, 'product_view'):
            self.product_view.table.verticalHeader().setDefaultSectionSize(height)
        
        # History view
        if hasattr(self, 'history_view'):
            self.history_view.table.verticalHeader().setDefaultSectionSize(height)
        
        # Bank view
        if hasattr(self, 'bank_view'):
            self.bank_view.table.verticalHeader().setDefaultSectionSize(height)
    
    def _on_widget_height_changed(self, height: int):
        """Cập nhật chiều cao widget - cần refresh lại views"""
        # Lưu giá trị mới
        if hasattr(self, 'calc_view'):
            self.calc_view._widget_height = height
            self.calc_view.refresh_table()
        
        if hasattr(self, 'stock_view'):
            self.stock_view._widget_height = height
            self.stock_view.refresh_list()
        
        if hasattr(self, 'product_view'):
            self.product_view._widget_height = height
            self.product_view.refresh_list()
    
    def _apply_theme(self):
        self.setStyleSheet(AppTheme.get_stylesheet())


def main():
    import ctypes
    try:
        myappid = 'bangtinh.warehouse.app.2.0'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except: pass
    
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    
    icon_path = BASE_DIR / "assets" / "icon.png"
    if icon_path.exists():
        icon = QIcon(str(icon_path))
        if not icon.isNull(): app.setWindowIcon(icon)
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
