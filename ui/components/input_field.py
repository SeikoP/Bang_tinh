"""
Input Field Components
"""
import flet as ft
from flet import Colors

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ui.theme import AppTheme


class StyledTextField(ft.TextField):
    """TextField với style mặc định của app"""
    
    def __init__(
        self,
        label: str = "",
        value: str = "",
        hint_text: str = "",
        is_dark: bool = False,
        width: int = None,
        **kwargs
    ):
        super().__init__(
            label=label,
            value=value,
            hint_text=hint_text,
            border_color=AppTheme.PRIMARY,
            focused_border_color=AppTheme.PRIMARY_LIGHT,
            cursor_color=AppTheme.PRIMARY,
            bgcolor=AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT,
            border_radius=8,
            width=width,
            **kwargs
        )


class QuantityInput(ft.Container):
    """Input cho số lượng với format đặc biệt (ví dụ: 3t4)"""
    
    def __init__(
        self,
        value: str = "0",
        display_text: str = "",
        width: int = 100,
        on_change: callable = None,
        is_dark: bool = False,
    ):
        self.on_change = on_change
        self.is_dark = is_dark
        
        self.input_field = ft.TextField(
            value=value,
            width=width,
            dense=True,
            text_size=14,
            border_color=AppTheme.PRIMARY,
            focused_border_color=AppTheme.PRIMARY_LIGHT,
            cursor_color=AppTheme.PRIMARY,
            border_radius=6,
            on_submit=self._handle_change,
            on_blur=self._handle_change,
            text_align=ft.TextAlign.CENTER,
        )
        
        self.display_label = ft.Text(
            display_text,
            size=11,
            weight=ft.FontWeight.BOLD,
            color=AppTheme.PRIMARY,
            text_align=ft.TextAlign.CENTER,
        )
        
        super().__init__(
            content=ft.Column([
                self.input_field,
                self.display_label,
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=2, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        )
    
    def _handle_change(self, e):
        if self.on_change:
            self.on_change(e)
    
    @property
    def value(self) -> str:
        return self.input_field.value
    
    @value.setter
    def value(self, val: str):
        self.input_field.value = val
    
    @property
    def error_text(self) -> str:
        return self.input_field.error_text
    
    @error_text.setter
    def error_text(self, val: str):
        self.input_field.error_text = val
    
    def set_display(self, text: str):
        self.display_label.value = text
        self.display_label.update()
