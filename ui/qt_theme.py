"""
Qt Theme - Modern Premium Design
Inspired by modern desktop applications with enhanced visual appeal
"""


class AppColors:
    """
    WCAG AA Compliant Color System
    
    Rules:
    - Only Roboto and Cabin fonts allowed
    - No white text on light backgrounds
    - Minimum contrast ratio: 4.5:1
    """

    # Primary colors (Emerald Green matching Android)
    PRIMARY = "#10b981"  # Emerald-500
    PRIMARY_HOVER = "#059669"  # Emerald-600
    PRIMARY_LIGHT = "#34d399"  # Emerald-400
    PRIMARY_DARK = "#047857"  # Emerald-700

    # Text colors (WCAG AA compliant)
    TEXT = "#1F2937"  # Gray-800 - Main text
    TEXT_SECONDARY = "#6B7280"  # Gray-500 - Secondary text
    TEXT_DISABLED = "#9CA3AF"  # Gray-400 - Disabled text
    TEXT_ON_PRIMARY = "#FFFFFF"  # White on primary
    TEXT_ON_DARK = "#F9FAFB"  # Light on dark

    # Background colors
    BG = "#FFFFFF"  # White
    BG_SECONDARY = "#F9FAFB"  # Gray-50
    BG_HOVER = "#F3F4F6"  # Gray-100
    BG_SELECTED = "#EFF6FF"  # Blue-50
    BG_GRADIENT_START = "#F9FAFB"
    BG_GRADIENT_END = "#F3F4F6"

    # Surface
    SURFACE = "#FFFFFF"
    SURFACE_HOVER = "#FAFBFC"

    # Border colors
    BORDER = "#E5E7EB"  # Gray-200
    BORDER_HOVER = "#CBD5E1"  # Gray-300
    BORDER_FOCUS = "#2563EB"  # Blue-600

    # Status colors
    SUCCESS = "#10B981"  # Emerald-500
    WARNING = "#DC2626"  # Red-600 (changed from amber for better contrast)
    ERROR = "#DC2626"  # Red-600
    INFO = "#2563EB"  # Blue-600

    # Sidebar colors (Slate theme)
    SIDEBAR_BG = "#0f172a"  # Slate-900
    SIDEBAR_TEXT = "#94a3b8"  # Slate-400
    SIDEBAR_ITEM_HOVER = "#1e293b"  # Slate-800
    SIDEBAR_ITEM_ACTIVE = "#10b981"  # Emerald-500

    # Accent colors
    ACCENT_PURPLE = "#8B5CF6"
    ACCENT_PINK = "#EC4899"
    ACCENT_TEAL = "#14B8A6"


