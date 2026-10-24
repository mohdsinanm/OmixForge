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
            self.private_mode_button.setIcon(QIcon(resource_path("src/assets/lock.svg")))
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

        illustration = QSvgWidget(resource_path("src/assets/startup_bioinformatics.svg"))
        illustration.setObjectName("workflowIllustration")
        illustration.setMinimumSize(330, 300)
        illustration.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        illustration.setToolTip("A visual overview of a reproducible bioinformatics workflow")
        content.addWidget(illustration, 6)
        page_layout.addLayout(content, 8)
        page_layout.addStretch(1)

        footer = QHBoxLayout()
        footer.addWidget(QLabel("REPRODUCIBLE BY DESIGN"))
        footer.addStretch(1)
        footer_note = QLabel(f"v{APP_VERSION}")
        footer.addWidget(footer_note)
        page_layout.addLayout(footer)
        self.setStyleSheet(self.stylesheet())

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
        return """
        QWidget#welcomePage { background: #f4f7f5; font-family: "Noto Sans"; }
        QLabel#brandLogo { min-width: 40px; }
        QLabel#brandName { color: #111111; font-size: 13px; font-weight: 800; letter-spacing: 2px; }
        QLabel#eyebrow, QLabel#kickerLabel { color: #628078; font-size: 10px; font-weight: 700; letter-spacing: 1.6px; }
        QLabel#kickerLabel { margin-bottom: 12px; }
        QLabel#titleLabel { color: #111111; font-size: 48px; font-weight: 700; line-height: 1.1; }
        QLabel#subtitleLabel { color: #647970; font-size: 14px; line-height: 1.5; margin-top: 14px; }
        QLabel#stepNumber { color: #b26340; font-size: 10px; font-weight: 800; letter-spacing: 1px; }
        QLabel#stepName { color: #252525; font-size: 13px; font-weight: 700; }
        QLabel#stepDetail { color: #82918c; font-size: 10px; }
        QLabel#stepArrow { color: #a5b9b1; font-size: 18px; margin: 0 3px; }
        QPushButton#publicStartButton { background: #111111; border: 1px solid #111111; border-radius: 7px; color: white; font-size: 13px; font-weight: 700; padding: 0 18px; }
        QPushButton#publicStartButton:hover { background: #292929; }
        QPushButton#publicStartButton:disabled { background: #79a89f; color: #f2f7f5; }
        QToolButton#privateModeButton { background: #ffffff; border: 1px solid #d4e1dc; border-radius: 7px; color: #31564c; font-weight: 600; padding: 0 12px; }
        QToolButton#privateModeButton:hover { background: #edf6f3; border-color: #7a8580; }
        QToolButton#privateModeButton:disabled { color: #8a9a95; }
        QFrame#requirementsPanel { background: #ffffff; border: 1px solid #dbe6e2; border-radius: 8px; }
        QWidget#workflowIllustration { background: transparent; }
        """
