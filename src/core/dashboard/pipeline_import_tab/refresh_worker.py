from PyQt6.QtCore import  QObject, pyqtSignal
from src.utils.nfcore_utils import NfcoreUtils

from src.utils.logger_module.omix_logger import OmixForgeLogger

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

