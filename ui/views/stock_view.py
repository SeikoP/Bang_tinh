"""
Stock View - Màn hình quản lý kho hàng (Số lượng chốt ca)
Thiết kế hiện đại với DataTable dạng Excel
"""
import flet as ft
from flet import Icons, Colors

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import AppTheme
from database import SessionRepository
from services import CalculatorService


class StockView(ft.Container):
    """View quản lý kho hàng - Điều chỉnh số lượng chốt ca dạng bảng Excel"""
    
    def __init__(self, page: ft.Page, on_refresh_calc: callable = None, is_dark: bool = False):
        self._page = page
        self.on_refresh_calc = on_refresh_calc
        self.is_dark = is_dark
        self.calc_service = CalculatorService()
        
        # Bảng kho hàng dạng DataTable
        self.stock_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("STT", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Tên sản phẩm", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Đơn vị", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Quy đổi", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("SL Lớn", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("SL Lẻ", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Tổng", weight=ft.FontWeight.W_600, size=13)),
                ft.DataColumn(ft.Text("Hiển thị", weight=ft.FontWeight.W_600, size=13)),
            ],
            rows=[],
            **AppTheme.data_table_style(self.is_dark),
        )
        
        super().__init__(
            content=ft.Column([
                self._build_header(),
                ft.Container(height=16),
                ft.Container(
                    content=ft.Column([self.stock_table], scroll=ft.ScrollMode.AUTO),
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
                        content=ft.Icon(Icons.INVENTORY_ROUNDED, color=Colors.WHITE, size=22),
                        width=42,
                        height=42,
                        bgcolor=AppTheme.SECONDARY,
                        border_radius=AppTheme.RADIUS_MD,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(
                            "Chốt ca Kho hàng",
                            size=22,
                            weight=ft.FontWeight.W_700,
                            color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                        ),
                        ft.Text(
                            "Điều chỉnh số lượng chốt ca (còn lại cuối ca)",
                            size=13,
                            color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                    ], spacing=2),
                ], spacing=14),
                ft.Row([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(Icons.INFO_OUTLINE_ROUNDED, color=AppTheme.INFO, size=16),
                            ft.Text(
                                "Nhấn +/- để điều chỉnh số lượng chốt ca",
                                size=12,
                                color=AppTheme.INFO,
                            ),
                        ], spacing=6),
                        bgcolor=Colors.with_opacity(0.1, AppTheme.INFO),
                        padding=ft.Padding(12, 8, 12, 8),
                        border_radius=AppTheme.RADIUS_MD,
                    ),
                    ft.Button(
                        "Làm mới",
                        icon=Icons.REFRESH_ROUNDED,
                        on_click=lambda e: self.refresh_list(),
                        style=AppTheme.secondary_button_style(self.is_dark),
                    ),
                ], spacing=12),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(0, 16, 0, 0),
        )
    
    def refresh_list(self, update: bool = True):
        """Refresh danh sách kho hàng"""
        sessions = SessionRepository.get_all()
        self.stock_table.rows.clear()
        
        for idx, s in enumerate(sessions, 1):
            product = s.product
            
            # Tính toán số lượng lớn và lẻ từ CHỐT CA (closing_qty)
            large_qty = s.closing_qty // product.conversion
            small_qty = s.closing_qty % product.conversion
            
            # Format hiển thị
            display_qty = self.calc_service.format_to_display(
                s.closing_qty, product.conversion, product.unit_char
            )
            
            # Tạo row
            self.stock_table.rows.append(
                self._build_table_row(idx, s, product, large_qty, small_qty, display_qty)
            )
        
        if update:
            self._page.update()
    
    def _build_table_row(self, idx, session_data, product, large_qty, small_qty, display_qty):
        """Build một row cho bảng"""
        
        def adjust_large_qty(delta: int):
            """Điều chỉnh số lượng đơn vị lớn của CHỐT CA"""
            change = delta * product.conversion
            new_closing = session_data.closing_qty + change
            if new_closing < 0:
                new_closing = 0
            # Không cho chốt ca lớn hơn giao ca
            if new_closing > session_data.handover_qty:
                new_closing = session_data.handover_qty
            SessionRepository.update_qty(product.id, session_data.handover_qty, new_closing)
            self.refresh_list()
            if self.on_refresh_calc:
                self.on_refresh_calc()
        
        def adjust_small_qty(delta: int):
            """Điều chỉnh số lượng đơn vị lẻ của CHỐT CA"""
            new_closing = session_data.closing_qty + delta
            if new_closing < 0:
                new_closing = 0
            # Không cho chốt ca lớn hơn giao ca
            if new_closing > session_data.handover_qty:
                new_closing = session_data.handover_qty
            SessionRepository.update_qty(product.id, session_data.handover_qty, new_closing)
            self.refresh_list()
            if self.on_refresh_calc:
                self.on_refresh_calc()
        
        def on_large_input_change(e):
            """Xử lý khi người dùng nhập trực tiếp số lượng lớn"""
            try:
                new_large = int(e.control.value) if e.control.value else 0
                if new_large < 0:
                    new_large = 0
                new_closing = new_large * product.conversion + small_qty
                # Không cho chốt ca lớn hơn giao ca
                if new_closing > session_data.handover_qty:
                    new_closing = session_data.handover_qty
                SessionRepository.update_qty(product.id, session_data.handover_qty, new_closing)
                self.refresh_list()
                if self.on_refresh_calc:
                    self.on_refresh_calc()
            except ValueError:
                pass
        
        def on_small_input_change(e):
            """Xử lý khi người dùng nhập trực tiếp số lượng lẻ"""
            try:
                new_small = int(e.control.value) if e.control.value else 0
                if new_small < 0:
                    new_small = 0
                new_closing = large_qty * product.conversion + new_small
                # Không cho chốt ca lớn hơn giao ca
                if new_closing > session_data.handover_qty:
                    new_closing = session_data.handover_qty
                SessionRepository.update_qty(product.id, session_data.handover_qty, new_closing)
                self.refresh_list()
                if self.on_refresh_calc:
                    self.on_refresh_calc()
            except ValueError:
                pass
        
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
                    content=ft.Text(product.large_unit, color=Colors.WHITE, size=12, weight=ft.FontWeight.W_500),
                    bgcolor=AppTheme.PRIMARY,
                    padding=ft.Padding(10, 5, 10, 5),
                    border_radius=AppTheme.RADIUS_SM,
                )),
                
                # Quy đổi
                ft.DataCell(ft.Text(
                    f"1 = {product.conversion}",
                    size=12,
                    color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                )),
                
                # SL Lớn (với nút +/- và input)
                ft.DataCell(ft.Row([
                    ft.IconButton(
                        Icons.REMOVE_CIRCLE_ROUNDED,
                        icon_color=AppTheme.ERROR,
                        icon_size=20,
                        on_click=lambda e: adjust_large_qty(-1),
                        tooltip="Giảm 1 đơn vị lớn",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_SM),
                        ),
                    ),
                    ft.Container(
                        content=ft.TextField(
                            value=str(large_qty),
                            width=50,
                            height=36,
                            dense=True,
                            text_size=14,
                            text_align=ft.TextAlign.CENTER,
                            border_radius=AppTheme.RADIUS_SM,
                            border_color=AppTheme.BORDER_DARK if self.is_dark else AppTheme.BORDER_LIGHT,
                            on_submit=on_large_input_change,
                            on_blur=on_large_input_change,
                        ),
                    ),
                    ft.IconButton(
                        Icons.ADD_CIRCLE_ROUNDED,
                        icon_color=AppTheme.SUCCESS,
                        icon_size=20,
                        on_click=lambda e: adjust_large_qty(1),
                        tooltip="Tăng 1 đơn vị lớn",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_SM),
                        ),
                    ),
                ], spacing=2)),
                
                # SL Lẻ (với nút +/- và input)
                ft.DataCell(ft.Row([
                    ft.IconButton(
                        Icons.REMOVE_ROUNDED,
                        icon_color=AppTheme.ERROR,
                        icon_size=18,
                        on_click=lambda e: adjust_small_qty(-1),
                        tooltip="Giảm 1 đơn vị lẻ",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_SM),
                        ),
                    ),
                    ft.Container(
                        content=ft.TextField(
                            value=str(small_qty),
                            width=45,
                            height=36,
                            dense=True,
                            text_size=14,
                            text_align=ft.TextAlign.CENTER,
                            border_radius=AppTheme.RADIUS_SM,
                            border_color=AppTheme.BORDER_DARK if self.is_dark else AppTheme.BORDER_LIGHT,
                            on_submit=on_small_input_change,
                            on_blur=on_small_input_change,
                        ),
                    ),
                    ft.IconButton(
                        Icons.ADD_ROUNDED,
                        icon_color=AppTheme.SUCCESS,
                        icon_size=18,
                        on_click=lambda e: adjust_small_qty(1),
                        tooltip="Tăng 1 đơn vị lẻ",
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_SM),
                        ),
                    ),
                ], spacing=2)),
                
                # Tổng (đơn vị lẻ) - Badge style
                ft.DataCell(ft.Container(
                    content=ft.Text(
                        str(session_data.closing_qty),
                        weight=ft.FontWeight.W_600,
                        size=13,
                        color=Colors.WHITE,
                    ),
                    bgcolor=AppTheme.SECONDARY,
                    padding=ft.Padding(12, 6, 12, 6),
                    border_radius=AppTheme.RADIUS_SM,
                )),
                
                # Hiển thị (format XX.YY)
                ft.DataCell(ft.Text(
                    display_qty,
                    size=16,
                    weight=ft.FontWeight.W_700,
                    color=AppTheme.PRIMARY,
                )),
            ]
        )
