"""
Dialog Components
"""
import flet as ft
from flet import Icons, Colors

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ui.theme import AppTheme


class ConfirmDialog(ft.AlertDialog):
    """Dialog xác nhận hành động"""
    
    def __init__(
        self,
        title: str,
        content: str,
        on_confirm: callable,
        on_cancel: callable = None,
        confirm_text: str = "Xác nhận",
        cancel_text: str = "Hủy",
        is_danger: bool = False,
    ):
        super().__init__(
            modal=True,
            title=ft.Text(title, weight=ft.FontWeight.BOLD),
            content=ft.Text(content),
            actions=[
                ft.TextButton(
                    cancel_text,
                    on_click=lambda e: on_cancel() if on_cancel else None,
                ),
                ft.Button(
                    confirm_text,
                    on_click=lambda e: on_confirm(),
                    style=AppTheme.danger_button_style() if is_danger else AppTheme.primary_button_style(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )


class ProductDialog(ft.AlertDialog):
    """Dialog thêm/sửa sản phẩm"""
    
    def __init__(
        self,
        on_save: callable,
        on_cancel: callable,
        product: dict = None,
        is_edit: bool = False,
    ):
        self.product = product
        self.is_edit = is_edit
        self.on_save = on_save
        self.on_cancel = on_cancel
        
        # Fields
        self.name_field = ft.TextField(
            label="Tên sản phẩm",
            value=product['name'] if product else "",
            autofocus=True,
            border_radius=8,
        )
        
        self.unit_field = ft.Dropdown(
            label="Đơn vị lớn",
            options=[
                ft.dropdown.Option("Thùng"),
                ft.dropdown.Option("Vỉ"),
                ft.dropdown.Option("Gói"),
                ft.dropdown.Option("Két"),
                ft.dropdown.Option("Hộp"),
                ft.dropdown.Option("Chai"),
            ],
            value=product['large_unit'] if product else "Thùng",
            border_radius=8,
        )
        
        self.conv_field = ft.TextField(
            label="Quy đổi (số đơn vị nhỏ trong 1 đơn vị lớn)",
            value=str(product['conversion']) if product else "24",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
        )
        
        self.price_field = ft.TextField(
            label="Đơn giá (VNĐ/đơn vị nhỏ)",
            value=str(int(product['unit_price'])) if product else "0",
            keyboard_type=ft.KeyboardType.NUMBER,
            border_radius=8,
        )
        
        super().__init__(
            modal=True,
            title=ft.Text(
                "Chỉnh sửa sản phẩm" if is_edit else "Thêm sản phẩm mới",
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Container(
                content=ft.Column([
                    self.name_field,
                    self.unit_field,
                    self.conv_field,
                    self.price_field,
                ], spacing=15, tight=True),
                width=350,
            ),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: self._handle_cancel()),
                ft.Button(
                    "Lưu",
                    icon=Icons.SAVE,
                    on_click=lambda e: self._handle_save(),
                    style=AppTheme.primary_button_style(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _validate(self) -> bool:
        """Validate input"""
        valid = True
        
        if not self.name_field.value.strip():
            self.name_field.error_text = "Vui lòng nhập tên"
            valid = False
        else:
            self.name_field.error_text = None
            
        try:
            conv = int(self.conv_field.value)
            if conv <= 0:
                self.conv_field.error_text = "Phải > 0"
                valid = False
            else:
                self.conv_field.error_text = None
        except ValueError:
            self.conv_field.error_text = "Số không hợp lệ"
            valid = False
            
        try:
            price = float(self.price_field.value)
            if price <= 0:
                self.price_field.error_text = "Phải > 0"
                valid = False
            else:
                self.price_field.error_text = None
        except ValueError:
            self.price_field.error_text = "Số không hợp lệ"
            valid = False
        
        return valid
    
    def _handle_save(self):
        if self._validate():
            data = {
                'id': self.product['id'] if self.product else None,
                'name': self.name_field.value.strip(),
                'large_unit': self.unit_field.value,
                'conversion': int(self.conv_field.value),
                'unit_price': float(self.price_field.value),
            }
            # Gọi callback lưu
            self.on_save(data)
    
    def _handle_cancel(self):
        self.on_cancel()


class SaveSessionDialog(ft.AlertDialog):
    """Dialog lưu phiên làm việc"""
    
    def __init__(
        self,
        total_amount: float,
        on_save: callable,
        on_cancel: callable,
    ):
        self.on_save = on_save
        self.on_cancel = on_cancel
        
        self.shift_field = ft.Dropdown(
            label="Ca làm việc",
            options=[
                ft.dropdown.Option("Ca sáng"),
                ft.dropdown.Option("Ca chiều"),
                ft.dropdown.Option("Ca tối"),
                ft.dropdown.Option("Ca đêm"),
            ],
            value="Ca sáng",
            border_radius=8,
        )
        
        self.notes_field = ft.TextField(
            label="Ghi chú (tùy chọn)",
            multiline=True,
            min_lines=2,
            max_lines=4,
            border_radius=8,
        )
        
        super().__init__(
            modal=True,
            title=ft.Text("Lưu phiên làm việc", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(Icons.MONETIZATION_ON, color=AppTheme.SUCCESS, size=28),
                            ft.Text(
                                f"Tổng tiền: {total_amount:,.0f} VNĐ",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                color=AppTheme.PRIMARY,
                            ),
                        ]),
                        padding=ft.padding.symmetric(vertical=10),
                    ),
                    ft.Divider(),
                    self.shift_field,
                    self.notes_field,
                ], spacing=15, tight=True),
                width=350,
            ),
            actions=[
                ft.TextButton("Hủy", on_click=lambda e: self._handle_cancel()),
                ft.Button(
                    "Lưu & Làm mới",
                    icon=Icons.SAVE,
                    on_click=lambda e: self._handle_save(),
                    style=AppTheme.primary_button_style(),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    
    def _handle_save(self):
        data = {
            'shift_name': self.shift_field.value,
            'notes': self.notes_field.value.strip() if self.notes_field.value else None,
        }
        self.on_save(data)
    
    def _handle_cancel(self):
        self.on_cancel()
