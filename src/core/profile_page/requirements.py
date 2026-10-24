from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QSizePolicy,
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

from src.utils.theme_manager import theme_manager


class RequirementsNotSatisfied(QWidget):
    """Inline requirements-missing notice that blends into the startup page typography."""

    def __init__(self, docker_installed: bool, nextflow_installed: bool, parent=None):
        super().__init__(parent)
        self.setObjectName("requirementsSection")
        self._docker = docker_installed
        self._nextflow = nextflow_installed
        self._build_ui()
        self._apply_styles()
        theme_manager.theme_changed.connect(self._apply_styles)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 110, 0, 0)
        layout.setSpacing(0)

        # ── Kicker ────────────────────────────────────────────────────
        self._kicker = QLabel("BEFORE YOU START")
        self._kicker.setObjectName("reqKicker")
        layout.addWidget(self._kicker)

        # ── Heading ───────────────────────────────────────────────────
        self._heading = QLabel("Set up your environment")
        self._heading.setObjectName("reqHeading")
        layout.addWidget(self._heading)

        layout.addSpacing(4)

        # ── Subtitle ──────────────────────────────────────────────────
        self._subtitle = QLabel(
            "OmixForge needs Docker and Nextflow to run bioinformatics pipelines."
        )
        self._subtitle.setObjectName("reqSubtitle")
        self._subtitle.setWordWrap(True)
        layout.addWidget(self._subtitle)

        layout.addSpacing(18)

        # ── Status rows ───────────────────────────────────────────────
        for name, installed in (("Docker", self._docker), ("Nextflow", self._nextflow)):
            layout.addWidget(self._make_status_row(name, installed))
            layout.addSpacing(8)

        layout.addSpacing(10)

        # ── Action row ────────────────────────────────────────────────
        actions = QHBoxLayout()
        actions.setContentsMargins(0, 0, 0, 0)
        actions.setSpacing(12)

        self._doc_btn = QPushButton("View installation guide")
        self._doc_btn.setObjectName("reqDocButton")
        self._doc_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._doc_btn.clicked.connect(self._open_docs)
        self._doc_btn.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        actions.addWidget(self._doc_btn)

        self._hint = QLabel("Then restart OmixForge.")
        self._hint.setObjectName("reqHint")
        actions.addWidget(self._hint)
        actions.addStretch(1)

        layout.addLayout(actions)

    def _make_status_row(self, name: str, installed: bool) -> QWidget:
        """Return a compact inline status row: ● Docker  [Installed / Missing]"""
        row = QWidget()
        row.setObjectName("reqRow")
        h = QHBoxLayout(row)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(10)

        # Dot indicator
        dot = QLabel()
        dot.setObjectName("reqDotOk" if installed else "reqDotMissing")
        dot.setFixedSize(8, 8)

        # Dependency name
        name_lbl = QLabel(name)
        name_lbl.setObjectName("reqDepName")

        # Status chip
        status_lbl = QLabel("Installed" if installed else "Not found")
        status_lbl.setObjectName("reqChipOk" if installed else "reqChipMissing")

        h.addWidget(dot, alignment=Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(name_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        h.addWidget(status_lbl, alignment=Qt.AlignmentFlag.AlignVCenter)
        h.addStretch(1)

        return row

    # ------------------------------------------------------------------
    # Styles
    # ------------------------------------------------------------------
    def _apply_styles(self):
        t = theme_manager.get_tokens()
        self.setStyleSheet(f"""
            QWidget#requirementsSection {{ background: transparent; }}
            QWidget#reqRow {{ background: transparent; }}

            QLabel#reqKicker {{
                color: {t.warning};
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 1.6px;
                margin-bottom: 6px;
            }}
            QLabel#reqHeading {{
                color: {t.text_primary};
                font-size: 22px;
                font-weight: 700;
            }}
            QLabel#reqSubtitle {{
                color: {t.text_secondary};
                font-size: 13px;
                line-height: 1.4;
            }}

            /* Dot indicators */
            QLabel#reqDotOk {{
                background: {t.success};
                border-radius: 4px;
            }}
            QLabel#reqDotMissing {{
                background: {t.error};
                border-radius: 4px;
            }}

            /* Dependency name */
            QLabel#reqDepName {{
                color: {t.text_primary};
                font-size: 13px;
                font-weight: 600;
                min-width: 80px;
            }}

            /* Status chips */
            QLabel#reqChipOk {{
                color: {t.success};
                background: transparent;
                font-size: 11px;
                font-weight: 600;
            }}
            QLabel#reqChipMissing {{
                color: {t.error};
                background: transparent;
                font-size: 11px;
                font-weight: 600;
            }}

            /* Doc button — ghost style matching privateModeButton */
            QPushButton#reqDocButton {{
                background: {t.btn_default_bg};
                border: 1px solid {t.btn_default_border};
                border-radius: 7px;
                color: {t.btn_default_fg};
                font-size: 12px;
                font-weight: 600;
                padding: 9px 18px;
            }}
            QPushButton#reqDocButton:hover {{
                background: {t.btn_default_hover_bg};
                border-color: {t.accent_primary};
            }}

            QLabel#reqHint {{
                color: {t.text_disabled};
                font-size: 11px;
            }}
        """)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _open_docs(self):
        """Open the installation guide in the default browser."""
        QDesktopServices.openUrl(
            QUrl("https://github.com/mohdsinanm/OmixForge/wiki/Dependency-installation")
        )
