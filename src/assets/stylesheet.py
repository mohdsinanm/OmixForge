from src.utils.resource import resource_path


def global_style_sheet():
    """Return the shared visual theme for the application."""
    stylesheet = """
    QWidget {
        color: #263b36;
        font-family: "Noto Sans";
        font-size: 13px;
    }

    QMainWindow#mainWindow, QStackedWidget#mainPageStack {
        background-color: #f3f7f6;
    }

    QDialog, QMessageBox {
        background-color: #f3f7f6;
        color: #263b36;
    }

    QToolBar#mainToolbar {
        background-color: #eaf1ee;
        border: none;
        border-right: 1px solid #d8e3df;
        padding: 8px 5px;
        spacing: 5px;
    }

    QToolBar#mainToolbar QToolButton {
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 8px;
    }

    QToolBar#mainToolbar QToolButton:hover,
    QToolBar#mainToolbar QToolButton:checked {
        background-color: #d6e9e2;
    }

    QToolBar#sessionActionsToolbar {
        background-color: #eaf1ee;
        border: none;
        border-bottom: 1px solid #d8e3df;
        padding: 5px 14px;
    }

    QPushButton#logoutButton {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 6px;
        color: #111111;
        font-weight: 700;
        padding: 0;
    }

    QPushButton#logoutButton:hover {
        background-color: #dfe7e4;
        border-color: #dfe7e4;
    }

    QDockWidget#navigationDock {
        background-color: #eaf1ee;
        border: none;
    }

    QDockWidget#navigationDock::title {
        background-color: #eaf1ee;
        padding: 0;
    }

    QListWidget#mainNavigation {
        background-color: #eaf1ee;
        border: none;
        outline: none;
        padding: 12px 8px;
    }

    QListWidget#mainNavigation::item {
        border-radius: 6px;
        color: #536a63;
        margin: 2px 0;
        min-height: 40px;
        padding: 0 11px;
    }

    QListWidget#mainNavigation::item:hover {
        background-color: #e2e9e6;
        color: #263b36;
    }

    QListWidget#mainNavigation::item:selected {
        background-color: #dfe7e4;
        border-left: 3px solid #b45c32;
        color: #263b36;
        font-weight: 700;
    }

    QListWidget#mainNavigation::item:disabled {
        color: #8a9a95;
        font-size: 10px;
        font-weight: 700;
        min-height: 20px;
        padding: 12px 11px 0;
    }

    QStatusBar {
        background-color: #ffffff;
        border-top: 1px solid #dbe6e2;
        color: #657a73;
    }

    QPushButton {
        background-color: #ffffff;
        color: #31564c;
        border: 1px solid #cbdad5;
        border-radius: 6px;
        padding: 8px 13px;
        font-size: 13px;
    }

    QPushButton:hover {
        background-color: #edf6f3;
        border-color: #7a8580;
    }

    QPushButton:pressed {
        background-color: #dceee8;
    }

    QPushButton:disabled {
        color: #95a49f;
        background-color: #edf1ef;
        border-color: #d8e0dd;
    }

    QPushButton#fetchAccessionsButton,
    QPushButton#loginButton,
    QPushButton#saveSettingsButton {
        background-color: #111111;
        border-color: #111111;
        color: #ffffff;
        font-weight: 700;
    }

    QPushButton#fetchAccessionsButton:hover,
    QPushButton#loginButton:hover,
    QPushButton#saveSettingsButton:hover {
        background-color: #292929;
        border-color: #292929;
    }

    QLineEdit, QTextEdit, QPlainTextEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QDateEdit, QDateTimeEdit {
        background-color: #ffffff;
        border: 1px solid #cbdad5;
        border-radius: 6px;
        color: #263b36;
        padding: 7px 9px;
        selection-background-color: #111111;
        selection-color: #ffffff;
    }

    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus,
    QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
        border: 1px solid #111111;
    }

    QCheckBox {
        color: #263b36;
        spacing: 8px;
    }

    QCheckBox::indicator {
        background-color: #ffffff;
        border: 1px solid #9aaca5;
        border-radius: 4px;
        height: 18px;
        width: 18px;
    }

    QCheckBox::indicator:hover {
        border-color: #111111;
    }

    QCheckBox::indicator:checked {
        background-color: #111111;
        border-color: #111111;
        image: url("__CHECKMARK_PATH__");
    }

    QCheckBox::indicator:disabled {
        background-color: #edf1ef;
        border-color: #d8e0dd;
    }

    QComboBox::drop-down {
        border: none;
        padding-right: 7px;
        width: 22px;
    }

    QComboBox QAbstractItemView {
        background-color: #ffffff;
        border: 1px solid #cbdad5;
        color: #263b36;
        outline: none;
        selection-background-color: #dfe7e4;
        selection-color: #263b36;
    }

    QComboBox QAbstractItemView::item {
        min-height: 24px;
        padding: 5px 8px;
    }

    QComboBox QAbstractItemView::item:selected {
        background-color: #dfe7e4;
        color: #263b36;
    }

    QListWidget, QListView {
        alternate-background-color: #f5f9f7;
        background-color: #ffffff;
        border: 1px solid #dbe6e2;
        border-radius: 6px;
        color: #263b36;
        outline: none;
        selection-background-color: #dfe7e4;
        selection-color: #263b36;
    }

    QListWidget::item, QListView::item {
        border-radius: 4px;
        padding: 7px 9px;
    }

    QListWidget::item:selected, QListView::item:selected {
        background-color: #dfe7e4;
        color: #263b36;
    }

    QWidget#enaDownloaderContent,
    QWidget#localPipelineScrollContent,
    QWidget#pluginStorePage,
    QWidget#pluginStoreTab,
    QWidget#pluginManageTab,
    QWidget[loadedPluginRoot="true"],
    QStackedWidget#loadedPluginStack {
        background-color: #f3f7f6;
    }

    QScrollArea#pluginScrollArea {
        background-color: #f3f7f6;
        border: none;
    }

    QWidget#pluginScrollAreaContent {
        background-color: #f3f7f6;
    }

    QLabel#pipelineInfoLog {
        background-color: #ffffff;
        color: #263b36;
        padding: 10px;
    }

    QLabel#encryptedRunNotice {
        background-color: #edf3f1;
        border-left: 3px solid #778780;
        border-radius: 4px;
        color: #536a63;
        padding: 9px 11px;
    }

    QFrame#pipelineResultCard {
        background-color: #ffffff;
        border: 1px solid #dbe6e2;
        border-left: 4px solid #9aa9a3;
        border-radius: 8px;
    }

    QFrame#pipelineResultCard[state="completed"] {
        border-left-color: #19825c;
    }

    QFrame#pipelineResultCard[state="failed"] {
        border-left-color: #be5540;
    }

    QFrame#pipelineResultCard[state="cancelled"] {
        border-left-color: #778780;
    }

    QFrame#pipelineResultCard[state="running"] {
        border-left-color: #b87718;
    }

    QLabel#resultStatusBadge {
        background-color: #edf1ef;
        border-radius: 4px;
        color: #657a73;
        font-size: 11px;
        font-weight: 700;
        padding: 4px 8px;
    }

    QLabel#resultStatusBadge[state="completed"] {
        background-color: #e5f3eb;
        color: #187b58;
    }

    QLabel#resultStatusBadge[state="failed"] {
        background-color: #fcebe8;
        color: #a94935;
    }

    QLabel#resultStatusBadge[state="cancelled"] {
        background-color: #edf1ef;
        color: #657a73;
    }

    QLabel#resultStatusBadge[state="running"] {
        background-color: #fff3df;
        color: #93600f;
    }

    QLabel#resultStatusBadge[state="encrypted"] {
        background-color: #e8eef8;
        color: #49617d;
    }

    QTabWidget::pane {
        background-color: #ffffff;
        border: 1px solid #dbe6e2;
        border-radius: 8px;
        top: -1px;
    }

    QTabBar::tab {
        background-color: #e7efec;
        border: 1px solid #dbe6e2;
        border-bottom: none;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
        color: #657a73;
        margin-right: 4px;
        padding: 10px 15px;
    }

    QTabBar::tab:selected {
        background-color: #ffffff;
        border-bottom: 2px solid #111111;
        color: #111111;
        font-weight: 700;
    }

    QTabBar::tab:hover:!selected {
        background-color: #dce9e5;
        color: #284b42;
    }

    QGroupBox {
        background-color: #ffffff;
        border: 1px solid #dbe6e2;
        border-radius: 8px;
        margin-top: 12px;
        padding: 14px 12px 10px;
    }

    QGroupBox::title {
        color: #31564c;
        left: 10px;
        padding: 0 5px;
    }

    QTableWidget, QTableView, QTreeWidget, QTreeView {
        alternate-background-color: #f5f9f7;
        background-color: #ffffff;
        border: 1px solid #dbe6e2;
        border-radius: 6px;
        gridline-color: #e7eeeb;
        selection-background-color: #d8eee6;
        selection-color: #203a34;
    }

    QHeaderView::section {
        background-color: #edf3f1;
        border: none;
        border-bottom: 1px solid #dbe6e2;
        color: #536a63;
        font-weight: 700;
        padding: 8px;
    }

    QHeaderView {
        background-color: #edf3f1;
    }

    QTableCornerButton::section {
        background-color: #edf3f1;
        border: none;
        border-bottom: 1px solid #dbe6e2;
    }

    QScrollArea#runResultsScroll,
    QScrollArea#runStatusScroll {
        background-color: #f3f7f6;
        border: none;
    }

    QWidget#runResultsScrollContent,
    QWidget#runStatusScrollContent {
        background-color: #f3f7f6;
    }

    QLabel#runLogContent {
        background-color: #ffffff;
        color: #263b36;
        padding: 10px;
    }

    QScrollArea#aboutScrollArea,
    QScrollArea#pipelineEditorScroll {
        background-color: #ffffff;
        border: 1px solid #dbe6e2;
    }

    QWidget#aboutPageContent,
    QWidget#pipelineEditorScrollContent {
        background-color: #ffffff;
    }

    QScrollBar:vertical {
        background: transparent;
        margin: 2px;
        width: 10px;
    }

    QScrollBar:horizontal {
        background: transparent;
        height: 10px;
        margin: 2px;
    }

    QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
        background: #c6d5d0;
        border-radius: 4px;
        min-height: 24px;
        min-width: 24px;
    }

    QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
        background: #9db9b0;
    }

    QScrollBar::add-line, QScrollBar::sub-line {
        background: none;
        border: none;
    }

    QProgressBar {
        background-color: #e5eeea;
        border: none;
        border-radius: 5px;
        color: #31564c;
        min-height: 10px;
        text-align: center;
    }

    QProgressBar::chunk {
        background-color: #111111;
        border-radius: 5px;
    }

    QToolTip {
        background-color: #203a34;
        border: 1px solid #203a34;
        color: #ffffff;
        padding: 5px 7px;
    }

    QMenu {
        background-color: #ffffff;
        border: 1px solid #dbe6e2;
        padding: 4px;
    }

    QMenu::item {
        border-radius: 4px;
        padding: 7px 22px;
    }

    QMenu::item:selected {
        background-color: #e4f1ec;
        color: #292929;
    }
    """
    checkmark_path = resource_path("src/assets/checkmark.svg").replace("\\", "/")
    return stylesheet.replace("__CHECKMARK_PATH__", checkmark_path)


def close_button_style():
    """Return CSS stylesheet for a neutral close button.
    
    Returns
    -------
    str
        CSS stylesheet string for close button styling.
    """
    return """
    QPushButton {
        color: #536a63;
        background-color: #ffffff;
        border: 1px solid #cbdad5;
        border-radius: 6px;
        padding: 6px 9px;
        font-size: 13px;
    }

    QPushButton:hover {
        background-color: #fcebe8;
        border-color: #db9a88;
        color: #9f452d;
    }

    QPushButton:pressed {
        background-color: #f6ddd7;
    }

    QPushButton:disabled {
        color: palette(Mid);
        background-color: palette(Base);
        border: 1px solid palette(Midlight);
    }
    """
