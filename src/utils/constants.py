from pathlib import Path
import os
import json

APP_DIR = Path(f"/home/{os.getenv("USER")}/OmxiForge")
LOG_DIR = APP_DIR /  "OmixForge_logs"
DATA_DIR = APP_DIR / "OmixForge_data"
RUN_DIR = APP_DIR / "OmixForge_run"
PIPELINES_RUNS = DATA_DIR / "pipelines_runs"
CONFIG_DIR = APP_DIR / ".omixforge"
AUTH_DIR = CONFIG_DIR / "auth"
SAMPLE_PREP_DIR = DATA_DIR / "sample_prep"
PLUGIN_DIR = CONFIG_DIR / "plugins"


## Files
AUTH_JSON = AUTH_DIR / "auth_data.json.enc"
INITIATE_CACHE_JSON = CONFIG_DIR / "nfcore_cache.json"
CONFIG_FILE = CONFIG_DIR / "app.config"

def populate_constants(config_path):
    try:
        global DATA_DIR 
        global RUN_DIR 
        global PIPELINES_RUNS 
        global SAMPLE_PREP_DIR 

        data = {
                "folders": {
                    "DATA_DIR": str(DATA_DIR),
                    "RUN_DIR": str(RUN_DIR),
                    "PIPELINES_RUNS": str(PIPELINES_RUNS),
                    "SAMPLE_PREP_DIR": str(SAMPLE_PREP_DIR)
                },
                "profile": {},
                "app": {}
            }
        
        os.makedirs(CONFIG_DIR, exist_ok=True)
        if not os.path.exists(config_path):
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=4)


        with open(config_path, 'r') as f:
            return json.load(f)
        
    except Exception as e:
        print(e)
        return data


