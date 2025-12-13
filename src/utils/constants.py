from pathlib import Path
import os

APP_DIR = Path(f"/home/{os.getenv("USER")}/OmxixForge")
LOG_DIR = APP_DIR /  "OmixForge_logs"
DATA_DIR = APP_DIR / "OmixForge_data"
RUN_DIR = APP_DIR / "OmixForge_run"
PIPELINES_RUNS = DATA_DIR / "pipelines_runs"
CONFIG_DIR = APP_DIR / ".omixforge"
AUTH_DIR = CONFIG_DIR / "auth"
SAMPLE_PREP_DIR = DATA_DIR / "sample_prep"


## Files
AUTH_JSON = AUTH_DIR / "auth_data.json.enc"
INITIATE_CACHE_JSON = CONFIG_DIR / "nfcore_cache.json"