class AppTheme:
    """Theme generator"""

    @staticmethod
    def get_stylesheet() -> str:
        """Main application stylesheet with modern premium design"""
        c = AppColors

        return f"""
        /* ===== Base ===== */
        QMainWindow {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c.BG_GRADIENT_START}, stop:1 {c.BG_GRADIENT_END});
        }}
        
        QWidget {{
            font-family: 'Roboto', 'Cabin', sans-serif;
            font-size: 11px;
            color: {c.TEXT};
        }}
        
        QDialog {{
            background-color: {c.SURFACE};
            border-radius: 8px;
        }}
        
        /* ===== Labels ===== */
        QLabel {{
            background: transparent;
            color: {c.TEXT};
        }}
        
        QLabel#title {{
            font-family: 'Cabin', 'Roboto', sans-serif;
            font-size: 18px;
            font-weight: 800;
            color: {c.TEXT};
            letter-spacing: -0.02em;
        }}
        
        QLabel#subtitle {{
            font-family: 'Cabin', 'Roboto', sans-serif;
            font-size: 12px;
            color: {c.TEXT_SECONDARY};
            font-weight: 500;
        }}
        
        /* ===== Buttons ===== */
        QPushButton {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c.PRIMARY_LIGHT}, stop:1 {c.PRIMARY});
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 12px;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c.PRIMARY}, stop:1 {c.PRIMARY_DARK});
        }}
        
        QPushButton:pressed {{
            background-color: {c.PRIMARY_DARK};
            padding: 9px 16px 7px 16px;
        }}
        
        QPushButton:disabled {{
            background-color: {c.BORDER};
            color: {c.TEXT_DISABLED};
        }}
        
        QPushButton#secondary {{
            background: {c.SURFACE};
            color: {c.TEXT};
            border: 2px solid {c.BORDER};
        }}
        
        QPushButton#secondary:hover {{
            background-color: {c.SURFACE_HOVER};
            border-color: {c.BORDER_HOVER};
        }}
        
        QPushButton#primary {{
            background: {c.PRIMARY};
            color: white;
            border-radius: 6px;
            font-weight: 700;
        }}
        
        QPushButton#primary:hover {{
            background: {c.PRIMARY_HOVER};
        }}

        /* Sidebar Item Style - Modern gradient */
        QPushButton#navItem {{
            background: transparent;
            color: {c.SIDEBAR_TEXT};
            text-align: left;
            padding: 12px 14px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            border: none;
            min-height: 44px;
            letter-spacing: 0.3px;
        }}
        
        QPushButton#navItem:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 rgba(59, 130, 246, 0.15), stop:1 rgba(139, 92, 246, 0.15));
            color: white;
            border-left: 3px solid #3B82F6;
        }}
        
        QPushButton#navItem[active="true"] {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #3B82F6, stop:1 #8B5CF6);
            color: white;
            font-weight: 800;
            border-left: 4px solid white;
            border-radius: 8px;
            margin-left: 4px;
        }}
        
        QPushButton#success {{
            background: {c.SUCCESS};
        }}
        
        QPushButton#success:hover {{
            background: #059669;
        }}
        
        QPushButton#danger {{
            background: {c.ERROR};
        }}
        
        QPushButton#danger:hover {{
            background: #dc2626;
        }}
        
        QPushButton#iconBtn {{
            background-color: {c.SURFACE};
            color: {c.TEXT_SECONDARY};
            border: 2px solid {c.BORDER};
            border-radius: 6px;
            padding: 6px;
            font-size: 12px;
            font-weight: 600;
            min-height: 32px;
        }}
        
        QPushButton#iconBtn:hover {{
            background-color: {c.PRIMARY};
            color: white;
            border-color: {c.PRIMARY};
        }}
        
        QPushButton#iconBtn:pressed {{
            background-color: {c.PRIMARY_DARK};
        }}
        
        /* ===== Inputs ===== */
        QLineEdit {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px 10px;
            selection-background-color: {c.PRIMARY};
            font-size: 12px;
            min-height: 32px;
        }}
        
        QLineEdit:focus {{
            border: 2px solid {c.PRIMARY};
            background-color: white;
        }}
        
        QLineEdit:hover {{
            border-color: {c.BORDER_HOVER};
        }}
        
        QTextEdit {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 2px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px;
            selection-background-color: {c.PRIMARY};
            font-size: 12px;
        }}
        
        QTextEdit:focus {{
            border-color: {c.PRIMARY};
        }}
        
        QSpinBox, QDoubleSpinBox {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px 10px;
            font-weight: 600;
            font-size: 12px;
            min-height: 32px;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border: 2px solid {c.PRIMARY};
        }}
        
        QSpinBox:hover, QDoubleSpinBox:hover {{
            border-color: {c.BORDER_HOVER};
        }}
        
        QComboBox {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 2px solid {c.BORDER};
            border-radius: 6px;
            padding: 8px 10px;
            min-height: 32px;
            max-height: 32px;
            font-weight: 500;
            font-size: 12px;
        }}
        
        QComboBox:hover {{
            border-color: {c.BORDER_HOVER};
        }}
        
        QComboBox:focus {{
            border-color: {c.PRIMARY};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
            padding-right: 4px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {c.TEXT_SECONDARY};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {c.SURFACE};
            border: 2px solid {c.BORDER};
            border-radius: 6px;
            selection-background-color: {c.PRIMARY};
            selection-color: white;
            padding: 4px;
            outline: none;
            color: {c.TEXT};
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 8px 10px;
            border-radius: 4px;
            min-height: 32px;
            color: {c.TEXT};
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {c.BG_HOVER};
            color: {c.TEXT};
        }}
        
        QComboBox QAbstractItemView::item:selected {{
            background-color: {c.PRIMARY};
            color: white;
        }}
        
        /* ===== Tab Widget ===== */
        QTabWidget::pane {{
            border: none;
            background: transparent;
            margin-top: -1px;
        }}
        
        QTabBar {{
            background-color: {c.SURFACE};
            border-bottom: 2px solid {c.BORDER};
        }}
        
        QTabBar::tab {{
            background-color: transparent;
            color: {c.TEXT_SECONDARY};
            padding: 14px 28px;
            border-bottom: 3px solid transparent;
            font-weight: 600;
            font-size: 14px;
            margin-right: 4px;
        }}
        
        QTabBar::tab:selected {{
            color: {c.PRIMARY};
            border-bottom-color: {c.PRIMARY};
        }}
        
        QTabBar::tab:hover:!selected {{
            color: {c.TEXT};
            background-color: {c.BG_HOVER};
            border-bottom-color: {c.BORDER_HOVER};
        }}
        
        /* ===== Tables ===== */
        QTableWidget {{
            background-color: {c.SURFACE};
            alternate-background-color: {c.BG_SECONDARY};
            border: 1px solid {c.BORDER};
            border-radius: 8px;
            gridline-color: transparent;
            outline: none;
            font-size: 11px;
        }}
        
        QTableWidget::item {{
            padding: 6px 8px;
            border: none;
            min-height: 40px;
        }}
        
        QTableWidget::item:selected {{
            background-color: rgba(37, 99, 235, 0.15);
            border-left: 3px solid {c.PRIMARY};
        }}
        
        QTableWidget::item:hover {{
            background-color: rgba(37, 99, 235, 0.05);
            color: {c.TEXT};
        }}
        
        QHeaderView::section {{
            background-color: {c.BG_SECONDARY};
            color: {c.TEXT_SECONDARY};
            font-weight: 700;
            font-size: 10px;
            letter-spacing: 0.05em;
            padding: 12px 8px;
            border: none;
            border-right: 1px solid {c.BORDER};
            border-bottom: 1px solid {c.BORDER};
            min-height: 44px;
        }}
        
        QHeaderView::section:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c.BG}, stop:1 {c.BG_SECONDARY});
            color: {c.TEXT};
        }}
        
        QTableWidget QTableCornerButton::section {{
            background-color: {c.SURFACE};
            border: none;
        }}
        
        /* ===== Scrollbars ===== */
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
            margin: 2px;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c.BORDER_HOVER};
            border-radius: 5px;
            min-height: 40px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 {c.PRIMARY}, stop:1 {c.PRIMARY_LIGHT});
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            background: transparent;
            height: 10px;
            margin: 2px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c.BORDER_HOVER};
            border-radius: 5px;
            min-width: 40px;
        }}
        
        QScrollBar::handle:horizontal:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c.PRIMARY}, stop:1 {c.PRIMARY_LIGHT});
        }}
        
        /* ===== Frames ===== */
        QFrame#card {{
            background-color: {c.SURFACE};
            border: 2px solid {c.BORDER};
            border-radius: 12px;
        }}
        
        QFrame#card:hover {{
            border-color: {c.BORDER_HOVER};
        }}
        
        /* ===== Message Box ===== */
        QMessageBox {{
            background-color: {c.SURFACE};
        }}
        
        QMessageBox QLabel {{
            color: {c.TEXT};
        }}
        """

    @staticmethod
    def card_style() -> str:
        return f"""
            background-color: {AppColors.SURFACE};
            border: 1px solid {AppColors.BORDER};
            border-radius: 8px;
        """

    @staticmethod
    def info_box_style(color: str) -> str:
        return f"""
            background-color: rgba(66, 133, 244, 0.08);
            color: {color};
            border-radius: 4px;
            padding: 6px 10px;
            font-size: 12px;
        """
