"""
Main Application - Phần mềm Quản lý Xuất kho & Dịch vụ v2.0
Thiết kế hiện đại với Navigation Bar
"""
import flet as ft
from flet import Icons, Colors, ThemeMode

# Initialize database first
from database.connection import init_db
init_db()

from config import APP_NAME, APP_VERSION, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT
from ui.theme import AppTheme
from ui.views.calculation_view import CalculationView
from ui.views.product_view import ProductView
from ui.views.stock_view import StockView
from ui.views.history_view import HistoryView
from ui.views.settings_view import SettingsView


def main(page: ft.Page):
    """Main function"""
    
    # === Page Configuration ===
    page.title = f"{APP_NAME} v{APP_VERSION}"
    page.theme_mode = ThemeMode.LIGHT
    page.bgcolor = AppTheme.BG_LIGHT
    page.padding = 0
    page.window.width = WINDOW_WIDTH
    page.window.height = WINDOW_HEIGHT
    page.window.min_width = WINDOW_MIN_WIDTH
    page.window.min_height = WINDOW_MIN_HEIGHT
    
    # Completely disable error display
    # page.on_error = lambda e: None
    
    # Custom theme with typography
    page.theme = ft.Theme(
        color_scheme_seed=AppTheme.PRIMARY,
        font_family="Segoe UI",
    )
    
    # State
    is_dark = False
    current_index = 0
    
    # === Views Storage ===
    views = {}
    content_area = ft.Container(expand=True, padding=ft.Padding(24, 16, 24, 24))

    # === Event Handlers (Delegate) ===
    def on_calc_result(e):
        if 'calc' in views and views['calc']:
            views['calc'].on_file_result(e)
            
    # === Create FilePickers ===
    # Initialize with callback immediately to ensure proper binding
    calc_picker = ft.FilePicker(on_result=on_calc_result)
    settings_picker = ft.FilePicker() # SettingsView binds its own callback dynamically

    # Add to overlay immediately
    if calc_picker not in page.overlay:
        page.overlay.append(calc_picker)
    if settings_picker not in page.overlay:
        page.overlay.append(settings_picker)
    page.update()
    
    def create_views():
        """Create all views"""
        nonlocal views
        
        def refresh_calc():
            if 'calc' in views and views['calc']:
                views['calc'].refresh_table()
        
        views['calc'] = CalculationView(page, file_picker=calc_picker, is_dark=is_dark)
        views['stock'] = StockView(page, on_refresh_calc=refresh_calc, is_dark=is_dark)
        views['product'] = ProductView(page, on_refresh_calc=refresh_calc, is_dark=is_dark)
        views['history'] = HistoryView(page, is_dark=is_dark)
        views['settings'] = SettingsView(page, file_picker=settings_picker, on_theme_change=toggle_theme, is_dark=is_dark)
    
    def toggle_theme(dark: bool):
        nonlocal is_dark
        is_dark = dark
        
        if dark:
            page.theme_mode = ThemeMode.DARK
            page.bgcolor = AppTheme.BG_DARK
        else:
            page.theme_mode = ThemeMode.LIGHT
            page.bgcolor = AppTheme.BG_LIGHT
        
        # Rebuild
        create_views()
        update_content(current_index)
        build_page()
        page.update()
    
    def update_content(index: int):
        """Update content area based on selected index"""
        nonlocal current_index
        current_index = index
        view_keys = ['calc', 'stock', 'product', 'history', 'settings']
        content_area.content = views[view_keys[index]]
    
    def on_nav_change(e):
        """Handle navigation change"""
        update_content(e.control.selected_index)
        page.update()
    
    # === Build Navigation Tabs ===
    def build_nav_tabs():
        """Build horizontal navigation tabs"""
        tab_items = [
            ("Bảng tính", Icons.CALCULATE_ROUNDED),
            ("Kho hàng", Icons.INVENTORY_ROUNDED),
            ("Sản phẩm", Icons.CATEGORY_ROUNDED),
            ("Lịch sử", Icons.HISTORY_ROUNDED),
            ("Cài đặt", Icons.SETTINGS_ROUNDED),
        ]
        
        def create_tab_button(label, icon, index):
            is_selected = current_index == index
            return ft.Container(
                content=ft.Row([
                    ft.Icon(icon, color=AppTheme.PRIMARY if is_selected else (AppTheme.TEXT_SECONDARY_DARK if is_dark else AppTheme.TEXT_SECONDARY_LIGHT), size=20),
                    ft.Text(
                        label,
                        size=14,
                        weight=ft.FontWeight.W_600 if is_selected else ft.FontWeight.W_500,
                        color=AppTheme.PRIMARY if is_selected else (AppTheme.TEXT_DARK if is_dark else AppTheme.TEXT_LIGHT),
                    ),
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                padding=ft.Padding(16, 12, 16, 12),
                border_radius=AppTheme.RADIUS_MD,
                bgcolor=Colors.with_opacity(0.1, AppTheme.PRIMARY) if is_selected else "transparent",
                border=ft.Border(bottom=ft.BorderSide(3, AppTheme.PRIMARY) if is_selected else ft.BorderSide(0, "transparent")),
                on_click=lambda e, idx=index: handle_tab_click(idx),
                on_hover=lambda e: handle_tab_hover(e),
            )
        
        def handle_tab_click(index):
            nonlocal current_index
            current_index = index
            update_content(index)
            build_page()
            page.update()
        
        def handle_tab_hover(e):
            if e.data == "true":
                e.control.bgcolor = Colors.with_opacity(0.08, AppTheme.PRIMARY)
            else:
                is_selected = e.control == tabs_row.controls[current_index] if hasattr(tabs_row, 'controls') else False
                e.control.bgcolor = Colors.with_opacity(0.1, AppTheme.PRIMARY) if is_selected else "transparent"
            e.control.update()
        
        tabs_row = ft.Row(
            [create_tab_button(label, icon, idx) for idx, (label, icon) in enumerate(tab_items)],
            spacing=4,
        )
        
        return ft.Container(
            content=tabs_row,
            bgcolor=AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT,
            padding=ft.Padding(24, 8, 24, 0),
            border=ft.Border(bottom=ft.BorderSide(1, AppTheme.BORDER_DARK if is_dark else AppTheme.BORDER_LIGHT)),
        )
    
    # === Header ===
    def build_header():
        """Build premium header"""
        return ft.Container(
            content=ft.Row([
                # Logo & Title
                ft.Row([
                    ft.Container(
                        content=ft.Icon(Icons.STORE_ROUNDED, color=Colors.WHITE, size=26),
                        width=48,
                        height=48,
                        bgcolor=AppTheme.PRIMARY,
                        border_radius=AppTheme.RADIUS_MD,
                        alignment=ft.Alignment(0, 0),
                        shadow=ft.BoxShadow(
                            blur_radius=8,
                            color=Colors.with_opacity(0.3, AppTheme.PRIMARY),
                            offset=ft.Offset(0, 2),
                        ),
                    ),
                    ft.Column([
                        ft.Text(
                            APP_NAME,
                            size=20,
                            weight=ft.FontWeight.W_700,
                            color=AppTheme.TEXT_DARK if is_dark else AppTheme.TEXT_LIGHT,
                        ),
                        ft.Text(
                            f"Phiên bản {APP_VERSION}",
                            size=12,
                            color=AppTheme.TEXT_SECONDARY_DARK if is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                        ),
                    ], spacing=2),
                ], spacing=16),
                
                # Actions
                ft.Row([
                    # Quick Stats (optional decorative element)
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(Icons.TRENDING_UP_ROUNDED, color=AppTheme.SUCCESS, size=18),
                            ft.Text(
                                "Hoạt động",
                                size=13,
                                color=AppTheme.SUCCESS,
                                weight=ft.FontWeight.W_500,
                            ),
                        ], spacing=6),
                        bgcolor=Colors.with_opacity(0.1, AppTheme.SUCCESS),
                        padding=ft.Padding(12, 8, 12, 8),
                        border_radius=AppTheme.RADIUS_LG,
                    ),
                    
                    # Theme Toggle
                    ft.Container(
                        content=ft.IconButton(
                            icon=Icons.DARK_MODE_ROUNDED if not is_dark else Icons.LIGHT_MODE_ROUNDED,
                            icon_color=AppTheme.TEXT_SECONDARY_DARK if is_dark else AppTheme.TEXT_SECONDARY_LIGHT,
                            tooltip="Chuyển chế độ sáng/tối",
                            on_click=lambda e: toggle_theme(not is_dark),
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=AppTheme.RADIUS_MD),
                                overlay_color=Colors.with_opacity(0.1, AppTheme.PRIMARY),
                            ),
                        ),
                        bgcolor=AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT,
                        border_radius=AppTheme.RADIUS_MD,
                        border=ft.Border.all(1, AppTheme.BORDER_DARK if is_dark else AppTheme.BORDER_LIGHT),
                    ),
                ], spacing=12),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.Padding(28, 20, 28, 16),
            bgcolor=AppTheme.SURFACE_DARK if is_dark else AppTheme.SURFACE_LIGHT,
        )
    
    # === Main Layout ===
    def build_page():
        page.controls.clear()
        page.add(
            ft.Column([
                build_header(),
                build_nav_tabs(),
                content_area,
            ], expand=True, spacing=0)
        )
    
    # Initialize
    try:
        create_views()
        update_content(0)
        build_page()
        page.update()
        
    except Exception as e:
        print(f"Error initializing app: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    ft.run(main)
