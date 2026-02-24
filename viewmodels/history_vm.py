"""
HistoryViewModel — Backend for HistoryView.qml
Manages session history list and detail view.
"""

from PySide6.QtCore import Signal, Slot, Property

from viewmodels.base_viewmodel import BaseViewModel
from viewmodels.list_models import HistoryListModel, HistoryItemModel


class HistoryViewModel(BaseViewModel):
    """ViewModel for session history."""

    dataRefreshed = Signal()
    detailLoaded = Signal()
    historyDeleted = Signal()
    exportCompleted = Signal(str)  # file path

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._history_model = HistoryListModel(self)
        self._detail_model = HistoryItemModel(self)
        self._selected_id = -1
        self._selected_shift = ""
        self._selected_date = ""
        self._selected_total = 0.0
        self._selected_notes = ""

    @Property("QVariant", constant=True)
    def histories(self):
        return self._history_model

    @Property("QVariant", constant=True)
    def detailItems(self):
        return self._detail_model

    # Selected history detail properties
    selectedIdChanged = Signal()
    
    def _get_selected_shift(self) -> str:
        return self._selected_shift

    selectedShift = Property(str, _get_selected_shift, notify=selectedIdChanged)
    
    def _get_selected_date(self) -> str:
        return self._selected_date
    
    selectedDate = Property(str, _get_selected_date, notify=selectedIdChanged)
    
    def _get_selected_total(self) -> float:
        return self._selected_total
    
    selectedTotal = Property(float, _get_selected_total, notify=selectedIdChanged)
    
    def _get_selected_notes(self) -> str:
        return self._selected_notes
    
    selectedNotes = Property(str, _get_selected_notes, notify=selectedIdChanged)

    @Slot()
    def refreshData(self):
        """Reload history list from database."""
        def _load():
            history_repo = self._get_service("history_repo")
            if history_repo:
                self._history_model.resetItems(history_repo.get_all())
            self.dataRefreshed.emit()
        self._safe_call(_load, error_msg="Failed to refresh history")

    @Slot(int)
    def loadDetail(self, history_id: int):
        """Load detail items for a specific history entry."""
        def _load():
            history_repo = self._get_service("history_repo")
            if not history_repo:
                return
            history = history_repo.get_by_id(history_id)
            if history:
                self._selected_id = history.id
                self._selected_shift = history.shift_name or ""
                self._selected_date = str(history.session_date) if history.session_date else ""
                self._selected_total = float(history.total_amount) if history.total_amount else 0.0
                self._selected_notes = history.notes or ""
                self._detail_model.resetItems(history.items)
                self.selectedIdChanged.emit()
                self.detailLoaded.emit()
        self._safe_call(_load, error_msg="Failed to load history detail")

    @Slot(int)
    def deleteHistory(self, history_id: int):
        """Delete a history entry."""
        def _delete():
            history_repo = self._get_service("history_repo")
            if history_repo:
                history_repo.delete(history_id)
                self.refreshData()
                self.historyDeleted.emit()
        self._safe_call(_delete, error_msg="Failed to delete history")

    @Slot(int, str)
    def exportHistory(self, history_id: int, file_path: str):
        """Export a history entry to Excel."""
        def _export():
            exporter = self._get_service("exporter")
            history_repo = self._get_service("history_repo")
            if not exporter or not history_repo:
                return
            history = history_repo.get_by_id(history_id)
            if history:
                exporter.export_session_history(history, file_path)
                self.exportCompleted.emit(file_path)
        self._safe_call(_export, error_msg="Failed to export history")
