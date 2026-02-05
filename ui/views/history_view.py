"""
History View - Màn hình lịch sử phiên làm việc
Thiết kế hiện đại và đồng nhất
"""
import flet as ft
from flet import Icons, Colors
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from ui.theme import AppTheme
from ui.components.dialogs import ConfirmDialog
from database import HistoryRepository
from services import ExportService
from utils import format_date, format_datetime, format_currency


class HistoryView(ft.Container):
    """View lịch sử phiên làm việc - Premium Design"""
    
    def __init__(self, page: ft.Page, is_dark: bool = False):
        self._page = page
        self.is_dark = is_dark
        self.export_service = ExportService()
        
        # History list
        self.history_list = ft.ListView(
            expand=True,
            spacing=10,
            padding=ft.Padding(0, 10, 0, 10),
        )
        
        # Detail panel
        self.detail_panel = ft.Container(
            visible=False,
            padding=20,
            bgcolor=AppTheme.CARD_DARK if is_dark else AppTheme.CARD_LIGHT,
            border_radius=AppTheme.RADIUS_LG,
            border=ft.Border.all(1, AppTheme.BORDER_DARK if is_dark else AppTheme.BORDER_LIGHT),
        )
        
        super().__init__(
            content=ft.Column([
                self._build_header(),
                ft.Container(height=16),
                ft.Row([
                    ft.Container(
                        content=self.history_list,
                        expand=2,
                        **AppTheme.card_style(self.is_dark),
                    ),
                    ft.Container(width=16),
                    ft.Container(
                        content=self.detail_panel,
                        expand=3,
                    ),
                ], expand=True),
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
                        content=ft.Icon(Icons.HISTORY_ROUNDED, color=Colors.WHITE, size=22),
                        width=42,
                        height=42,
                        bgcolor=AppTheme.INFO,
                        border_radius=AppTheme.RADIUS_MD,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(
                            "Lịch sử Phiên",
                            size=22,
                            weight=ft.FontWeight.W_700,
                            color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                        ),
                        ft.Text(
                            "Xem và quản lý các phiên làm việc đã lưu",
                            size=13,
                            color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                    ], spacing=2),
                ], spacing=14),
                ft.Button(
                    "Làm mới",
                    icon=Icons.REFRESH_ROUNDED,
                    on_click=lambda e: self.refresh_list(),
                    style=AppTheme.secondary_button_style(self.is_dark),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(0, 16, 0, 0),
        )
    
    def refresh_list(self, update: bool = True):
        """Refresh danh sách lịch sử"""
        histories = HistoryRepository.get_all(limit=50)
        self.history_list.controls.clear()
        
        if not histories:
            self.history_list.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Icon(Icons.HISTORY_ROUNDED, size=56, color=Colors.with_opacity(0.3, AppTheme.TEXT_SECONDARY_LIGHT)),
                        ft.Text(
                            "Chưa có lịch sử phiên nào",
                            size=15,
                            color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                        ft.Text(
                            "Các phiên làm việc đã lưu sẽ xuất hiện ở đây",
                            size=12,
                            color=Colors.with_opacity(0.5, AppTheme.TEXT_SECONDARY_LIGHT),
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    padding=40,
                )
            )
        else:
            for h in histories:
                self.history_list.controls.append(
                    self._build_history_card(h)
                )
        
        self.detail_panel.visible = False
        if update:
            self._page.update()
    
    def _build_history_card(self, history) -> ft.Container:
        """Build card cho một phiên lịch sử"""
        return ft.Container(
            content=ft.Row([
                ft.Column([
                    ft.Text(
                        format_date(history.session_date),
                        size=15,
                        weight=ft.FontWeight.W_600,
                        color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                    ),
                    ft.Container(
                        content=ft.Text(
                            history.shift_name or "Không có ca",
                            size=11,
                            color=AppTheme.INFO,
                        ),
                        bgcolor=Colors.with_opacity(0.1, AppTheme.INFO),
                        padding=ft.Padding(8, 4, 8, 4),
                        border_radius=AppTheme.RADIUS_SM,
                    ),
                ], expand=True, spacing=6),
                ft.Column([
                    ft.Text(
                        format_currency(history.total_amount),
                        size=15,
                        weight=ft.FontWeight.W_700,
                        color=AppTheme.SUCCESS,
                    ),
                ]),
                ft.Icon(
                    Icons.CHEVRON_RIGHT_ROUNDED,
                    color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                    size=20,
                ),
            ]),
            padding=14,
            border_radius=AppTheme.RADIUS_MD,
            bgcolor=Colors.with_opacity(0.02, AppTheme.PRIMARY) if not self.is_dark else Colors.with_opacity(0.05, Colors.WHITE),
            border=ft.Border.all(1, AppTheme.BORDER_DARK if self.is_dark else AppTheme.BORDER_LIGHT),
            on_click=lambda e, h=history: self._show_detail(h.id),
            on_hover=lambda e: self._on_card_hover(e),
        )
    
    def _on_card_hover(self, e):
        """Handle hover effect"""
        if e.data == "true":
            e.control.bgcolor = Colors.with_opacity(0.08, AppTheme.PRIMARY)
        else:
            e.control.bgcolor = Colors.with_opacity(0.02, AppTheme.PRIMARY) if not self.is_dark else Colors.with_opacity(0.05, Colors.WHITE)
        e.control.update()
    
    def _show_detail(self, history_id: int):
        """Hiển thị chi tiết một phiên"""
        history = HistoryRepository.get_by_id(history_id)
        if not history:
            return
        
        # Build detail table
        rows = []
        for item in history.items:
            rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(item.product_name, size=13, weight=ft.FontWeight.W_500)),
                    ft.DataCell(ft.Text(str(item.handover_qty), size=13)),
                    ft.DataCell(ft.Text(str(item.closing_qty), size=13)),
                    ft.DataCell(ft.Container(
                        content=ft.Text(str(item.used_qty), weight=ft.FontWeight.W_600, color=Colors.WHITE, size=12),
                        bgcolor=AppTheme.SECONDARY,
                        padding=ft.Padding(8, 4, 8, 4),
                        border_radius=AppTheme.RADIUS_SM,
                    )),
                    ft.DataCell(ft.Text(format_currency(item.amount), size=13, color=AppTheme.SUCCESS)),
                ])
            )
        
        detail_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Sản phẩm", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Giao", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Chốt", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Dùng", weight=ft.FontWeight.W_600, size=12)),
                ft.DataColumn(ft.Text("Tiền", weight=ft.FontWeight.W_600, size=12)),
            ],
            rows=rows,
            **AppTheme.data_table_style(self.is_dark),
        )
        
        self.detail_panel.content = ft.Column([
            # Header
            ft.Row([
                ft.Text(
                    f"Chi tiết phiên #{history.id}",
                    size=18,
                    weight=ft.FontWeight.W_700,
                    color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                ),
                ft.Row([
                    ft.IconButton(
                        icon=Icons.FILE_DOWNLOAD_ROUNDED,
                        icon_color=AppTheme.PRIMARY,
                        tooltip="Xuất file",
                        on_click=lambda e: self._export_history(history.id),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_SM),
                            overlay_color=Colors.with_opacity(0.1, AppTheme.PRIMARY),
                        ),
                    ),
                    ft.IconButton(
                        icon=Icons.DELETE_ROUNDED,
                        icon_color=AppTheme.ERROR,
                        tooltip="Xóa",
                        on_click=lambda e: self._confirm_delete(history.id),
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_SM),
                            overlay_color=Colors.with_opacity(0.1, AppTheme.ERROR),
                        ),
                    ),
                ], spacing=4),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            # Info badges
            ft.Row([
                ft.Container(
                    content=ft.Row([
                        ft.Icon(Icons.CALENDAR_TODAY_ROUNDED, size=14, color=AppTheme.INFO),
                        ft.Text(format_date(history.session_date), size=12, color=AppTheme.INFO),
                    ], spacing=4),
                    bgcolor=Colors.with_opacity(0.1, AppTheme.INFO),
                    padding=ft.Padding(10, 6, 10, 6),
                    border_radius=AppTheme.RADIUS_SM,
                ),
                ft.Container(
                    content=ft.Row([
                        ft.Icon(Icons.ACCESS_TIME_ROUNDED, size=14, color=AppTheme.SECONDARY),
                        ft.Text(history.shift_name or "N/A", size=12, color=AppTheme.SECONDARY),
                    ], spacing=4),
                    bgcolor=Colors.with_opacity(0.1, AppTheme.SECONDARY),
                    padding=ft.Padding(10, 6, 10, 6),
                    border_radius=AppTheme.RADIUS_SM,
                ),
            ], spacing=8),
            
            ft.Container(height=8),
            ft.Divider(),
            
            # Table
            ft.Container(
                content=ft.Column([detail_table], scroll=ft.ScrollMode.AUTO),
                expand=True,
            ),
            
            ft.Divider(),
            
            # Total
            ft.Container(
                content=ft.Row([
                    ft.Row([
                        ft.Icon(Icons.MONETIZATION_ON_ROUNDED, color=AppTheme.SUCCESS, size=22),
                        ft.Text("Tổng cộng:", size=16, weight=ft.FontWeight.W_500),
                    ], spacing=8),
                    ft.Text(
                        format_currency(history.total_amount),
                        size=20,
                        weight=ft.FontWeight.W_700,
                        color=AppTheme.SUCCESS,
                    ),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                bgcolor=Colors.with_opacity(0.1, AppTheme.SUCCESS),
                padding=ft.Padding(16, 12, 16, 12),
                border_radius=AppTheme.RADIUS_MD,
            ),
            
            # Notes
            ft.Container(
                content=ft.Row([
                    ft.Icon(Icons.NOTE_ROUNDED, size=16, color=AppTheme.TEXT_SECONDARY_LIGHT),
                    ft.Text(
                        f"Ghi chú: {history.notes}" if history.notes else "Không có ghi chú",
                        size=13,
                        italic=True,
                        color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                    ),
                ], spacing=8),
                visible=True,
                padding=ft.Padding(0, 8, 0, 0),
            ),
        ], spacing=10)
        
        self.detail_panel.visible = True
        self._page.update()
    
    def _export_history(self, history_id: int):
        """Xuất lịch sử ra file"""
        filepath = self.export_service.export_history_to_text(history_id)
        if filepath:
            self._show_snackbar(f"Đã xuất file: {filepath}", "success")
        else:
            self._show_snackbar("Không thể xuất file!", "error")
    
    def _confirm_delete(self, history_id: int):
        """Xác nhận xóa lịch sử"""
        def do_delete():
            HistoryRepository.delete(history_id)
            dialog.open = False
            self._page.update()
            self.refresh_list()
            self._show_snackbar("Đã xóa phiên lịch sử!", "warning")
        
        def cancel():
            dialog.open = False
            self._page.update()
        
        dialog = ConfirmDialog(
            title="Xác nhận xóa",
            content="Bạn có chắc muốn xóa phiên lịch sử này?",
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
