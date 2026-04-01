"""Update dialog for desktop application releases."""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
                             QMessageBox, QPushButton, QProgressBar, QTextEdit,
                             QVBoxLayout)

from ...core.updater import GitHubReleaseUpdater, UpdateInfo
from ..theme import AppColors


class UpdateDownloadWorker(QThread):
    progress_changed = pyqtSignal(int)
    status_changed = pyqtSignal(str)
    download_finished = pyqtSignal(str)
    download_failed = pyqtSignal(str)

    def __init__(self, updater: GitHubReleaseUpdater, update_info: UpdateInfo):
        super().__init__()
        self.updater = updater
        self.update_info = update_info

    def run(self):
        try:
            self.status_changed.emit("Đang tải bản cập nhật mới nhất...")
            update_file = self.updater.download_update(
                self.update_info,
                progress_callback=self._emit_progress,
            )
            self.download_finished.emit(str(update_file))
        except Exception as e:
            self.download_failed.emit(str(e))

    def _emit_progress(self, downloaded_bytes: int, total_bytes: int):
        if total_bytes <= 0:
            self.progress_changed.emit(0)
            return
        progress = int((downloaded_bytes / total_bytes) * 100)
        self.progress_changed.emit(max(0, min(progress, 100)))


class UpdateDialog(QDialog):
    ignore_requested = pyqtSignal(str)
    update_started = pyqtSignal()

    def __init__(
        self,
        update_info: UpdateInfo,
        updater: GitHubReleaseUpdater,
        backup_service=None,
        parent=None,
    ):
        super().__init__(parent)
        self.update_info = update_info
        self.updater = updater
        self.backup_service = backup_service
        self._download_worker: Optional[UpdateDownloadWorker] = None

        self.setWindowTitle("Có bản cập nhật mới")
        self.setModal(True)
        self.resize(560, 480)
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(
            f"""
            QDialog {{
                background: {AppColors.BG};
            }}
            QLabel#title {{
                color: {AppColors.TEXT};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#meta {{
                color: {AppColors.TEXT_SECONDARY};
                font-size: 12px;
            }}
            QTextEdit {{
                background: {AppColors.SURFACE};
                border: 1px solid {AppColors.BORDER};
                border-radius: 12px;
                padding: 8px;
                color: {AppColors.TEXT};
            }}
            QProgressBar {{
                border: 1px solid {AppColors.BORDER};
                border-radius: 10px;
                background: {AppColors.BG_SECONDARY};
                min-height: 18px;
                text-align: center;
                color: {AppColors.TEXT};
            }}
            QProgressBar::chunk {{
                background: {AppColors.PRIMARY};
                border-radius: 9px;
            }}
            QPushButton {{
                min-height: 40px;
                padding: 0 16px;
                border-radius: 10px;
                font-weight: 600;
            }}
            QPushButton#primary {{
                background: {AppColors.PRIMARY};
                color: {AppColors.TEXT_ON_PRIMARY};
                border: none;
            }}
            QPushButton#primary:hover {{
                background: {AppColors.PRIMARY_HOVER};
            }}
            QPushButton#secondary, QPushButton#ghost {{
                background: {AppColors.BG_SECONDARY};
                color: {AppColors.TEXT};
                border: 1px solid {AppColors.BORDER};
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        title = QLabel("Bản cập nhật mới đã sẵn sàng")
        title.setObjectName("title")
        layout.addWidget(title)

        meta = QLabel(
            f"Phiên bản hiện tại: {self.updater.current_version}  •  Phiên bản mới: {self.update_info.version}"
        )
        meta.setObjectName("meta")
        layout.addWidget(meta)

        self.status_label = QLabel("Kiểm tra xong. Bạn có thể tải và cài ngay.")
        self.status_label.setObjectName("meta")
        layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.notes_edit = QTextEdit()
        self.notes_edit.setReadOnly(True)
        self.notes_edit.setMarkdown(
            self.update_info.release_notes or "Chưa có ghi chú phát hành cho bản này."
        )
        layout.addWidget(self.notes_edit, 1)

        actions = QHBoxLayout()
        actions.setSpacing(10)

        self.remind_button = QPushButton("Nhắc lại sau")
        self.remind_button.setObjectName("secondary")
        self.remind_button.clicked.connect(self.reject)
        actions.addWidget(self.remind_button)

        self.ignore_button = QPushButton("Bỏ qua phiên bản này")
        self.ignore_button.setObjectName("ghost")
        self.ignore_button.clicked.connect(self._ignore_version)
        actions.addWidget(self.ignore_button)

        self.update_button = QPushButton("Cập nhật ngay")
        self.update_button.setObjectName("primary")
        self.update_button.clicked.connect(self._start_update)
        actions.addWidget(self.update_button)

        layout.addLayout(actions)

    def _set_busy(self, busy: bool):
        self.remind_button.setEnabled(not busy)
        self.ignore_button.setEnabled(not busy)
        self.update_button.setEnabled(not busy)

    def _ignore_version(self):
        self.ignore_requested.emit(self.update_info.version)
        self.accept()

    def _start_update(self):
        if self._download_worker and self._download_worker.isRunning():
            return

        self._set_busy(True)
        self.status_label.setText("Chuẩn bị tải bản cài đặt mới...")
        self.progress_bar.setValue(0)

        self._download_worker = UpdateDownloadWorker(self.updater, self.update_info)
        self._download_worker.progress_changed.connect(self.progress_bar.setValue)
        self._download_worker.status_changed.connect(self.status_label.setText)
        self._download_worker.download_finished.connect(self._on_download_finished)
        self._download_worker.download_failed.connect(self._on_download_failed)
        self._download_worker.start()

    def _on_download_finished(self, update_file: str):
        try:
            if self.backup_service:
                safe_version = self.update_info.version.replace(".", "_")
                self.backup_service.create_backup(prefix=f"pre_update_{safe_version}")

            self.status_label.setText("Đang khởi chạy trình cài đặt...")
            self.progress_bar.setValue(100)
            self.updater.apply_update(Path(update_file))
            self.update_started.emit()
            QApplication.instance().quit()
        except Exception as e:
            self._on_download_failed(str(e))

    def _on_download_failed(self, error_message: str):
        self._set_busy(False)
        self.status_label.setText("Không thể hoàn tất cập nhật.")
        QMessageBox.warning(self, "Cập nhật thất bại", error_message)

    def reject(self):
        if self._download_worker and self._download_worker.isRunning():
            QMessageBox.information(
                self,
                "Đang tải cập nhật",
                "Vui lòng chờ tải xong hoặc để ứng dụng hoàn tất bước hiện tại.",
            )
            return
        super().reject()