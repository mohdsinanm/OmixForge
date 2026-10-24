from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QStackedWidget
from PyQt6.QtCore import Qt

from src.utils.theme_manager import theme_manager
from src.utils.widgets.page_header import PageHeader


class PluginsPage(QWidget):
    def __init__(self, plugin_manager):
        """Initialize the plugins page widget with plugin manager reference.
        
        Parameters
        ----------
        plugin_manager : PluginManager
            Manager instance to handle plugin operations.
        """
        super().__init__()
        self.setObjectName("loadedPluginPage")
        self.plugin_manager = plugin_manager
        self.plugin_widgets = {} 

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(14)

        self.page_header = PageHeader("Plugins", self)
        layout.addWidget(self.page_header)

        # Scroll area for plugin UIs – transparent so global theme controls background
        self.scroll = QScrollArea()
        self.scroll.setObjectName("pluginScrollArea")
        self.scroll.viewport().setStyleSheet("background: transparent;")
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

        # Stacked widget inside scroll – transparent background
        self.stack = QStackedWidget()
        self.stack.setObjectName("loadedPluginStack")
        self.stack.setStyleSheet("background: transparent;")
        self.scroll.setWidget(self.stack)

        theme_manager.theme_changed.connect(self._on_theme_changed)

    def add_plugin_widget(self, plugin_name, widget):
        """Register and add a plugin's widget to the plugin page.
        
        Parameters
        ----------
        plugin_name : str
            Unique name identifier for the plugin.
        widget : QWidget
            The plugin's main widget to display.
        """
        self.plugin_widgets[plugin_name] = widget
        widget.setProperty("loadedPluginRoot", True)
        widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.stack.addWidget(widget)

    def show_plugin(self, plugin_name):
        """Display the UI of the selected plugin.
        
        Parameters
        ----------
        plugin_name : str
            The name of the plugin to display.
        """
        widget = self.plugin_widgets.get(plugin_name)
        if widget:
            self.page_header.set_title(plugin_name)
            self.stack.setCurrentWidget(widget)

    def _on_theme_changed(self, _theme_name: str):
        """Keep viewport transparent after theme switches."""
        self.scroll.viewport().setStyleSheet("background: transparent;")
        self.stack.setStyleSheet("background: transparent;")
