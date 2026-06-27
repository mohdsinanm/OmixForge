import os
import sys
from pathlib import Path
from src.utils.constants import PLUGIN_DIR


def resource_path(relative_path):
    """Get an absolute path to a resource for dev, PyInstaller, and Debian installs."""
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = None

    candidates = []
    if base_path:
        candidates.append(Path(base_path))

    project_root = Path(__file__).resolve().parents[2]
    candidates.extend([project_root, Path("/usr/share/omixforge")])

    for base in candidates:
        candidate = base / relative_path
        if candidate.exists():
            return str(candidate)

    if base_path is None:
        return os.path.join(os.path.abspath("."), relative_path)
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