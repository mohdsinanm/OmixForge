from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt, QTimer


class LoadingSpinner(QWidget):
    def __init__(self, message="Loading...", parent=None):
        """Initialize the loading bar animation widget.
        
        Parameters
        ----------
        message : str, optional
            Message to display while loading. Default is "Loading...".
        parent : QWidget, optional
            Parent widget for this spinner.
        """
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 20, 50, 20)

        # Message label
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.message_label.setStyleSheet("font-size: 13px; color: #666; font-weight: 500;")
        layout.addWidget(self.message_label)
        
        # Animated progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ddd;
                border-radius: 5px;
                background-color: #f0f0f0;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        # Animation timer for smooth progress
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_progress)
        self.progress_value = 0
        self.direction = 1  # 1 for forward, -1 for backward
        
        # Set a fixed height to reserve space regardless of visibility
        self.setFixedHeight(100)
        
        # Initially hide content to show empty space
        self.message_label.hide()
        self.progress_bar.hide()

    def _update_progress(self):
        """Update the progress bar animation."""
        self.progress_value += self.direction * 20
        
        # Change direction at boundaries
        if self.progress_value >= 95:
            self.direction = -1
        elif self.progress_value <= 5:
            self.direction = 1
        
        self.progress_bar.setValue(self.progress_value)

    def start_loading(self):
        """Show the progress bar and start animation."""
        self.progress_value = 0
        self.direction = 1
        self.progress_bar.setValue(0)
        self.message_label.show()
        self.progress_bar.show()
        self.timer.start(50)

    def stop_loading(self):
        """Hide the progress bar and stop animation."""
        self.timer.stop()
        self.message_label.hide()
        self.progress_bar.hide()



