from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class SettingsSection(QWidget):
    def __init__(self, title: str):
        super().__init__()

        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(8)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #31564c; font-weight: 700; font-size: 14px;")

        self.layout.addWidget(title_label)

    def get_settings(self) -> dict:
        """Return section settings"""
        return {}

    def load_settings(self, data: dict):
        """Load section settings"""
        pass
