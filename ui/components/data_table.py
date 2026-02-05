"""
Data Table Component
"""
import flet as ft
from flet import Colors

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ui.theme import AppTheme


class StyledDataTable(ft.DataTable):
    """DataTable với style mặc định của app"""
    
    def __init__(
        self,
        columns: list,
        rows: list = None,
        is_dark: bool = False,
        **kwargs
    ):
        super().__init__(
            columns=columns,
            rows=rows or [],
            heading_row_color=Colors.with_opacity(0.1, AppTheme.PRIMARY),
            border=ft.Border.all(1, Colors.BLACK12 if not is_dark else Colors.WHITE12),
            border_radius=10,
            vertical_lines=ft.BorderSide(1, Colors.BLACK12 if not is_dark else Colors.WHITE12),
            horizontal_lines=ft.BorderSide(1, Colors.BLACK12 if not is_dark else Colors.WHITE12),
            heading_text_style=ft.TextStyle(
                weight=ft.FontWeight.BOLD,
                color=AppTheme.TEXT_DARK if is_dark else AppTheme.TEXT_LIGHT,
            ),
            data_text_style=ft.TextStyle(
                color=AppTheme.TEXT_DARK if is_dark else AppTheme.TEXT_LIGHT,
            ),
            **kwargs
        )


class SessionDataRow(ft.DataRow):
    """DataRow cho session data với input fields"""
    
    def __init__(
        self,
        product_id: int,
        unit: str,
        name: str,
        handover_widget,
        closing_widget,
        conversion_text: str,
        used_qty: int,
        unit_price: float,
        amount: float,
        is_dark: bool = False,
    ):
        used_color = AppTheme.SECONDARY if used_qty > 0 else Colors.BLUE_GREY_200
        
        super().__init__(
            cells=[
                ft.DataCell(ft.Text(unit, size=13)),
                ft.DataCell(ft.Text(
                    name, 
                    weight=ft.FontWeight.W_500,
                    color=AppTheme.TEXT_DARK if is_dark else AppTheme.TEXT_LIGHT,
                )),
                ft.DataCell(handover_widget),
                ft.DataCell(closing_widget),
                ft.DataCell(ft.Text(conversion_text, size=12, italic=True)),
                ft.DataCell(ft.Container(
                    content=ft.Text(
                        str(used_qty),
                        weight=ft.FontWeight.BOLD,
                        color=Colors.WHITE,
                        size=14,
                    ),
                    bgcolor=used_color,
                    padding=ft.padding.symmetric(horizontal=12, vertical=5),
                    border_radius=8,
                )),
                ft.DataCell(ft.Text(f"{unit_price:,.0f}", size=13)),
                ft.DataCell(ft.Text(
                    f"{amount:,.0f}",
                    weight=ft.FontWeight.BOLD,
                    color=AppTheme.PRIMARY,
                    size=14,
                )),
            ],
        )
