
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget

from src.core.status_page.status.run_status import PipelineRunStatus
from src.core.status_page.results.run_results import PipelineResultsPage
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.widgets.page_header import PageHeader

logger = OmixForgeLogger.get_logger()

class PipelineStatus(QWidget):
    def __init__(self):
        """Initialize the pipeline status widget with status and results tabs."""
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(12)

        tab_widget = QTabWidget(self)
        tab_widget.setObjectName("pipelineStatusTabs")

        layout.addWidget(PageHeader("Pipeline Status", self))

        self.run_status = PipelineRunStatus()
        self.results_page = PipelineResultsPage()

        tab_widget.addTab(self.run_status, "Status")
        tab_widget.addTab(self.results_page, "Results")

        layout.addWidget(tab_widget)

        self.widget = self

