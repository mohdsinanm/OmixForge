from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QStackedWidget


class PluginsPage(QWidget):
    def __init__(self, plugin_manager):
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
        """Add plugin widget to stacked widget"""
        self.plugin_widgets[plugin_name] = widget
        self.stack.addWidget(widget)

    def show_plugin(self, plugin_name):
        widget = self.plugin_widgets.get(plugin_name)
        if widget:
            self.stack.setCurrentWidget(widget)
