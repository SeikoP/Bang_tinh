"""
CalculationViewModel — Backend for CalculationView.qml

Manages shift sessions: product table, handover/closing quantities,
total calculation, save/reset, drag-drop reorder.
"""

from PySide6.QtCore import Signal, Slot, Property

from viewmodels.base_viewmodel import BaseViewModel
from viewmodels.list_models import SessionListModel, ProductListModel


class CalculationViewModel(BaseViewModel):
    """ViewModel for the main calculation / shift management view."""

    # Signals
    sessionSaved = Signal()
    sessionReset = Signal()
    dataRefreshed = Signal()
    totalAmountChanged = Signal()
    currentShiftChanged = Signal()

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._session_model = SessionListModel(self)
        self._product_model = ProductListModel(self)
        self._current_shift = ""
        self._total_amount = 0.0

    # ---- Properties exposed to QML ----

    @Property("QVariant", constant=True)
    def sessionItems(self):
        return self._session_model

    @Property("QVariant", constant=True)
    def productItems(self):
        return self._product_model

    def _get_total_amount(self) -> float:
        return self._session_model.totalAmount

    totalAmount = Property(float, _get_total_amount, notify=totalAmountChanged)

    def _get_current_shift(self) -> str:
        return self._current_shift

    def _set_current_shift(self, val: str):
        if self._current_shift != val:
            self._current_shift = val
            self.currentShiftChanged.emit()

    currentShift = Property(str, _get_current_shift, _set_current_shift, notify=currentShiftChanged)

    # ---- Slots callable from QML ----

    @Slot()
    def refreshData(self):
        """Reload session data from database."""
        def _load():
            session_repo = self._get_service("session_repo")
            product_repo = self._get_service("product_repo")
            if session_repo:
                items = session_repo.get_all()
                self._session_model.resetItems(items)
            if product_repo:
                products = product_repo.get_all()
                self._product_model.resetItems(products)
            self.totalAmountChanged.emit()
            self.dataRefreshed.emit()
        self._safe_call(_load, error_msg="Failed to refresh data")

    @Slot(int, str)
    def updateHandoverQty(self, row: int, value: str):
        """Update handover quantity for a row. Supports 'XtY' notation via calculator service."""
        def _update():
            calc = self._get_service("calculator")
            session_repo = self._get_service("session_repo")
            item = self._session_model.get(row)
            if not item or not calc:
                return
            parsed = calc.parse_to_small_units(value, item.product.conversion)
            item.handover_qty = parsed
            if session_repo:
                session_repo.update_qty(item.product.id, handover_qty=parsed)
            idx = self._session_model.index(row)
            self._session_model.dataChanged.emit(idx, idx, [])
            self.totalAmountChanged.emit()
        self._safe_call(_update, error_msg="Failed to update handover qty")

    @Slot(int, str)
    def updateClosingQty(self, row: int, value: str):
        """Update closing quantity for a row."""
        def _update():
            calc = self._get_service("calculator")
            session_repo = self._get_service("session_repo")
            item = self._session_model.get(row)
            if not item or not calc:
                return
            parsed = calc.parse_to_small_units(value, item.product.conversion)
            # Validate: closing cannot exceed handover
            if parsed > item.handover_qty:
                self.errorOccurred.emit("Số đóng không thể lớn hơn số giao")
                return
            item.closing_qty = parsed
            if session_repo:
                session_repo.update_qty(item.product.id, closing_qty=parsed)
            idx = self._session_model.index(row)
            self._session_model.dataChanged.emit(idx, idx, [])
            self.totalAmountChanged.emit()
        self._safe_call(_update, error_msg="Failed to update closing qty")

    @Slot(str, str)
    def saveSession(self, shift_name: str, notes: str):
        """Save current session to history."""
        def _save():
            history_repo = self._get_service("history_repo")
            if not history_repo:
                return
            history_repo.save_current_session(shift_name=shift_name, notes=notes)
            self.sessionSaved.emit()
            self._logger.info(f"Session saved: {shift_name}")
        self._safe_call(_save, error_msg="Failed to save session")

    @Slot()
    def resetSession(self):
        """Reset all quantities to zero."""
        def _reset():
            session_repo = self._get_service("session_repo")
            if session_repo:
                session_repo.reset_all()
            self.refreshData()
            self.sessionReset.emit()
        self._safe_call(_reset, error_msg="Failed to reset session")

    @Slot(int, int)
    def moveItem(self, fromRow: int, toRow: int):
        """Drag-drop reorder."""
        self._session_model.moveItem(fromRow, toRow)

    @Slot(result=str)
    def formatTotal(self) -> str:
        """Return formatted total amount string."""
        total = self._session_model.totalAmount
        return f"{total:,.0f}"
