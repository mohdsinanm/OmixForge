
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget, QVBoxLayout, QTabWidget

from src.core.dashboard.pipeline_import_tab.pipeline_import import PipelineImport
from src.core.dashboard.pipeline_dash_tab.local_pipeline import PipelineLocal
from src.core.dashboard.pipeline_editor_tab.pipeline_editor import PipelineEditorTab

from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class PipelineDashboard(QWidget):
    def __init__(self):
        """Initialize the pipeline dashboard with import and local pipeline tabs."""
        super().__init__()
        self.setObjectName("pipelineDashboardRoot")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 18, 22, 22)
        layout.setSpacing(14)

        header = QWidget(self)
        header.setObjectName("dashboardHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(2, 0, 2, 2)
        title = QLabel("Pipeline workspace", header)
        title.setObjectName("dashboardTitle")
        header_layout.addWidget(title)
        header_layout.addStretch()
        layout.addWidget(header)

        tab_widget = QTabWidget(self)
        tab_widget.setObjectName("pipelineDashboardTabs")

        self.pipeline_import_tab = PipelineImport()
        self.local_pipeline_tab = PipelineLocal()
        self.pipeline_editor_tab = PipelineEditorTab()
        
        # Connect import success signal to refresh local pipelines
        self.pipeline_import_tab.import_successful.connect(self.local_pipeline_tab.refresh_pipelines)

        tab_widget.addTab(self.local_pipeline_tab, "Pipeline")
        tab_widget.addTab(self.pipeline_import_tab, "Import")
        tab_widget.addTab(self.pipeline_editor_tab, "Pipeline Editor")

        layout.addWidget(tab_widget, 1)

        self.setStyleSheet("""
            QWidget#pipelineDashboardRoot {
                background-color: #f3f7f6;
                color: #203a34;
                font-family: "Noto Sans";
                font-size: 13px;
            }
            QLabel#dashboardTitle {
                color: #193b34;
                font-size: 23px;
                font-weight: 700;
            }
            QLabel#dashboardSectionTitle {
                color: #203a34;
                font-size: 17px;
                font-weight: 700;
            }
            QLabel#pipelineDetailTitle {
                color: #203a34;
                font-size: 15px;
                font-weight: 700;
            }
            QTabWidget#pipelineDashboardTabs::pane {
                background: #ffffff;
                border: 1px solid #dbe6e2;
                border-radius: 8px;
                top: -1px;
            }
            QTabWidget#pipelineDashboardTabs QTabBar::tab {
                background: #e7efec;
                border: 1px solid #dbe6e2;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                color: #657a73;
                margin-right: 4px;
                padding: 10px 16px;
            }
            QTabWidget#pipelineDashboardTabs QTabBar::tab:selected {
                background: #ffffff;
                border-bottom: 2px solid #087f70;
                color: #087f70;
                font-weight: 700;
            }
            QTabWidget#pipelineDashboardTabs QTabBar::tab:hover:!selected {
                background: #dce9e5;
                color: #284b42;
            }
            QLineEdit, QComboBox {
                background: #ffffff;
                border: 1px solid #cbdad5;
                border-radius: 6px;
                color: #203a34;
                min-height: 20px;
                padding: 7px 9px;
                selection-background-color: #087f70;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 1px solid #087f70;
            }
            QPushButton {
                background: #ffffff;
                border: 1px solid #cbdad5;
                border-radius: 6px;
                color: #31564c;
                padding: 8px 13px;
            }
            QPushButton:hover {
                background: #edf6f3;
                border-color: #79b6a8;
            }
            QPushButton:pressed {
                background: #dceee8;
            }
            QPushButton:disabled {
                background: #edf1ef;
                border-color: #d8e0dd;
                color: #95a49f;
            }
            QPushButton#dashboardPrimaryButton,
            QPushButton#import_from_url,
            QPushButton#import_selected_pipeline,
            QPushButton#pipeline_run_btn {
                background: #087f70;
                border-color: #087f70;
                color: #ffffff;
                font-weight: 700;
            }
            QPushButton#dashboardPrimaryButton:hover,
            QPushButton#import_from_url:hover,
            QPushButton#import_selected_pipeline:hover,
            QPushButton#pipeline_run_btn:hover {
                background: #066b60;
                border-color: #066b60;
            }
            QScrollArea {
                background: transparent;
                border: none;
            }
            QWidget#dashboardScrollContent {
                background: transparent;
            }
            QFrame#pipelineCard {
                background: #ffffff;
                border: 1px solid #dbe6e2;
                border-radius: 8px;
            }
            QFrame#pipelineCard:hover {
                background: #f1f8f5;
                border-color: #66a99a;
            }
            QLabel#pipelineCardName {
                color: #203a34;
                font-size: 14px;
                font-weight: 700;
            }
            QLabel#dashboardCount {
                color: #b45c32;
                font-size: 12px;
                font-weight: 700;
            }
            QLabel#dashboardEmptyState {
                background: #f7faf9;
                border: 1px dashed #cbdad5;
                border-radius: 8px;
                color: #71847d;
                padding: 28px;
            }
            QFrame#pipeline_info_box, QFrame#pipelineEditorDetails {
                background: #f7faf9;
                border: 1px solid #dbe6e2;
                border-radius: 8px;
            }
            QLabel#pipeline_import_status {
                background: #edf6f3;
                border-left: 3px solid #087f70;
                border-radius: 4px;
                color: #31564c;
                padding: 9px 11px;
            }
        """)

        # expose the widget so callers can embed this dashboard without
        # PipelineDashboard itself forcing it as the main window central widget
        self.widget = self

