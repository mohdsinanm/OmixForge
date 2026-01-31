from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt


class LoadingDialog(QDialog):
    def __init__(self, message="Processing...", parent=None):
        """Initialize the loading dialog widget.
        
        Parameters
        ----------
        message : str, optional
            Message to display while processing. Default is "Processing...".
        parent : QWidget, optional
            Parent widget for this dialog.
        """
        super().__init__(parent)

        self.setWindowTitle("Please wait")
        self.setModal(True)
        self.setFixedSize(300, 120)
        self.setWindowFlags(
            Qt.WindowType.Dialog |
            Qt.WindowType.CustomizeWindowHint |
            Qt.WindowType.WindowTitleHint
        )

        layout = QVBoxLayout(self)

        label = QLabel(message)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)

        # Indeterminate progress bar (spinner-like)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        layout.addWidget(self.progress)
        
    def close_dialog(self):
        """Safely close the loading dialog."""
        try:
            self.accept()
        except RuntimeError:
            pass