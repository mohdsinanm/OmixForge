from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QFileDialog, QLabel
)

from src.core.settings_page.sections.section_base import SettingsSection

class FolderPathsSection(SettingsSection):
    def __init__(self):
        super().__init__("Folder Paths")

        self.data_dir = self._add_path_row("Data directory")
        self.run_dir = self._add_path_row("Run directory")
        self.pipeline_runs = self._add_path_row("Pipeline run directory")
        self.sample_prep_dir = self._add_path_row("Sample preperation directory")

    def _add_path_row(self, label_text):
        from PyQt6.QtWidgets import QLabel, QHBoxLayout, QLineEdit, QPushButton

        row = QHBoxLayout()
        label = QLabel(label_text)
        edit = QLineEdit()
        browse = QPushButton("Browse")

        browse.clicked.connect(lambda: self._browse_folder(edit))

        row.addWidget(label)
        row.addWidget(edit)
        row.addWidget(browse)
        self.layout.addLayout(row)

        return edit

    def get_settings(self):
        return {
            "DATA_DIR": self.data_dir.text(),
            "RUN_DIR": self.run_dir.text(),
            "PIPELINES_RUNS": self.pipeline_runs.text(),
            "SAMPLE_PREP_DIR": self.sample_prep_dir.text()
        }

    def load_settings(self, data):
        self.data_dir.setText(data.get("DATA_DIR", ""))
        self.run_dir.setText(data.get("RUN_DIR", ""))
        self.pipeline_runs.setText(data.get("PIPELINES_RUNS", ""))
        self.sample_prep_dir.setText(data.get("SAMPLE_PREP_DIR", ""))

    def _browse_folder(self, line_edit):
        path = QFileDialog.getExistingDirectory(self, "Select folder")
        if path:
            line_edit.setText(path)

