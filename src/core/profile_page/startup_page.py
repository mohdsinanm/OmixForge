from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel,QToolButton
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtCore import Qt, pyqtSignal

from src.core.profile_page.requirements import RequirementsNotSatisfied
from src.utils.resource import resource_path

class AccessModePage(QWidget):
    public_selected = pyqtSignal()
    private_selected = pyqtSignal()

    def __init__(self, docker_installed :bool, nextflow_installed: bool):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.setSpacing(25)

        # TITLE
        title = QLabel("OmixForge")
        title.setObjectName("titleLabel")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)  

        if docker_installed and nextflow_installed:
            # SUBTITLE
            subtitle = QLabel("Offline Bioinformatics Pipeline Execution")
            subtitle.setObjectName("subtitleLabel")
            subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
            main_layout.addWidget(subtitle)
            self.show_access_modes(main_layout)
        else:
            self.show_requirements_not_satisfied(main_layout, docker_installed, nextflow_installed)

    def show_requirements_not_satisfied(self, main_layout, docker_installed, nextflow_installed):
        self.req_page = RequirementsNotSatisfied(main_layout, docker_installed, nextflow_installed)
        self.setStyleSheet(self.stylesheet())

    def show_access_modes(self, main_layout):

        # CARD CONTAINER
        card_layout = QHBoxLayout()
        card_layout.setSpacing(40)
        main_layout.addLayout(card_layout)

        # PUBLIC MODE
        public_card = self.create_card("Public Mode", "Run without login", resource_path("src/assets/users-alt.svg"), "The run data will be stored locally on your machine without any encryption.")
        public_card.mousePressEvent = lambda e: self.public_selected.emit()
        card_layout.addWidget(public_card)
        public_card.setObjectName("public_access_card")

        # PRIVATE MODE
        private_card = self.create_card("Private Mode", "Requires login", resource_path("src/assets/lock.svg"), "The run data will be encrypted and stored locally, ensuring privacy and security. Only one user will be able to access the private mode on this installation.")

        private_card.mousePressEvent = lambda e: self.private_selected.emit()
        card_layout.addWidget(private_card)
        private_card.setObjectName("private_access_card")

        self.setStyleSheet(self.stylesheet())


    
    def create_card(self, title, subtitle, svg_path=None, info_text=None):
        card = QFrame()
        card.setObjectName("accessCard")
        card.setFixedSize(300, 200)

        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # --- TOP RIGHT INFO BUTTON ---
        if info_text:
            info_btn = QToolButton()
            info_btn.setText("i")
            info_btn.setToolTip(info_text)
            info_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            info_btn.setFixedSize(20, 20)
            info_btn.setStyleSheet("""
                QToolButton {
                    border: 1px solid gray;
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 0px;
                    background: transparent;
                }
                QToolButton:hover {
                    border: 1px solid #4a90e2;
                    color: #4a90e2;
                }
            """)

            top_layout = QHBoxLayout()
            top_layout.addStretch()
            top_layout.addWidget(info_btn)
            top_layout.setContentsMargins(0, 0, 0, 0)
            layout.addLayout(top_layout)

        # --- ICON (SVG) ---
        if svg_path:
            icon_widget = QSvgWidget(svg_path)
            icon_widget.setFixedSize(48, 48)

            icon_container = QWidget()
            icon_layout = QHBoxLayout(icon_container)
            icon_layout.addWidget(icon_widget)
            icon_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_layout.setContentsMargins(0, 0, 0, 0)

            layout.addWidget(icon_container)

        # --- TITLE ---
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # --- SUBTITLE ---
        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("cardSubtitle")
        subtitle_label.setWordWrap(True)
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle_label)

        return card

    def stylesheet(self):
        return """
        QLabel#titleLabel {
            font-size: 40px;
            font-weight: 800;
            letter-spacing: 1px;
        }

        QLabel#subtitleLabel {
            font-size: 15px;
            margin-bottom: 12px;
            opacity: 0.7;
        }
        QFrame#public_access_card,
        QFrame#private_access_card,
        QFrame#accessCard {
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(120,120,120,0.4);
        }
        QFrame#public_access_card:hover,
        QFrame#private_access_card:hover,
        QFrame#accessCard:hover {
            border: 1px solid #4a90e2;
        }

        QLabel#cardTitle {
            font-size: 20px;
            font-weight: 600;
        }

        QLabel#cardSubtitle {
            font-size: 14px;
            opacity: 0.75;
        }
        """
