"""Test để tìm nguyên nhân border bị cắt"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
    QWidget, QVBoxLayout, QLineEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import Qt

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Border Issue")
        self.resize(800, 600)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Test 1: QLineEdit trực tiếp
        test1 = QLineEdit("Test 1: Direct QLineEdit")
        test1.setFixedHeight(28)
        test1.setStyleSheet("""
            QLineEdit {
                border: 3px solid red;
                border-radius: 5px;
                background: white;
            }
        """)
        layout.addWidget(test1)
        
        # Test 2: QLineEdit trong QTableWidget
        table = QTableWidget()
        table.setColumnCount(2)
        table.setRowCount(3)
        table.setHorizontalHeaderLabels(["Test", "Widget"])
        table.verticalHeader().setVisible(False)
        
        # Row 1: QLineEdit với height khác nhau
        table.verticalHeader().setDefaultSectionSize(50)
        table.setItem(0, 0, QTableWidgetItem("Row height: 50px"))
        
        container1 = QWidget()
        layout1 = QVBoxLayout(container1)
        layout1.setContentsMargins(5, 5, 5, 5)
        layout1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit1 = QLineEdit("Widget 28px")
        edit1.setFixedHeight(28)
        edit1.setStyleSheet("""
            QLineEdit {
                border: 3px solid blue;
                border-radius: 5px;
                background: yellow;
            }
        """)
        layout1.addWidget(edit1)
        table.setCellWidget(0, 1, container1)
        
        # Row 2: Row height = widget height
        table.setRowHeight(1, 32)
        table.setItem(1, 0, QTableWidgetItem("Row height: 32px"))
        
        container2 = QWidget()
        layout2 = QVBoxLayout(container2)
        layout2.setContentsMargins(0, 0, 0, 0)
        layout2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        edit2 = QLineEdit("Widget 28px")
        edit2.setFixedHeight(28)
        edit2.setStyleSheet("""
            QLineEdit {
                border: 3px solid green;
                border-radius: 5px;
                background: lightblue;
            }
        """)
        layout2.addWidget(edit2)
        table.setCellWidget(1, 1, container2)
        
        # Row 3: Buttons
        table.setRowHeight(2, 60)
        table.setItem(2, 0, QTableWidgetItem("Buttons"))
        
        container3 = QWidget()
        layout3 = QVBoxLayout(container3)
        layout3.setContentsMargins(0, 0, 0, 0)
        layout3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(5)
        
        btn1 = QPushButton("Sửa")
        btn1.setFixedSize(60, 30)
        btn1.setStyleSheet("""
            QPushButton {
                border: 2px solid purple;
                border-radius: 4px;
                background: white;
            }
        """)
        btn_layout.addWidget(btn1)
        
        btn2 = QPushButton("Xóa")
        btn2.setFixedSize(60, 30)
        btn2.setStyleSheet("""
            QPushButton {
                border: 2px solid orange;
                border-radius: 4px;
                background: white;
            }
        """)
        btn_layout.addWidget(btn2)
        
        inner_widget = QWidget()
        inner_widget.setLayout(btn_layout)
        layout3.addWidget(inner_widget)
        table.setCellWidget(2, 1, container3)
        
        layout.addWidget(table)
        
        # Info label
        info = QLineEdit("Kiểm tra xem border có hiển thị đầy đủ 4 cạnh không?")
        info.setReadOnly(True)
        layout.addWidget(info)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec())
