from PyQt6.QtWidgets import QLabel, QWidget, QVBoxLayout, QComboBox, QScrollArea, QSizePolicy, QPushButton
from PyQt6.QtCore import QThread, QObject, pyqtSignal, Qt
from pyqtwaitingspinner import WaitingSpinner
from src.utils.nfcore_utils import NfcoreUtils
import os, subprocess

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.core.dashboard.pipeline_import_tab.import_worker import PipelineImportWorker
from src.core.dashboard.pipeline_import_tab.refresh_worker import PipelineRefreshWorker

logger = OmixForgeLogger.get_logger()



class PipelineImport(QWidget):
    """Pipeline import tab implemented as a QWidget with a vertical
    QScrollArea so content is constrained to the screen and can be
    scrolled vertically when it's larger than the available space.
    """
    
    import_successful = pyqtSignal()  # Emitted when a pipeline is successfully imported

    def __init__(self, parent=None):
        """Initialize the pipeline import tab.
        
        Parameters
        ----------
        parent : QWidget, optional
            Parent widget for this tab.
        """
        super().__init__(parent)

        self.pipelines = []
        
        # Worker threads for async operations
        self.refresh_worker = None
        self.refresh_worker_thread = None
        self.import_worker = None
        self.import_worker_thread = None
        self.refresh_spinner = None
        self.import_spinner = None
        self.active_refresh_spinner = None  # Track active refresh spinner
        self.active_import_spinner = None   # Track active import spinner

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
        
        # Mark old spinner as inactive
        self.active_refresh_spinner = None
        
        # Stop any existing worker thread and disconnect its signals
        if self.refresh_worker_thread is not None:
            if self.refresh_worker_thread.isRunning():
                try:
                    # Disconnect all signals from old worker to prevent interference
                    if self.refresh_worker is not None:
                        self.refresh_worker.pipelines_ready.disconnect()
                        self.refresh_worker.error.disconnect()
                        self.refresh_worker.finished.disconnect()
                except (RuntimeError, TypeError):
                    # Signals already disconnected or worker deleted
                    pass
                
                self.refresh_worker_thread.quit()
                # Wait longer to ensure thread stops
                if not self.refresh_worker_thread.wait(5000):
                    logger.warning("Refresh worker thread didn't stop gracefully")
        
        # Create and show spinner
        self.refresh_spinner = WaitingSpinner(self.content)
        self.refresh_spinner.start()
        self.active_refresh_spinner = self.refresh_spinner  # Track as active
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
        # Ignore signal if this spinner is no longer active
        if self.refresh_spinner is not self.active_refresh_spinner:
            logger.debug("Ignoring pipelines_ready signal for stale spinner")
            return
        
        self.pipelines = pipelines
        
        # Stop spinner
        if self.refresh_spinner:
            try:
                self.refresh_spinner.stop()
            except RuntimeError:
                logger.debug("Spinner already deleted, skipping stop()")
                return
            self.content_layout.removeWidget(self.refresh_spinner)
            self.refresh_spinner.deleteLater()
            self.refresh_spinner = None
            self.active_refresh_spinner = None
        
        # Update combo
        self.combobox.clear()
        for pipeline in self.pipelines:
            self.combobox.addItem(pipeline.name)
        
        self.btn.setText("Refresh Pipelines")
        self.btn.setEnabled(True)
        logger.info(f"Successfully loaded {len(self.pipelines)} pipelines")
    
    def _on_refresh_error(self, error_msg):
        """Handle refresh error."""
        # Ignore signal if this spinner is no longer active
        if self.refresh_spinner is not self.active_refresh_spinner:
            logger.debug("Ignoring refresh_error signal for stale spinner")
            return
        
        # Stop spinner
        if self.refresh_spinner:
            try:
                self.refresh_spinner.stop()
            except RuntimeError:
                logger.debug("Spinner already deleted, skipping stop()")
                return
            self.content_layout.removeWidget(self.refresh_spinner)
            self.refresh_spinner.deleteLater()
            self.refresh_spinner = None
            self.active_refresh_spinner = None
        
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
        self.combobox.setEnabled(False)  # Disable dropdown while importing
        self.btn.setEnabled(False)  # Disable refresh button while importing
        
        # Mark old spinner as inactive
        self.active_import_spinner = None
        
        # Stop any existing worker thread and disconnect its signals
        if self.import_worker_thread is not None:
            if self.import_worker_thread.isRunning():
                try:
                    # Disconnect all signals from old worker to prevent interference
                    if self.import_worker is not None:
                        self.import_worker.import_ready.disconnect()
                        self.import_worker.error.disconnect()
                        self.import_worker.finished.disconnect()
                except (RuntimeError, TypeError):
                    # Signals already disconnected or worker deleted
                    pass
                
                self.import_worker_thread.quit()
                # Wait longer to ensure thread stops
                if not self.import_worker_thread.wait(5000):
                    logger.warning("Import worker thread didn't stop gracefully")
        
        # Create and show spinner
        self.import_spinner = WaitingSpinner(self.content)
        self.import_spinner.start()
        self.active_import_spinner = self.import_spinner  # Track as active
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
        # Ignore signal if this spinner is no longer active
        if self.import_spinner is not self.active_import_spinner:
            logger.debug("Ignoring import_ready signal for stale spinner")
            return
        
        # Stop spinner
        if self.import_spinner:
            try:
                self.import_spinner.stop()
            except RuntimeError:
                logger.debug("Spinner already deleted, skipping stop()")
                # Continue cleanup even if spinner is already deleted
        
        self.active_import_spinner = None
        
        # Remove spinner widgets from detail_widgets
        for w in [self.import_spinner] + [w for w in self.detail_widgets if isinstance(w, QLabel) and "Importing" in (w.text() if hasattr(w, 'text') else "")]:
            if w in self.detail_widgets:
                self.detail_widgets.remove(w)
                self.content_layout.removeWidget(w)
                w.deleteLater()
        
        self.import_btn.setEnabled(True)
        self.combobox.setEnabled(True)  # Re-enable dropdown after import
        self.btn.setEnabled(True)  # Re-enable refresh button
        
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
        # Ignore signal if this spinner is no longer active
        if self.import_spinner is not self.active_import_spinner:
            logger.debug("Ignoring import_error signal for stale spinner")
            return
        
        # Stop spinner
        if self.import_spinner:
            try:
                self.import_spinner.stop()
            except RuntimeError:
                logger.debug("Spinner already deleted, skipping stop()")
                # Continue cleanup even if spinner is already deleted
        
        self.active_import_spinner = None
        
        # Remove spinner widgets
        for w in [self.import_spinner] + [w for w in self.detail_widgets if isinstance(w, QLabel) and "Importing" in (w.text() if hasattr(w, 'text') else "")]:
            if w in self.detail_widgets:
                self.detail_widgets.remove(w)
                self.content_layout.removeWidget(w)
                w.deleteLater()
        
        self.import_btn.setEnabled(True)
        self.combobox.setEnabled(True)  # Re-enable dropdown on error
        self.btn.setEnabled(True)  # Re-enable refresh button
        logger.error(f"Error importing pipeline: {error_msg}")
        self.import_btn.setText("Import Failed")