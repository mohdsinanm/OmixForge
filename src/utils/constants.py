from pathlib import Path
import os

APP_DIR = Path(f"/home/{os.getenv("USER")}/OmxixForge")
LOG_DIR = APP_DIR /  "OmixForge_logs"
DATA_DIR = APP_DIR / "OmixForge_data"
RUN_DIR = APP_DIR / "OmixForge_run"
CONFIG_DIR = APP_DIR / ".omixforge"
