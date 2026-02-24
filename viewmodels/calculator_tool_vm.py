"""
CalculatorToolViewModel — Backend for CalculatorToolView.qml
Standalone calculator with history.
"""

from PySide6.QtCore import Signal, Slot, Property

from viewmodels.base_viewmodel import BaseViewModel


class CalculatorToolViewModel(BaseViewModel):
    """ViewModel for the standalone calculator tool."""

    displayChanged = Signal()
    historyChanged = Signal()

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._display = "0"
        self._expression = ""
        self._history: list = []  # list of {"expression": str, "result": str}
        self._last_operator = ""
        self._reset_on_next = False

    # ---- Properties ----

    def _get_display(self) -> str:
        return self._display

    display = Property(str, _get_display, notify=displayChanged)

    def _get_expression(self) -> str:
        return self._expression

    expression = Property(str, _get_expression, notify=displayChanged)

    def _get_history(self) -> list:
        return self._history

    history = Property("QVariant", _get_history, notify=historyChanged)

    # ---- Slots ----

    @Slot(str)
    def inputDigit(self, digit: str):
        """Append a digit to the display."""
        if self._reset_on_next:
            self._display = digit
            self._reset_on_next = False
        elif self._display == "0":
            self._display = digit
        else:
            self._display += digit
        self.displayChanged.emit()

    @Slot(str)
    def inputOperator(self, op: str):
        """Set operator (+, -, *, /)."""
        if self._expression and not self._reset_on_next:
            self.calculate()
        self._expression = f"{self._display} {op} "
        self._reset_on_next = True
        self._last_operator = op
        self.displayChanged.emit()

    @Slot()
    def inputDecimal(self):
        """Add decimal point."""
        if "." not in self._display:
            self._display += "."
            self.displayChanged.emit()

    @Slot()
    def calculate(self):
        """Evaluate the current expression."""
        if not self._expression:
            return
        full = self._expression + self._display
        try:
            # Safe eval — only numbers and operators
            allowed = set("0123456789.+-*/ ()")
            if all(c in allowed for c in full.replace(" ", "")):
                result = eval(full)
                result_str = self._format_number(result)
                self._history.insert(0, {"expression": full.strip(), "result": result_str})
                if len(self._history) > 50:
                    self._history = self._history[:50]
                self._display = result_str
                self._expression = ""
                self._reset_on_next = True
                self.displayChanged.emit()
                self.historyChanged.emit()
        except Exception as e:
            self._display = "Lỗi"
            self._expression = ""
            self._reset_on_next = True
            self.displayChanged.emit()

    @Slot()
    def clear(self):
        """Clear display and expression (C)."""
        self._display = "0"
        self._expression = ""
        self._reset_on_next = False
        self.displayChanged.emit()

    @Slot()
    def clearEntry(self):
        """Clear current entry only (CE)."""
        self._display = "0"
        self._reset_on_next = False
        self.displayChanged.emit()

    @Slot()
    def backspace(self):
        """Remove last character."""
        if len(self._display) > 1:
            self._display = self._display[:-1]
        else:
            self._display = "0"
        self.displayChanged.emit()

    @Slot()
    def negate(self):
        """Toggle sign."""
        if self._display != "0":
            if self._display.startswith("-"):
                self._display = self._display[1:]
            else:
                self._display = "-" + self._display
            self.displayChanged.emit()

    @Slot()
    def percent(self):
        """Calculate percentage."""
        try:
            val = float(self._display) / 100.0
            self._display = self._format_number(val)
            self.displayChanged.emit()
        except ValueError:
            pass

    @Slot()
    def clearHistory(self):
        """Clear calculation history."""
        self._history.clear()
        self.historyChanged.emit()

    @staticmethod
    def _format_number(val) -> str:
        """Format number for display."""
        if isinstance(val, float) and val == int(val):
            return str(int(val))
        if isinstance(val, float):
            return f"{val:.10g}"
        return str(val)
