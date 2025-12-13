from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
import sys

from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QWidget,
    QStatusBar,
    QToolBar,QListWidget, QDockWidget, 
)
import sys
from src.utils.resource import resource_path
from src.core.dashboard.pipeline_dashboard import PipelineDashboard
from src.core.status_page.pipeline_status import PipelineStatus
from src.core.settings_page.settings import SettingsPage
from src.core.sample.sample_prep import SamplePrepPage
from src.core.initiate import InitiateApp
from src.core.profile_page.profile import ProfilePage
from src.core.profile_page.startup_page import AccessModePage

from PyQt6.QtWidgets import QStackedWidget

CRED = {}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OmixForge")

        self.show_access_page()

    def show_login(self):
        self.profile = ProfilePage()
        self.setCentralWidget(self.profile)

        # Return to access page
        self.profile.go_back.connect(self.show_access_page)

        # On success → go to main app
        self.profile.login_success.connect(self.load_main_app)

    def show_access_page(self):
        # ALWAYS create a fresh page to avoid "wrapped C/C++ object deleted"
        self.access_page = AccessModePage()

        # reconnect signals
        self.access_page.public_selected.connect(self.load_main_app)
        self.access_page.private_selected.connect(self.show_login)

        self.setCentralWidget(self.access_page)

    def load_main_app(self):
        """Switch to full application after login."""
        toolbar = QToolBar("My main toolbar")
        toolbar.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        icon_path = resource_path('src/assets/omixforge.png')

        # Sidebar
        self.sidebar = QDockWidget("", self)
        self.sidebar.setTitleBarWidget(QWidget())
        self.sidebar.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        sidebar_widget = QListWidget()
        sidebar_widget.addItems(["Pipeline Dashboard","Sample Prep", "Pipeline Status", "Settings"])
        sidebar_widget.itemClicked.connect(self.list_item_clicked)
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setWidget(sidebar_widget)
        self.sidebar.setMaximumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        # Toggle button
        self.toggle_sidebar_action = QAction(QIcon(icon_path), "Toggle Sidebar", self)
        self.toggle_sidebar_action.setCheckable(True)
        self.toggle_sidebar_action.setChecked(True)
        self.toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        toolbar.addAction(self.toggle_sidebar_action)

        # Status bar
        self.setStatusBar(QStatusBar(self))

        # Load all pages
        self.pipeline_dashboard = PipelineDashboard()
        self.pipeline_status = PipelineStatus()
        self.settings_page = SettingsPage()
        self.sample_prep_page = SamplePrepPage()

        # Stacked pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self.pipeline_dashboard.widget)
        self.stack.addWidget(self.sample_prep_page.widget)
        self.stack.addWidget(self.pipeline_status.widget)
        self.stack.addWidget(self.settings_page.widget)

        # Switch main UI
        self.setCentralWidget(self.stack)

    def toggle_sidebar(self, checked):
            """Show/hide sidebar based on button state"""
            self.sidebar.setVisible(checked)
            


    def list_item_clicked(self, item):
        page = item.text()
        if page == 'Pipeline Dashboard':
            self.stack.setCurrentWidget(self.pipeline_dashboard.widget)
        elif page == 'Pipeline Status':
            self.stack.setCurrentWidget(self.pipeline_status.widget)
        elif page == "Settings":
            self.stack.setCurrentWidget(self.settings_page.widget)
        elif page == "Sample Prep":
            self.stack.setCurrentWidget(self.sample_prep_page.widget)
       
app = QApplication(sys.argv)
initiate = InitiateApp()
window = MainWindow()
window.showMaximized()
window.show()

app.exec()