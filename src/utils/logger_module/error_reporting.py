import sys
import threading
import traceback

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QMessageBox

from src.utils.logger_module.log_viewer import ApplicationLogDialog
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()


def show_error_dialog(parent, title, message, details=None):
    """Show concise recovery guidance and provide access to saved diagnostics."""
    log_path = OmixForgeLogger.get_log_file_path()
    dialog = QMessageBox(QMessageBox.Icon.Critical, title, message, parent=parent)
    dialog.setInformativeText(
        f"OmixForge will remain open. You can retry the action.\n"
        f"Diagnostics are saved at:\n{log_path}"
    )
    if details:
        dialog.setDetailedText(str(details))

    view_logs = dialog.addButton("View Logs", QMessageBox.ButtonRole.ActionRole)
    dialog.addButton(QMessageBox.StandardButton.Close)
    dialog.exec()
    if dialog.clickedButton() is view_logs:
        ApplicationLogDialog(parent).exec()


class ApplicationExceptionHandler(QObject):
    """Log uncaught Python and background-thread exceptions and notify the UI."""

    unhandled_exception = pyqtSignal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_widget = None
        self._previous_sys_hook = sys.excepthook
        self._previous_thread_hook = getattr(threading, "excepthook", None)
        sys.excepthook = self._handle_sys_exception
        if self._previous_thread_hook is not None:
            threading.excepthook = self._handle_thread_exception
        self.unhandled_exception.connect(self._show_unhandled_exception)

    def _record_exception(self, context, exc_type, exc_value, exc_traceback):
        logger.error(
            context,
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        summary = f"{exc_type.__name__}: {exc_value}"
        details = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        self.unhandled_exception.emit(summary, details)

    def _handle_sys_exception(self, exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            self._previous_sys_hook(exc_type, exc_value, exc_traceback)
            return
        self._record_exception(
            "Unhandled application exception",
            exc_type,
            exc_value,
            exc_traceback,
        )

    def _handle_thread_exception(self, args):
        thread_name = getattr(args.thread, "name", "unknown")
        self._record_exception(
            f"Unhandled exception in thread {thread_name}",
            args.exc_type,
            args.exc_value,
            args.exc_traceback,
        )

    def _show_unhandled_exception(self, summary, details):
        show_error_dialog(
            self.parent_widget,
            "Unexpected Error",
            "An unexpected error occurred. Review the log and retry the action.",
            f"{summary}\n\n{details}",
        )

    def restore(self):
        """Restore the process exception hooks when the application exits."""
        if sys.excepthook == self._handle_sys_exception:
            sys.excepthook = self._previous_sys_hook
        if (
            self._previous_thread_hook is not None
            and threading.excepthook == self._handle_thread_exception
        ):
            threading.excepthook = self._previous_thread_hook
