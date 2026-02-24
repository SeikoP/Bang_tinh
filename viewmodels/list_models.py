"""
QAbstractListModel subclasses for QML data binding.

Each model wraps a Python list of domain objects and exposes named roles
so QML delegates can bind to properties like model.name, model.amount, etc.
"""

from decimal import Decimal
from typing import Any, Dict, List

from PySide6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    Qt,
    Signal,
    Slot,
    QByteArray,
)


# ─────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────

def _decimal_to_float(val) -> float:
    """Safely convert Decimal/str/int to float for QML."""
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (int, float)):
        return float(val)
    return 0.0


# ─────────────────────────────────────────────
# ProductListModel
# ─────────────────────────────────────────────

class ProductListModel(QAbstractListModel):
    """Expose list of Product domain objects to QML."""

    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    LargeUnitRole = Qt.UserRole + 3
    ConversionRole = Qt.UserRole + 4
    UnitPriceRole = Qt.UserRole + 5
    IsActiveRole = Qt.UserRole + 6
    IsFavoriteRole = Qt.UserRole + 7
    DisplayOrderRole = Qt.UserRole + 8
    UnitCharRole = Qt.UserRole + 9

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []

    # --- QAbstractListModel API ---

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        p = self._items[index.row()]
        mapping = {
            self.IdRole: p.id,
            self.NameRole: p.name,
            self.LargeUnitRole: p.large_unit,
            self.ConversionRole: p.conversion,
            self.UnitPriceRole: _decimal_to_float(p.unit_price),
            self.IsActiveRole: p.is_active,
            self.IsFavoriteRole: p.is_favorite,
            self.DisplayOrderRole: p.display_order,
            self.UnitCharRole: p.unit_char,
        }
        return mapping.get(role)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.IdRole: QByteArray(b"productId"),
            self.NameRole: QByteArray(b"name"),
            self.LargeUnitRole: QByteArray(b"largeUnit"),
            self.ConversionRole: QByteArray(b"conversion"),
            self.UnitPriceRole: QByteArray(b"unitPrice"),
            self.IsActiveRole: QByteArray(b"isActive"),
            self.IsFavoriteRole: QByteArray(b"isFavorite"),
            self.DisplayOrderRole: QByteArray(b"displayOrder"),
            self.UnitCharRole: QByteArray(b"unitChar"),
        }

    # --- Mutators ---

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()

    @Slot(object)
    def appendItem(self, item):
        row = len(self._items)
        self.beginInsertRows(QModelIndex(), row, row)
        self._items.append(item)
        self.endInsertRows()
        self.countChanged.emit()

    @Slot(int)
    def removeAt(self, row: int):
        if 0 <= row < len(self._items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()
            self.countChanged.emit()

    @Slot(int, object)
    def updateAt(self, row: int, item):
        if 0 <= row < len(self._items):
            self._items[row] = item
            idx = self.index(row)
            self.dataChanged.emit(idx, idx, [])

    def get(self, row: int):
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)


# ─────────────────────────────────────────────
# SessionListModel  (for CalculationView table)
# ─────────────────────────────────────────────

