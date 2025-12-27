from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QComboBox, QScrollArea, QSizePolicy, QPushButton
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt
from pyqtwaitingspinner import WaitingSpinner
from src.utils.nfcore_utils import NfcoreUtils
import os, subprocess

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.core.dashboard.pipeline_import_tab.import_worker import PipelineImportWorker
from src.core.dashboard.pipeline_import_tab.refresh_worker import PipelineRefreshWorker

logger = OmixForgeLogger.get_logger()


class PipelineRefreshWorker(QObject):
    """Worker thread to fetch pipeline list without blocking UI."""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    pipelines_ready = pyqtSignal(list)
    
    def run(self):
        """Fetch pipelines from nf-core."""
        try:
            utils = NfcoreUtils()
            pipelines = utils.get_pipelines()
            self.pipelines_ready.emit(pipelines)
        except Exception as e:
            logger.error(f"Error refreshing pipelines: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()



class PipelineImport(QWidget):
    """Pipeline import tab implemented as a QWidget with a vertical
    QScrollArea so content is constrained to the screen and can be
    scrolled vertically when it's larger than the available space.
    """
    
    import_successful = pyqtSignal()  # Emitted when a pipeline is successfully imported

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pipelines = []
        
        # Worker threads for async operations
        self.refresh_worker = None
        self.refresh_worker_thread = None
        self.import_worker = None
        self.import_worker_thread = None
        self.refresh_spinner = None
        self.import_spinner = None

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
        self.btn.setObjectName("refersh_pipeline")
        self.content_layout.addWidget(self.btn)

        # Combo box
        self.combobox = QComboBox(parent=self.content)
        self.combobox.setObjectName("select_pipelines_box")
        self.combobox.currentIndexChanged.connect(self.current_text)
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
        """Refresh pipelines asynchronously with spinner."""
        logger.info("Refreshing nf-core pipeline list...")
        self.clear_details()
        self.btn.setText("Refreshing...")
        self.btn.setEnabled(False)
        
        # Stop any existing worker thread
        if self.refresh_worker_thread is not None:
            self.refresh_worker_thread.quit()
            self.refresh_worker_thread.wait()
        
        # Create and show spinner
        self.refresh_spinner = WaitingSpinner(self.content)
        self.refresh_spinner.start()
        self.content_layout.insertWidget(3, self.refresh_spinner)
        
        # Create worker thread
        self.refresh_worker = PipelineRefreshWorker()
        self.refresh_worker_thread = QThread()
        self.refresh_worker.moveToThread(self.refresh_worker_thread)
        
        # Connect signals
        self.refresh_worker_thread.started.connect(self.refresh_worker.run)
        self.refresh_worker.pipelines_ready.connect(self._on_pipelines_ready)
        self.refresh_worker.error.connect(self._on_refresh_error)
        self.refresh_worker.finished.connect(self.refresh_worker_thread.quit)
        
        # Start the thread
        self.refresh_worker_thread.start()
    
    def _on_pipelines_ready(self, pipelines):
        """Handle pipelines ready signal."""
        self.pipelines = pipelines
        
        # Stop spinner
        if self.refresh_spinner:
            self.refresh_spinner.stop()
            self.content_layout.removeWidget(self.refresh_spinner)
            self.refresh_spinner.deleteLater()
            self.refresh_spinner = None
        
        # Update combo
        self.combobox.clear()
        for pipeline in self.pipelines:
            self.combobox.addItem(pipeline.name)
        
        self.btn.setText("Refresh Pipelines")
        self.btn.setEnabled(True)
        logger.info(f"Successfully loaded {len(self.pipelines)} pipelines")
    
    def _on_refresh_error(self, error_msg):
        """Handle refresh error."""
        # Stop spinner
        if self.refresh_spinner:
            self.refresh_spinner.stop()
            self.content_layout.removeWidget(self.refresh_spinner)
            self.refresh_spinner.deleteLater()
            self.refresh_spinner = None
        
        self.btn.setText("Refresh Pipelines")
        self.btn.setEnabled(True)
        logger.error(f"Error refreshing pipelines: {error_msg}")

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
                self.import_btn.setObjectName("import_selected_pipeline")

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
        """Import pipeline asynchronously with spinner."""
        pipeline_name = self.combobox.currentText()
        logger.info(f"Importing nf-core/{pipeline_name}")
        
        self.import_btn.setEnabled(False)
        
        # Stop any existing worker thread
        if self.import_worker_thread is not None:
            self.import_worker_thread.quit()
            self.import_worker_thread.wait()
        
        # Create and show spinner
        self.import_spinner = WaitingSpinner(self.content)
        self.import_spinner.start()
        spinner_label = QLabel("Importing pipeline...")
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_layout.addWidget(self.import_spinner)
        self.content_layout.addWidget(spinner_label)
        self.detail_widgets.extend([self.import_spinner, spinner_label])
        
        # Create worker thread
        self.import_worker = PipelineImportWorker(pipeline_name)
        self.import_worker_thread = QThread()
        self.import_worker.moveToThread(self.import_worker_thread)
        
        # Connect signals
        self.import_worker_thread.started.connect(self.import_worker.run)
        self.import_worker.import_ready.connect(self._on_import_ready)
        self.import_worker.error.connect(self._on_import_error)
        self.import_worker.finished.connect(self.import_worker_thread.quit)
        
        # Start the thread
        self.import_worker_thread.start()
    
    def _on_import_ready(self, success, message):
        """Handle import completion."""
        # Stop spinner
        if self.import_spinner:
            self.import_spinner.stop()
        
        # Remove spinner widgets from detail_widgets
        for w in [self.import_spinner] + [w for w in self.detail_widgets if isinstance(w, QLabel) and "Importing" in (w.text() if hasattr(w, 'text') else "")]:
            if w in self.detail_widgets:
                self.detail_widgets.remove(w)
                self.content_layout.removeWidget(w)
                w.deleteLater()
        
        self.import_btn.setEnabled(True)
        
        if success:
            logger.info(f"Successfully imported pipeline: {message}")
            self.import_btn.setText("Imported Successfully")
            # Emit signal to trigger refresh in local pipeline tab
            self.import_successful.emit()
        else:
            logger.error(f"Import failed: {message}")
            self.import_btn.setText(f"Import Failed: {message}")
    
    def _on_import_error(self, error_msg):
        """Handle import error."""
        # Stop spinner
        if self.import_spinner:
            self.import_spinner.stop()
        
        # Remove spinner widgets
        for w in [self.import_spinner] + [w for w in self.detail_widgets if isinstance(w, QLabel) and "Importing" in (w.text() if hasattr(w, 'text') else "")]:
            if w in self.detail_widgets:
                self.detail_widgets.remove(w)
                self.content_layout.removeWidget(w)
                w.deleteLater()
        
        self.import_btn.setEnabled(True)
        logger.error(f"Error importing pipeline: {error_msg}")
        self.import_btn.setText("Import Failed")