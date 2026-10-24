from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QToolButton, QPushButton,
    QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtSvgWidgets import QSvgWidget

from src.core.profile_page.requirements import RequirementsNotSatisfied
from src.utils.resource import resource_path
from src.utils.widgets.loading_spinner import LoadingSpinner
from src.utils.version import APP_VERSION
from src.utils.theme_manager import theme_manager

class AccessModePage(QWidget):
    public_selected = pyqtSignal()
    private_selected = pyqtSignal()

    def __init__(self, docker_installed: bool, nextflow_installed: bool):
        """Welcome page and access-mode selector for OmixForge."""
        super().__init__()
        self.setObjectName("welcomePage")
        self._selected_mode = None

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(56, 38, 56, 30)
        page_layout.setSpacing(0)

        brand_row = QHBoxLayout()
        brand_row.setSpacing(10)
        logo = QLabel()
        logo.setObjectName("brandLogo")
        pixmap = QPixmap(resource_path("src/assets/omixforge.png"))
        if not pixmap.isNull():
            logo.setPixmap(pixmap.scaledToWidth(40, Qt.TransformationMode.SmoothTransformation))
        brand_row.addWidget(logo)
        brand_name = QLabel("OimxForge")
        brand_name.setObjectName("brandName")
        brand_row.addWidget(brand_name)
        brand_row.addStretch(1)
        eyebrow = QLabel("BIOINFORMATICS WORKFLOW STUDIO")
        eyebrow.setObjectName("eyebrow")
        brand_row.addWidget(eyebrow)
        page_layout.addLayout(brand_row)
        page_layout.addStretch(1)

        content = QHBoxLayout()
        content.setSpacing(36)
        content.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        copy = QVBoxLayout()
        copy.setSpacing(0)
        copy.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        kicker = QLabel("FROM SEQUENCE TO SCIENTIFIC INSIGHT")
        kicker.setObjectName("kickerLabel")
        copy.addWidget(kicker)

        title = QLabel("Your science,\nin motion.")
        title.setObjectName("titleLabel")
        title.setWordWrap(True)
        copy.addWidget(title)

        subtitle = QLabel(
            "Bring samples, pipelines, and results together in one calm workspace.\n"
            "Build a reproducible path from raw data to discovery."
        )
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        copy.addWidget(subtitle)

        workflow = QHBoxLayout()
        workflow.setSpacing(10)
        workflow.setContentsMargins(0, 24, 0, 26)
        for number, heading, detail in (
            ("01", "Prepare", "Samples & metadata"),
            ("02", "Execute", "Nextflow pipelines"),
            ("03", "Explore", "Outputs & results"),
        ):
            item = QVBoxLayout()
            item.setSpacing(4)
            step = QLabel(number)
            step.setObjectName("stepNumber")
            item.addWidget(step)
            name = QLabel(heading)
            name.setObjectName("stepName")
            item.addWidget(name)
            desc = QLabel(detail)
            desc.setObjectName("stepDetail")
            item.addWidget(desc)
            workflow.addLayout(item)
            if number != "03":
                arrow = QLabel("→")
                arrow.setObjectName("stepArrow")
                workflow.addWidget(arrow, alignment=Qt.AlignmentFlag.AlignTop)
        copy.addLayout(workflow)

        if docker_installed and nextflow_installed:
            actions = QHBoxLayout()
            actions.setSpacing(12)
            self.public_start_button = QPushButton("Start a workspace")
            self.public_start_button.setObjectName("publicStartButton")
            self.public_start_button.setMinimumSize(190, 48)
            self.public_start_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.public_start_button.clicked.connect(lambda: self._on_card_clicked("public"))
            actions.addWidget(self.public_start_button)

            self.private_mode_button = QToolButton()
            self.private_mode_button.setObjectName("privateModeButton")
            self.private_mode_button.setIcon(theme_manager.get_icon("lock"))
            self.private_mode_button.setIconSize(QSize(19, 19))
            self.private_mode_button.setText("  Private mode")
            self.private_mode_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
            self.private_mode_button.setMinimumSize(154, 48)
            self.private_mode_button.setCursor(Qt.CursorShape.PointingHandCursor)
            self.private_mode_button.setToolTip("Encrypted workspace; requires login")
            self.private_mode_button.setAccessibleName("Private mode (encrypted)")
            self.private_mode_button.clicked.connect(self.private_selected.emit)
            actions.addWidget(self.private_mode_button)
            actions.addStretch(1)
            copy.addLayout(actions)

            self.loading_spinner = LoadingSpinner("Preparing your workspace…", parent=self)
            copy.addWidget(self.loading_spinner)
        else:
            self.requirements_frame = QFrame()
            self.requirements_frame.setObjectName("requirementsPanel")
            req_layout = QVBoxLayout(self.requirements_frame)
            req_layout.setContentsMargins(16, 12, 16, 12)
            self.req_page = RequirementsNotSatisfied(req_layout, docker_installed, nextflow_installed)
            copy.addWidget(self.requirements_frame)

        copy.addStretch(1)
        content.addLayout(copy, 5)

        self.illustration = QSvgWidget(theme_manager.get_svg_path("startup_bioinformatics"))
        self.illustration.setObjectName("workflowIllustration")
        self.illustration.setMinimumSize(330, 300)
        self.illustration.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.illustration.setToolTip("A visual overview of a reproducible bioinformatics workflow")
        content.addWidget(self.illustration, 6)
        page_layout.addLayout(content, 8)
        page_layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("REPRODUCIBLE BY DESIGN"))
        footer.addStretch(1)
        footer_note = QLabel(f"v{APP_VERSION}")
        footer.addWidget(footer_note)
        page_layout.addLayout(footer)
        self.setStyleSheet(self.stylesheet())
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, theme_name: str):
        """Update startup page styling and assets when theme changes."""
        self.setStyleSheet(self.stylesheet())
        if hasattr(self, "private_mode_button") and self.private_mode_button:
            self.private_mode_button.setIcon(theme_manager.get_icon("lock"))
        if hasattr(self, "illustration") and self.illustration:
            self.illustration.load(theme_manager.get_svg_path("startup_bioinformatics"))

    def _on_card_clicked(self, mode: str):
        """Show the loading indicator, then emit the selected access mode."""
        self._selected_mode = mode
        self.loading_spinner.start_loading()
        self.public_start_button.setEnabled(False)
        self.private_mode_button.setEnabled(False)
        QTimer.singleShot(100, self._emit_selected_signal)

    def _emit_selected_signal(self):
        if self._selected_mode == "public":
            self.public_selected.emit()
        elif self._selected_mode == "private":
            self.private_selected.emit()

    def stylesheet(self):
        t = theme_manager.get_tokens()
        return f"""
        QWidget#welcomePage {{ background: {t.main_bg}; font-family: "Noto Sans"; }}
        QLabel#brandLogo {{ min-width: 40px; }}
        QLabel#brandName {{ color: {t.text_primary}; font-size: 13px; font-weight: 800; letter-spacing: 2px; }}
        QLabel#eyebrow, QLabel#kickerLabel {{ color: {t.accent_primary}; font-size: 10px; font-weight: 700; letter-spacing: 1.6px; }}
        QLabel#kickerLabel {{ margin-bottom: 12px; }}
        QLabel#titleLabel {{ color: {t.text_primary}; font-size: 48px; font-weight: 700; line-height: 1.1; }}
        QLabel#subtitleLabel {{ color: {t.text_secondary}; font-size: 14px; line-height: 1.5; margin-top: 14px; }}
        QLabel#stepNumber {{ color: {t.warning}; font-size: 10px; font-weight: 800; letter-spacing: 1px; }}
        QLabel#stepName {{ color: {t.text_primary}; font-size: 13px; font-weight: 700; }}
        QLabel#stepDetail {{ color: {t.text_secondary}; font-size: 10px; }}
        QLabel#stepArrow {{ color: {t.text_disabled}; font-size: 18px; margin: 0 3px; }}
        QPushButton#publicStartButton {{ background: {t.btn_primary_bg}; border: 1px solid {t.btn_primary_border}; border-radius: 7px; color: {t.btn_primary_fg}; font-size: 13px; font-weight: 700; padding: 0 18px; }}
        QPushButton#publicStartButton:hover {{ background: {t.btn_primary_hover_bg}; }}
        QPushButton#publicStartButton:disabled {{ background: {t.btn_primary_disabled_bg}; color: {t.btn_primary_disabled_fg}; }}
        QToolButton#privateModeButton {{ background: {t.btn_default_bg}; border: 1px solid {t.btn_default_border}; border-radius: 7px; color: {t.btn_default_fg}; font-weight: 600; padding: 0 12px; }}
        QToolButton#privateModeButton:hover {{ background: {t.btn_default_hover_bg}; border-color: {t.btn_default_hover_border}; }}
        QToolButton#privateModeButton:disabled {{ color: {t.btn_default_disabled_fg}; }}
        QFrame#requirementsPanel {{ background: {t.elevated_card_bg}; border: 1px solid {t.border_divider}; border-radius: 8px; }}
        QWidget#workflowIllustration {{ background: transparent; }}
        """
