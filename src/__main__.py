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
    QLabel,
    QMessageBox,
    QSizePolicy,
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
from src.utils.theme_manager import theme_manager


class MainWindow(QMainWindow):
    def __init__(self, initiate : InitiateApp):
        """Initialize the MainWindow with configuration and UI setup.
        
        Parameters
        ----------
        initiate : InitiateApp
            Application initialization handler with system configuration.
        """
        super().__init__()
        self.setObjectName("mainWindow")

        self.initiate = initiate

        self.setWindowTitle("OmixForge")

        # Flags
        self._main_ui_loaded = False

        # App shell widgets
        self.toolbar = None
        self.sidebar = None
        self.stack = None
        self.plugin_manager = None
        self.logout_toolbar = None
        self.logout_button = None
        self.session_start_page = None
        self.session_login_page = None

        self.statusBar().hide()

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

        sb = self.statusBar()
        if sb is not None:
            sb.hide()

        self._main_ui_loaded = False

    
    def show_access_page(self):
        """Display the access mode selection page (public or private)."""
        if self._main_ui_loaded:
            if self.session_start_page is None or self.stack.indexOf(self.session_start_page) < 0:
                self.session_start_page = AccessModePage(
                    self.initiate.docker_installed,
                    self.initiate.nextflow_installed,
                )
                self.session_start_page.public_selected.connect(self.load_main_app)
                self.session_start_page.private_selected.connect(self.show_login)
                self.stack.addWidget(self.session_start_page)
            self.stack.setCurrentWidget(self.session_start_page)
            self._show_session_navigation(False)
            return

        self.cleanup_main_ui()

        self.access_page = AccessModePage(self.initiate.docker_installed , self.initiate.nextflow_installed)
        self.access_page.public_selected.connect(self.load_main_app)
        self.access_page.private_selected.connect(self.show_login)

        self.setCentralWidget(self.access_page)

    def show_login(self):
        """Display the login/signup page for private access mode."""
        if self._main_ui_loaded:
            if self.session_login_page is None or self.stack.indexOf(self.session_login_page) < 0:
                self.session_login_page = ProfilePage()
                self.session_login_page.go_back.connect(self.show_access_page)
                self.session_login_page.login_success.connect(self.load_main_app)
                self.stack.addWidget(self.session_login_page)
            self.stack.setCurrentWidget(self.session_login_page)
            self._show_session_navigation(False)
            return

        self.cleanup_main_ui()

        self.profile = ProfilePage()
        self.profile.go_back.connect(self.show_access_page)
        self.profile.login_success.connect(self.load_main_app)

        self.setCentralWidget(self.profile)

   
    def load_main_app(self):
        """Initialize and load the main application UI with all components and plugins."""
        if self._main_ui_loaded:
            app = QApplication.instance()
            credential = getattr(app, "cred", None) if app is not None else None
            if isinstance(credential, dict):
                self.pipeline_dashboard.local_pipeline_tab.attach_private_credentials(credential)
            self._clear_session_pages()
            self.stack.setCurrentWidget(self.pipeline_dashboard.widget)
            self._show_session_navigation(True)
            return 

        self._main_ui_loaded = True

        
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setObjectName("mainToolbar")
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

        self.logout_toolbar = QToolBar("Session actions", self)
        self.logout_toolbar.setObjectName("sessionActionsToolbar")
        self.logout_toolbar.setMovable(False)
        self.logout_toolbar.setAllowedAreas(Qt.ToolBarArea.TopToolBarArea)
        toolbar_spacer = QWidget(self.logout_toolbar)
        toolbar_spacer.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )
        self.logout_toolbar.addWidget(toolbar_spacer)

        # Theme toggle button (sun ↔ moon)
        self.theme_toggle_button = QPushButton(self.logout_toolbar)
        self.theme_toggle_button.setObjectName("themeToggleButton")
        self.theme_toggle_button.setIcon(QIcon(theme_manager.get_icon("theme")))
        self.theme_toggle_button.setIconSize(QSize(20, 20))
        self.theme_toggle_button.setFixedSize(42, 40)
        self.theme_toggle_button.setToolTip("Toggle dark / light mode")
        self.theme_toggle_button.setAccessibleName("Toggle theme")
        self.theme_toggle_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle_button.clicked.connect(theme_manager.toggle_theme)
        self.logout_toolbar.addWidget(self.theme_toggle_button)

        self.logout_button = QPushButton(self.logout_toolbar)
        self.logout_button.setObjectName("logoutButton")
        self.logout_button.setIcon(QIcon(theme_manager.get_icon("logout")))
        self.logout_button.setIconSize(QSize(20, 20))
        self.logout_button.setFixedSize(42, 40)
        self.logout_button.setToolTip("Log out")
        self.logout_button.setAccessibleName("Log out")
        self.logout_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.logout_button.clicked.connect(self.logout_to_startup)
        self.logout_toolbar.addWidget(self.logout_button)
        toolbar_end_spacer = QWidget(self.logout_toolbar)
        toolbar_end_spacer.setFixedWidth(8)
        self.logout_toolbar.addWidget(toolbar_end_spacer)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.logout_toolbar)

        # Update toolbar icons and badge whenever the theme changes
        theme_manager.theme_changed.connect(self._on_theme_changed)


        # back_btn = QPushButton("Back")
        # back_btn.clicked.connect(self.show_access_page)
        # self.toolbar.addWidget(back_btn)

        
        self.sidebar = QDockWidget("", self)
        self.sidebar.setObjectName("navigationDock")
        self.sidebar.setTitleBarWidget(QWidget())
        self.sidebar.setAllowedAreas(Qt.DockWidgetArea.LeftDockWidgetArea)
        self.sidebar.setFeatures(QDockWidget.DockWidgetFeature.NoDockWidgetFeatures)
        self.sidebar.setMinimumWidth(185)
        self.sidebar.setMaximumWidth(220)

        

        self.sidebar_list = QListWidget()
        self.sidebar_list.setObjectName("mainNavigation")
        self.sidebar_list.setSpacing(3)
        self.plugin_sidebar_items = {} 
        self.menu_items_head = QListWidgetItem("WORKSPACE")
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
        pipeline_status_widget.setFixedHeight(40)

        layout = QHBoxLayout(pipeline_status_widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # status_label = QLabel("Pipeline Status")
        # status_label.setFont(QFont("Arial", 10, QFont.Weight.DemiBold))
        # status_label.setStyleSheet("color: #333333;")
        # layout.addWidget(status_label)
        
        self.badge_label = QLabel()
        self.badge_label.setObjectName("pipelineStatusBadge")
        self.badge_label.setFont(QFont("Noto Sans", 8, QFont.Weight.Bold))
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.setMinimumWidth(24)
        self.badge_label.setFixedHeight(22)
        self.badge_label.setStyleSheet("""
            QLabel {
                background-color: #b74f3b;
                color: white;
                border-radius: 11px;
                padding: 0 6px;
            }
        """)
        self.badge_label.hide()  # Initially hidden
        
        layout.addStretch()
        layout.addWidget(
            self.badge_label,
            0,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        
        self.sidebar_list.setItemWidget(self.pipeline_status_item, pipeline_status_widget)
        self.pipeline_status_item.setSizeHint(QSize(0, 40))
        
        self.sidebar_list.addItem("Plugin Store")
        self.sidebar_list.addItem("Settings")
        self.sidebar_list.addItem("About")

        self.plugin_header = QListWidgetItem("PLUGINS")
        self.plugin_header.setFlags(Qt.ItemFlag.NoItemFlags) 
        self.sidebar_list.addItem(self.plugin_header)

        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        self.plugin_insert_row = self.sidebar_list.row(self.plugin_header) + 1
        self.sidebar_list.itemClicked.connect(self.list_item_clicked)
        self.sidebar_list.setCurrentRow(1)

        self.sidebar.setWidget(self.sidebar_list)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        
        self.setStatusBar(QStatusBar(self))

        
        self.pipeline_dashboard = PipelineDashboard()
        self.sample_prep_page = Sample()
        self.pipeline_status = PipelineStatus()
        self.settings_page = SettingsPage()
        self.about_page = AboutPage()

        self.plugin_manager = PluginManager()

        app = QApplication.instance()
        credential = getattr(app, "cred", None) if app is not None else None
        if isinstance(credential, dict):
            self.pipeline_dashboard.local_pipeline_tab.attach_private_credentials(credential)

        self.plugins_page = PluginsPage(self.plugin_manager)
        self.plugin_store = PluginStore(self)

        self.pipeline_status.run_status.running_jobs_count_changed.connect(self.update_pipeline_status_badge)

        # Initialize the badge
        self.update_pipeline_status_badge(self.pipeline_status.run_status.get_running_jobs_count())

        self.stack = QStackedWidget()
        self.stack.setObjectName("mainPageStack")
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

    def _on_theme_changed(self, _theme_name: str):
        """React to theme changes: refresh stylesheet, icons, and badge colors."""
        # Re-apply the global application stylesheet
        app = QApplication.instance()
        if app:
            app.setStyleSheet(global_style_sheet())

        # Update toolbar icons
        if self.logout_button:
            self.logout_button.setIcon(QIcon(theme_manager.get_icon("logout")))
        if hasattr(self, "theme_toggle_button") and self.theme_toggle_button:
            self.theme_toggle_button.setIcon(QIcon(theme_manager.get_icon("theme")))

    def _show_session_navigation(self, visible: bool):
        """Show navigation while a workspace is open; hide it on access screens."""
        for widget in (self.toolbar, self.logout_toolbar, self.sidebar):
            if widget is not None:
                widget.setVisible(visible)
        sb = self.statusBar()
        if sb is not None:
            sb.setVisible(visible)

    def _clear_session_pages(self):
        """Remove temporary access/login pages after returning to the workspace."""
        for attr in ("session_start_page", "session_login_page"):
            page = getattr(self, attr, None)
            if page is not None and self.stack.indexOf(page) >= 0:
                if attr == "session_login_page":
                    for field in ("username_input", "password_input"):
                        input_widget = getattr(page, field, None)
                        if input_widget is not None:
                            input_widget.clear()
                self.stack.removeWidget(page)
                page.deleteLater()
            setattr(self, attr, None)

    def logout_to_startup(self):
        """Return to startup after choosing how active runs should be handled."""
        local_pipeline = self.pipeline_dashboard.local_pipeline_tab
        running_processes = local_pipeline.get_active_run_names()
        private_runs = [
            run_name for run_name in running_processes
            if local_pipeline.processes.get(run_name, {}).get("metadata", {}).get("encrypted")
        ]
        app = QApplication.instance()
        private_session = bool(getattr(app, "cred", None)) if app is not None else False

        if running_processes:
            prompt = QMessageBox(self)
            prompt.setWindowTitle("Pipeline is running")
            prompt.setIcon(QMessageBox.Icon.Question)
            if private_runs and not private_session:
                prompt.setText(
                    "A private pipeline is running. Log out to return to startup, "
                    "then sign in privately to cancel it, or stay here."
                )
                logout_button = prompt.addButton(
                    "Log out to cancel from private mode", QMessageBox.ButtonRole.AcceptRole
                )
                prompt.addButton("Stay here", QMessageBox.ButtonRole.RejectRole)
                prompt.exec()
                if prompt.clickedButton() is not logout_button:
                    return
            else:
                prompt.setText(
                    f"{len(running_processes)} pipeline process(es) are running. "
                    "Choose whether to keep them running while you return to startup."
                )
                background_button = prompt.addButton(
                    "Continue in background", QMessageBox.ButtonRole.AcceptRole
                )
                cancel_button = prompt.addButton(
                    "Cancel process and log out", QMessageBox.ButtonRole.DestructiveRole
                )
                prompt.addButton("Stay here", QMessageBox.ButtonRole.RejectRole)
                prompt.exec()
                chosen = prompt.clickedButton()
                if chosen is cancel_button:
                    local_pipeline.cancel_active_runs()
                elif chosen is not background_button:
                    return

        self._complete_logout()

    def _complete_logout(self):
        """Clear session credentials and return to the access-mode screen."""
        app = QApplication.instance()
        if app is not None:
            app.cred = None
        if hasattr(self, "pipeline_status"):
            self.pipeline_status.run_status.refresh_visibility()
            self.pipeline_status.results_page.refresh_visibility()
        self.show_access_page()

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
        if self._main_ui_loaded:
            local_pipeline = self.pipeline_dashboard.local_pipeline_tab
            app = QApplication.instance()
            private_session = bool(getattr(app, "cred", None)) if app is not None else False
            running_processes = local_pipeline.get_active_run_names()
            private_runs = [
                run_name for run_name in running_processes
                if local_pipeline.processes.get(run_name, {}).get("metadata", {}).get("encrypted")
            ]
            pending_private_encryption = bool(private_runs or local_pipeline._encrypting_runs) or any(
                metadata.get("encrypted")
                for metadata, _exit_code in local_pipeline.completed_detached_runs.values()
            )

            if running_processes or pending_private_encryption:
                prompt = QMessageBox(self)
                prompt.setWindowTitle(
                    "Pipeline is running" if running_processes else "Encryption is pending"
                )
                if running_processes:
                    message = f"{len(running_processes)} pipeline process(es) are running. "
                    if private_runs and not private_session:
                        message += (
                            "Private runs cannot be cancelled from this session; "
                            "they may continue in the background."
                        )
                    else:
                        message += "Choose whether they should continue after OmixForge closes."
                else:
                    message = "Private pipeline results are still being encrypted."
                if pending_private_encryption:
                    message += (
                        "\n\nIf OmixForge closes before encryption finishes, the run data "
                        "will remain unencrypted until you reopen OmixForge and sign in "
                        "with the same private account. Encryption will then resume."
                    )
                prompt.setText(message)
                prompt.setIcon(QMessageBox.Icon.Question)
                switch_to_private_button = None
                continue_button = None
                if running_processes and private_runs and not private_session:
                    message += (
                        " Log out and cancel the private run from private mode, "
                        "or keep the app open."
                    )
                    prompt.setText(message)
                    switch_to_private_button = prompt.addButton(
                        "Log out and cancel from private mode",
                        QMessageBox.ButtonRole.AcceptRole,
                    )
                else:
                    continue_button = prompt.addButton(
                        "Close; encrypt on next login" if pending_private_encryption
                        else "Continue after closing",
                        QMessageBox.ButtonRole.AcceptRole,
                    )
                cancel_button = None
                if running_processes and (private_session or not private_runs):
                    cancel_button = prompt.addButton(
                        "Cancel runs and close", QMessageBox.ButtonRole.DestructiveRole
                    )
                prompt.addButton("Keep app open", QMessageBox.ButtonRole.RejectRole)
                prompt.exec()
                chosen = prompt.clickedButton()
                if switch_to_private_button is not None and chosen is switch_to_private_button:
                    e.ignore()
                    self._complete_logout()
                    return
                if cancel_button is not None and chosen is cancel_button:
                    local_pipeline.cancel_active_runs()
                elif chosen is not continue_button:
                    e.ignore()
                    return

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

    # Load the user's saved theme preference BEFORE creating the main window
    # so the initial palette is set and there is no flash of the wrong theme.
    theme_manager.load_saved_theme()
    app.setPalette(theme_manager.get_palette())
    app.setStyleSheet(global_style_sheet())

    initiate = InitiateApp()
    window = MainWindow(initiate)
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
