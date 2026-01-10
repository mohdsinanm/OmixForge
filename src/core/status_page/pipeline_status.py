
from PyQt6.QtWidgets import QLabel, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

from src.core.status_page.status.run_status import PipelineRunStatus
from src.core.status_page.results.run_results import PipelineResultsPage
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class PipelineStatus(QWidget):
    def __init__(self):
        """Initialize the pipeline status widget with status and results tabs."""
        super().__init__()

        layout = QVBoxLayout()

        tab_widget = QTabWidget()

        pipeline_status_tab = PipelineRunStatus()
        pipeline_result_tab = PipelineResultsPage()

        tab_widget.addTab(pipeline_status_tab, "Status")
        tab_widget.addTab(pipeline_result_tab, "Results")

        layout.addWidget(tab_widget)

        self.setLayout(layout)
        self.widget = self

