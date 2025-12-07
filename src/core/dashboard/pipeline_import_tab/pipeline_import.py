from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QComboBox, QScrollArea, QSizePolicy, QPushButton
from src.utils.nfcore_utils import NfcoreUtils
import os, subprocess

from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()


class PipelineImport(QWidget):
    """Pipeline import tab implemented as a QWidget with a vertical
    QScrollArea so content is constrained to the screen and can be
    scrolled vertically when it's larger than the available space.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pipelines = []

        # Main layout for this widget (contains the scroll area)
        self.main_layout = QVBoxLayout(self)

        # Content widget that lives inside the scroll area
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)

        # Header label
        label = QLabel("This Pipeline import tab")
        self.content_layout.addWidget(label)

        # Refresh button
        self.btn = QPushButton("Refresh Pipelines", parent=self.content)
        self.btn.clicked.connect(self.refresh_pipelines)
        self.content_layout.addWidget(self.btn)

        # Combo box
        self.combobox = QComboBox(parent=self.content)
        self.combobox.activated.connect(self.current_text)
        self.content_layout.addWidget(self.combobox)

        # Container to keep track of dynamically-added detail widgets
        self.detail_widgets = []

        # Set up scroll area so the content fits the screen and scrolls vertically
        self.scroll = QScrollArea(parent=self)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.content)
        self.scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # Add scroll area to main layout
        self.main_layout.addWidget(self.scroll)

    def refresh_pipelines(self):
        # clear any shown details while we refresh
        logger.info("Refreshing nf-core pipeline list...")
        self.clear_details()
        self.btn.setText("Refreshing...")
        utils = NfcoreUtils()
        self.pipelines = utils.get_pipelines()

        # Update combo
        self.combobox.clear()
        for pipeline in self.pipelines:
            self.combobox.addItem(pipeline.name)
        self.btn.setText("Refresh Pipelines")

    def current_text(self, _):  # We receive the index, but don't use it.
        # Clear previous detail widgets so new selection doesn't duplicate
        self.clear_details()

        ctext = self.combobox.currentText()
        if not ctext:
            # nothing selected -> show nothing
            return

        for pipeline in self.pipelines:
            if pipeline.name == ctext:
                # create and track detail labels so we can clear them later
                self.pipeline_name = QLabel(f"Name: {pipeline.name}")
                self.full_name = QLabel(f"Full Name: {pipeline.full_name}")
                self.description = QLabel(f"Description: {pipeline.description}")
                self.description.setWordWrap(True)
                self.topics = QLabel(f"Topics: {', '.join(pipeline.topics)}")
                self.topics.setWordWrap(True)
                self.archived = QLabel(f"Archived: {pipeline.archived}")

                self.import_btn = QPushButton("Import Pipelines", parent=self.content)
                self.import_btn.clicked.connect(self.import_pipeline)

                for w in (
                    self.pipeline_name,
                    self.full_name,
                    self.description,
                    self.topics,
                    self.archived,
                    self.import_btn
                ):
                    self.content_layout.addWidget(w)
                    self.detail_widgets.append(w)
                return

        # If we get here no matching pipeline found -> show nothing
        return

    def clear_details(self):
        """Remove previously-added detail widgets from the layout and delete them."""
        while self.detail_widgets:
            w = self.detail_widgets.pop()
            try:
                self.content_layout.removeWidget(w)
            except Exception:
                pass
            w.deleteLater()
    
    def import_pipeline(self):
        logger.info(f"Importing nf-core/{self.combobox.currentText()}")   
        try:
            pipeline_exist = subprocess.run(["nextflow", "list"],stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True)
            if (self.combobox.currentText() in pipeline_exist.stdout):
                logger.info(f"Pipeline nf-core/{self.combobox.currentText()} already exists locally.")
                self.import_btn.setText("Imported Already Exists")
                return
            import_process = subprocess.run(["nextflow", "pull", f"nf-core/{self.combobox.currentText()}",], stdout=subprocess.PIPE,stderr=subprocess.PIPE, text=True)
            if import_process.returncode == 0:
                logger.info(f"Successfully imported nf-core/{self.combobox.currentText()}.")
                self.import_btn.setText("Imported Successfully")
            else:
                logger.error(f"Failed to import nf-core/{self.combobox.currentText()}: {import_process.stderr}")
        except Exception as e:
            logger.error(f"Error importing pipeline: {e}")