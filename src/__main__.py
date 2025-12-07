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
from PyQt6.QtWidgets import QStackedWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OmixForge")

        toolbar = QToolBar("My main toolbar")
        toolbar.setAllowedAreas(Qt.ToolBarArea.LeftToolBarArea)
        toolbar.setMovable(False)
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)
        icon_path = resource_path('src/assets/omixforge.png')


        # Sidebar (Dock widget)
        self.sidebar = QDockWidget("", self)
        self.sidebar.setTitleBarWidget(QWidget()) 
        self.sidebar.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea 
        )
        sidebar_widget = QListWidget()
        sidebar_widget.addItems(["Pipeline Dashboard","Sample Prep", "Pipeline Status", "Settings"])
        sidebar_widget.itemClicked.connect(self.list_item_clicked)
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setWidget(sidebar_widget)
        self.sidebar.setMaximumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        # Toggle button in toolbar
        self.toggle_sidebar_action = QAction(QIcon(icon_path), "Toggle Sidebar", self)
        self.toggle_sidebar_action.setCheckable(True)
        self.toggle_sidebar_action.setChecked(True)  # start visible
        self.toggle_sidebar_action.triggered.connect(self.toggle_sidebar)
        toolbar.addAction(self.toggle_sidebar_action)

        # Status bar
        self.setStatusBar(QStatusBar(self))

        # Create pages and keep them so state (like running processes) persists
        self.pipeline_dashboard = PipelineDashboard()
        self.pipeline_status = PipelineStatus()
        self.settings_page = SettingsPage()
        self.sample_prep_page = SamplePrepPage()

        # Stacked widget to host pages without destroying them when switching
        self.stack = QStackedWidget()
        self.stack.addWidget(self.pipeline_dashboard.widget)
        self.stack.addWidget(self.pipeline_status.widget)
        self.stack.addWidget(self.settings_page.widget)
        self.stack.addWidget(self.sample_prep_page.widget)

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