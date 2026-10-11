from PyQt6.QtWidgets import (
    QWidget, QGridLayout, QLineEdit, QPushButton, QFileDialog, QLabel
)

from src.core.settings_page.sections.section_base import SettingsSection

class FolderPathsSection(SettingsSection):
    def __init__(self):
        super().__init__("Folder Paths")

        self.path_layout = QGridLayout()
        self.path_layout.setColumnStretch(1, 1)
        self.layout.addLayout(self.path_layout)

        self.data_dir = self._add_path_row("Data directory")
        self.run_dir = self._add_path_row("Run directory")
        self.pipeline_runs = self._add_path_row("Pipeline run directory")
        self.sample_prep_dir = self._add_path_row("Sample preperation directory")

    def _add_path_row(self, label_text):
        label = QLabel(label_text)
        edit = QLineEdit()
        browse = QPushButton("Browse")

        browse.clicked.connect(lambda: self._browse_folder(edit))

        row = self.path_layout.rowCount()
        self.path_layout.addWidget(label, row, 0)
        self.path_layout.addWidget(edit, row, 1)
        self.path_layout.addWidget(browse, row, 2)

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