class SessionListModel(QAbstractListModel):
    """Expose list of SessionData for calculation table."""

    ProductNameRole = Qt.UserRole + 1
    LargeUnitRole = Qt.UserRole + 2
    ConversionRole = Qt.UserRole + 3
    UnitPriceRole = Qt.UserRole + 4
    HandoverQtyRole = Qt.UserRole + 5
    ClosingQtyRole = Qt.UserRole + 6
    UsedQtyRole = Qt.UserRole + 7
    AmountRole = Qt.UserRole + 8
    ProductIdRole = Qt.UserRole + 9
    UnitCharRole = Qt.UserRole + 10

    countChanged = Signal()
    totalChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        s = self._items[index.row()]
        mapping = {
            self.ProductNameRole: s.product.name,
            self.LargeUnitRole: s.product.large_unit,
            self.ConversionRole: s.product.conversion,
            self.UnitPriceRole: _decimal_to_float(s.product.unit_price),
            self.HandoverQtyRole: s.handover_qty,
            self.ClosingQtyRole: s.closing_qty,
            self.UsedQtyRole: s.used_qty,
            self.AmountRole: _decimal_to_float(s.amount),
            self.ProductIdRole: s.product.id,
            self.UnitCharRole: s.product.unit_char,
        }
        return mapping.get(role)

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or index.row() >= len(self._items):
            return False
        s = self._items[index.row()]
        if role == self.HandoverQtyRole:
            s.handover_qty = int(value)
        elif role == self.ClosingQtyRole:
            s.closing_qty = int(value)
        else:
            return False
        self.dataChanged.emit(index, index, [role, self.UsedQtyRole, self.AmountRole])
        self.totalChanged.emit()
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        default = super().flags(index)
        return default | Qt.ItemIsEditable

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.ProductNameRole: QByteArray(b"productName"),
            self.LargeUnitRole: QByteArray(b"largeUnit"),
            self.ConversionRole: QByteArray(b"conversion"),
            self.UnitPriceRole: QByteArray(b"unitPrice"),
            self.HandoverQtyRole: QByteArray(b"handoverQty"),
            self.ClosingQtyRole: QByteArray(b"closingQty"),
            self.UsedQtyRole: QByteArray(b"usedQty"),
            self.AmountRole: QByteArray(b"amount"),
            self.ProductIdRole: QByteArray(b"productId"),
            self.UnitCharRole: QByteArray(b"unitChar"),
        }

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()
        self.totalChanged.emit()

    @Slot(int, int)
    def moveItem(self, fromRow: int, toRow: int):
        """Support drag-drop reorder in QML."""
        if fromRow == toRow:
            return
        if not (0 <= fromRow < len(self._items) and 0 <= toRow < len(self._items)):
            return
        # Qt model move requires specific beginMoveRows logic
        if fromRow < toRow:
            self.beginMoveRows(QModelIndex(), fromRow, fromRow, QModelIndex(), toRow + 1)
        else:
            self.beginMoveRows(QModelIndex(), fromRow, fromRow, QModelIndex(), toRow)
        item = self._items.pop(fromRow)
        self._items.insert(toRow, item)
        self.endMoveRows()

    def get(self, row: int):
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)

    @Property(float, notify=totalChanged)
    def totalAmount(self) -> float:
        return sum(_decimal_to_float(s.amount) for s in self._items)


# ─────────────────────────────────────────────
# TaskListModel
# ─────────────────────────────────────────────

class TaskListModel(QAbstractListModel):
    """Expose list of Task objects to QML."""

    IdRole = Qt.UserRole + 1
    TypeRole = Qt.UserRole + 2
    TypeDisplayRole = Qt.UserRole + 3
    DescriptionRole = Qt.UserRole + 4
    CustomerRole = Qt.UserRole + 5
    AmountRole = Qt.UserRole + 6
    CompletedRole = Qt.UserRole + 7
    CreatedAtRole = Qt.UserRole + 8
    NotesRole = Qt.UserRole + 9

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        t = self._items[index.row()]
        mapping = {
            self.IdRole: t.id,
            self.TypeRole: t.task_type.value if hasattr(t.task_type, 'value') else str(t.task_type),
            self.TypeDisplayRole: t.type_display if hasattr(t, 'type_display') else str(t.task_type),
            self.DescriptionRole: t.description or "",
            self.CustomerRole: t.customer_name or "",
            self.AmountRole: _decimal_to_float(t.amount) if t.amount else 0.0,
            self.CompletedRole: bool(t.completed),
            self.CreatedAtRole: str(t.created_at) if t.created_at else "",
            self.NotesRole: t.notes or "",
        }
        return mapping.get(role)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.IdRole: QByteArray(b"taskId"),
            self.TypeRole: QByteArray(b"taskType"),
            self.TypeDisplayRole: QByteArray(b"typeDisplay"),
            self.DescriptionRole: QByteArray(b"description"),
            self.CustomerRole: QByteArray(b"customerName"),
            self.AmountRole: QByteArray(b"amount"),
            self.CompletedRole: QByteArray(b"completed"),
            self.CreatedAtRole: QByteArray(b"createdAt"),
            self.NotesRole: QByteArray(b"notes"),
        }

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()

    @Slot(int)
    def removeAt(self, row: int):
        if 0 <= row < len(self._items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()
            self.countChanged.emit()

    def get(self, row: int):
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)


# ─────────────────────────────────────────────
# HistoryListModel
# ─────────────────────────────────────────────

