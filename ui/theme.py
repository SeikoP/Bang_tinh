"""
Theme - Định nghĩa theme và styles cho ứng dụng
Thiết kế hiện đại, đẹp mắt và đồng nhất
"""
import flet as ft
from flet import Colors, ThemeMode


class AppTheme:
    """Quản lý theme của ứng dụng - Premium Design System"""
    
    # === Typography ===
    FONT_FAMILY = "Segoe UI, Inter, Roboto, sans-serif"
    
    # === Modern Color Palette ===
    # Primary - Deep Blue Gradient
    PRIMARY = "#4F46E5"  # Indigo 600
    PRIMARY_LIGHT = "#818CF8"  # Indigo 400
    PRIMARY_DARK = "#3730A3"  # Indigo 800
    PRIMARY_GRADIENT_START = "#6366F1"
    PRIMARY_GRADIENT_END = "#4F46E5"
    
    # Secondary - Warm Orange/Coral
    SECONDARY = "#F97316"  # Orange 500
    SECONDARY_LIGHT = "#FB923C"
    
    # Accent - Cyan/Teal
    ACCENT = "#06B6D4"  # Cyan 500
    ACCENT_LIGHT = "#22D3EE"
    
    # === Light Theme ===
    BG_LIGHT = "#F8FAFC"  # Slate 50
    SURFACE_LIGHT = "#FFFFFF"
    CARD_LIGHT = "#FFFFFF"
    BORDER_LIGHT = "#E2E8F0"  # Slate 200
    TEXT_LIGHT = "#1E293B"  # Slate 800
    TEXT_SECONDARY_LIGHT = "#64748B"  # Slate 500
    
    # === Dark Theme ===
    BG_DARK = "#0F172A"  # Slate 900
    SURFACE_DARK = "#1E293B"  # Slate 800
    CARD_DARK = "#334155"  # Slate 700
    BORDER_DARK = "#475569"  # Slate 600
    TEXT_DARK = "#F8FAFC"  # Slate 50
    TEXT_SECONDARY_DARK = "#94A3B8"  # Slate 400
    
    # === Status Colors ===
    SUCCESS = "#10B981"  # Emerald 500
    SUCCESS_LIGHT = "#34D399"
    WARNING = "#F59E0B"  # Amber 500
    WARNING_LIGHT = "#FBBF24"
    ERROR = "#EF4444"  # Red 500
    ERROR_LIGHT = "#F87171"
    INFO = "#3B82F6"  # Blue 500
    INFO_LIGHT = "#60A5FA"
    
    # === Shadows ===
    SHADOW_SM = ft.BoxShadow(
        blur_radius=4,
        spread_radius=0,
        color=Colors.with_opacity(0.05, "black"),
        offset=ft.Offset(0, 1),
    )
    
    SHADOW_MD = ft.BoxShadow(
        blur_radius=10,
        spread_radius=-1,
        color=Colors.with_opacity(0.08, "black"),
        offset=ft.Offset(0, 4),
    )
    
    SHADOW_LG = ft.BoxShadow(
        blur_radius=20,
        spread_radius=-3,
        color=Colors.with_opacity(0.1, "black"),
        offset=ft.Offset(0, 10),
    )
    
    # === Border Radius ===
    RADIUS_SM = 6
    RADIUS_MD = 10
    RADIUS_LG = 16
    RADIUS_XL = 24
    
    @classmethod
    def get_page_theme(cls, is_dark: bool = False) -> dict:
        """Lấy config theme cho page"""
        return {
            "theme_mode": ThemeMode.DARK if is_dark else ThemeMode.LIGHT,
            "bgcolor": cls.BG_DARK if is_dark else cls.BG_LIGHT,
        }
    
    @classmethod
    def card_style(cls, is_dark: bool = False) -> dict:
        """Style cho card container - Premium look"""
        return {
            "bgcolor": cls.CARD_DARK if is_dark else cls.CARD_LIGHT,
            "border_radius": cls.RADIUS_LG,
            "padding": 24,
            "border": ft.Border.all(1, cls.BORDER_DARK if is_dark else cls.BORDER_LIGHT),
            "shadow": cls.SHADOW_MD,
        }
    
    @classmethod
    def header_text_style(cls, is_dark: bool = False) -> dict:
        """Style cho header text - Bold & Clean"""
        return {
            "size": 26,
            "weight": ft.FontWeight.W_800,
            "color": cls.TEXT_DARK if is_dark else cls.PRIMARY,
            "font_family": cls.FONT_FAMILY,
        }
    
    @classmethod
    def subheader_text_style(cls, is_dark: bool = False) -> dict:
        """Style cho subheader text"""
        return {
            "size": 18,
            "weight": ft.FontWeight.W_600,
            "color": cls.TEXT_DARK if is_dark else cls.TEXT_LIGHT,
            "font_family": cls.FONT_FAMILY,
        }
    
    @classmethod
    def body_text_style(cls, is_dark: bool = False) -> dict:
        """Style cho body text"""
        return {
            "size": 14,
            "color": cls.TEXT_SECONDARY_DARK if is_dark else cls.TEXT_SECONDARY_LIGHT,
            "font_family": cls.FONT_FAMILY,
        }
    
    @classmethod
    def primary_button_style(cls) -> ft.ButtonStyle:
        """Style cho primary button - Gradient feel"""
        return ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: cls.PRIMARY,
                ft.ControlState.HOVERED: cls.PRIMARY_LIGHT,
            },
            color=Colors.WHITE,
            padding=ft.Padding(24, 14, 24, 14),
            shape=ft.RoundedRectangleBorder(radius=cls.RADIUS_MD),
            elevation={"": 2, "hovered": 4},
            animation_duration=200,
        )
    
    @classmethod
    def secondary_button_style(cls, is_dark: bool = False) -> ft.ButtonStyle:
        """Style cho secondary button - Outlined"""
        return ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: "transparent",
                ft.ControlState.HOVERED: Colors.with_opacity(0.1, cls.PRIMARY),
            },
            color=cls.PRIMARY,
            padding=ft.Padding(24, 14, 24, 14),
            shape=ft.RoundedRectangleBorder(radius=cls.RADIUS_MD),
            side=ft.BorderSide(1.5, cls.PRIMARY),
            animation_duration=200,
        )
    
    @classmethod
    def danger_button_style(cls) -> ft.ButtonStyle:
        """Style cho danger button"""
        return ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: cls.ERROR,
                ft.ControlState.HOVERED: cls.ERROR_LIGHT,
            },
            color=Colors.WHITE,
            padding=ft.Padding(24, 14, 24, 14),
            shape=ft.RoundedRectangleBorder(radius=cls.RADIUS_MD),
            elevation=2,
        )
    
    @classmethod
    def success_button_style(cls) -> ft.ButtonStyle:
        """Style cho success button"""
        return ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: cls.SUCCESS,
                ft.ControlState.HOVERED: cls.SUCCESS_LIGHT,
            },
            color=Colors.WHITE,
            padding=ft.Padding(24, 14, 24, 14),
            shape=ft.RoundedRectangleBorder(radius=cls.RADIUS_MD),
            elevation=2,
        )
    
    @classmethod
    def input_field_style(cls, is_dark: bool = False) -> dict:
        """Style cho input field - Clean & Modern"""
        return {
            "border_color": cls.BORDER_DARK if is_dark else cls.BORDER_LIGHT,
            "focused_border_color": cls.PRIMARY,
            "focused_border_width": 2,
            "cursor_color": cls.PRIMARY,
            "bgcolor": cls.SURFACE_DARK if is_dark else cls.SURFACE_LIGHT,
            "border_radius": cls.RADIUS_MD,
            "content_padding": ft.Padding(16, 14, 16, 14),
        }
    
    @classmethod
    def data_table_style(cls, is_dark: bool = False) -> dict:
        """Style cho data table - Modern & Clean"""
        return {
            "heading_row_color": Colors.with_opacity(0.08, cls.PRIMARY),
            "heading_row_height": 56,
            "data_row_min_height": 52,
            "data_row_max_height": 60,
            "border": ft.Border.all(1, cls.BORDER_DARK if is_dark else cls.BORDER_LIGHT),
            "border_radius": cls.RADIUS_LG,
            "horizontal_lines": ft.BorderSide(1, cls.BORDER_DARK if is_dark else cls.BORDER_LIGHT),
            "column_spacing": 24,
        }
    
    @classmethod
    def tab_style(cls, is_dark: bool = False) -> dict:
        """Style cho tabs - Modern horizontal tabs"""
        return {
            "indicator_color": cls.PRIMARY,
            "indicator_border_radius": cls.RADIUS_SM,
            "indicator_padding": ft.Padding(0, 0, 0, 0),
            "label_color": cls.TEXT_DARK if is_dark else cls.TEXT_LIGHT,
            "unselected_label_color": cls.TEXT_SECONDARY_DARK if is_dark else cls.TEXT_SECONDARY_LIGHT,
            "divider_color": cls.BORDER_DARK if is_dark else cls.BORDER_LIGHT,
            "overlay_color": Colors.with_opacity(0.1, cls.PRIMARY),
        }
    
    @classmethod
    def badge_style(cls, color: str = None) -> dict:
        """Style cho badge/tag"""
        bg_color = color or cls.PRIMARY
        return {
            "bgcolor": Colors.with_opacity(0.15, bg_color),
            "border_radius": cls.RADIUS_SM,
            "padding": ft.Padding(10, 6, 10, 6),
        }
    
    @classmethod
    def icon_button_style(cls, color: str = None) -> dict:
        """Style cho icon button với hover effect"""
        btn_color = color or cls.PRIMARY
        return {
            "icon_color": btn_color,
            "style": ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=cls.RADIUS_MD),
                overlay_color=Colors.with_opacity(0.1, btn_color),
            ),
        }
    
    @classmethod
    def snackbar_style(cls, type: str = "info") -> dict:
        """Style cho snackbar notification"""
        colors_map = {
            "success": cls.SUCCESS,
            "warning": cls.WARNING,
            "error": cls.ERROR,
            "info": cls.INFO,
        }
        return {
            "bgcolor": colors_map.get(type, cls.INFO),
        }
    
    @classmethod 
    def get_gradient_header(cls, is_dark: bool = False) -> ft.Container:
        """Tạo header với gradient background"""
        return ft.Container(
            gradient=ft.LinearGradient(
                begin=ft.Alignment(-1, 0),
                end=ft.Alignment(1, 0),
                colors=[cls.PRIMARY_GRADIENT_START, cls.PRIMARY_GRADIENT_END],
            ),
            border_radius=ft.BorderRadius(0, 0, cls.RADIUS_XL, cls.RADIUS_XL),
        )
