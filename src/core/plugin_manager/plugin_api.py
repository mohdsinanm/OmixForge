from abc import ABC, abstractmethod
from PyQt6.QtWidgets import QMainWindow, QWidget

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
