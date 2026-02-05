"""
Product View - Màn hình quản lý sản phẩm
Thiết kế hiện đại với DataTable
"""
import flet as ft
from flet import Icons, Colors

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import AppTheme
from ui.components.dialogs import ProductDialog, ConfirmDialog
from database import ProductRepository


class ProductView(ft.Container):
    """View quản lý sản phẩm - Hiển thị dạng bảng hiện đại"""
    
    def __init__(self, page: ft.Page, on_refresh_calc: callable = None, is_dark: bool = False):
        self._page = page
        self.on_refresh_calc = on_refresh_calc
        self.is_dark = is_dark
        
        # Search field với style mới
        self.search_field = ft.TextField(
            hint_text="Tìm kiếm sản phẩm...",
            prefix_icon=Icons.SEARCH_ROUNDED,
            border_radius=AppTheme.RADIUS_LG,
            width=280,
            height=44,
            dense=True,
            border_color=AppTheme.BORDER_DARK if is_dark else AppTheme.BORDER_LIGHT,
            focused_border_color=AppTheme.PRIMARY,
            on_change=self._on_search,
        )
        
        # Product table
        self.product_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("STT", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Tên sản phẩm", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Đơn vị", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Quy đổi", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Đơn giá", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Thao tác", weight=ft.FontWeight.W_600, size=13)),
            ],
            rows=[],
            **AppTheme.data_table_style(self.is_dark),
        )
        
        super().__init__(
            content=ft.Column([
                self._build_header(),
                ft.Container(height=16),
                ft.Container(
                    content=ft.Column([self.product_table], scroll=ft.ScrollMode.AUTO),
                    expand=True,
                    **AppTheme.card_style(self.is_dark),
                ),
            ]),
            padding=0,
            expand=True,
        )
        
        self.refresh_list()
    
    def _build_header(self) -> ft.Container:
        """Build header section - Premium style"""
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(Icons.CATEGORY_ROUNDED, color=Colors.WHITE, size=22),
                        width=42,
                        height=42,
                        bgcolor=AppTheme.ACCENT,
                        border_radius=AppTheme.RADIUS_MD,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(
                            "Quản lý Sản phẩm",
                            size=22,
                            weight=ft.FontWeight.W_700,
                            color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                        ),
                        ft.Text(
                            "Thêm, sửa, xóa danh mục sản phẩm",
                            size=13,
                            color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                    ], spacing=2),
                ], spacing=14),
                ft.Row([
                    self.search_field,
                    ft.Container(
                        content=ft.Button(
                            "Thêm mới",
                            icon=Icons.ADD_ROUNDED,
                            on_click=self._on_add_click,
                            style=AppTheme.primary_button_style(),
                        ),
                    ),
                ], spacing=12),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(0, 16, 0, 0),
        )
    
    def _on_add_click(self, e):
        """Handle click nút thêm sản phẩm"""
        self._open_product_dialog()
    
    def refresh_list(self, keyword: str = ""):
        """Refresh danh sách sản phẩm"""
        if keyword:
            products = ProductRepository.search(keyword)
        else:
            products = ProductRepository.get_all()
        
        self.product_table.rows.clear()
        
        if not products:
            # Empty state
            self.product_table.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Container(
                        content=ft.Column([
                            ft.Icon(Icons.INVENTORY_2_OUTLINED, size=48, color=Colors.with_opacity(0.4, AppTheme.TEXT_SECONDARY_LIGHT)),
                            ft.Text(
                                "Chưa có sản phẩm nào" if not keyword else "Không tìm thấy sản phẩm",
                                size=14,
                                color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                            ),
                            ft.Text(
                                "Nhấn 'Thêm mới' để tạo sản phẩm" if not keyword else "Thử tìm kiếm với từ khóa khác",
                                size=12,
                                color=Colors.with_opacity(0.5, AppTheme.TEXT_SECONDARY_LIGHT),
                            ),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                        padding=30,
                    )),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                    ft.DataCell(ft.Text("")),
                ])
            )
        else:
            for idx, p in enumerate(products, 1):
                self.product_table.rows.append(
                    self._build_product_row(idx, p)
                )
        
        self._page.update()
    
    def _build_product_row(self, idx: int, product) -> ft.DataRow:
        """Build một row cho bảng sản phẩm"""
        product_id = product.id
        
        return ft.DataRow(
            cells=[
                # STT
                ft.DataCell(ft.Container(
                    content=ft.Text(str(idx), weight=ft.FontWeight.W_500, size=13),
                    width=30,
                    alignment=ft.Alignment(0, 0),
                )),
                
                # Tên sản phẩm
                ft.DataCell(ft.Text(
                    product.name,
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                )),
                
                # Đơn vị lớn - Badge style
                ft.DataCell(ft.Container(
                    content=ft.Text(product.large_unit, size=12, color=Colors.WHITE, weight=ft.FontWeight.W_500),
                    bgcolor=AppTheme.PRIMARY,
                    padding=ft.Padding(10, 5, 10, 5),
                    border_radius=AppTheme.RADIUS_SM,
                )),
                
                # Quy đổi
                ft.DataCell(ft.Text(
                    f"1 = {product.conversion} đơn vị lẻ",
                    size=13,
                    color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                )),
                
                # Đơn giá - Highlighted
                ft.DataCell(ft.Text(
                    f"{product.unit_price:,.0f} đ",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=AppTheme.SUCCESS,
                )),
                
                # Thao tác - Icon buttons
                ft.DataCell(ft.Row([
                    ft.IconButton(
                        icon=Icons.EDIT_ROUNDED,
                        icon_color=AppTheme.PRIMARY,
                        icon_size=20,
                        tooltip="Chỉnh sửa",
                        on_click=lambda e, pid=product_id: self._open_product_dialog(pid),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_SM),
                            overlay_color=Colors.with_opacity(0.1, AppTheme.PRIMARY),
                        ),
                    ),
                    ft.IconButton(
                        icon=Icons.DELETE_ROUNDED,
                        icon_color=AppTheme.ERROR,
                        icon_size=20,
                        tooltip="Xóa",
                        on_click=lambda e, pid=product_id: self._confirm_delete(pid),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_SM),
                            overlay_color=Colors.with_opacity(0.1, AppTheme.ERROR),
                        ),
                    ),
                ], spacing=4)),
            ]
        )
    
    def _on_search(self, e):
        """Handle search input"""
        self.refresh_list(e.control.value)
    
    def _open_product_dialog(self, product_id: int = None):
        """Mở dialog thêm/sửa sản phẩm"""
        product = None
        if product_id:
            p = ProductRepository.get_by_id(product_id)
            if p:
                product = {
                    'id': p.id,
                    'name': p.name,
                    'large_unit': p.large_unit,
                    'conversion': p.conversion,
                    'unit_price': p.unit_price,
                }
        
        def on_save(data):
            if data['id']:
                ProductRepository.update(
                    data['id'], data['name'], data['large_unit'],
                    data['conversion'], data['unit_price']
                )
                self._show_snackbar("Đã cập nhật sản phẩm!", "success")
            else:
                ProductRepository.add(
                    data['name'], data['large_unit'],
                    data['conversion'], data['unit_price']
                )
                self._show_snackbar("Đã thêm sản phẩm mới!", "success")
            
            dialog.open = False
            self._page.update()
            self.refresh_list()
            if self.on_refresh_calc:
                self.on_refresh_calc()
        
        def on_cancel():
            dialog.open = False
            self._page.update()
        
        dialog = ProductDialog(
            on_save=on_save,
            on_cancel=on_cancel,
            product=product,
            is_edit=product is not None,
        )
        
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()
    
    def _confirm_delete(self, product_id: int):
        """Xác nhận xóa sản phẩm"""
        product = ProductRepository.get_by_id(product_id)
        if not product:
            return
        
        def do_delete():
            ProductRepository.delete(product_id)
            dialog.open = False
            self._page.update()
            self.refresh_list()
            if self.on_refresh_calc:
                self.on_refresh_calc()
            self._show_snackbar("Đã xóa sản phẩm!", "warning")
        
        def cancel():
            dialog.open = False
            self._page.update()
        
        dialog = ConfirmDialog(
            title="Xác nhận xóa",
            content=f"Bạn có chắc muốn xóa sản phẩm \"{product.name}\"?",
            on_confirm=do_delete,
            on_cancel=cancel,
            confirm_text="Xóa",
            is_danger=True,
        )
        
        self._page.overlay.append(dialog)
        dialog.open = True
        self._page.update()
    
    def _show_snackbar(self, message: str, type: str = "info"):
        """Hiển thị snackbar notification"""
        colors_map = {
            "success": AppTheme.SUCCESS,
            "warning": AppTheme.WARNING,
            "error": AppTheme.ERROR,
            "info": AppTheme.INFO,
        }
        self._page.snack_bar = ft.SnackBar(
            content=ft.Row([
                ft.Icon(
                    Icons.CHECK_CIRCLE_ROUNDED if type == "success" else 
                    Icons.WARNING_ROUNDED if type == "warning" else
                    Icons.ERROR_ROUNDED if type == "error" else Icons.INFO_ROUNDED,
                    color=Colors.WHITE,
                    size=20,
                ),
                ft.Text(message, color=Colors.WHITE, weight=ft.FontWeight.W_500),
            ], spacing=10),
            bgcolor=colors_map.get(type, AppTheme.INFO),
            duration=3000,
            behavior=ft.SnackBarBehavior.FLOATING,
            margin=20,
            padding=16,
        )
        self._page.snack_bar.open = True
        self._page.update()
