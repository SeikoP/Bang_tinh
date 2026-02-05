import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem, 
    QWidget, QHBoxLayout, QPushButton, QHeaderView, QSizePolicy
)
from PyQt6.QtCore import Qt

class TableButtonExample(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QTableWidget Button Fix Example")
        self.resize(600, 400)
        
        self.table = QTableWidget()
        self.setCentralWidget(self.table)
        self.setup_table()
        
    def setup_table(self):
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", "Sản phẩm", "Thao tác"])
        self.table.setRowCount(5)
        
        # =======================================================
        # 4. Auto resize column logic (Cấu hình Header)
        # =======================================================
        header = self.table.horizontalHeader()
        
        # ID: Cố định
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 50)
        
        # Tên: Giãn hết cỡ
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        # Thao tác: Tự động co giãn theo nội dung (ResizeToContents)
        # Hoặc dùng Fixed nếu muốn kích thước cố định an toàn
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        
        # Đặt chiều cao hàng phù hợp để button không bị đè
        self.table.verticalHeader().setDefaultSectionSize(40)

        for row in range(5):
            self.table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            self.table.setItem(row, 1, QTableWidgetItem(f"Sản phẩm mẫu {row + 1}"))
            
            # Tạo widget chứa button
            action_widget = self.create_action_widget(row)
            self.table.setCellWidget(row, 2, action_widget)
            
    def create_action_widget(self, row_index):
        # 1. Tối ưu layout trong cell bằng QHBoxLayout
        container = QWidget()
        layout = QHBoxLayout(container)
        
        # 2. Set contentsMargins hợp lý
        # Default PyQt để margin khá lớn (khoảng 11px), cần set về nhỏ (ví dụ 0 hoặc 2)
        # Thứ tự: Left, Top, Right, Bottom
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(6) # Khoảng cách giữa các nút
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Căn giữa
        
        # CSS cho nút đẹp hơn
        common_style = """
            QPushButton {
                padding: 4px 12px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f8f9fa;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #e2e6ea; }
        """
        
        # Nút Sửa
        btn_edit = QPushButton("Sửa")
        btn_edit.setStyleSheet(common_style)
        
        # Nút Xóa
        btn_delete = QPushButton("Xóa")
        btn_delete.setStyleSheet(common_style.replace("#f8f9fa", "#fff5f5").replace("#ccc", "#ffc9c9"))
        
        # 3. Set sizePolicy cho button
        # Expanding: Cho phép nút giãn ra nếu còn chỗ
        # Fixed: Giữ nguyên size hint
        # Ở đây dùng Fixed hoặc Preferred kèm MinWidth/MaxHeight để tránh bị nát
        btn_edit.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        btn_delete.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        
        # 5. Đảm bảo button không bị clipped (Quan trọng)
        # Không dùng setFixedSize cứng nếu không kiểm soát được column width
        # Nhưng setFixedHeight thì OK để căn vertical
        btn_edit.setFixedHeight(28) 
        btn_delete.setFixedHeight(28)
        
        layout.addWidget(btn_edit)
        layout.addWidget(btn_delete)
        
        return container

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TableButtonExample()
    window.show()
    sys.exit(app.exec())
