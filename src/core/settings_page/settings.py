from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QMessageBox, QHBoxLayout, QPushButton
)

from src.core.settings_page.sections.folder_path_section import FolderPathsSection
from src.core.settings_page.sections.profile_section import ProfileSettingsSection
from src.core.settings_page.sections.app_settings_section import AppSettingsSection
from src.utils.constants import CONFIG_DIR, CONFIG_FILE, populate_constants
from src.utils.fileops.file_handle import ensure_directory, json_read, json_write, file_exists
import json


class SettingsPage(QWidget):

    def __init__(self):
        
        super().__init__()

        self.folder_section = FolderPathsSection()
        self.profile_section = ProfileSettingsSection()
        self.app_section = AppSettingsSection()

        layout = QVBoxLayout(self)

        layout.addWidget(self.folder_section)
        # TBD
        # layout.addWidget(self.profile_section)
        # layout.addWidget(self.app_section)
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_settings)

        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        self.load_settings()

        self.widget = self

    def save_settings(self):
        config = {
            "folders": self.folder_section.get_settings(),
            "profile": self.profile_section.get_settings(),
            "app": self.app_section.get_settings(),
        }

        ensure_directory(CONFIG_DIR)
        json_write(CONFIG_FILE, config)

        QMessageBox.information(self, "Settings", "Settings saved successfully. Restart the app to reflect the changes")

    def load_settings(self):
        if not file_exists(CONFIG_FILE):
            return

        data = json_read(CONFIG_FILE)

        self.folder_section.load_settings(data.get("folders", {}))
        self.profile_section.load_settings(data.get("profile", {}))
        self.app_section.load_settings(data.get("app", {}))

