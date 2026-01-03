import os
import sys
from pathlib import Path
from src.utils.constants import PLUGIN_DIR

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and PyInstaller """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_plugins_dir() -> Path:

    plugins = PLUGIN_DIR
    plugins.mkdir(parents=True, exist_ok=True)
    return plugins