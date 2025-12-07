import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from src.utils.constants import LOG_DIR

class OmixForgeLogger:
    _logger = None

    @staticmethod
    def get_logger(name: str = "OmixForge"):
        """
        Returns a global logger instance.
        Creates it on first use.
        """
        if OmixForgeLogger._logger:
            return OmixForgeLogger._logger

        # Ensure log directory exists
        log_dir = LOG_DIR
        os.makedirs(log_dir, exist_ok=True)
    

        log_file = log_dir / "OmixForge.log"

        # Logger setup
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.propagate = False   # prevent duplicate logs

        # ---- Console Handler ----
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # ---- Rotating File Handler ----
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,   # 5 MB per file
            backupCount=3              # keep 3 backups
        )
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] "
            "%(filename)s:%(lineno)d - %(message)s"
        )

        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        # Add handlers once
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        OmixForgeLogger._logger = logger
        return logger
