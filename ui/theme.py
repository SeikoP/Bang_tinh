"""
Centralized Theme System
Single source of truth for all UI styling
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict


class FontWeight(Enum):
    """Font weight constants"""
    LIGHT = 300
    REGULAR = 400
    MEDIUM = 500
    SEMIBOLD = 600
    BOLD = 700
    EXTRABOLD = 800
    BLACK = 900


class FontSize(Enum):
    """Font size constants (px)"""
    TINY = 10
    SMALL = 11
    NORMAL = 12
    MEDIUM = 14
    LARGE = 16
    XLARGE = 18
    XXLARGE = 20
    HUGE = 24
    MASSIVE = 32


class Spacing(Enum):
    """Spacing constants (px)"""
    NONE = 0
    TINY = 4
    SMALL = 8
    NORMAL = 12
    MEDIUM = 16
    LARGE = 20
    XLARGE = 24
    XXLARGE = 32


@dataclass
class ColorPalette:
    """Color palette"""
    # Primary colors
    primary: str = "#334e88"
    primary_light: str = "#5472b8"
    primary_dark: str = "#1a2d5a"
    
    # Secondary colors
    secondary: str = "#ff7043"
    secondary_light: str = "#ffa270"
    secondary_dark: str = "#c63f17"
    
    # Neutral colors
    background: str = "#f5f6f9"
    surface: str = "#ffffff"
    border: str = "#e0e0e0"
    divider: str = "#eeeeee"
    
    # Text colors
    text_primary: str = "#212121"
    text_secondary: str = "#757575"
    text_disabled: str = "#bdbdbd"
    text_hint: str = "#9e9e9e"
    
    # Semantic colors
    success: str = "#4caf50"
    success_light: str = "#81c784"
    success_dark: str = "#388e3c"
    
    warning: str = "#ff9800"
    warning_light: str = "#ffb74d"
    warning_dark: str = "#f57c00"
    
    error: str = "#f44336"
    error_light: str = "#e57373"
    error_dark: str = "#d32f2f"
    
    info: str = "#2196f3"
    info_light: str = "#64b5f6"
    info_dark: str = "#1976d2"
    
    # Sidebar
    sidebar_bg: str = "#2c3e50"
    sidebar_text: str = "#ecf0f1"
    sidebar_hover: str = "#34495e"
    sidebar_active: str = "#3498db"


@dataclass
class Typography:
    """Typography settings"""
    # Font family - ONLY Cabin
    font_family: str = "Cabin"
    font_family_mono: str = "Courier New"
    
    # Font sizes
    size_tiny: int = FontSize.TINY.value
    size_small: int = FontSize.SMALL.value
    size_normal: int = FontSize.NORMAL.value
    size_medium: int = FontSize.MEDIUM.value
    size_large: int = FontSize.LARGE.value
    size_xlarge: int = FontSize.XLARGE.value
    size_xxlarge: int = FontSize.XXLARGE.value
    size_huge: int = FontSize.HUGE.value
    size_massive: int = FontSize.MASSIVE.value
    
    # Font weights
    weight_light: int = FontWeight.LIGHT.value
    weight_regular: int = FontWeight.REGULAR.value
    weight_medium: int = FontWeight.MEDIUM.value
    weight_semibold: int = FontWeight.SEMIBOLD.value
    weight_bold: int = FontWeight.BOLD.value
    weight_extrabold: int = FontWeight.EXTRABOLD.value
    weight_black: int = FontWeight.BLACK.value
    
    # Line heights
    line_height_tight: float = 1.2
    line_height_normal: float = 1.5
    line_height_relaxed: float = 1.8


@dataclass
class Layout:
    """Layout settings"""
    # Spacing
    spacing_none: int = Spacing.NONE.value
    spacing_tiny: int = Spacing.TINY.value
    spacing_small: int = Spacing.SMALL.value
    spacing_normal: int = Spacing.NORMAL.value
    spacing_medium: int = Spacing.MEDIUM.value
    spacing_large: int = Spacing.LARGE.value
    spacing_xlarge: int = Spacing.XLARGE.value
    spacing_xxlarge: int = Spacing.XXLARGE.value
    
    # Border radius
    radius_none: int = 0
    radius_small: int = 4
    radius_normal: int = 8
    radius_large: int = 12
    radius_xlarge: int = 16
    radius_round: int = 9999
    
    # Shadows
    shadow_none: str = "none"
    shadow_small: str = "0 1px 3px rgba(0,0,0,0.12)"
    shadow_normal: str = "0 2px 8px rgba(0,0,0,0.15)"
    shadow_large: str = "0 4px 16px rgba(0,0,0,0.18)"
    
    # Transitions
    transition_fast: str = "all 0.15s ease"
    transition_normal: str = "all 0.3s ease"
    transition_slow: str = "all 0.5s ease"


class AppTheme:
    """
    Application theme
    
    Usage:
        theme = AppTheme()
        stylesheet = theme.get_stylesheet()
        app.setStyleSheet(stylesheet)
    """
    
    def __init__(self):
        self.colors = ColorPalette()
        self.typography = Typography()
        self.layout = Layout()
    
    def get_stylesheet(self) -> str:
        """
        Get complete QSS stylesheet
        
        Returns:
            QSS stylesheet string
        """
        return f"""
        /* ========================================
           GLOBAL STYLES
           ======================================== */
        
        * {{
            font-family: "{self.typography.font_family}", sans-serif;
            font-size: {self.typography.size_normal}px;
            color: {self.colors.text_primary};
        }}
        
        QMainWindow {{
            background-color: {self.colors.background};
        }}
        
        QWidget {{
            background-color: transparent;
        }}
        
        /* ========================================
           SIDEBAR
           ======================================== */
        
        QFrame#sidebar {{
            background-color: {self.colors.sidebar_bg};
            border-right: 1px solid {self.colors.border};
        }}
        
        QLabel#logo {{
            color: {self.colors.sidebar_text};
            font-size: {self.typography.size_xlarge}px;
            font-weight: {self.typography.weight_black};
            padding: 0 {self.layout.spacing_small}px {self.layout.spacing_medium}px {self.layout.spacing_small}px;
        }}
        
        QPushButton#nav_button {{
            background-color: transparent;
            color: {self.colors.sidebar_text};
            border: none;
            border-radius: {self.layout.radius_small}px;
            padding: {self.layout.spacing_normal}px {self.layout.spacing_medium}px;
            text-align: left;
            font-size: {self.typography.size_medium}px;
            font-weight: {self.typography.weight_medium};
        }}
        
        QPushButton#nav_button:hover {{
            background-color: {self.colors.sidebar_hover};
        }}
        
        QPushButton#nav_button[active="true"] {{
            background-color: {self.colors.sidebar_active};
            font-weight: {self.typography.weight_bold};
        }}
        
        QLabel#version {{
            color: {self.colors.sidebar_text};
            font-size: {self.typography.size_small}px;
            padding: {self.layout.spacing_normal}px;
            opacity: 0.7;
        }}
        
        /* ========================================
           HEADER
           ======================================== */
        
        QFrame#header {{
            background-color: {self.colors.surface};
            border-bottom: 1px solid {self.colors.border};
        }}
        
        QLabel#breadcrumb {{
            color: {self.colors.text_secondary};
            font-size: {self.typography.size_medium}px;
            font-weight: {self.typography.weight_medium};
        }}
        
        /* ========================================
           BUTTONS
           ======================================== */
        
        QPushButton {{
            background-color: {self.colors.primary};
            color: white;
            border: none;
            border-radius: {self.layout.radius_small}px;
            padding: {self.layout.spacing_small}px {self.layout.spacing_medium}px;
            font-size: {self.typography.size_normal}px;
            font-weight: {self.typography.weight_semibold};
            min-height: 36px;
        }}
        
        QPushButton:hover {{
            background-color: {self.colors.primary_light};
        }}
        
        QPushButton:pressed {{
            background-color: {self.colors.primary_dark};
        }}
        
        QPushButton:disabled {{
            background-color: {self.colors.border};
            color: {self.colors.text_disabled};
        }}
        
        QPushButton#secondary {{
            background-color: transparent;
            color: {self.colors.primary};
            border: 2px solid {self.colors.primary};
        }}
        
        QPushButton#secondary:hover {{
            background-color: {self.colors.primary};
            color: white;
        }}
        
        QPushButton#danger {{
            background-color: {self.colors.error};
        }}
        
        QPushButton#danger:hover {{
            background-color: {self.colors.error_dark};
        }}
        
        QPushButton#success {{
            background-color: {self.colors.success};
        }}
        
        QPushButton#success:hover {{
            background-color: {self.colors.success_dark};
        }}
        
        /* ========================================
           INPUTS
           ======================================== */
        
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {self.colors.surface};
            border: 1px solid {self.colors.border};
            border-radius: {self.layout.radius_small}px;
            padding: {self.layout.spacing_small}px {self.layout.spacing_normal}px;
            font-size: {self.typography.size_normal}px;
            color: {self.colors.text_primary};
            selection-background-color: {self.colors.primary_light};
        }}
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {self.colors.primary};
        }}
        
        QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {{
            background-color: {self.colors.background};
            color: {self.colors.text_disabled};
        }}
        
        /* ========================================
           COMBOBOX
           ======================================== */
        
        QComboBox {{
            background-color: {self.colors.surface};
            border: 1px solid {self.colors.border};
            border-radius: {self.layout.radius_small}px;
            padding: {self.layout.spacing_small}px {self.layout.spacing_normal}px;
            font-size: {self.typography.size_normal}px;
            min-height: 32px;
        }}
        
        QComboBox:hover {{
            border: 1px solid {self.colors.primary};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {self.colors.text_secondary};
            margin-right: 10px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {self.colors.surface};
            border: 1px solid {self.colors.border};
            selection-background-color: {self.colors.primary_light};
            selection-color: white;
        }}
        
        /* ========================================
           TABLES
           ======================================== */
        
        QTableWidget {{
            background-color: {self.colors.surface};
            border: 1px solid {self.colors.border};
            border-radius: {self.layout.radius_small}px;
            gridline-color: {self.colors.divider};
            font-size: {self.typography.size_normal}px;
        }}
        
        QTableWidget::item {{
            padding: {self.layout.spacing_small}px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {self.colors.primary_light};
            color: white;
        }}
        
        QTableWidget::item:hover {{
            background-color: {self.colors.background};
        }}
        
        QHeaderView::section {{
            background-color: {self.colors.background};
            color: {self.colors.text_primary};
            padding: {self.layout.spacing_normal}px;
            border: none;
            border-bottom: 2px solid {self.colors.border};
            font-weight: {self.typography.weight_bold};
            font-size: {self.typography.size_normal}px;
        }}
        
        QTableWidget QTableCornerButton::section {{
            background-color: {self.colors.background};
            border: none;
        }}
        
        /* Alternating row colors */
        QTableWidget::item:alternate {{
            background-color: {self.colors.background};
        }}
        
        /* ========================================
           SCROLLBARS
           ======================================== */
        
        QScrollBar:vertical {{
            background-color: {self.colors.background};
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {self.colors.border};
            border-radius: 6px;
            min-height: 30px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {self.colors.text_disabled};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            background-color: {self.colors.background};
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {self.colors.border};
            border-radius: 6px;
            min-width: 30px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background-color: {self.colors.text_disabled};
        }}
        
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        
        /* ========================================
           TABS
           ======================================== */
        
        QTabWidget::pane {{
            border: 1px solid {self.colors.border};
            border-radius: {self.layout.radius_small}px;
            background-color: {self.colors.surface};
        }}
        
        QTabBar::tab {{
            background-color: {self.colors.background};
            color: {self.colors.text_secondary};
            padding: {self.layout.spacing_normal}px {self.layout.spacing_large}px;
            margin-right: {self.layout.spacing_tiny}px;
            border: 1px solid {self.colors.border};
            border-bottom: none;
            border-top-left-radius: {self.layout.radius_small}px;
            border-top-right-radius: {self.layout.radius_small}px;
            font-size: {self.typography.size_normal}px;
            font-weight: {self.typography.weight_medium};
        }}
        
        QTabBar::tab:selected {{
            background-color: {self.colors.surface};
            color: {self.colors.primary};
            border-bottom: 2px solid {self.colors.primary};
            font-weight: {self.typography.weight_bold};
        }}
        
        QTabBar::tab:hover {{
            background-color: {self.colors.primary_light};
            color: white;
        }}
        
        /* ========================================
           LABELS
           ======================================== */
        
        QLabel#title {{
            font-size: {self.typography.size_xxlarge}px;
            font-weight: {self.typography.weight_extrabold};
            color: {self.colors.text_primary};
        }}
        
        QLabel#subtitle {{
            font-size: {self.typography.size_large}px;
            font-weight: {self.typography.weight_bold};
            color: {self.colors.text_primary};
        }}
        
        QLabel#section_header {{
            font-size: {self.typography.size_medium}px;
            font-weight: {self.typography.weight_bold};
            color: {self.colors.text_primary};
        }}
        
        QLabel#hint {{
            font-size: {self.typography.size_small}px;
            color: {self.colors.text_hint};
            font-style: italic;
        }}
        
        /* ========================================
           CARDS
           ======================================== */
        
        QFrame#card {{
            background-color: {self.colors.surface};
            border: 1px solid {self.colors.border};
            border-radius: {self.layout.radius_normal}px;
            padding: {self.layout.spacing_medium}px;
        }}
        
        QFrame#card:hover {{
            box-shadow: {self.layout.shadow_normal};
        }}
        
        /* ========================================
           DIALOGS
           ======================================== */
        
        QDialog {{
            background-color: {self.colors.surface};
        }}
        
        QMessageBox {{
            background-color: {self.colors.surface};
        }}
        
        /* ========================================
           PROGRESS BAR
           ======================================== */
        
        QProgressBar {{
            background-color: {self.colors.background};
            border: 1px solid {self.colors.border};
            border-radius: {self.layout.radius_small}px;
            text-align: center;
            font-size: {self.typography.size_small}px;
            font-weight: {self.typography.weight_semibold};
            height: 24px;
        }}
        
        QProgressBar::chunk {{
            background-color: {self.colors.primary};
            border-radius: {self.layout.radius_small}px;
        }}
        
        /* ========================================
           CHECKBOXES & RADIO BUTTONS
           ======================================== */
        
        QCheckBox, QRadioButton {{
            spacing: {self.layout.spacing_small}px;
            font-size: {self.typography.size_normal}px;
        }}
        
        QCheckBox::indicator, QRadioButton::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid {self.colors.border};
            background-color: {self.colors.surface};
        }}
        
        QCheckBox::indicator {{
            border-radius: {self.layout.radius_small}px;
        }}
        
        QRadioButton::indicator {{
            border-radius: 9px;
        }}
        
        QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
            background-color: {self.colors.primary};
            border-color: {self.colors.primary};
        }}
        
        QCheckBox::indicator:hover, QRadioButton::indicator:hover {{
            border-color: {self.colors.primary};
        }}
        """
    
    def get_color(self, color_name: str) -> str:
        """Get color by name"""
        return getattr(self.colors, color_name, self.colors.text_primary)
    
    def get_font_size(self, size_name: str) -> int:
        """Get font size by name"""
        return getattr(self.typography, f"size_{size_name}", self.typography.size_normal)
    
    def get_spacing(self, spacing_name: str) -> int:
        """Get spacing by name"""
        return getattr(self.layout, f"spacing_{spacing_name}", self.layout.spacing_normal)