class HistoryListModel(QAbstractListModel):
    """Expose list of SessionHistory to QML."""

    IdRole = Qt.UserRole + 1
    DateRole = Qt.UserRole + 2
    ShiftRole = Qt.UserRole + 3
    TotalRole = Qt.UserRole + 4
    NotesRole = Qt.UserRole + 5
    CreatedAtRole = Qt.UserRole + 6

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        h = self._items[index.row()]
        mapping = {
            self.IdRole: h.id,
            self.DateRole: str(h.session_date) if h.session_date else "",
            self.ShiftRole: h.shift_name or "",
            self.TotalRole: _decimal_to_float(h.total_amount),
            self.NotesRole: h.notes or "",
            self.CreatedAtRole: str(h.created_at) if h.created_at else "",
        }
        return mapping.get(role)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.IdRole: QByteArray(b"historyId"),
            self.DateRole: QByteArray(b"sessionDate"),
            self.ShiftRole: QByteArray(b"shiftName"),
            self.TotalRole: QByteArray(b"totalAmount"),
            self.NotesRole: QByteArray(b"notes"),
            self.CreatedAtRole: QByteArray(b"createdAt"),
        }

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()

    @Slot(int)
    def removeAt(self, row: int):
        if 0 <= row < len(self._items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()
            self.countChanged.emit()

    def get(self, row: int):
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)


# ─────────────────────────────────────────────
# BankNotificationModel
# ─────────────────────────────────────────────

class BankNotificationModel(QAbstractListModel):
    """Expose list of BankNotification to QML."""

    IdRole = Qt.UserRole + 1
    TimeRole = Qt.UserRole + 2
    SourceRole = Qt.UserRole + 3
    AmountRole = Qt.UserRole + 4
    ContentRole = Qt.UserRole + 5
    SenderRole = Qt.UserRole + 6
    CreatedAtRole = Qt.UserRole + 7

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        n = self._items[index.row()]
        mapping = {
            self.IdRole: n.id,
            self.TimeRole: n.time_str or "",
            self.SourceRole: n.source or "",
            self.AmountRole: n.amount or "",
            self.ContentRole: n.content or "",
            self.SenderRole: n.sender_name or "",
            self.CreatedAtRole: str(n.created_at) if n.created_at else "",
        }
        return mapping.get(role)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.IdRole: QByteArray(b"notificationId"),
            self.TimeRole: QByteArray(b"timeStr"),
            self.SourceRole: QByteArray(b"source"),
            self.AmountRole: QByteArray(b"amount"),
            self.ContentRole: QByteArray(b"content"),
            self.SenderRole: QByteArray(b"senderName"),
            self.CreatedAtRole: QByteArray(b"createdAt"),
        }

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()

    @Slot(int)
    def removeAt(self, row: int):
        if 0 <= row < len(self._items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()
            self.countChanged.emit()

    def get(self, row: int):
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)


# ─────────────────────────────────────────────
# StockModel
# ─────────────────────────────────────────────

class StockModel(QAbstractListModel):
    """Product + stock quantity for StockView."""

    ProductIdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    LargeUnitRole = Qt.UserRole + 3
    QuantityRole = Qt.UserRole + 4
    ConversionRole = Qt.UserRole + 5

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[Dict] = []  # [{product_id, name, large_unit, quantity, conversion}]

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        item = self._items[index.row()]
        mapping = {
            self.ProductIdRole: item.get("product_id", 0),
            self.NameRole: item.get("name", ""),
            self.LargeUnitRole: item.get("large_unit", ""),
            self.QuantityRole: item.get("quantity", 0),
            self.ConversionRole: item.get("conversion", 1),
        }
        return mapping.get(role)

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole) -> bool:
        if not index.isValid() or index.row() >= len(self._items):
            return False
        if role == self.QuantityRole:
            self._items[index.row()]["quantity"] = int(value)
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.ProductIdRole: QByteArray(b"productId"),
            self.NameRole: QByteArray(b"name"),
            self.LargeUnitRole: QByteArray(b"largeUnit"),
            self.QuantityRole: QByteArray(b"quantity"),
            self.ConversionRole: QByteArray(b"conversion"),
        }

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()

    @Slot(int, int)
    def updateQuantity(self, row: int, qty: int):
        if 0 <= row < len(self._items):
            self._items[row]["quantity"] = qty
            idx = self.index(row)
            self.dataChanged.emit(idx, idx, [self.QuantityRole])

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)


