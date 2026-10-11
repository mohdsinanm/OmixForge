
from src.utils.constants import INITIATE_CACHE_JSON, CONFIG_DIR, CONFIG_FILE, populate_constants
from src.utils.nfcore_utils import NfcoreUtils
from src.utils.fileops.file_handle import json_read, json_write, ensure_directory
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class InitiateApp:
    def __init__(self):
        """Initialize the application with system checks and configuration loading."""
        self.load_json_data() 
        self.docker_installed = self.check_docker_installed()
        self.nextflow_installed = self.check_nextflow_installed()     
        self.constants = populate_constants(CONFIG_FILE)  

    
    def load_json_data(self):
        """Load and cache JSON pipeline data from nfcore API."""
        logger.info("Loading initiate cache JSON data.")
        self.nfcore_utils = NfcoreUtils()
        try:
            payload = self.nfcore_utils.get_pipelines_json()
            if not isinstance(payload, dict) or not isinstance(payload.get("remote_workflows"), list):
                raise ValueError("nf-core response did not contain a workflow list")

            self.cache_json_data = payload
            ensure_directory(CONFIG_DIR)
            json_write(INITIATE_CACHE_JSON, self.cache_json_data)
            logger.info("Successfully loaded initiate cache JSON data.")
            return
        except Exception as error:
            logger.warning(f"Unable to load workflows from nf-core: {error}")

        try:
            cached_payload = json_read(INITIATE_CACHE_JSON)
            if isinstance(cached_payload, dict) and isinstance(
                cached_payload.get("remote_workflows"), list
            ):
                self.cache_json_data = cached_payload
                logger.info("Using cached nf-core workflow data.")
                return
        except (OSError, ValueError) as error:
            logger.warning(f"Could not read cached nf-core workflow data: {error}")

        self.cache_json_data = {"remote_workflows": []}
        logger.warning("Starting without remote workflows; refresh the pipeline list when online.")
        
    def check_docker_installed(self) -> bool:
        """Check if Docker is installed on the system."""
        import shutil
        docker_path = shutil.which("docker")
        if docker_path:
            logger.info(f"Docker is installed at: {docker_path}")
            return True
        else:
            logger.warning("Docker is not installed.")
            return False
        
    def check_nextflow_installed(self) -> bool:
        """Check if Nextflow is installed on the system."""
        import shutil
        nextflow_path = shutil.which("nextflow")
        if nextflow_path:
            logger.info(f"Nextflow is installed at: {nextflow_path}")
            return True
        else:
            logger.warning("Nextflow is not installed.")
            return False
                
    def generate_encrypted_file(self, data: str, filepath: str, key: bytes):
        """Encrypt and save data to a file using Fernet encryption.
        
        Parameters
        ----------
        data : str
            The plaintext data to encrypt.
        filepath : str
            Path where the encrypted file will be saved.
        key : bytes
            Fernet encryption key for encryption.
        """
        from cryptography.fernet import Fernet
        fernet = Fernet(key)
        encrypted_data = fernet.encrypt(data.encode())
        with open(filepath, 'wb') as file:
            file.write(encrypted_data)
        logger.info(f"Encrypted file generated at: {filepath}")

   