import time

from PyQt6.QtCore import  QObject, pyqtSignal
from src.utils.subcommands.shell import run_shell_command
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()
TRANSIENT_ERROR_MARKERS = (
    "timed out",
    "timeout",
    "temporary failure",
    "could not resolve",
    "connection reset",
    "connection refused",
    "network is unreachable",
    "tls handshake",
)

class PipelineImportWorker(QObject):
    """Worker thread to import pipeline without blocking UI."""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    import_ready = pyqtSignal(bool, str)  # (success, message)
    
    def __init__(self, pipeline_name):
        """Initialize the import worker for a specific pipeline.
        
        Parameters
        pipeline_name : str
            Name of the pipeline to import from nf-core.
        """
        super().__init__()
        self.pipeline_name = pipeline_name
    
    def run(self):
        """Import pipeline from nf-core repository."""
        try:
            # Check if pipeline already exists
            pipeline_exist = run_shell_command("nextflow list")
            if pipeline_exist is None or pipeline_exist.returncode != 0:
                details = getattr(pipeline_exist, "stderr", "") if pipeline_exist else ""
                self.import_ready.emit(
                    False,
                    "Could not check installed workflows. Verify that Nextflow is installed and available in PATH. "
                    f"{details}".strip(),
                )
                return
            if self.pipeline_name in pipeline_exist.stdout:
                self.import_ready.emit(False, "Pipeline already exists locally")
                return
            
            for attempt in range(1, 4):
                import_process = run_shell_command(
                    "nextflow pull " + f"nf-core/{self.pipeline_name}"
                )
                if import_process is not None and import_process.returncode == 0:
                    logger.info(f"Successfully imported nf-core/{self.pipeline_name}.")
                    self.import_ready.emit(True, "Imported successfully")
                    return

                stderr = getattr(import_process, "stderr", "") if import_process else ""
                details = stderr.strip() or "Nextflow could not start the import command."
                is_transient = any(
                    marker in details.casefold() for marker in TRANSIENT_ERROR_MARKERS
                )
                if is_transient and attempt < 3:
                    logger.warning(
                        f"Transient error importing nf-core/{self.pipeline_name}; retrying "
                        f"({attempt}/3): {details}"
                    )
                    time.sleep(attempt)
                    continue

                logger.error(f"Failed to import nf-core/{self.pipeline_name}: {details}")
                guidance = (
                    "Check your network connection and retry."
                    if is_transient
                    else "Verify the workflow name and your Nextflow installation, then retry."
                )
                self.import_ready.emit(
                    False,
                    f"Could not import nf-core/{self.pipeline_name}: {details} {guidance}",
                )
                return
        except Exception as e:
            logger.error(f"Error importing pipeline: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()
