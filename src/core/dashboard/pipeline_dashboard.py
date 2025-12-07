
from PyQt6.QtWidgets import QLabel, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

from src.core.dashboard.pipeline_import_tab.pipeline_import import PipelineImport
from src.core.dashboard.pipeline_dash_tab.local_pipeline import PipelineLocal

from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class PipelineDashboard(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        tab_widget = QTabWidget()

        pipeline_import_tab = PipelineImport()
        local_pipeline_tab = PipelineLocal()

        tab_widget.addTab(local_pipeline_tab, "Pipeline")
        tab_widget.addTab(pipeline_import_tab, "Import")

        layout.addWidget(tab_widget)

        self.setLayout(layout)

        # expose the widget so callers can embed this dashboard without
        # PipelineDashboard itself forcing it as the main window central widget
        self.widget = self

