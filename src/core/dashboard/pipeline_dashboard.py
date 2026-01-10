
from PyQt6.QtWidgets import QLabel, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

from src.core.dashboard.pipeline_import_tab.pipeline_import import PipelineImport
from src.core.dashboard.pipeline_dash_tab.local_pipeline import PipelineLocal

from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class PipelineDashboard(QWidget):
    def __init__(self):
        """Initialize the pipeline dashboard with import and local pipeline tabs."""
        super().__init__()

        layout = QVBoxLayout()

        tab_widget = QTabWidget()

        pipeline_import_tab = PipelineImport()
        local_pipeline_tab = PipelineLocal()
        
        # Connect import success signal to refresh local pipelines
        pipeline_import_tab.import_successful.connect(local_pipeline_tab.refresh_pipelines)

        tab_widget.addTab(local_pipeline_tab, "Pipeline")
        tab_widget.addTab(pipeline_import_tab, "Import")

        layout.addWidget(tab_widget)

        self.setLayout(layout)

        # expose the widget so callers can embed this dashboard without
        # PipelineDashboard itself forcing it as the main window central widget
        self.widget = self

