
from PyQt6.QtWidgets import QLabel, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

from src.core.sample.sample_prep_tab.sample_prep import SamplePrepPage
from src.core.sample.ena_fastq_downloader_tab.ena_fastq_downloader import ENAFastqDownloader

from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class Sample(QWidget):
    def __init__(self):
        """Initialize the sample page with sample prep and ENA downloader tabs."""
        super().__init__()

        layout = QVBoxLayout()

        tab_widget = QTabWidget()

        sample_prep_tab = SamplePrepPage()
        ena_downloader = ENAFastqDownloader()
            
     

        tab_widget.addTab(sample_prep_tab, "Sample Prep")
        tab_widget.addTab(ena_downloader, "ENA Fastq Downloader")



        layout.addWidget(tab_widget)

        self.setLayout(layout)

        # expose the widget so callers can embed this dashboard without
        # PipelineDashboard itself forcing it as the main window central widget
        self.widget = self