# ─────────────────────────────────────────────
# QuickPriceModel
# ─────────────────────────────────────────────

class QuickPriceModel(QAbstractListModel):
    """Expose QuickPrice list to QML."""

    IdRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    PriceRole = Qt.UserRole + 3

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        qp = self._items[index.row()]
        mapping = {
            self.IdRole: qp.id,
            self.NameRole: qp.name,
            self.PriceRole: _decimal_to_float(qp.price),
        }
        return mapping.get(role)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.IdRole: QByteArray(b"priceId"),
            self.NameRole: QByteArray(b"name"),
            self.PriceRole: QByteArray(b"price"),
        }

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()

    @Slot(int)
    def removeAt(self, row: int):
        if 0 <= row < len(self._items):
            self.beginRemoveRows(QModelIndex(), row, row)
            self._items.pop(row)
            self.endRemoveRows()
            self.countChanged.emit()

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)


# ─────────────────────────────────────────────
# StockChangeLogModel
# ─────────────────────────────────────────────

class StockChangeLogModel(QAbstractListModel):
    """Expose StockChangeLog list to QML."""

    IdRole = Qt.UserRole + 1
    ProductNameRole = Qt.UserRole + 2
    OldQtyRole = Qt.UserRole + 3
    NewQtyRole = Qt.UserRole + 4
    ChangeTypeRole = Qt.UserRole + 5
    ChangedAtRole = Qt.UserRole + 6

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        cl = self._items[index.row()]
        mapping = {
            self.IdRole: cl.id,
            self.ProductNameRole: cl.product_name,
            self.OldQtyRole: cl.old_qty,
            self.NewQtyRole: cl.new_qty,
            self.ChangeTypeRole: cl.change_type,
            self.ChangedAtRole: str(cl.changed_at) if cl.changed_at else "",
        }
        return mapping.get(role)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.IdRole: QByteArray(b"logId"),
            self.ProductNameRole: QByteArray(b"productName"),
            self.OldQtyRole: QByteArray(b"oldQty"),
            self.NewQtyRole: QByteArray(b"newQty"),
            self.ChangeTypeRole: QByteArray(b"changeType"),
            self.ChangedAtRole: QByteArray(b"changedAt"),
        }

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)


# ─────────────────────────────────────────────
# HistoryItemModel (detail items of a session)
# ─────────────────────────────────────────────

class HistoryItemModel(QAbstractListModel):
    """Expose SessionHistoryItem list for detail dialog."""

    ProductNameRole = Qt.UserRole + 1
    LargeUnitRole = Qt.UserRole + 2
    ConversionRole = Qt.UserRole + 3
    UnitPriceRole = Qt.UserRole + 4
    HandoverRole = Qt.UserRole + 5
    ClosingRole = Qt.UserRole + 6
    UsedRole = Qt.UserRole + 7
    AmountRole = Qt.UserRole + 8

    countChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: list = []

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or index.row() >= len(self._items):
            return None
        it = self._items[index.row()]
        mapping = {
            self.ProductNameRole: it.product_name,
            self.LargeUnitRole: it.large_unit,
            self.ConversionRole: it.conversion,
            self.UnitPriceRole: _decimal_to_float(it.unit_price),
            self.HandoverRole: it.handover_qty,
            self.ClosingRole: it.closing_qty,
            self.UsedRole: it.used_qty,
            self.AmountRole: _decimal_to_float(it.amount),
        }
        return mapping.get(role)

    def roleNames(self) -> Dict[int, QByteArray]:
        return {
            self.ProductNameRole: QByteArray(b"productName"),
            self.LargeUnitRole: QByteArray(b"largeUnit"),
            self.ConversionRole: QByteArray(b"conversion"),
            self.UnitPriceRole: QByteArray(b"unitPrice"),
            self.HandoverRole: QByteArray(b"handoverQty"),
            self.ClosingRole: QByteArray(b"closingQty"),
            self.UsedRole: QByteArray(b"usedQty"),
            self.AmountRole: QByteArray(b"amount"),
        }

    @Slot(list)
    def resetItems(self, items: list):
        self.beginResetModel()
        self._items = list(items)
        self.endResetModel()
        self.countChanged.emit()

    @Property(int, notify=countChanged)
    def count(self) -> int:
        return len(self._items)
