
from PyQt6.QtWidgets import QLabel, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

from src.core.status_page.status.run_status import PipelineRunStatus
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class PipelineStatus(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        tab_widget = QTabWidget()

        pipeline_status_tab = PipelineRunStatus()
        pipeline_result_tab = PipelineRunStatus()

        tab_widget.addTab(pipeline_status_tab, "Status")
        tab_widget.addTab(pipeline_result_tab, "Results")

        layout.addWidget(tab_widget)

        self.setLayout(layout)
        self.widget = self

