from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QPushButton,
    QLabel, QMessageBox, QLineEdit
)
from src.utils.resource import get_plugins_dir
import requests
from PyQt6.QtCore import Qt
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.core.plugin_manager.plugin_installer_tabs.lib_imports import *
from src.utils.constants import PLUGINS_API_URL

logger = OmixForgeLogger.get_logger()

class StoreTab(QWidget):
    """Fetch plugins from public GitHub repo with search functionality"""

    def __init__(self, store: "PluginStore"):
        super().__init__()
        self.store = store

        layout = QVBoxLayout(self)

        # Search bar
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search plugins...")
        self.search_input.textChanged.connect(self.filter_plugins)
        layout.addWidget(self.search_input)

        # Plugin list
        self.list_widget = QListWidget()
        layout.addWidget(QLabel("Available plugins:"))
        layout.addWidget(self.list_widget)

        # Install button
        self.install_button = QPushButton("Install Selected Plugin")
        self.install_button.clicked.connect(self.install_selected)
        layout.addWidget(self.install_button)

        self.plugins_dir = get_plugins_dir()
        self.available_plugins = []       # Full list
        self.filtered_plugins = []        # Filtered by search

        self.fetch_available_plugins()

    def fetch_available_plugins(self):
        """Fetch plugin files from GitHub repo"""
        try:
            api_url = PLUGINS_API_URL
            r = requests.get(api_url)
            r.raise_for_status()
            contents = r.json()
            self.available_plugins = [f['name'] for f in contents if f['name'].endswith(".py") and f['name'] !='check_plugins.py']
            self.filtered_plugins = self.available_plugins.copy()
            self.update_list()
        except Exception as e:
            logger.error(f"Failed to fetch plugins: {e}")
            QMessageBox.warning(self, "Error", f"Failed to fetch plugins: {e}")

    def update_list(self):
        """Update QListWidget with filtered plugins"""
        self.list_widget.clear()
        self.list_widget.addItems(self.filtered_plugins)

    def filter_plugins(self, text: str):
        """Filter available plugins based on search input"""
        text = text.lower()
        self.filtered_plugins = [p for p in self.available_plugins if text in p.lower()]
        self.update_list()

    def install_selected(self):
        selected = self.list_widget.currentItem()
        if not selected:
            return
        plugin_name = selected.text()
        dest_file = self.plugins_dir / plugin_name

        if dest_file.exists():
            QMessageBox.information(self, "Already Installed", f"{plugin_name} is already installed.")
            return

        try:
            url = f"https://raw.githubusercontent.com/mohdsinanm/OmixForge-plugins/main/{plugin_name}"
            r = requests.get(url)
            r.raise_for_status()
            dest_file.write_bytes(r.content)
            QMessageBox.information(self, "Installed", f"{plugin_name} installed successfully.")
            logger.info(f"Installed plugin: {plugin_name}")

            # --- Load only the newly installed plugin ---
            plugin = self.store.plugin_manager._load_plugin_file(dest_file)
            plugin.load(self.store.main_window, self.store.main_window.plugins_page)

            # Add to plugin manager dict
            self.store.plugin_manager.plugins[plugin.name()] = plugin
            self.store.plugin_manager.loaded_plugins.append(plugin)

            # Add to sidebar if not present
            sidebar = self.store.main_window.sidebar_list
            existing_names = [
                sidebar.item(i).data(Qt.ItemDataRole.UserRole)[1]
                for i in range(sidebar.count())
                if sidebar.item(i).data(Qt.ItemDataRole.UserRole)
            ]
            if plugin.name() not in existing_names:
                self.store.main_window.add_plugin_sidebar_item(plugin.name())

            # Refresh Manage tab
            self.store.manage_tab.refresh_installed_plugins()

        except Exception as e:
            logger.error(f"Failed to install plugin {plugin_name}: {e}")
            QMessageBox.warning(self, "Error", f"Failed to install plugin: {e}")

