"""
StockViewModel — Backend for StockView.qml

Manages inventory quantities with stepper controls and change history.
"""

from PySide6.QtCore import Signal, Slot, Property

from viewmodels.base_viewmodel import BaseViewModel
from viewmodels.list_models import StockModel, StockChangeLogModel


class StockViewModel(BaseViewModel):
    """ViewModel for inventory / stock management."""

    dataRefreshed = Signal()

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._stock_model = StockModel(self)
        self._changelog_model = StockChangeLogModel(self)

    @Property("QVariant", constant=True)
    def stockItems(self):
        return self._stock_model

    @Property("QVariant", constant=True)
    def changeLog(self):
        return self._changelog_model

    @Slot()
    def refreshData(self):
        """Reload stock data from database."""
        def _load():
            session_repo = self._get_service("session_repo")
            product_repo = self._get_service("product_repo")
            if not session_repo or not product_repo:
                return
            products = product_repo.get_all()
            sessions = session_repo.get_all()
            # Build stock list from products + sessions
            stock_items = []
            session_map = {s.product.id: s for s in sessions}
            for p in products:
                if not p.is_active:
                    continue
                s = session_map.get(p.id)
                qty = s.closing_qty if s else 0
                stock_items.append({
                    "product_id": p.id,
                    "name": p.name,
                    "large_unit": p.large_unit,
                    "quantity": qty,
                    "conversion": p.conversion,
                })
            self._stock_model.resetItems(stock_items)
            # Load change log
            from database.repositories import StockChangeLogRepository
            logs = StockChangeLogRepository.get_all()
            self._changelog_model.resetItems(logs)
            self.dataRefreshed.emit()
        self._safe_call(_load, error_msg="Failed to refresh stock data")

    @Slot(int, int)
    def adjustQuantity(self, row: int, delta: int):
        """Increase or decrease quantity for a product."""
        def _adjust():
            item = self._stock_model._items[row] if 0 <= row < len(self._stock_model._items) else None
            if not item:
                return
            old_qty = item["quantity"]
            new_qty = max(0, old_qty + delta)
            item["quantity"] = new_qty
            idx = self._stock_model.index(row)
            self._stock_model.dataChanged.emit(idx, idx, [StockModel.QuantityRole])
            # Persist
            session_repo = self._get_service("session_repo")
            if session_repo:
                session_repo.update_qty(item["product_id"], closing_qty=new_qty)
            # Log change
            from database.repositories import StockChangeLogRepository
            change_type = "increase" if delta > 0 else "decrease"
            StockChangeLogRepository.add_log(
                product_id=item["product_id"],
                product_name=item["name"],
                old_qty=old_qty,
                new_qty=new_qty,
                change_type=change_type,
            )
            # Refresh changelog
            logs = StockChangeLogRepository.get_all()
            self._changelog_model.resetItems(logs)
        self._safe_call(_adjust, error_msg="Failed to adjust stock quantity")

    @Slot(int, int)
    def setQuantity(self, row: int, qty: int):
        """Set absolute quantity for a product."""
        def _set():
            item = self._stock_model._items[row] if 0 <= row < len(self._stock_model._items) else None
            if not item:
                return
            old_qty = item["quantity"]
            item["quantity"] = qty
            idx = self._stock_model.index(row)
            self._stock_model.dataChanged.emit(idx, idx, [StockModel.QuantityRole])
            session_repo = self._get_service("session_repo")
            if session_repo:
                session_repo.update_qty(item["product_id"], closing_qty=qty)
            from database.repositories import StockChangeLogRepository
            change_type = "increase" if qty > old_qty else "decrease"
            StockChangeLogRepository.add_log(
                product_id=item["product_id"],
                product_name=item["name"],
                old_qty=old_qty,
                new_qty=qty,
                change_type=change_type,
            )
            logs = StockChangeLogRepository.get_all()
            self._changelog_model.resetItems(logs)
        self._safe_call(_set, error_msg="Failed to set stock quantity")
