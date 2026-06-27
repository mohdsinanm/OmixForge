import sys
from PyQt6.QtCore import QSize, Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QStatusBar,
    QToolBar,
    QListWidget,
    QDockWidget,
    QPushButton,
    QStackedWidget,
    QListWidgetItem,
    QHBoxLayout,
    QLabel
)

from src.utils.resource import resource_path
from src.core.dashboard.pipeline_dashboard import PipelineDashboard
from src.core.status_page.pipeline_status import PipelineStatus
from src.core.settings_page.settings import SettingsPage
from src.core.sample.sample_page import Sample
from src.core.profile_page.profile import ProfilePage
from src.core.profile_page.startup_page import AccessModePage
from src.core.initiate import InitiateApp
from src.core.plugin_manager.plugin_page import PluginsPage
from src.core.plugin_manager.manager import PluginManager
from src.core.plugin_manager.plugin_installer import PluginStore
from src.core.about_page.about import AboutPage
from src.assets.stylesheet import global_style_sheet


class MainWindow(QMainWindow):
    def __init__(self, initiate : InitiateApp):
        """Initialize the MainWindow with configuration and UI setup.
        
        Parameters
        ----------
        initiate : InitiateApp
            Application initialization handler with system configuration.
        """
        super().__init__()

        self.initiate = initiate

        self.setWindowTitle("OmixForge")

        # Flags
        self._main_ui_loaded = False

        # App shell widgets
        self.toolbar = None
        self.sidebar = None
        self.stack = None
        self.plugin_manager = None

        self.show_access_page()


    def cleanup_main_ui(self):
        """Remove toolbars, dock widgets, and central widget safely"""

        # Remove toolbars
        for tb in self.findChildren(QToolBar):
            self.removeToolBar(tb)
            tb.deleteLater()

        # Remove dock widgets
        for dock in self.findChildren(QDockWidget):
            self.removeDockWidget(dock)
            dock.deleteLater()

        # Remove central widget
        cw = self.centralWidget()
        if cw:
            cw.deleteLater()
            self.setCentralWidget(None)

        self._main_ui_loaded = False

    
    def show_access_page(self):
        """Display the access mode selection page (public or private)."""
        self.cleanup_main_ui()

        self.access_page = AccessModePage(self.initiate.docker_installed , self.initiate.nextflow_installed)
        self.access_page.public_selected.connect(self.load_main_app)
        self.access_page.private_selected.connect(self.show_login)

        self.setCentralWidget(self.access_page)

    def show_login(self):
        """Display the login/signup page for private access mode."""
        self.cleanup_main_ui()

        self.profile = ProfilePage()
        self.profile.go_back.connect(self.show_access_page)
        self.profile.login_success.connect(self.load_main_app)

        self.setCentralWidget(self.profile)

   
    def load_main_app(self):
        """Initialize and load the main application UI with all components and plugins."""
        if self._main_ui_loaded:
            return 

        self._main_ui_loaded = True

        
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea)
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(self.toolbar)

        icon_path = resource_path("src/assets/omixforge.png")

        toggle_sidebar_action = QAction(QIcon(icon_path), "Toggle Sidebar", self)
        toggle_sidebar_action.setCheckable(True)
        toggle_sidebar_action.setChecked(True)
        toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        self.toolbar.addAction(toggle_sidebar_action)

        # back_btn = QPushButton("Back")
        # back_btn.clicked.connect(self.show_access_page)
        # self.toolbar.addWidget(back_btn)

        
        self.sidebar = QDockWidget("", self)
        self.sidebar.setTitleBarWidget(QWidget())
        self.sidebar.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setMaximumWidth(200)

        

        self.sidebar_list = QListWidget()
        self.plugin_sidebar_items = {} 
        self.menu_items_head = QListWidgetItem("Menu\n")
        self.menu_items_head.setFlags(Qt.ItemFlag.NoItemFlags) 
        self.sidebar_list.addItem(self.menu_items_head)
        
        # Add items one by one to handle custom widgets
        self.sidebar_list.addItem("Pipeline Dashboard")
        self.sidebar_list.addItem("Sample Prep")
        
        # Pipeline Status with custom badge widget
        self.pipeline_status_item = QListWidgetItem("Pipeline Status")
        self.sidebar_list.addItem(self.pipeline_status_item)
        
        # Create custom widget for Pipeline Status badge
        pipeline_status_widget = QWidget()
        pipeline_status_widget.setStyleSheet("background: transparent;")
        pipeline_status_widget.setFixedHeight(24)

        layout = QHBoxLayout(pipeline_status_widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # status_label = QLabel("Pipeline Status")
        # status_label.setFont(QFont("Arial", 10, QFont.Weight.DemiBold))
        # status_label.setStyleSheet("color: #333333;")
        # layout.addWidget(status_label)
        
        self.badge_label = QLabel()
        self.badge_label.setFont(QFont("Arial", 8, QFont.Weight.Bold))
        self.badge_label.setStyleSheet("""
            QLabel {
                background-color: #dc3545;
                color: white;
                border-radius: 8px;
                padding: 2px 6px;
                min-width: 18px;
                qproperty-alignment: AlignCenter;
            }
        """)
        self.badge_label.hide()  # Initially hidden
        
        layout.addStretch()
        layout.addWidget(self.badge_label)
        
        self.sidebar_list.setItemWidget(self.pipeline_status_item, pipeline_status_widget)
        self.pipeline_status_item.setSizeHint(QSize(0, 24))
        
        self.sidebar_list.addItem("Plugin Store")
        self.sidebar_list.addItem("Settings")
        self.sidebar_list.addItem("About")

        self.plugin_header = QListWidgetItem("\nPlugins\n")
        self.plugin_header.setFlags(Qt.ItemFlag.NoItemFlags) 
        self.sidebar_list.addItem(self.plugin_header)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        self.plugin_insert_row = self.sidebar_list.row(self.plugin_header) + 1
        self.sidebar_list.itemClicked.connect(self.list_item_clicked)

        self.sidebar.setWidget(self.sidebar_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        
        self.setStatusBar(QStatusBar(self))

        
        self.pipeline_dashboard = PipelineDashboard()
        self.sample_prep_page = Sample()
        self.pipeline_status = PipelineStatus()
        self.settings_page = SettingsPage()
        self.about_page = AboutPage()

        self.plugin_manager = PluginManager()

        self.plugins_page = PluginsPage(self.plugin_manager)
        self.plugin_store = PluginStore(self)

        self.pipeline_status.run_status.running_jobs_count_changed.connect(self.update_pipeline_status_badge)

        # Initialize the badge
        self.update_pipeline_status_badge(self.pipeline_status.run_status.get_running_jobs_count())

        self.stack = QStackedWidget()
        self.stack.addWidget(self.pipeline_dashboard.widget)
        self.stack.addWidget(self.sample_prep_page.widget)
        self.stack.addWidget(self.pipeline_status.widget)
        self.stack.addWidget(self.plugins_page)     # plugin page in stack
        self.stack.addWidget(self.settings_page.widget)
        self.stack.addWidget(self.plugin_store.widget)
        self.stack.addWidget(self.about_page.widget)

        self.setCentralWidget(self.stack)

        self.plugin_manager.load_all(self)
        
        # Hide loading dialog after main app finishes loading
        QTimer.singleShot(500, self._hide_loading_spinner)

    def _hide_loading_spinner(self):
        """Hide the loading spinner after main app has loaded."""
        try:
            if hasattr(self, 'access_page') and self.access_page:
                if hasattr(self.access_page, 'loading_spinner'):
                    self.access_page.loading_spinner.stop_loading()
        except RuntimeError:
            # Widget may have been deleted
            pass

    def closeEvent(self, e):
        """Handle window close event and perform plugin cleanup.
        
        Parameters
        ----------
        e : QCloseEvent
            The close event object.
        """
        if self.plugin_manager:
            self.plugin_manager.unload_all()
        super().closeEvent(e)

    def add_plugin_sidebar_item(self, name: str):
        """Add a plugin item to the sidebar menu.
        
        Parameters
        ----------
        name : str
            The display name of the plugin.
        """
        item = QListWidgetItem(f"  {name}")
        item.setData(Qt.ItemDataRole.UserRole, ("plugin", name))
        self.sidebar_list.insertItem(self.plugin_insert_row, item)
        self.plugin_insert_row += 1

    def update_pipeline_status_badge(self, count):
        """Update the Pipeline Status sidebar badge."""
        if count > 0:
            self.badge_label.setText(str(count))
            self.badge_label.show()
        else:
            self.badge_label.hide()


    def toggle_sidebar(self, checked: bool):
        """Toggle the visibility of the sidebar dock widget.
        
        Parameters
        ----------
        checked : bool
            True to show sidebar, False to hide it.
        """
        if self.sidebar:
            self.sidebar.setVisible(checked)

    def list_item_clicked(self, item):
        """Handle sidebar menu item selection and switch pages accordingly.
        
        Parameters
        ----------
        item : QListWidgetItem
            The clicked menu item.
        """
        role = item.data(Qt.ItemDataRole.UserRole)

        if not role:
            page = item.text()
            if page == "Pipeline Dashboard":
                self.stack.setCurrentWidget(self.pipeline_dashboard.widget)
            elif page == "Sample Prep":
                self.stack.setCurrentWidget(self.sample_prep_page.widget)
            elif page.startswith("Pipeline Status"):
                self.stack.setCurrentWidget(self.pipeline_status.widget)
            elif page == "Settings":
                self.stack.setCurrentWidget(self.settings_page.widget)
            elif page == "Plugin Store":
                self.stack.setCurrentWidget(self.plugin_store.widget)
            elif page == "About":
                self.stack.setCurrentWidget(self.about_page.widget)

        else:
            role_type, plugin_name = role
            if role_type == "plugin":
                self.stack.setCurrentWidget(self.plugins_page)
                self.plugins_page.show_plugin(plugin_name)


def main():
    app = QApplication(sys.argv)

    app.setStyleSheet(global_style_sheet())

    initiate = InitiateApp()
    window = MainWindow(initiate)
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
