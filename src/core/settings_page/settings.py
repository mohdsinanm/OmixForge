from PyQt6.QtWidgets import QLabel


from PyQt6.QtWidgets import QWidget, QVBoxLayout


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Settings")
        layout.addWidget(label)
        self.setLayout(layout)
        self.widget = self
