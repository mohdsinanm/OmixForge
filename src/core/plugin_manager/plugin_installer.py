from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget\
)
from src.core.plugin_manager.manager import PluginManager
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.core.plugin_manager.plugin_installer_tabs.manage_tab import ManageTab
from src.core.plugin_manager.plugin_installer_tabs.store_tab import StoreTab
from src.utils.widgets.page_header import PageHeader

logger = OmixForgeLogger.get_logger()


class PluginStore(QWidget):
    def __init__(self, main_window):
        """
        main_window: reference to MainWindow
        """
        super().__init__()
        self.setObjectName("pluginStorePage")
        self.main_window = main_window
        self.plugin_manager: PluginManager = main_window.plugin_manager

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(14)
        layout.addWidget(PageHeader("Plugin Store", self))

        # Tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        self.store_tab = StoreTab(self)
        self.manage_tab = ManageTab(self)

        self.tab_widget.addTab(self.store_tab, "Store")
        self.tab_widget.addTab(self.manage_tab, "Manage")

        # Initial refresh
        self.manage_tab.refresh_installed_plugins()

        self.widget = self

