"""
DPI-aware sizing helpers for PyQt6 widgets.

All height calculations derive from QFontMetrics so they automatically scale
with system DPI and user-selected font sizes.  Import the helper functions
instead of hard-coding pixel values.

Usage:
    from ..ui.dpi import scaled, text_height, row_height

    btn.setMinimumHeight(text_height(btn, padding=16))
    table.verticalHeader().setMinimumSectionSize(row_height(table, padding=20))
"""

from PyQt6.QtGui import QFont, QFontMetrics
from PyQt6.QtWidgets import QApplication, QWidget


def _screen_scale() -> float:
    """Return the primary screen's devicePixelRatio (1.0 at 100% DPI)."""
    app = QApplication.instance()
    if app:
        screen = app.primaryScreen()
        if screen:
            return screen.devicePixelRatio()
    return 1.0


def scaled(px: int) -> int:
    """Scale a *design-time* pixel value by the current DPI factor.

    Use this for paddings, margins, icon sizes — anything that is not
    text-driven.  For text containers prefer ``text_height()``.
    """
    return max(1, round(px * _screen_scale()))


def font_metrics(widget_or_font=None) -> QFontMetrics:
    """Return QFontMetrics for a widget, QFont, or the app default."""
    if isinstance(widget_or_font, QWidget):
        return widget_or_font.fontMetrics()
    if isinstance(widget_or_font, QFont):
        return QFontMetrics(widget_or_font)
    app = QApplication.instance()
    if app:
        return QFontMetrics(app.font())
    return QFontMetrics(QFont())


def text_height(source=None, *, padding: int = 12, lines: int = 1) -> int:
    """Minimum height that guarantees no vertical clipping.

    Parameters
    ----------
    source : QWidget | QFont | None
        Widget or font from which to derive metrics.
    padding : int
        Extra vertical space (top + bottom combined), in logical pixels.
    lines : int
        Number of visible text lines.

    Returns
    -------
    int
        Pixel height safe for ``setMinimumHeight()``.
    """
    fm = font_metrics(source)
    line_h = fm.height()
    return line_h * lines + (fm.leading() * max(0, lines - 1)) + padding


def row_height(source=None, *, padding: int = 20) -> int:
    """Recommended table-row height: single-line text + generous padding."""
    return text_height(source, padding=padding)


def button_height(source=None, *, padding: int = 16) -> int:
    """Minimum QPushButton height that won't clip text."""
    return text_height(source, padding=padding)


def input_height(source=None, *, padding: int = 18) -> int:
    """Minimum QLineEdit / QComboBox / QSpinBox height."""
    return text_height(source, padding=padding)


def banner_height(source=None, *, padding: int = 14) -> int:
    """MinimumHeight for a slim notification banner."""
    return text_height(source, padding=padding)
