"""Centralized error handling with logging and user notification"""

import logging

from PyQt6.QtWidgets import QMessageBox

from core.exceptions import AppException


class ErrorHandler:
    """Centralized error handling for the application"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def handle(self, error: Exception, parent_widget=None) -> None:
        """
        Handle an error with logging and user notification

        Args:
            error: The exception to handle
            parent_widget: Optional parent widget for message box
        """

        if isinstance(error, AppException):
            self.logger.error(
                f"{error.code}: {error.message}", extra={"details": error.details}
            )
            self._show_user_message(error.message, parent_widget)
        else:
            self.logger.exception("Unexpected error occurred")
            self._show_user_message(
                "Đã xảy ra lỗi không mong muốn. Vui lòng thử lại.", parent_widget
            )

    def _show_user_message(self, message: str, parent=None):
        """Show error message to user"""
        msg_box = QMessageBox(parent)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Lỗi")
        msg_box.exec()

    def handle_critical(self, error: Exception, parent_widget=None) -> None:
        """
        Handle a critical error that may require application shutdown

        Args:
            error: The critical exception
            parent_widget: Optional parent widget for message box
        """
        self.logger.critical(f"Critical error: {str(error)}", exc_info=True)

        msg_box = QMessageBox(parent_widget)
        msg_box.setIcon(QMessageBox.Icon.Critical)
        msg_box.setText(
            "Đã xảy ra lỗi nghiêm trọng. Ứng dụng có thể cần khởi động lại."
        )
        msg_box.setInformativeText(str(error))
        msg_box.setWindowTitle("Lỗi Nghiêm Trọng")
        msg_box.exec()

    def handle_warning(self, message: str, parent_widget=None) -> None:
        """
        Handle a warning message

        Args:
            message: Warning message to display
            parent_widget: Optional parent widget for message box
        """
        self.logger.warning(message)

        msg_box = QMessageBox(parent_widget)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Cảnh Báo")
        msg_box.exec()

    def handle_info(self, message: str, parent_widget=None) -> None:
        """
        Handle an informational message

        Args:
            message: Info message to display
            parent_widget: Optional parent widget for message box
        """
        self.logger.info(message)

        msg_box = QMessageBox(parent_widget)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setText(message)
        msg_box.setWindowTitle("Thông Báo")
        msg_box.exec()
