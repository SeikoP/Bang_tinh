"""
Settings View - Màn hình cài đặt
Thiết kế hiện đại và đồng nhất
"""
import flet as ft
from flet import Icons, Colors
import os
import shutil
from datetime import datetime

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config import DB_PATH, BACKUP_DIR, APP_NAME, APP_VERSION
from ui.theme import AppTheme
from ui.components.dialogs import ConfirmDialog


class SettingsView(ft.Container):
    """View cài đặt ứng dụng - Premium Design"""
    
    def __init__(self, page: ft.Page, file_picker: ft.FilePicker = None, on_theme_change: callable = None, is_dark: bool = False):
        self._page = page
        self.on_theme_change = on_theme_change
        self.is_dark = is_dark
        
        # Use provided FilePicker (already in overlay)
        self.fp = file_picker
        
        super().__init__(
            content=ft.Column([
                self._build_header(),
                ft.Container(height=16),
                ft.Container(
                    content=ft.Column([
                        self._build_theme_section(),
                        ft.Container(height=16),
                        self._build_backup_section(),
                        ft.Container(height=16),
                        self._build_about_section(),
                    ], spacing=0, scroll=ft.ScrollMode.AUTO),
                    expand=True,
                ),
            ]),
            padding=0,
            expand=True,
        )
    
    def _build_header(self) -> ft.Container:
        """Build header section - Premium style"""
        return ft.Container(
            content=ft.Row([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(Icons.SETTINGS_ROUNDED, color=Colors.WHITE, size=22),
                        width=42,
                        height=42,
                        bgcolor=AppTheme.TEXT_SECONDARY_LIGHT,
                        border_radius=AppTheme.RADIUS_MD,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(
                            "Cài đặt",
                            size=22,
                            weight=ft.FontWeight.W_700,
                            color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                        ),
                        ft.Text(
                            "Tùy chỉnh ứng dụng theo ý muốn",
                            size=13,
                            color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                    ], spacing=2),
                ], spacing=14),
            ]),
            padding=ft.Padding(0, 16, 0, 0),
        )
    
    def _build_section_card(self, icon, icon_color, title, description, content) -> ft.Container:
        """Build một section card chung"""
        return ft.Container(
            content=ft.Column([
                # Section header
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, color=Colors.WHITE, size=18),
                        width=36,
                        height=36,
                        bgcolor=icon_color,
                        border_radius=AppTheme.RADIUS_SM,
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Column([
                        ft.Text(title, size=16, weight=ft.FontWeight.W_600,
                                color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT),
                        ft.Text(description, size=12,
                                color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT),
                    ], spacing=2),
                ], spacing=12),
                ft.Container(height=16),
                ft.Divider(),
                ft.Container(height=12),
                content,
            ]),
            **AppTheme.card_style(self.is_dark),
        )
    
    def _build_theme_section(self) -> ft.Container:
        """Build theme settings section"""
        theme_switch = ft.Switch(
            value=self.is_dark,
            active_color=AppTheme.PRIMARY,
            on_change=self._toggle_theme,
        )
        
        content = ft.Row([
            ft.Row([
                ft.Icon(
                    Icons.DARK_MODE_ROUNDED if self.is_dark else Icons.LIGHT_MODE_ROUNDED,
                    color=AppTheme.PRIMARY,
                    size=24,
                ),
                ft.Column([
                    ft.Text("Chế độ tối", size=14, weight=ft.FontWeight.W_500,
                            color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT),
                    ft.Text(
                        "Đang bật" if self.is_dark else "Đang tắt",
                        size=12,
                        color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                    ),
                ], spacing=2),
            ], spacing=12),
            theme_switch,
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
        
        return self._build_section_card(
            Icons.PALETTE_ROUNDED,
            AppTheme.PRIMARY,
            "Giao diện",
            "Tùy chỉnh màu sắc và chế độ hiển thị",
            content
        )
    
    def _build_backup_section(self) -> ft.Container:
        """Build backup settings section"""
        content = ft.Column([
            # Backup row
            ft.Row([
                ft.Row([
                    ft.Icon(Icons.BACKUP_ROUNDED, color=AppTheme.SUCCESS, size=24),
                    ft.Column([
                        ft.Text("Sao lưu dữ liệu", size=14, weight=ft.FontWeight.W_500,
                                color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT),
                        ft.Text(
                            "Tạo bản sao lưu database",
                            size=12,
                            color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                    ], spacing=2),
                ], spacing=12),
                ft.Button(
                    "Sao lưu",
                    icon=Icons.SAVE_ALT_ROUNDED,
                    on_click=lambda e: self._backup_database(),
                    style=AppTheme.success_button_style(),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            
            ft.Container(height=12),
            ft.Divider(),
            ft.Container(height=12),
            
            # Restore row
            ft.Row([
                ft.Row([
                    ft.Icon(Icons.RESTORE_ROUNDED, color=AppTheme.WARNING, size=24),
                    ft.Column([
                        ft.Text("Khôi phục dữ liệu", size=14, weight=ft.FontWeight.W_500,
                                color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT),
                        ft.Text(
                            "Khôi phục từ file backup",
                            size=12,
                            color=AppTheme.TEXT_SECONDARY_DARK if self.is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                    ], spacing=2),
                ], spacing=12),
                ft.Button(
                    "Chọn file",
                    icon=Icons.FOLDER_OPEN_ROUNDED,
                    on_click=lambda e: self._show_restore_picker(),
                    style=AppTheme.secondary_button_style(self.is_dark),
                ),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ])
        
        return self._build_section_card(
            Icons.STORAGE_ROUNDED,
            AppTheme.SUCCESS,
            "Sao lưu & Khôi phục",
            "Bảo vệ dữ liệu của bạn",
            content
        )
    
    def _build_about_section(self) -> ft.Container:
        """Build about section"""
        content = ft.Column([
            # App name
            ft.Row([
                ft.Container(
                    content=ft.Icon(Icons.STORE_ROUNDED, color=Colors.WHITE, size=28),
                    width=48,
                    height=48,
                    bgcolor=AppTheme.PRIMARY,
                    border_radius=AppTheme.RADIUS_MD,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(APP_NAME, size=18, weight=ft.FontWeight.W_700,
                            color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT),
                    ft.Container(
                        content=ft.Text(f"v{APP_VERSION}", size=11, color=Colors.WHITE, weight=ft.FontWeight.W_500),
                        bgcolor=AppTheme.PRIMARY,
                        padding=ft.Padding(8, 3, 8, 3),
                        border_radius=AppTheme.RADIUS_SM,
                    ),
                ], spacing=6),
            ], spacing=14),
            
            ft.Container(height=12),
            
            # Info rows
            ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Phiên bản:", size=13, color=AppTheme.TEXT_SECONDARY_LIGHT),
                        ft.Text(APP_VERSION, size=13, weight=ft.FontWeight.W_500,
                                color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Divider(),
                    ft.Row([
                        ft.Text("Database:", size=13, color=AppTheme.TEXT_SECONDARY_LIGHT),
                        ft.Text(str(DB_PATH), size=11, 
                                color=AppTheme.TEXT_DARK if self.is_dark else AppTheme.TEXT_LIGHT,
                                overflow=ft.TextOverflow.ELLIPSIS,
                                width=300),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ], spacing=10),
                bgcolor=Colors.with_opacity(0.03, AppTheme.PRIMARY) if not self.is_dark else Colors.with_opacity(0.05, Colors.WHITE),
                padding=14,
                border_radius=AppTheme.RADIUS_MD,
                border=ft.Border.all(1, AppTheme.BORDER_DARK if self.is_dark else AppTheme.BORDER_LIGHT),
            ),
        ])
        
        return self._build_section_card(
            Icons.INFO_ROUNDED,
            AppTheme.INFO,
            "Thông tin",
            "Chi tiết về ứng dụng",
            content
        )
    
    def _toggle_theme(self, e):
        """Toggle dark/light theme"""
        if self.on_theme_change:
            self.on_theme_change(e.control.value)
    
    def _backup_database(self):
        """Backup database"""
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = BACKUP_DIR / f"backup_{timestamp}.db"
            shutil.copy2(DB_PATH, backup_file)
            self._show_snackbar(f"Đã sao lưu: {backup_file}", "success")
        except Exception as e:
            self._show_snackbar(f"Lỗi sao lưu: {str(e)}", "error")
    
    def _show_restore_picker(self):
        """Sử dụng shared FilePicker để chọn file phục hồi"""
        if not self.fp:
            return
            
        def on_result(e: ft.FilePickerResultEvent):
            if e.files:
                self._restore_database(e.files[0].path)
        
        self.fp.on_result = on_result
        self.fp.pick_files(
            allowed_extensions=["db"],
            dialog_title="Chọn file backup",
            allow_multiple=False,
        )
    
    def _restore_database(self, backup_path: str):
        """Khôi phục database từ backup"""
        def do_restore():
            try:
                shutil.copy2(backup_path, DB_PATH)
                dialog.open = False
                self._page.update()
                # Remove dialog from overlay to prevent accumulation
                if dialog in self._page.overlay:
                    self._page.overlay.remove(dialog)
                self._show_snackbar("Đã khôi phục dữ liệu! Vui lòng khởi động lại ứng dụng.", "success")
            except Exception as e:
                self._show_snackbar(f"Lỗi khôi phục: {str(e)}", "error")
        
        def cancel():
            dialog.open = False
            self._page.update()
            # Remove dialog from overlay to prevent accumulation
            if dialog in self._page.overlay:
                self._page.overlay.remove(dialog)
        
        dialog = ConfirmDialog(
            title="Xác nhận khôi phục",
            content="Dữ liệu hiện tại sẽ bị ghi đè. Bạn có chắc chắn?",
            on_confirm=do_restore,
            on_cancel=cancel,
            confirm_text="Khôi phục",
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
