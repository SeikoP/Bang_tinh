from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QComboBox, QDialog, QDoubleSpinBox, QFormLayout,
                             QHBoxLayout, QLineEdit, QMessageBox, QPushButton,
                             QSpinBox, QVBoxLayout)

from ...core.constants import DEFAULT_UNITS


class ProductDialog(QDialog):
    """Dialog thêm/sửa sản phẩm"""

    def __init__(self, product=None, parent=None):
        super().__init__(parent)
        self.product = product
        self.result_data = None
        self._setup_ui()

    def keyPressEvent(self, event):
        """Handle Enter key to submit dialog"""
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if (
                not event.modifiers()
                or event.modifiers() == Qt.KeyboardModifier.KeypadModifier
            ):
                self._save()
                return
        super().keyPressEvent(event)

    def _setup_ui(self):
        self.setWindowTitle("Thêm sản phẩm" if not self.product else "Sửa sản phẩm")
        self.setFixedWidth(420)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(28, 24, 28, 24)

        form = QFormLayout()
        form.setSpacing(16)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

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
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập tên!")
            return

        self.result_data = {
            "name": name,
            "large_unit": self.unit_combo.currentText(),
            "conversion": self.conversion_spin.value(),
            "unit_price": self.price_spin.value(),
        }
        self.accept()
