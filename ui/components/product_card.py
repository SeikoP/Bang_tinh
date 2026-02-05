"""
Product Card Component
"""
import flet as ft
from flet import Icons, Colors

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ui.theme import AppTheme


class ProductCard(ft.Container):
    """Card hiển thị thông tin sản phẩm"""
    
    def __init__(
        self,
        product_id: int,
        name: str,
        unit: str,
        conversion: int,
        price: float,
        on_edit: callable = None,
        on_delete: callable = None,
        is_dark: bool = False,
    ):
        self.product_id = product_id
        self.is_dark = is_dark
        self.on_edit = on_edit
        self.on_delete = on_delete
        
        super().__init__(
            content=ft.Row([
                # Icon
                ft.Container(
                    content=ft.Icon(Icons.INVENTORY_2, color=AppTheme.PRIMARY, size=32),
                    padding=10,
                ),
                # Info
                ft.Column([
                    ft.Text(
                        name, 
                        size=18, 
                        weight=ft.FontWeight.BOLD,
                        color=AppTheme.TEXT_DARK if is_dark else AppTheme.TEXT_LIGHT,
                    ),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(unit, size=12, color=Colors.WHITE),
                            bgcolor=AppTheme.PRIMARY,
                            padding=ft.padding.symmetric(horizontal=8, vertical=2),
                            border_radius=4,
                        ),
                        ft.Text(
                            f"Quy đổi: {conversion}",
                            size=13,
                            color=AppTheme.TEXT_SECONDARY_DARK if is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                        ft.Text(
                            f"Đơn giá: {price:,.0f}đ",
                            size=13,
                            color=AppTheme.PRIMARY,
                            weight=ft.FontWeight.W_500,
                        ),
                    ], spacing=10),
                ], expand=True, spacing=5),
                # Actions
                ft.Row([
                    ft.IconButton(
                        icon=Icons.EDIT_OUTLINED,
                        icon_color=AppTheme.PRIMARY,
                        tooltip="Chỉnh sửa",
                        on_click=lambda e, pid=product_id: self.on_edit(pid) if self.on_edit else None,
                    ),
                    ft.IconButton(
                        icon=Icons.DELETE_OUTLINE,
                        icon_color=AppTheme.ERROR,
                        tooltip="Xóa",
                        on_click=lambda e, pid=product_id: self.on_delete(pid) if self.on_delete else None,
                    ),
                ], spacing=0),
            ]),
            padding=15,
            border_radius=12,
            bgcolor=AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT,
            shadow=ft.BoxShadow(
                blur_radius=8,
                spread_radius=1,
                color=Colors.with_opacity(0.1 if not is_dark else 0.3, "black"),
            ),
            animate=ft.Animation(200, ft.AnimationCurve.EASE_OUT),
            on_hover=self._on_hover,
        )
    
    def _on_hover(self, e):
        """Hiệu ứng hover"""
        if e.data == "true":
            self.shadow = ft.BoxShadow(
                blur_radius=15,
                spread_radius=2,
                color=Colors.with_opacity(0.15 if not self.is_dark else 0.4, "black"),
            )
            self.scale = 1.01
        else:
            self.shadow = ft.BoxShadow(
                blur_radius=8,
                spread_radius=1,
                color=Colors.with_opacity(0.1 if not self.is_dark else 0.3, "black"),
            )
            self.scale = 1.0
        self.update()
