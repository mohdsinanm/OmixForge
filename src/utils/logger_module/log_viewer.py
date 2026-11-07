from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)
from PyQt6.QtGui import QTextCursor

from src.utils.logger_module.omix_logger import OmixForgeLogger


class ApplicationLogDialog(QDialog):
    """View and export the current OmixForge application log."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OmixForge Application Log")
        self.resize(850, 520)

        self.log_path = OmixForgeLogger.get_log_file_path()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(f"Log file: {self.log_path}"))

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text, 1)

        buttons = QHBoxLayout()
        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_log)
        buttons.addWidget(refresh_button)

        export_button = QPushButton("Export Log")
        export_button.clicked.connect(self.export_log)
        buttons.addWidget(export_button)
        buttons.addStretch()

        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        buttons.addWidget(close_button)
        layout.addLayout(buttons)
        self.refresh_log()

    def refresh_log(self):
        try:
            content = self.log_path.read_text(encoding="utf-8")
        except FileNotFoundError:
            content = "No log file has been created yet."
        except OSError as exc:
            content = f"Could not read the log file: {exc}"
        self.log_text.setPlainText(content)
        self.log_text.moveCursor(QTextCursor.MoveOperation.End)

    def export_log(self):
        if not self.log_path.is_file():
            QMessageBox.information(self, "No Log File", "The application log does not exist yet.")
            return

        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Export Application Log",
            str(Path.home() / "OmixForge.log"),
            "Log Files (*.log *.txt);;All Files (*)",
        )
        if not destination:
            return

        try:
            Path(destination).write_bytes(self.log_path.read_bytes())
        except OSError as exc:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Could not export the application log:\n{exc}",
            )
            return

        QMessageBox.information(self, "Log Exported", f"Log exported to:\n{destination}")
