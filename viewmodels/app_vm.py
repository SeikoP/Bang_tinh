"""
AppViewModel — Root ViewModel for application-level state.

Manages:
- Navigation state (current view index)
- Notification processing pipeline
- Server status
- TTS triggers
- App-wide alerts
"""

from PySide6.QtCore import Signal, Slot, Property, QTimer

from viewmodels.base_viewmodel import BaseViewModel


class AppViewModel(BaseViewModel):
    """Root application ViewModel — exposed as 'appVM' in QML."""

    # Signals
    currentViewChanged = Signal()
    serverStatusChanged = Signal()
    bankNotificationReceived = Signal(str, str, str)  # source, amount, sender
    toastRequested = Signal(str, str)  # message, type (success/error/warning/info)
    taskAlertChanged = Signal()
    appVersionChanged = Signal()

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._current_view = 0
        self._server_status = "disconnected"  # "connected" | "disconnected" | "connecting"
        self._pending_tasks = 0
        self._app_version = ""

        # Periodic status check
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._check_server_status)

        # Alert check timer
        self._alert_timer = QTimer(self)
        self._alert_timer.timeout.connect(self._check_alerts)

    # ---- Properties ----

    def _get_current_view(self) -> int:
        return self._current_view

    def _set_current_view(self, idx: int):
        if self._current_view != idx:
            self._current_view = idx
            self.currentViewChanged.emit()

    currentView = Property(int, _get_current_view, _set_current_view, notify=currentViewChanged)

    def _get_server_status(self) -> str:
        return self._server_status

    serverStatus = Property(str, _get_server_status, notify=serverStatusChanged)

    def _get_pending_tasks(self) -> int:
        return self._pending_tasks

    pendingTasks = Property(int, _get_pending_tasks, notify=taskAlertChanged)

    def _get_app_version(self) -> str:
        return self._app_version

    appVersion = Property(str, _get_app_version, notify=appVersionChanged)

    # ---- Slots ----

    @Slot(int)
    def switchView(self, index: int):
        """Switch to a different main view."""
        self.currentView = index

    @Slot()
    def startServices(self):
        """Start background services (notification server, timers)."""
        self._status_timer.start(10000)  # 10s
        self._alert_timer.start(300000)   # 5min
        self._logger.info("App services started")

    @Slot()
    def stopServices(self):
        """Stop all background services."""
        self._status_timer.stop()
        self._alert_timer.stop()

    @Slot(str)
    def handleNotification(self, raw_message: str):
        """Process incoming notification from server."""
        def _process():
            from services.bank_parser import BankStatementParser
            parsed = BankStatementParser.parse(raw_message)
            if parsed:
                source = parsed.get("source", "")
                amount = parsed.get("amount", "")
                sender = parsed.get("sender_name", "")
                self.bankNotificationReceived.emit(source, str(amount), sender)
                self.toastRequested.emit(
                    f"💰 {source}: {amount} từ {sender}",
                    "success"
                )
                # Save to DB
                bank_repo = self._get_service("bank_repo")
                if bank_repo:
                    bank_repo.add(parsed)
        self._safe_call(_process, error_msg="Notification processing failed")

    @Slot(str)
    def setAppVersion(self, version: str):
        self._app_version = version
        self.appVersionChanged.emit()

    # ---- Internal ----

    def _check_server_status(self):
        """Poll notification server status."""
        notification_svc = self._get_service("notification")
        if notification_svc and hasattr(notification_svc, 'is_running'):
            new_status = "connected" if notification_svc.is_running() else "disconnected"
        else:
            new_status = "disconnected"
        if new_status != self._server_status:
            self._server_status = new_status
            self.serverStatusChanged.emit()

    def _check_alerts(self):
        """Check for pending task alerts."""
        def _check():
            from database.task_repository import TaskRepository
            count = TaskRepository.count_pending()
            if count != self._pending_tasks:
                self._pending_tasks = count
                self.taskAlertChanged.emit()
        self._safe_call(_check, error_msg="Alert check failed")
