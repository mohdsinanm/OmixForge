from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QStackedWidget


class PluginsPage(QWidget):
    def __init__(self, plugin_manager):
        """Initialize the plugins page widget with plugin manager reference.
        
        Parameters
        ----------
        plugin_manager : PluginManager
            Manager instance to handle plugin operations.
        """
        super().__init__()
        self.plugin_manager = plugin_manager
        self.plugin_widgets = {} 

        layout = QVBoxLayout(self)

        # Scroll area for plugin UIs
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

        # Stacked widget inside scroll
        self.stack = QStackedWidget()
        self.scroll.setWidget(self.stack)

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
            self.stack.setCurrentWidget(widget)
