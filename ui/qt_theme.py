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
    
    # Text - Senior Corporate Palette
    TEXT = "#0f172a"          # Trùng với thiết kế SaaS hiện đại
    TEXT_SECONDARY = "#334155"   # Đơn mức Slate 700 để đạt độ tương phản tối đa trên nền xám
    TEXT_DISABLED = "#94a3b8"
    
    # Sidebar - Solid Core Design
    SIDEBAR_BG = "#0f172a"
    SIDEBAR_TEXT = "#94a3b8"
    SIDEBAR_ITEM_HOVER = "#1e293b"
    SIDEBAR_ITEM_ACTIVE = "#2563eb"
    
    # Border - Subtle and refined
    BORDER = "#e2e8f0"
    BORDER_HOVER = "#cbd5e1"
    
    # Status - Standard Enterprise
    SUCCESS = "#10b981"
    WARNING = "#f59e0b"
    ERROR = "#ef4444"
    INFO = "#3b82f6"
    
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
            font-size: 22px;
            font-weight: 800;
            color: {c.TEXT};
            letter-spacing: -0.02em;
        }}
        
        QLabel#subtitle {{
            font-size: 14px;
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
            padding: 10px 20px;
            font-weight: 600;
            font-size: 13px;
            min-height: 36px;
        }}
        
        QPushButton:hover {{
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {c.PRIMARY}, stop:1 {c.PRIMARY_DARK});
        }}
        
        QPushButton:pressed {{
            background-color: {c.PRIMARY_DARK};
            padding: 11px 20px 9px 20px;
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
            border-radius: 8px;
            font-weight: 700;
        }}
        
        QPushButton#primary:hover {{
            background: {c.PRIMARY_HOVER};
        }}

        /* Sidebar Item Style */
        QPushButton#navItem {{
            background: transparent;
            color: {c.SIDEBAR_TEXT};
            text-align: left;
            padding: 10px 14px;
            border-radius: 8px;
            font-weight: 500;
            font-size: 14px;
            border: none;
            min-height: 44px;
        }}
        
        QPushButton#navItem:hover {{
            background-color: {c.SIDEBAR_ITEM_HOVER};
            color: white;
        }}
        
        QPushButton#navItem[active="true"] {{
            background-color: {c.PRIMARY};
            color: white;
            font-weight: 800;
            border-right: 4px solid white;
            border-radius: 8px 0 0 8px;
            margin-left: 8px;
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
            padding: 4px;
            font-size: 14px;
            font-weight: 600;
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
            padding: 8px 12px;
            selection-background-color: {c.PRIMARY};
            font-size: 14px;
            min-height: 20px;
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
            padding: 10px;
            selection-background-color: {c.PRIMARY};
        }}
        
        QTextEdit:focus {{
            border-color: {c.PRIMARY};
        }}
        
        QSpinBox, QDoubleSpinBox {{
            background-color: {c.SURFACE};
            color: {c.TEXT};
            border: 1px solid {c.BORDER};
            border-radius: 6px;
            padding: 6px 10px;
            font-weight: 600;
            font-size: 14px;
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
            padding: 10px 12px;
            min-height: 24px;
            font-weight: 500;
        }}
        
        QComboBox:hover {{
            border-color: {c.BORDER_HOVER};
        }}
        
        QComboBox:focus {{
            border-color: {c.PRIMARY};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 24px;
            padding-right: 4px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid {c.TEXT_SECONDARY};
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {c.SURFACE};
            border: 2px solid {c.BORDER};
            border-radius: 6px;
            selection-background-color: {c.PRIMARY};
            selection-color: white;
            padding: 4px;
            outline: none;
        }}
        
        QComboBox QAbstractItemView::item {{
            padding: 8px 12px;
            border-radius: 4px;
        }}
        
        QComboBox QAbstractItemView::item:hover {{
            background-color: {c.BG};
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
            background-color: {c.BG};
            border-bottom-color: {c.BORDER_HOVER};
        }}
        
        /* ===== Tables ===== */
        QTableWidget {{
            background-color: {c.SURFACE};
            alternate-background-color: {c.BG};
            border: 1px solid {c.BORDER};
            border-radius: 12px;
            gridline-color: transparent;
            outline: none;
        }}
        
        QTableWidget::item {{
            padding: 8px 8px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: rgba(37, 99, 235, 0.1);
            color: {c.TEXT};
        }}
        
        QTableWidget::item:hover {{
            background-color: rgba(37, 99, 235, 0.05);
        }}
        
        QHeaderView::section {{
            background-color: {c.BG};
            color: {c.TEXT_SECONDARY};
            font-weight: 700;
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            padding: 12px 10px;
            border: none;
            border-right: 1px solid {c.BORDER}; /* Vạch phân cách cột tiêu đề */
            border-bottom: 1px solid {c.BORDER};
        }}
        
        QHeaderView::section:hover {{
            background: {c.BG};
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
            background-color: {c.PRIMARY};
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
            background-color: {c.PRIMARY};
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
