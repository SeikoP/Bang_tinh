"""
BankViewModel — Backend for BankView.qml
Manages bank transaction notifications.
"""

from PySide6.QtCore import Signal, Slot, Property

from viewmodels.base_viewmodel import BaseViewModel
from viewmodels.list_models import BankNotificationModel


class BankViewModel(BaseViewModel):
    """ViewModel for bank transaction view."""

    dataRefreshed = Signal()
    sourceFilterChanged = Signal()

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._notification_model = BankNotificationModel(self)
        self._source_filter = ""  # empty = all

    @Property("QVariant", constant=True)
    def notifications(self):
        return self._notification_model

    def _get_source_filter(self) -> str:
        return self._source_filter

    def _set_source_filter(self, val: str):
        if self._source_filter != val:
            self._source_filter = val
            self.sourceFilterChanged.emit()
            self.refreshData()

    sourceFilter = Property(str, _get_source_filter, _set_source_filter, notify=sourceFilterChanged)

    @Slot()
    def refreshData(self):
        """Reload bank notifications from database."""
        def _load():
            from database.repositories import BankRepository
            all_notifs = BankRepository.get_all()
            if self._source_filter:
                filtered = [n for n in all_notifs if n.source == self._source_filter]
            else:
                filtered = all_notifs
            self._notification_model.resetItems(filtered)
            self.dataRefreshed.emit()
        self._safe_call(_load, error_msg="Failed to refresh bank data")

    @Slot(int)
    def deleteNotification(self, notif_id: int):
        """Delete a bank notification."""
        def _delete():
            from database.repositories import BankRepository
            BankRepository.delete(notif_id)
            self.refreshData()
        self._safe_call(_delete, error_msg="Failed to delete notification")

    @Slot()
    def clearAll(self):
        """Clear all bank notifications."""
        def _clear():
            from database.repositories import BankRepository
            BankRepository.clear_all()
            self.refreshData()
        self._safe_call(_clear, error_msg="Failed to clear notifications")

    rawLogsChanged = Signal()

    def _get_raw_logs(self) -> str:
        """Return raw notification log text."""
        try:
            from database.repositories import BankRepository
            all_notifs = BankRepository.get_all()
            lines = []
            for n in all_notifs:
                lines.append(f"[{n.received_at}] {n.source}: {n.raw_content or n.description}")
            return "\n".join(lines)
        except Exception:
            return ""

    rawLogs = Property(str, _get_raw_logs, notify=rawLogsChanged)

    @Slot(result=list)
    def getAvailableSources(self) -> list:
        """Return unique source names for filter ComboBox."""
        try:
            from database.repositories import BankRepository
            all_notifs = BankRepository.get_all()
            sources = sorted(set(n.source for n in all_notifs if n.source))
            return sources
        except Exception:
            return []
