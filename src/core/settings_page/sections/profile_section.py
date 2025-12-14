from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit
from src.core.settings_page.sections.section_base import SettingsSection


class ProfileSettingsSection(SettingsSection):
    def __init__(self):
        super().__init__("Profile Settings")

        self._add_field("User name")
        self._add_field("Email")

    def _add_field(self, label_text):
        row = QHBoxLayout()

        label = QLabel(label_text)
        edit = QLineEdit()

        row.addWidget(label)
        row.addWidget(edit)

        self.layout.addLayout(row)
