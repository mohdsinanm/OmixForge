
import os
from PyQt6.QtWidgets import (
    QMainWindow, QTextEdit, QScrollArea, QVBoxLayout, QWidget, QToolBar, QPushButton
)
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

class FileViewerWindow(QMainWindow):
    def __init__(self, file_path: str, parent=None):
        """Initialize the file viewer window.
        
        Parameters
        ----------
        file_path : str
            Path to the file to display.
        parent : QWidget, optional
            Parent widget for this window.
        """
        super().__init__(parent)

        self.file_path = file_path
        self.setWindowTitle(os.path.basename(file_path))
        self.resize(900, 600)

        self._load_file()

    # ------------------------------------------------------------------

    def _load_file(self):
        """Load and display file content based on file type."""
        ext = os.path.splitext(self.file_path)[1].lower()

        if ext == ".txt":
            self._load_text()
        elif ext in (".html", ".pdf"):
            self._load_web()
        elif ext == ".svg":
            self._load_svg()
        else:
            self._load_text()  # Fallback to text viewer

    # ------------------------------------------------------------------

    def _load_text(self):
        """Load and display plain text file content with edit and save capability."""
        # Create central widget and layout
        central_widget = QWidget()
        layout = QVBoxLayout()
        
        # Create toolbar
        toolbar = QToolBar()
        save_action = QPushButton("Save")
        save_action.setShortcut("Ctrl+S")
        save_action.clicked.connect(self._save_file)
        toolbar.addWidget(save_action)
        
        # Create editor
        self.editor = QTextEdit()
        self.editor.setFont(QFont("Courier New", 10))

        try:
            with open(self.file_path, "r", encoding="utf-8", errors="ignore") as f:
                self.editor.setText(f.read())
        except Exception as e:
            self.editor.setText(f"Error loading file: {str(e)}")

        # Layout setup
        layout.addWidget(toolbar)
        layout.addWidget(self.editor)
        layout.setContentsMargins(0, 0, 0, 0)
        central_widget.setLayout(layout)
        
        self.setCentralWidget(central_widget)
    
    def _save_file(self):
        """Save the current editor content to the file."""
        try:
            content = self.editor.toPlainText()
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.setWindowTitle(f"{os.path.basename(self.file_path)} [Saved]")
            # Reset title after 2 seconds
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(2000, lambda: self.setWindowTitle(os.path.basename(self.file_path)))
        except Exception as e:
            self.editor.setText(f"Error saving file: {str(e)}\n\n--- Previous content ---\n{self.editor.toPlainText()}")


    def _load_web(self):
        """Load and display HTML/web content in a browser view."""
        QDesktopServices.openUrl(QUrl.fromLocalFile(self.file_path))
        return


    def _load_svg(self):
        """Load and display SVG content."""
        svg = QSvgWidget(self.file_path)
        scroll = QScrollArea()
        scroll.setWidget(svg)
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)
