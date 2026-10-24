
from PyQt6.QtWidgets import QLabel, QHBoxLayout, QWidget, QVBoxLayout, QTabWidget

from src.core.dashboard.pipeline_import_tab.pipeline_import import PipelineImport
from src.core.dashboard.pipeline_dash_tab.local_pipeline import PipelineLocal
from src.core.dashboard.pipeline_editor_tab.pipeline_editor import PipelineEditorTab

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.theme_manager import theme_manager

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

        # Expose self.widget so callers (e.g. MainWindow.stack) can embed it
        self.widget = self

        self.setStyleSheet(self.get_custom_stylesheet())
        theme_manager.theme_changed.connect(self._on_theme_changed)

    @property
    def widget(self):
        return self

    @widget.setter
    def widget(self, val):
        pass

    def _on_theme_changed(self, _theme_name: str):
        self.setStyleSheet(self.get_custom_stylesheet())

    def get_custom_stylesheet(self):
        t = theme_manager.get_tokens()
        return f"""
            QWidget#pipelineDashboardRoot {{
                background-color: {t.main_bg};
                color: {t.text_primary};
                font-family: "Noto Sans";
                font-size: 13px;
            }}
            QLabel#dashboardTitle {{
                color: {t.text_heading};
                font-size: 23px;
                font-weight: 700;
            }}
            QLabel#dashboardSectionTitle {{
                color: {t.text_heading};
                font-size: 17px;
                font-weight: 700;
            }}
            QLabel#pipelineDetailTitle {{
                color: {t.text_heading};
                font-size: 15px;
                font-weight: 700;
            }}
            QTabWidget#pipelineDashboardTabs::pane {{
                background: {t.primary_content_bg};
                border: 1px solid {t.border_divider};
                border-radius: 8px;
                top: -1px;
            }}
            QTabWidget#pipelineDashboardTabs QTabBar::tab {{
                background: {t.tab_bg};
                border: 1px solid {t.tab_border};
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                color: {t.tab_fg};
                margin-right: 4px;
                padding: 10px 16px;
            }}
            QTabWidget#pipelineDashboardTabs QTabBar::tab:selected {{
                background: {t.primary_content_bg};
                border-bottom: 2px solid {t.tab_selected_border};
                color: {t.tab_selected_fg};
                font-weight: 700;
            }}
            QTabWidget#pipelineDashboardTabs QTabBar::tab:hover:!selected {{
                background: {t.tab_hover_bg};
                color: {t.tab_hover_fg};
            }}
            QLineEdit, QComboBox {{
                background: {t.input_bg};
                border: 1px solid {t.border_standard};
                border-radius: 6px;
                color: {t.text_primary};
                min-height: 20px;
                padding: 7px 9px;
                selection-background-color: {t.selection_bg};
                selection-color: {t.selection_fg};
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {t.border_focus};
            }}
            QPushButton {{
                background: {t.btn_default_bg};
                border: 1px solid {t.btn_default_border};
                border-radius: 6px;
                color: {t.btn_default_fg};
                padding: 8px 13px;
            }}
            QPushButton:hover {{
                background: {t.btn_default_hover_bg};
                border-color: {t.btn_default_hover_border};
            }}
            QPushButton:pressed {{
                background: {t.btn_default_pressed_bg};
            }}
            QPushButton:disabled {{
                background: {t.btn_default_disabled_bg};
                border-color: {t.btn_default_disabled_border};
                color: {t.btn_default_disabled_fg};
            }}
            QPushButton#dashboardPrimaryButton,
            QPushButton#import_from_url,
            QPushButton#import_selected_pipeline,
            QPushButton#pipeline_run_btn {{
                background: {t.btn_primary_bg};
                border-color: {t.btn_primary_border};
                color: {t.btn_primary_fg};
                font-weight: 700;
            }}
            QPushButton#dashboardPrimaryButton:hover,
            QPushButton#import_from_url:hover,
            QPushButton#import_selected_pipeline:hover,
            QPushButton#pipeline_run_btn:hover {{
                background: {t.btn_primary_hover_bg};
                border-color: {t.btn_primary_hover_bg};
            }}
            QPushButton#import_from_url:disabled,
            QPushButton#import_selected_pipeline:disabled,
            QPushButton#pipeline_run_btn:disabled {{
                background: {t.btn_primary_disabled_bg};
                border-color: {t.btn_primary_disabled_bg};
                color: {t.btn_primary_disabled_fg};
            }}
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QWidget#dashboardScrollContent {{
                background: transparent;
            }}
            QFrame#pipelineCard {{
                background: {t.elevated_card_bg};
                border: 1px solid {t.border_divider};
                border-radius: 8px;
            }}
            QFrame#pipelineCard:hover {{
                background: {t.hover_bg};
                border-color: {t.border_handle_hover};
            }}
            QLabel#pipelineCardName {{
                color: {t.text_heading};
                font-size: 14px;
                font-weight: 700;
            }}
            QLabel#dashboardCount {{
                color: {t.warning};
                font-size: 12px;
                font-weight: 700;
            }}
            QLabel#dashboardEmptyState {{
                background: {t.subtle_surface_bg};
                border: 1px dashed {t.border_standard};
                border-radius: 8px;
                color: {t.text_placeholder};
                padding: 28px;
            }}
            QFrame#pipeline_info_box, QFrame#pipelineEditorDetails {{
                background: {t.subtle_surface_bg};
                border: 1px solid {t.border_divider};
                border-radius: 8px;
                color: {t.text_primary};
            }}
            QFrame#pipelineImportDetails {{
                background: {t.subtle_surface_bg};
                color: {t.text_primary};
                border: 1px solid {t.border_divider};
                border-radius: 8px;
            }}
            QWidget#pipelineImportDetailsContent {{
                background: {t.subtle_surface_bg};
                color: {t.text_primary};
            }}
            QLabel#pipeline_import_status {{
                background: {t.secondary_surface_bg};
                border-left: 3px solid {t.accent_primary};
                border-radius: 4px;
                color: {t.text_heading};
                padding: 9px 11px;
            }}
        """

        # expose the widget so callers can embed this dashboard without
        # PipelineDashboard itself forcing it as the main window central widget
        self.widget = self

