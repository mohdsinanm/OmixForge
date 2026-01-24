from PyQt6.QtCore import  QObject, pyqtSignal
from src.utils.subcommands.shell import run_shell_command
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

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
            pipeline_exist  = run_shell_command("nextflow list")
            if self.pipeline_name in pipeline_exist.stdout:
                self.import_ready.emit(False, "Pipeline already exists locally")
                return
            
            # Import pipeline
            import_process = run_shell_command("nextflow pull " + f"nf-core/{self.pipeline_name}")
            if import_process.returncode == 0:
                logger.info(f"Successfully imported nf-core/{self.pipeline_name}.")
                self.import_ready.emit(True, "Imported successfully")
            else:
                logger.error(f"Failed to import nf-core/{self.pipeline_name}: {import_process.stderr}")
                self.import_ready.emit(False, f"Import failed: {import_process.stderr}")
        except Exception as e:
            logger.error(f"Error importing pipeline: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()
