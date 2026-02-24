"""
SettingsViewModel — Backend for SettingsView.qml
Manages app settings, TTS, backup, QR code for Android pairing.
"""

from PySide6.QtCore import Signal, Slot, Property

from viewmodels.base_viewmodel import BaseViewModel


class SettingsViewModel(BaseViewModel):
    """ViewModel for app settings."""

    settingsSaved = Signal()
    backupCompleted = Signal(str)
    backupFailed = Signal(str)
    restoreCompleted = Signal()
    qrCodeChanged = Signal()
    rowHeightChanged = Signal()
    widgetHeightChanged = Signal()
    ttsEnabledChanged = Signal()
    ttsVolumeChanged = Signal()
    autoBackupChanged = Signal()
    settingsReset = Signal()
    backupCreated = Signal()
    backupRestored = Signal()

    def __init__(self, container=None, parent=None):
        super().__init__(container, parent)
        self._row_height = 38
        self._widget_height = 32
        self._tts_enabled = True
        self._tts_voice = "vi-VN-HoaiMyNeural"
        self._tts_volume = 80
        self._qr_code_data = ""
        self._machine_count = 1
        self._server_ip = ""
        self._server_port = 5000
        self._auto_backup_enabled = False
        self._last_backup_time = ""

    # ---- Properties ----

    def _get_row_height(self) -> int:
        return self._row_height

    def _set_row_height(self, val: int):
        if self._row_height != val:
            self._row_height = val
            self.rowHeightChanged.emit()

    rowHeight = Property(int, _get_row_height, _set_row_height, notify=rowHeightChanged)

    def _get_widget_height(self) -> int:
        return self._widget_height

    def _set_widget_height(self, val: int):
        if self._widget_height != val:
            self._widget_height = val
            self.widgetHeightChanged.emit()

    widgetHeight = Property(int, _get_widget_height, _set_widget_height, notify=widgetHeightChanged)

    def _get_tts_enabled(self) -> bool:
        return self._tts_enabled

    def _set_tts_enabled(self, val: bool):
        if self._tts_enabled != val:
            self._tts_enabled = val
            self.ttsEnabledChanged.emit()

    ttsEnabled = Property(bool, _get_tts_enabled, _set_tts_enabled, notify=ttsEnabledChanged)

    def _get_tts_voice(self) -> str:
        return self._tts_voice

    ttsVoiceChanged = Signal()

    def _set_tts_voice(self, val: str):
        if self._tts_voice != val:
            self._tts_voice = val
            self.ttsVoiceChanged.emit()

    ttsVoice = Property(str, _get_tts_voice, _set_tts_voice, notify=ttsVoiceChanged)

    def _get_qr_code_data(self) -> str:
        return self._qr_code_data

    qrCodeData = Property(str, _get_qr_code_data, notify=qrCodeChanged)

    def _get_tts_volume(self) -> int:
        return self._tts_volume

    def _set_tts_volume(self, val: int):
        if self._tts_volume != val:
            self._tts_volume = val
            self.ttsVolumeChanged.emit()

    ttsVolume = Property(int, _get_tts_volume, _set_tts_volume, notify=ttsVolumeChanged)

    def _get_auto_backup_enabled(self) -> bool:
        return self._auto_backup_enabled

    autoBackupEnabled = Property(bool, _get_auto_backup_enabled, notify=autoBackupChanged)

    def _get_last_backup_time(self) -> str:
        return self._last_backup_time

    lastBackupTime = Property(str, _get_last_backup_time, notify=autoBackupChanged)

    machineCountChanged = Signal()

    def _get_machine_count(self) -> int:
        return self._machine_count

    def _set_machine_count(self, val: int):
        if self._machine_count != val:
            self._machine_count = val
            self.machineCountChanged.emit()

    machineCount = Property(int, _get_machine_count, _set_machine_count, notify=machineCountChanged)

    serverIpChanged = Signal()

    def _get_server_ip(self) -> str:
        return self._server_ip

    serverIp = Property(str, _get_server_ip, notify=serverIpChanged)

    def _get_server_port(self) -> int:
        return self._server_port

    serverPort = Property(int, _get_server_port, notify=serverIpChanged)

    # ---- Slots ----

    @Slot()
    def loadSettings(self):
        """Load settings from config."""
        config = self._get_service("config")
        if config:
            self._server_port = getattr(config, 'notification_port', 5000)
            self.serverIpChanged.emit()
        self._generate_qr_code()

    @Slot()
    def createBackup(self):
        """Create a database backup."""
        def _backup():
            backup_svc = self._get_service("backup_service")
            if backup_svc:
                path = backup_svc.create_backup()
                self.backupCompleted.emit(str(path))
        self._safe_call(_backup, error_msg="Backup failed")

    @Slot(str)
    def restoreBackup(self, file_path: str):
        """Restore database from backup file."""
        def _restore():
            backup_svc = self._get_service("backup_service")
            if backup_svc:
                backup_svc.restore_backup(file_path)
                self.restoreCompleted.emit()
        self._safe_call(_restore, error_msg="Restore failed")

    @Slot(result=list)
    def getBackupList(self) -> list:
        """Return list of available backup files."""
        try:
            backup_svc = self._get_service("backup_service")
            if backup_svc:
                backups = backup_svc.list_backups()
                return [{"name": b.name, "path": str(b), "size": b.stat().st_size} for b in backups]
        except Exception:
            pass
        return []

    @Slot()
    def testTts(self):
        """Play a TTS test phrase."""
        def _test():
            tts_svc = self._get_service("tts_service")
            if tts_svc:
                tts_svc.speak("Xin chào, đây là giọng thử nghiệm.")
        self._safe_call(_test, error_msg="TTS test failed")

    @Slot()
    def resetDefaults(self):
        """Reset all settings to defaults."""
        self._row_height = 38
        self._widget_height = 32
        self._tts_enabled = True
        self._tts_voice = "vi-VN-HoaiMyNeural"
        self._tts_volume = 80
        self._machine_count = 1
        self.rowHeightChanged.emit()
        self.widgetHeightChanged.emit()
        self.ttsEnabledChanged.emit()
        self.ttsVoiceChanged.emit()
        self.ttsVolumeChanged.emit()
        self.machineCountChanged.emit()
        self.settingsReset.emit()

    def _generate_qr_code(self):
        """Generate QR code data for Android pairing."""
        try:
            import socket
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            self._server_ip = ip
            self._qr_code_data = f"http://{ip}:{self._server_port}"
            self.serverIpChanged.emit()
            self.qrCodeChanged.emit()
        except Exception as e:
            self._logger.warning(f"Failed to generate QR code: {e}")
