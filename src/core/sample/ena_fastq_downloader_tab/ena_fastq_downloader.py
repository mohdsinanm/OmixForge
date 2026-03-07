"""ENA FASTQ Downloader Tab - Main UI Component"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, 
    QScrollArea, QFrame, QProgressBar, QFileDialog, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QTabWidget, QCheckBox
)
from PyQt6.QtCore import Qt, QThread, QThreadPool, pyqtSignal, QTimer, QRunnable, pyqtSlot, QObject
from PyQt6.QtGui import QFont, QColor
from pyqtwaitingspinner import WaitingSpinner

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.core.sample.ena_fastq_downloader_tab.ena_fetcher_worker import ENAFetcherWorker
from src.utils.widgets.loading_spinner import LoadingSpinner

logger = OmixForgeLogger.get_logger()


class DownloadSignals(QObject):
    """Signals for file download worker."""
    progress = pyqtSignal(str, int)
    finished = pyqtSignal(str, bool, str)
    error = pyqtSignal(str, str)


class DownloadWorkerThread(QRunnable):
    """Runnable for parallel file downloads."""
    
    def __init__(self, file_url, output_dir, should_cancel_func=None):
        super().__init__()
        self.file_url = file_url
        self.output_dir = output_dir
        self.signals = DownloadSignals()
        self.should_cancel_func = should_cancel_func
    
    @pyqtSlot()
    def run(self):
        """Download a file."""
        import requests
        from pathlib import Path
        
        try:
            # Check if download was cancelled before starting
            if self.should_cancel_func and self.should_cancel_func():
                self.signals.finished.emit(self.file_url, False, "Download cancelled")
                return
            
            filename = self.file_url.split('/')[-1]
            output_path = os.path.join(self.output_dir, filename)
            
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            
            response = requests.get(self.file_url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    # Check if cancelled during download
                    if self.should_cancel_func and self.should_cancel_func():
                        f.close()
                        if os.path.exists(output_path):
                            os.remove(output_path)
                        self.signals.finished.emit(self.file_url, False, "Download cancelled")
                        return
                    
                    if chunk:
                        f.write(chunk)
            
            self.signals.finished.emit(self.file_url, True, f"Downloaded: {filename}")
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            self.signals.finished.emit(self.file_url, False, error_msg)


class ENAFastqDownloader(QWidget):
    """Main ENA FASTQ Downloader tab widget."""
    
    def __init__(self):
        """Initialize the ENA FASTQ Downloader tab."""
        super().__init__()
        
        self.fetcher_worker = None
        self.fetcher_thread = None
        self.thread_pool = QThreadPool.globalInstance()
        self.thread_pool.setMaxThreadCount(3)  # Max 3 parallel downloads
        
        self.successful_results = []
        self.failed_accessions = []
        self.selected_downloads = []
        
        # Download state tracking
        self.is_downloading = False
        self.active_download_workers = []
        self.should_cancel_downloads = False
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the user interface."""
        # Create outer layout for the widget
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)
        
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        # Create content widget and layout
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Title
        title = QLabel("ENA FASTQ Downloader")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        main_layout.addWidget(title)
        
        # Instructions
        instructions = QLabel(
            "Paste accession numbers (one per line) or upload a file with accession IDs.\n"
            "Supported formats: SRR, ERR, DRR accession numbers"
        )
        instructions.setStyleSheet("color: #666; font-size: 11px;")
        main_layout.addWidget(instructions)
        
        # Input section
        input_label = QLabel("Accession List:")
        input_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        main_layout.addWidget(input_label)
        
        # Text area for pasting accessions
        self.accession_input = QTextEdit()
        self.accession_input.setPlaceholderText(
            "Paste accession numbers here (one per line)...\n\n"
            "Example:\nSRR10376955\nSRR10376956"
        )
        self.accession_input.setMaximumHeight(120)
        main_layout.addWidget(self.accession_input)
        
        # Button row
        button_layout = QHBoxLayout()
        
        upload_btn = QPushButton("Upload File")
        upload_btn.clicked.connect(self._upload_accession_file)
        button_layout.addWidget(upload_btn)
        
        clear_btn = QPushButton("Clear")
        clear_btn.clicked.connect(self.accession_input.clear)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        fetch_btn = QPushButton("Fetch Accessions")
        fetch_btn.setStyleSheet(
            "QPushButton { background-color: #4a90e2; color: white; "
            "padding: 8px 20px; border-radius: 5px; font-weight: bold; }"
            "QPushButton:hover { background-color: #357abd; }"
        )
        fetch_btn.clicked.connect(self._on_fetch_clicked)
        button_layout.addWidget(fetch_btn)
        
        main_layout.addLayout(button_layout)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
        
        # Results section
        results_title = QLabel("Fetch Results")
        results_title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        results_title.setVisible(False)
        self.results_title = results_title
        main_layout.addWidget(results_title)
        
        # Status frame
        status_frame = QFrame()
        status_frame.setStyleSheet("background-color: #f5f5f5; border-radius: 5px; padding: 10px;")
        status_frame.setVisible(False)
        self.status_frame = status_frame
        status_layout = QHBoxLayout(status_frame)
        
        self.successful_label = QLabel("Successful: 0")
        self.successful_label.setStyleSheet("color: #27ae60; font-weight: bold;")
        status_layout.addWidget(self.successful_label)
        
        self.failed_label = QLabel("Failed: 0")
        self.failed_label.setStyleSheet("color: #e74c3c; font-weight: bold;")
        status_layout.addWidget(self.failed_label)
        
        status_layout.addStretch()
        main_layout.addWidget(status_frame)
        
        # Results table
        results_label = QLabel("Successful Accessions:")
        results_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        results_label.setVisible(False)
        self.results_label = results_label
        main_layout.addWidget(results_label)
        
        # Results table with checkbox column
        results_btn_layout = QHBoxLayout()
        select_all_btn = QPushButton("Select All")
        select_all_btn.setVisible(False)
        self.select_all_btn = select_all_btn
        select_all_btn.clicked.connect(self._select_all_results)
        results_btn_layout.addWidget(select_all_btn)
        
        deselect_all_btn = QPushButton("Deselect All")
        deselect_all_btn.setVisible(False)
        self.deselect_all_btn = deselect_all_btn
        deselect_all_btn.clicked.connect(self._deselect_all_results)
        results_btn_layout.addWidget(deselect_all_btn)
        results_btn_layout.addStretch()
        main_layout.addLayout(results_btn_layout)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Download", "Accession", "Sample", "Organism", "Files", "Status"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.results_table.setMinimumHeight(250)  # Show at least 5 rows
        self.results_table.setVisible(False)
        main_layout.addWidget(self.results_table, 1)  # Add stretch factor to allow expansion
        
        # Failed accessions
        failed_section_label = QLabel("Failed Accessions:")
        failed_section_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        failed_section_label.setVisible(False)
        self.failed_section_label = failed_section_label
        main_layout.addWidget(failed_section_label)
        
        self.failed_table = QTableWidget()
        self.failed_table.setColumnCount(2)
        self.failed_table.setHorizontalHeaderLabels(["Accession", "Error"])
        self.failed_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.failed_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.failed_table.setMinimumHeight(150)  # Show at least 3-4 rows
        self.failed_table.setVisible(False)
        main_layout.addWidget(self.failed_table, 1)  # Add stretch factor to allow expansion
        
        # Download section
        download_label = QLabel("Download Files:")
        download_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        download_label.setVisible(False)
        self.download_label = download_label
        main_layout.addWidget(download_label)
        
        # Download progress
        self.download_progress_label = QLabel("Ready to download")
        self.download_progress_label.setVisible(False)
        main_layout.addWidget(self.download_progress_label)
        
        self.download_progress_bar = QProgressBar()
        self.download_progress_bar.setVisible(False)
        main_layout.addWidget(self.download_progress_bar)
        
        # Download button row
        download_btn_layout = QHBoxLayout()
        download_btn_layout_widget = QWidget()
        download_btn_layout_widget.setLayout(download_btn_layout)
        download_btn_layout_widget.setVisible(False)
        self.download_btn_layout_widget = download_btn_layout_widget
        
        self.download_all_btn = QPushButton("Download Selected Files")
        self.download_all_btn.setEnabled(False)
        self.download_all_btn.setStyleSheet(
            "QPushButton { padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:disabled { opacity: 0.5; }"
        )
        self.download_all_btn.clicked.connect(self._on_download_all_clicked)
        download_btn_layout.addWidget(self.download_all_btn)
        
        self.cancel_download_btn = QPushButton("Cancel Download")
        self.cancel_download_btn.setEnabled(False)
        self.cancel_download_btn.setStyleSheet(
            "QPushButton { padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:disabled { opacity: 0.5; }"
        )
        self.cancel_download_btn.clicked.connect(self._on_cancel_download)
        download_btn_layout.addWidget(self.cancel_download_btn)
        
        self.output_dir_btn = QPushButton("Select Download Folder")
        self.output_dir_btn.setEnabled(False)
        self.output_dir_btn.setStyleSheet(
            "QPushButton { padding: 8px 20px; border-radius: 5px; }"
            "QPushButton:disabled { opacity: 0.5; }"
        )
        self.output_dir_btn.clicked.connect(self._select_download_folder)
        download_btn_layout.addWidget(self.output_dir_btn)
        
        self.output_dir_label = QLabel("No folder selected")
        self.output_dir_label.setStyleSheet("color: #666;")
        download_btn_layout.addWidget(self.output_dir_label)
        
        main_layout.addWidget(download_btn_layout_widget)
        main_layout.addStretch()
        
        # Set content widget in scroll area
        scroll_area.setWidget(content_widget)
        
        # Add scroll area to outer layout
        outer_layout.addWidget(scroll_area)
        
        
        # Create fixed fetch progress panel (stays at bottom, doesn't scroll)
        fetch_progress_panel = QFrame()
        fetch_progress_panel.setStyleSheet("background-color: #f9f9f9; border-top: 1px solid #ddd;")
        fetch_progress_panel.setVisible(False)
        self.fetch_progress_panel = fetch_progress_panel
        fetch_progress_layout = QVBoxLayout(fetch_progress_panel)
        fetch_progress_layout.setContentsMargins(15, 10, 15, 10)
        fetch_progress_layout.setSpacing(5)
        
        fetch_status_label = QLabel("Fetching accessions...")
        fetch_status_label.setStyleSheet("font-weight: bold; color: #333;")
        self.fetch_status_label = fetch_status_label
        fetch_progress_layout.addWidget(fetch_status_label)
        
        fetch_progress_bar = QProgressBar()
        fetch_progress_bar.setMaximumHeight(20)
        self.fetch_progress_bar = fetch_progress_bar
        fetch_progress_layout.addWidget(fetch_progress_bar)
        
        outer_layout.addWidget(fetch_progress_panel)
        
        # Store output directory
        self.output_dir = None
    
    def _upload_accession_file(self):
        """Handle file upload for accession list."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Accession File",
            "",
            "Text Files (*.txt);;CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                self.accession_input.setText(content)
                logger.info(f"Loaded accessions from file: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {e}")
                logger.error(f"Failed to load accession file: {e}")
    
    def _on_fetch_clicked(self):
        """Start fetching accession data."""
        accession_text = self.accession_input.toPlainText().strip()
        
        if not accession_text:
            QMessageBox.warning(self, "Input Error", "Please enter or upload accession numbers")
            return
        
        # Parse accessions
        accessions = [line.strip() for line in accession_text.split('\n') if line.strip()]
        
        if not accessions:
            QMessageBox.warning(self, "Input Error", "No valid accession numbers found")
            return
        
        logger.info(f"Starting fetch for {len(accessions)} accessions")
        self._fetch_accessions(accessions)
    
    def _fetch_accessions(self, accessions):
        """Fetch data for accessions from ENA API."""
        # Show fixed progress panel
        self.fetch_progress_panel.setVisible(True)
        
        # Create worker thread
        self.fetcher_worker = ENAFetcherWorker(accessions)
        self.fetcher_thread = QThread()
        self.fetcher_worker.moveToThread(self.fetcher_thread)
        
        # Connect signals
        self.fetcher_thread.started.connect(self.fetcher_worker.run)
        self.fetcher_worker.fetch_progress.connect(
            lambda c, t: self._update_fetch_progress(c, t)
        )
        self.fetcher_worker.result_ready.connect(
            lambda s, f: self._on_fetch_complete(s, f)
        )
        self.fetcher_worker.error.connect(
            lambda e: self._on_fetch_error(e)
        )
        self.fetcher_worker.finished.connect(self.fetcher_thread.quit)
        self.fetcher_worker.finished.connect(self.fetcher_worker.deleteLater)
        
        self.fetcher_thread.start()
    
    def _update_fetch_progress(self, current, total):
        """Update fetch progress."""
        # Update fixed progress bar
        self.fetch_progress_bar.setMaximum(total)
        self.fetch_progress_bar.setValue(current)
        self.fetch_status_label.setText(f"Fetching accession {current}/{total}...")
    
    def _on_fetch_complete(self, successful_results, failed_accessions):
        """Handle fetch completion."""
        try:
            # Hide fixed progress panel
            self.fetch_progress_panel.setVisible(False)
            
            self.successful_results = successful_results
            self.failed_accessions = failed_accessions
            
            self._populate_results_tables()
            self._enable_download_options()
            
            logger.info(f"Fetch complete: {len(successful_results)} successful, {len(failed_accessions)} failed")
            
        except Exception as e:
            logger.error(f"Error displaying results: {e}")
    
    def _on_fetch_error(self, error_msg):
        """Handle fetch error."""
        # Hide fixed progress panel
        self.fetch_progress_panel.setVisible(False)
        QMessageBox.critical(self, "Fetch Error", f"Failed to fetch accessions:\n{error_msg}")
        logger.error(f"Fetch error: {error_msg}")
    
    def _populate_results_tables(self):
        """Populate the results tables."""
        # Clear existing rows
        self.results_table.setRowCount(0)
        self.failed_table.setRowCount(0)
        
        # Show results section
        self.results_title.setVisible(True)
        self.status_frame.setVisible(True)
        self.results_label.setVisible(True)
        self.select_all_btn.setVisible(True)
        self.deselect_all_btn.setVisible(True)
        self.results_table.setVisible(True)
        
        # Show download section
        self.download_label.setVisible(True)
        self.download_progress_label.setVisible(True)
        self.download_btn_layout_widget.setVisible(True)
        
        # Populate successful results
        for result in self.successful_results:
            row_pos = self.results_table.rowCount()
            self.results_table.insertRow(row_pos)
            
            accession = result['accession']
            data = result['data']
            num_files = len(result['fastq_urls'])
            
            # Checkbox (download column) - checked by default
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.results_table.setCellWidget(row_pos, 0, checkbox)
            
            # Accession
            item = QTableWidgetItem(accession)
            self.results_table.setItem(row_pos, 1, item)
            
            # Sample
            sample = data.get('sample_accession', 'N/A')
            item = QTableWidgetItem(sample)
            self.results_table.setItem(row_pos, 2, item)
            
            # Organism
            organism = data.get('scientific_name', 'N/A')
            item = QTableWidgetItem(organism)
            self.results_table.setItem(row_pos, 3, item)
            
            # Files
            item = QTableWidgetItem(str(num_files))
            self.results_table.setItem(row_pos, 4, item)
            
            # Status
            status_item = QTableWidgetItem("✓ Ready")
            status_item.setForeground(QColor("#27ae60"))
            self.results_table.setItem(row_pos, 5, status_item)
        
        # Populate failed accessions only if there are any
        if self.failed_accessions:
            self.failed_section_label.setVisible(True)
            self.failed_table.setVisible(True)
            
            for accession, error in self.failed_accessions:
                row_pos = self.failed_table.rowCount()
                self.failed_table.insertRow(row_pos)
                
                item = QTableWidgetItem(accession)
                self.failed_table.setItem(row_pos, 0, item)
                
                error_item = QTableWidgetItem(error)
                error_item.setForeground(QColor("#e74c3c"))
                self.failed_table.setItem(row_pos, 1, error_item)
        else:
            # Hide failed section if no failures
            self.failed_section_label.setVisible(False)
            self.failed_table.setVisible(False)
        
        # Update status labels
        self.successful_label.setText(f"Successful: {len(self.successful_results)}")
        self.failed_label.setText(f"Failed: {len(self.failed_accessions)}")
    
    def _select_all_results(self):
        """Select all checkboxes in results table."""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(True)
    
    def _deselect_all_results(self):
        """Deselect all checkboxes in results table."""
        for row in range(self.results_table.rowCount()):
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(False)
    
    def _enable_download_options(self):
        """Enable download options if there are successful results and no download in progress."""
        has_results = len(self.successful_results) > 0
        can_download = has_results and not self.is_downloading
        self.download_all_btn.setEnabled(can_download)
        self.output_dir_btn.setEnabled(can_download)
    
    def _select_download_folder(self):
        """Select output directory for downloads."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Download Folder",
            os.path.expanduser("~")
        )
        
        if folder:
            self.output_dir = folder
            self.output_dir_label.setText(folder)
            logger.info(f"Output directory selected: {folder}")
    
    def _on_download_all_clicked(self):
        """Start downloading all selected files."""
        if not self.output_dir:
            QMessageBox.warning(
                self,
                "Folder Not Selected",
                "Please select a download folder first"
            )
            return
        
        # Collect selected file URLs
        all_urls = []
        for row in range(self.results_table.rowCount()):
            # Get checkbox from first column
            checkbox = self.results_table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                # Find the corresponding result by accession
                accession_item = self.results_table.item(row, 1)
                if accession_item:
                    accession = accession_item.text()
                    # Find matching result and get its URLs
                    for result in self.successful_results:
                        if result['accession'] == accession:
                            all_urls.extend(result['fastq_urls'])
                            break
        
        if not all_urls:
            QMessageBox.warning(self, "No Files", "No files selected for download")
            return
        
        logger.info(f"Starting download of {len(all_urls)} files to {self.output_dir}")
        
        # Mark download as in progress
        self.is_downloading = True
        self.active_download_workers = []
        
        # Disable buttons during download
        self.download_all_btn.setEnabled(False)
        self.output_dir_btn.setEnabled(False)
        self.cancel_download_btn.setEnabled(True)
        
        # Show progress
        self.download_progress_bar.setVisible(True)
        self.download_progress_bar.setMaximum(len(all_urls))
        self.download_progress_bar.setValue(0)
        self.download_progress_label.setText(f"Downloading 0/{len(all_urls)} files...")
        
        # Start downloads in thread pool
        self.active_downloads = len(all_urls)
        self.completed_downloads = 0
        self.should_cancel_downloads = False
        
        for url in all_urls:
            worker = DownloadWorkerThread(url, self.output_dir, lambda: self.should_cancel_downloads)
            worker.signals.finished.connect(self._on_file_download_finished)
            self.active_download_workers.append(worker)
            self.thread_pool.start(worker)
    
    def _on_file_download_finished(self, url, success, message):
        """Handle file download completion."""
        # Only process if still downloading (not cancelled)
        if not self.is_downloading:
            return
        
        self.completed_downloads += 1
        self.download_progress_bar.setValue(self.completed_downloads)
        
        status = "✓" if success else "✗"
        self.download_progress_label.setText(
            f"Downloading {self.completed_downloads}/{self.active_downloads} files... {status} {message}"
        )
        
        if success:
            logger.info(f"Downloaded: {url}")
        else:
            logger.warning(f"Failed to download {url}: {message}")
        
        # Check if all downloads are complete
        if self.completed_downloads >= self.active_downloads:
            self._downloads_complete()
    
    def _on_cancel_download(self):
        """Cancel the current download operation."""
        logger.info("User initiated download cancellation")
        
        # Signal workers to stop
        self.should_cancel_downloads = True
        
        # Clear active workers and mark as not downloading
        self.is_downloading = False
        self.active_download_workers = []
        
        # Re-enable buttons
        self.download_all_btn.setEnabled(True)
        self.output_dir_btn.setEnabled(True)
        self.cancel_download_btn.setEnabled(False)
        
        # Reset progress display
        self.download_progress_bar.setVisible(False)
        self.download_progress_label.setText("Cancelled")
        
        # Show cancellation message
        QMessageBox.information(
            self,
            "Download Cancelled",
            "Download operation has been cancelled."
        )
    
    def _downloads_complete(self):
        """Handle completion of all downloads."""
        # Mark as not downloading
        self.is_downloading = False
        self.active_download_workers = []
        
        # Re-enable buttons
        self.download_all_btn.setEnabled(True)
        self.output_dir_btn.setEnabled(True)
        self.cancel_download_btn.setEnabled(False)
        
        self.download_progress_label.setText(
            f"Download complete! All {self.active_downloads} files downloaded."
        )
        QMessageBox.information(
            self,
            "Download Complete",
            f"Successfully downloaded {self.active_downloads} files to:\n{self.output_dir}"
        )
        logger.info(f"All downloads complete to {self.output_dir}")
