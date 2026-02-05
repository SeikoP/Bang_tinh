"""
Qt Theme - Modern Premium Design
Inspired by modern desktop applications with enhanced visual appeal
"""

class AppColors:
    """Modern premium color palette"""
    # Background - Softer gradients
    BG = "#f5f7fa"
    BG_DARK = "#eef1f6"
    BG_GRADIENT_START = "#f8f9fc"
    BG_GRADIENT_END = "#f0f2f7"
    
    # Surface - Pure white with subtle shadow
    SURFACE = "#ffffff"
    SURFACE_HOVER = "#fafbfc"
    
    # Primary - Vibrant blue with depth
    PRIMARY = "#2563eb"
    PRIMARY_HOVER = "#1d4ed8"
    PRIMARY_LIGHT = "#3b82f6"
    PRIMARY_DARK = "#1e40af"
    
    # Text - Rich contrast
    TEXT = "#1e293b"
    TEXT_SECONDARY = "#64748b"
    TEXT_DISABLED = "#94a3b8"
    
    # Border - Subtle and refined
    BORDER = "#e2e8f0"
    BORDER_HOVER = "#cbd5e1"
    
    # Status - Vibrant and clear
    SUCCESS = "#10b981"
    SUCCESS_LIGHT = "#34d399"
    WARNING = "#f59e0b"
    WARNING_LIGHT = "#fbbf24"
    ERROR = "#ef4444"
    ERROR_LIGHT = "#f87171"
    INFO = "#3b82f6"
    INFO_LIGHT = "#60a5fa"
    
    # Accent colors
    ACCENT_PURPLE = "#8b5cf6"
    ACCENT_PINK = "#ec4899"
    ACCENT_TEAL = "#14b8a6"


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
            font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 13px;
            color: {c.TEXT};
        }}
        
        QDialog {{
            background-color: {c.SURFACE};
            border-radius: 12px;
        }}
        
        /* ===== Labels ===== */
        QLabel {{
            background: transparent;
            color: {c.TEXT};
        }}
        
        QLabel#title {{
            font-size: 20px;
            font-weight: 700;
            color: {c.TEXT};
            letter-spacing: -0.5px;
        }}
        
        QLabel#subtitle {{
            font-size: 13px;
            color: {c.TEXT_SECONDARY};
            font-weight: 500;
        }}
        
        /* ===== Buttons ===== */
        QPushButton {{
            background-color: {c.PRIMARY};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 8px 16px;
            font-weight: 500;
            min-height: 32px;
        }}
        
        QPushButton:hover {{
            background-color: {c.PRIMARY_HOVER};
        }}
        
        QPushButton:pressed {{
            background-color: {c.PRIMARY_HOVER};
        }}
        
        QPushButton:disabled {{
            background-color: {c.BORDER};
            color: {c.TEXT_DISABLED};
        }}
        
        QPushButton#secondary {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 1px solid {c.BORDER};
        }}
        
        QPushButton#secondary:hover {{
            background-color: {c.BG};
        }}
        
        QPushButton#success {{
            background-color: {c.SUCCESS};
        }}
        
        QPushButton#success:hover {{
            background-color: #2d9248;
        }}
        
        QPushButton#danger {{
            background-color: {c.ERROR};
        }}
        
        QPushButton#danger:hover {{
            background-color: #d93025;
        }}
        
        QPushButton#iconBtn {{
            background-color: transparent;
            color: {c.TEXT_SECONDARY};
            border: 1px solid {c.BORDER};
            border-radius: 4px;
            padding: 4px;
            min-width: 30px;
            max-width: 30px;
            min-height: 30px;
            max-height: 30px;
            font-size: 14px;
        }}
        
        QPushButton#iconBtn:hover {{
            background-color: {c.BG};
            color: {c.PRIMARY};
            border-color: {c.PRIMARY};
        }}
        
        /* ===== Inputs ===== */
        QLineEdit {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 1px solid {c.BORDER};
            border-radius: 4px;
            padding: 8px 10px;
            selection-background-color: {c.PRIMARY};
        }}
        
        QLineEdit:focus {{
            border-color: {c.PRIMARY};
            border-width: 2px;
            padding: 7px 9px;
        }}
        
        QTextEdit {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 1px solid {c.BORDER};
            border-radius: 4px;
            padding: 8px;
        }}
        
        QSpinBox, QDoubleSpinBox {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 1px solid {c.BORDER};
            border-radius: 4px;
            padding: 6px 8px;
        }}
        
        QSpinBox:focus, QDoubleSpinBox:focus {{
            border-color: {c.PRIMARY};
        }}
        
        QComboBox {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 1px solid {c.BORDER};
            border-radius: 4px;
            padding: 8px 10px;
            min-height: 20px;
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 4px solid transparent;
            border-right: 4px solid transparent;
            border-top: 5px solid {c.TEXT_SECONDARY};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {c.SURFACE};
            border: 1px solid {c.BORDER};
            selection-background-color: {c.BG};
            selection-color: {c.TEXT};
        }}
        
        /* ===== Tab Widget ===== */
        QTabWidget::pane {{
            border: none;
            background: transparent;
        }}
        
        QTabBar {{
            background-color: {c.SURFACE};
        }}
        
        QTabBar::tab {{
            background-color: transparent;
            color: {c.TEXT_SECONDARY};
            padding: 12px 24px;
            border-bottom: 2px solid transparent;
            font-weight: 500;
        }}
        
        QTabBar::tab:selected {{
            color: {c.PRIMARY};
            border-bottom-color: {c.PRIMARY};
        }}
        
        QTabBar::tab:hover:!selected {{
            color: {c.TEXT};
            background-color: {c.BG};
        }}
        
        /* ===== Tables ===== */
        QTableWidget {{
            background-color: {c.SURFACE};
            alternate-background-color: {c.BG};
            border: 1px solid {c.BORDER};
            border-radius: 4px;
            gridline-color: transparent;
            outline: none;
        }}
        
        QTableWidget::item {{
            padding: 8px 6px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: rgba(26, 115, 232, 0.08);
            color: {c.TEXT};
        }}
        
        QHeaderView::section {{
            background-color: {c.SURFACE};
            color: {c.TEXT_SECONDARY};
            font-weight: 600;
            font-size: 11px;
            text-transform: uppercase;
            padding: 12px 8px;
            border: none;
            border-bottom: 2px solid {c.BORDER};
        }}
        
        QTableWidget QTableCornerButton::section {{
            background-color: {c.SURFACE};
            border: none;
        }}
        
        /* ===== Scrollbars ===== */
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0;
        }}
        
        QScrollBar::handle:vertical {{
            background-color: {c.BORDER};
            border-radius: 4px;
            min-height: 40px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background-color: {c.TEXT_SECONDARY};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
            background: none;
            height: 0;
        }}
        
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
        }}
        
        QScrollBar::handle:horizontal {{
            background-color: {c.BORDER};
            border-radius: 4px;
        }}
        
        /* ===== Frames ===== */
        QFrame#card {{
            background-color: {c.SURFACE};
            border: 1px solid {c.BORDER};
            border-radius: 8px;
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
