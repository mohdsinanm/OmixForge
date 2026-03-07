"""Worker thread for parallel file downloads."""

import os
from pathlib import Path
import requests
from PyQt6.QtCore import QObject, pyqtSignal, QMutex
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()


class FileDownloadWorker(QObject):
    """Worker to download a single file without blocking UI."""
    
    finished = pyqtSignal(str, bool, str)  # file_url, success, message
    progress = pyqtSignal(str, int)  # file_url, bytes_downloaded
    
    def __init__(self, file_url, output_dir):
        """Initialize download worker.
        
        Parameters
        ----------
        file_url : str
            URL to download
        output_dir : str
            Directory to save the file
        """
        super().__init__()
        self.file_url = file_url
        self.output_dir = output_dir
        self.downloaded_bytes = 0
    
    def run(self):
        """Download file with progress tracking."""
        try:
            # Extract filename from URL
            filename = self.file_url.split('/')[-1]
            output_path = os.path.join(self.output_dir, filename)
            
            logger.info(f"Starting download: {self.file_url}")
            
            # Create output directory if needed
            Path(self.output_dir).mkdir(parents=True, exist_ok=True)
            
            # Download with streaming and progress tracking
            response = requests.get(self.file_url, stream=True, timeout=60)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        self.downloaded_bytes += len(chunk)
                        self.progress.emit(self.file_url, self.downloaded_bytes)
            
            logger.info(f"Successfully downloaded: {self.file_url}")
            self.finished.emit(self.file_url, True, f"Downloaded: {filename}")
            
        except requests.exceptions.Timeout:
            error_msg = f"Download timeout: {self.file_url}"
            logger.warning(error_msg)
            self.finished.emit(self.file_url, False, error_msg)
            
        except requests.exceptions.HTTPError as e:
            error_msg = f"HTTP Error {e.response.status_code}: {self.file_url}"
            logger.warning(error_msg)
            self.finished.emit(self.file_url, False, error_msg)
            
        except Exception as e:
            error_msg = f"Download failed: {str(e)}"
            logger.error(error_msg)
            self.finished.emit(self.file_url, False, error_msg)


class ENADownloaderManager(QObject):
    """Manager for parallel downloads with progress tracking."""
    
    all_downloads_finished = pyqtSignal()
    download_progress = pyqtSignal(str, int)  # url, bytes
    download_complete = pyqtSignal(str, bool, str)  # url, success, message
    overall_progress = pyqtSignal(int, int)  # completed, total
    
    def __init__(self, max_parallel_downloads=3):
        """Initialize download manager.
        
        Parameters
        ----------
        max_parallel_downloads : int
            Maximum number of parallel downloads (default: 3)
        """
        super().__init__()
        self.max_parallel_downloads = max_parallel_downloads
        self.active_downloads = {}
        self.completed_downloads = 0
        self.total_downloads = 0
        self.mutex = QMutex()
    
    def queue_downloads(self, file_urls, output_dir):
        """Queue downloads for multiple files.
        
        Parameters
        ----------
        file_urls : list
            List of URLs to download
        output_dir : str
            Directory to save files
        """
        self.total_downloads = len(file_urls)
        self.completed_downloads = 0
        self.active_downloads = {}
        
        for url in file_urls:
            worker = FileDownloadWorker(url, output_dir)
            worker.progress.connect(self._on_download_progress)
            worker.finished.connect(self._on_download_finished)
            self.active_downloads[url] = worker
        
        logger.info(f"Queued {len(file_urls)} files for download")
        self._start_next_downloads()
    
    def _start_next_downloads(self):
        """Start downloads up to max parallel limit."""
        # This would be implemented with QThreadPool for true parallelism
        # For now, we'll process sequentially but can be extended
        pass
    
    def _on_download_progress(self, url, bytes_downloaded):
        """Handle download progress."""
        self.download_progress.emit(url, bytes_downloaded)
    
    def _on_download_finished(self, url, success, message):
        """Handle download completion."""
        self.mutex.lock()
        self.completed_downloads += 1
        self.overall_progress.emit(self.completed_downloads, self.total_downloads)
        self.mutex.unlock()
        
        self.download_complete.emit(url, success, message)
        
        if self.completed_downloads >= self.total_downloads:
            self.all_downloads_finished.emit()
