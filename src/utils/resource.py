import os
import sys
from pathlib import Path
from src.utils.constants import PLUGIN_DIR

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller.
    
    Parameters
    ----------
    relative_path : str
        Relative path to the resource file.
    
    Returns
    -------
    str
        Absolute path to the resource.
    """
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def get_plugins_dir() -> Path:
    """Get or create the plugins directory path.
    
    Returns
    -------
    Path
        Path object to the plugins directory.
    """
    plugins = PLUGIN_DIR
    plugins.mkdir(parents=True, exist_ok=True)
    return plugins