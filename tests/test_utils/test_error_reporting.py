import sys
import threading
from types import SimpleNamespace

from PyQt6.QtWidgets import QFileDialog, QMessageBox

from src.utils.logger_module import error_reporting
from src.utils.logger_module.log_viewer import ApplicationLogDialog
from src.utils.logger_module import omix_logger
from src.utils.logger_module.omix_logger import OmixForgeLogger


def test_log_viewer_reads_and_exports_active_log(qtbot, monkeypatch, tmp_path):
    log_path = tmp_path / "OmixForge.log"
    log_path.write_text("ERROR: test failure\n", encoding="utf-8")
    export_path = tmp_path / "support.log"
    monkeypatch.setattr(
        "src.utils.logger_module.log_viewer.OmixForgeLogger.get_log_file_path",
        staticmethod(lambda: log_path),
    )
    monkeypatch.setattr(
        QFileDialog,
        "getSaveFileName",
        lambda *_args, **_kwargs: (str(export_path), "Log Files (*.log *.txt)"),
    )

    dialog = ApplicationLogDialog()
    qtbot.addWidget(dialog)
    assert dialog.log_text.toPlainText() == "ERROR: test failure\n"

    dialog.export_log()
    assert export_path.read_text(encoding="utf-8") == "ERROR: test failure\n"


def test_error_dialog_mentions_log_and_retry(qtbot, monkeypatch):
    dialogs = []

    def fake_exec(dialog):
        dialogs.append(dialog)
        return QMessageBox.StandardButton.Close

    monkeypatch.setattr(QMessageBox, "exec", fake_exec)
    error_reporting.show_error_dialog(
        None,
        "Worker Failed",
        "The action failed. Check your setup and retry.",
        "Technical detail",
    )

    assert dialogs[0].text() == "The action failed. Check your setup and retry."
    assert str(OmixForgeLogger.get_log_file_path()) in dialogs[0].informativeText()
    assert dialogs[0].detailedText() == "Technical detail"


def test_logger_persists_exception_traceback(monkeypatch, tmp_path):
    monkeypatch.setattr(omix_logger, "LOG_DIR", tmp_path)
    monkeypatch.setattr(OmixForgeLogger, "_logger", None)
    test_logger = OmixForgeLogger.get_logger("OmixForgeErrorReportingTest")
    try:
        try:
            raise ValueError("background operation failed")
        except ValueError:
            test_logger.exception("Worker failed")

        log_path = OmixForgeLogger.get_log_file_path()
        content = log_path.read_text(encoding="utf-8")
        assert "Traceback (most recent call last)" in content
        assert "ValueError: background operation failed" in content
    finally:
        for handler in test_logger.handlers[:]:
            test_logger.removeHandler(handler)
            handler.close()


def test_uncaught_exception_handler_logs_trace_and_notifies_user(
    monkeypatch,
):
    logged = []
    notifications = []

    class LoggerSpy:
        def error(self, message, **kwargs):
            logged.append((message, kwargs))

    monkeypatch.setattr(error_reporting, "logger", LoggerSpy())
    monkeypatch.setattr(
        error_reporting,
        "show_error_dialog",
        lambda _parent, title, message, details: notifications.append(
            (title, message, details)
        ),
    )

    previous_sys_hook = sys.excepthook
    handler = error_reporting.ApplicationExceptionHandler()
    try:
        assert sys.excepthook == handler._handle_sys_exception
        try:
            raise RuntimeError("unexpected worker failure")
        except RuntimeError as exc:
            handler._record_exception(
                "Unhandled test exception",
                type(exc),
                exc,
                exc.__traceback__,
            )

        try:
            raise RuntimeError("thread failure")
        except RuntimeError as exc:
            thread_error = exc
            thread_traceback = exc.__traceback__
        handler._handle_thread_exception(
            SimpleNamespace(
                thread=None,
                exc_type=type(thread_error),
                exc_value=thread_error,
                exc_traceback=thread_traceback,
            )
        )
    finally:
        handler.restore()

    assert logged[0][1]["exc_info"][0] is RuntimeError
    assert "thread unknown" in logged[1][0]
    assert notifications[0][0] == "Unexpected Error"
    assert "unexpected worker failure" in notifications[0][2]
    assert sys.excepthook is previous_sys_hook


def test_background_thread_exception_reaches_ui_reporter(monkeypatch, qtbot):
    notifications = []

    class LoggerSpy:
        def error(self, _message, **_kwargs):
            pass

    monkeypatch.setattr(error_reporting, "logger", LoggerSpy())
    monkeypatch.setattr(
        error_reporting,
        "show_error_dialog",
        lambda _parent, title, message, details: notifications.append(
            (title, message, details)
        ),
    )
    handler = error_reporting.ApplicationExceptionHandler()

    def fail_in_thread():
        raise RuntimeError("thread crashed")

    worker_thread = threading.Thread(target=fail_in_thread, name="test-worker")
    try:
        worker_thread.start()
        worker_thread.join()
        qtbot.waitUntil(lambda: bool(notifications))
    finally:
        handler.restore()

    assert notifications[0][0] == "Unexpected Error"
    assert "thread crashed" in notifications[0][2]
