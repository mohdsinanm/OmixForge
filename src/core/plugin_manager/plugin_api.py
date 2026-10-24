from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QMainWindow, QWidget

# Re-export theme_manager so plugins can access it via:
#   from src.core.plugin_manager.plugin_api import PluginBase, theme_manager
from src.utils.theme_manager import theme_manager  # noqa: F401

API_VERSION = "1.0"

class PluginBase(ABC):

    @abstractmethod
    def name(self) -> str:
        """Human readable plugin name."""
        ...

    @abstractmethod
    def api_version(self) -> str:
        """Return supported API version."""
        ...

    @abstractmethod
    def load(self, window: QMainWindow, plugin_container: QWidget):
        """Attach UI only inside plugin container"""
        ...

    @abstractmethod
    def unload(self):
        """Called when plugin unloaded."""
        ...

    def on_theme_changed(self, theme_name: str):
        """Called by PluginManager when the application theme changes.

        Override this method in your plugin to update any hardcoded colors or
        icons that are not automatically styled by the global QSS palette.

        Parameters
        ----------
        theme_name : str
            Either ``"light"`` or ``"dark"``.
        """
        pass
