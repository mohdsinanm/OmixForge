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
from utils.resource import resource_path
from core.dashboard.pipeline_dashboard import PipelineDashboard
from core.status_page.pipeline_status import PipelineStatus
from core.settings_page.settings import SettingsPage

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
        sidebar_widget.addItems(["Pipeline Dashboard", "Pipeline Status", "Settings"])
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
        PipelineDashboard(self)

    def toggle_sidebar(self, checked):
            """Show/hide sidebar based on button state"""
            self.sidebar.setVisible(checked)


    def list_item_clicked(self, item):
        page = item.text()
        if page == 'Pipeline Dashboard':
            PipelineDashboard(self)
        elif page == 'Pipeline Status':
            PipelineStatus(self)
        elif page == "Settings":
            SettingsPage(self)
       

app = QApplication(sys.argv)

window = MainWindow()
window.showMaximized()
window.show()

app.exec()