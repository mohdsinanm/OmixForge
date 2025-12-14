import sys
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QStatusBar,
    QToolBar,
    QListWidget,
    QDockWidget,
    QPushButton,
    QStackedWidget
)

from src.utils.resource import resource_path
from src.core.dashboard.pipeline_dashboard import PipelineDashboard
from src.core.status_page.pipeline_status import PipelineStatus
from src.core.settings_page.settings import SettingsPage
from src.core.sample.sample_prep import SamplePrepPage
from src.core.profile_page.profile import ProfilePage
from src.core.profile_page.startup_page import AccessModePage
from src.core.initiate import InitiateApp


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("OmixForge")

        # Flags
        self._main_ui_loaded = False

        # App shell widgets
        self.toolbar = None
        self.sidebar = None
        self.stack = None

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
        self.cleanup_main_ui()

        self.access_page = AccessModePage()
        self.access_page.public_selected.connect(self.load_main_app)
        self.access_page.private_selected.connect(self.show_login)

        self.setCentralWidget(self.access_page)

    def show_login(self):
        self.cleanup_main_ui()

        self.profile = ProfilePage()
        self.profile.go_back.connect(self.show_access_page)
        self.profile.login_success.connect(self.load_main_app)

        self.setCentralWidget(self.profile)

   
    def load_main_app(self):
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

        sidebar_list = QListWidget()
        sidebar_list.addItems([
            "Pipeline Dashboard",
            "Sample Prep",
            "Pipeline Status",
            "Settings"
        ])
        sidebar_list.itemClicked.connect(self.list_item_clicked)

        self.sidebar.setWidget(sidebar_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        
        self.setStatusBar(QStatusBar(self))

        
        self.pipeline_dashboard = PipelineDashboard()
        self.sample_prep_page = SamplePrepPage()
        self.pipeline_status = PipelineStatus()
        self.settings_page = SettingsPage()

        self.stack = QStackedWidget()
        self.stack.addWidget(self.pipeline_dashboard.widget)
        self.stack.addWidget(self.sample_prep_page.widget)
        self.stack.addWidget(self.pipeline_status.widget)
        self.stack.addWidget(self.settings_page.widget)

        self.setCentralWidget(self.stack)


    def toggle_sidebar(self, checked: bool):
        if self.sidebar:
            self.sidebar.setVisible(checked)

    def list_item_clicked(self, item):
        page = item.text()

        if page == "Pipeline Dashboard":
            self.stack.setCurrentWidget(self.pipeline_dashboard.widget)
        elif page == "Sample Prep":
            self.stack.setCurrentWidget(self.sample_prep_page.widget)
        elif page == "Pipeline Status":
            self.stack.setCurrentWidget(self.pipeline_status.widget)
        elif page == "Settings":
            self.stack.setCurrentWidget(self.settings_page.widget)



if __name__ == "__main__":
    app = QApplication(sys.argv)

    initiate = InitiateApp()
    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())
