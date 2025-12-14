from PyQt6.QtWidgets import QCheckBox
from src.core.settings_page.sections.section_base import SettingsSection


class AppSettingsSection(SettingsSection):
    def __init__(self):
        super().__init__("Application Settings")

        self.auto_update = QCheckBox("Enable auto updates")
        self.dark_mode = QCheckBox("Enable dark mode")
        self.confirm_exit = QCheckBox("Confirm before exit")

        self.layout.addWidget(self.auto_update)
        self.layout.addWidget(self.dark_mode)
        self.layout.addWidget(self.confirm_exit)
