
import os
from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QScrollArea
)
from PyQt6.QtGui import QFont
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

class FileViewerWindow(QMainWindow):
    def __init__(self, file_path: str, parent=None):
        super().__init__(parent)

        self.file_path = file_path
        self.setWindowTitle(os.path.basename(file_path))
        self.resize(900, 600)

        self._load_file()

    # ------------------------------------------------------------------

    def _load_file(self):
        ext = os.path.splitext(self.file_path)[1].lower()

        if ext == ".txt":
            self._load_text()
        elif ext in (".html", ".pdf"):
            self._load_web()
        elif ext == ".svg":
            self._load_svg()

    # ------------------------------------------------------------------

    def _load_text(self):
        editor = QTextEdit()
        editor.setReadOnly(True)
        editor.setFont(QFont("Courier New", 10))

        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                editor.setText(f.read())
        except Exception as e:
            editor.setText(str(e))

        self.setCentralWidget(editor)


    def _load_web(self):
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.file_path))
        return


    def _load_svg(self):
        svg = QSvgWidget(self.file_path)
        scroll = QScrollArea()
        scroll.setWidget(svg)
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
