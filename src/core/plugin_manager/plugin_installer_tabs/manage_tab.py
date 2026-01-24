from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton,
    QLabel, QMessageBox,
)
from src.utils.resource import get_plugins_dir
from src.core.plugin_manager.manager import PluginManager
from src.utils.logger_module.omix_logger import OmixForgeLogger
from pathlib import Path
logger = OmixForgeLogger.get_logger()


class ManageTab(QWidget):
    """Show installed plugins and allow removing them"""

    def __init__(self, store: "PluginStore"):
        """Initialize the manage plugins tab.
        
        Parameters
        ----------
        store : PluginStore
            The plugin store instance for accessing plugins.
        """
        super().__init__()
        self.store = store
        self.plugin_manager: PluginManager = store.plugin_manager

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        layout.addWidget(QLabel("Installed plugins:"))
        layout.addWidget(self.list_widget)

        remove_btn = QPushButton("Remove Selected Plugin")
        remove_btn.clicked.connect(self.remove_selected)
        layout.addWidget(remove_btn)

        self.plugins_dir = get_plugins_dir()

    def refresh_installed_plugins(self):
        """Refresh the list of installed plugins in the manage tab."""
        self.list_widget.clear()
        installed = [f.name for f in self.plugins_dir.glob("*.py")]
        self.list_widget.addItems(installed)

    def remove_selected(self):
        """Remove the selected plugin from the installed plugins list."""
        selected = self.list_widget.currentItem()
        if not selected:
            return

        file_name = selected.text() 
        plugin_file = self.plugins_dir / file_name

        if not plugin_file.exists():
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Remove",
            f"Are you sure you want to remove {file_name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        try:
            plugin_manager = self.store.plugin_manager
            plugins_page = self.store.main_window.plugins_page

            # Get plugin object BEFORE deleting file
            plugin = None
            plugin_display_name = None

            for p in list(plugin_manager.plugins.values()):
                if hasattr(p, "file_path") and Path(p.file_path).name == file_name:
                    plugin = p
                    plugin_display_name = p.name()
                    break

            # Delete file
            plugin_file.unlink()
            logger.info(f"Removed plugin file: {file_name}")

            #  Fully unload plugin
            if plugin:
                try:
                    plugin.unload()
                except Exception as e:
                    logger.error(f"Error unloading {plugin_display_name}: {e}")

                plugin_manager.loaded_plugins = [
                    p for p in plugin_manager.loaded_plugins if p is not plugin
                ]

                plugin_manager.plugins.pop(plugin_display_name, None)

                # Remove widget
                widget = plugins_page.plugin_widgets.pop(plugin_display_name, None)
                if widget:
                    if plugins_page.stack.currentWidget() == widget:
                        plugins_page.stack.setCurrentWidget(QWidget())
                    widget.setParent(None)
                    widget.deleteLater()

                # Remove sidebar item (NOW using the display name)
                self.store.main_window.remove_plugin_sidebar_item(plugin_display_name)

            # Refresh list
            self.refresh_installed_plugins()

        except Exception as e:
            logger.error(f"Failed to remove plugin {file_name}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to remove plugin: {e}")
