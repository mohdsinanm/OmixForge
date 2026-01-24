from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea, QFrame
)
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtCore import Qt

from src.utils.resource import resource_path
from src.utils.version import APP_VERSION


class AboutPage(QWidget):
    """About page displaying application information, version, license, and authors."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.widget = self
        self.init_ui()
    
    def init_ui(self):
        """Initialize the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Create scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Create content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        # Logo section
        logo_layout = QHBoxLayout()
        logo_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        try:
            logo_path = resource_path("src/assets/omixforge.png")
            logo_label = QLabel()
            pixmap = QPixmap(logo_path)
            scaled_pixmap = pixmap.scaledToWidth(100, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_layout.addWidget(logo_label)
        except Exception:
            pass
        content_layout.addLayout(logo_layout)
        
        # Title
        title_label = QLabel("OmixForge")
        title_font = QFont()
        title_font.setPointSize(24)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(title_label)
        
        # Version
        version_label = QLabel(f"Version: {APP_VERSION}")
        version_font = QFont()
        version_font.setPointSize(12)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_layout.addWidget(version_label)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(separator)
        
        # Description
        description_label = QLabel(
            "OmixForge is a comprehensive bioinformatics analysis platform designed to "
            "streamline nextflow pipeline execution and management. It provides an intuitive "
            "interface for running complex computational workflows with ease."
        )
        description_label.setWordWrap(True)
        description_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(description_label)
        
        # Section: License
        license_title = QLabel("License")
        license_title_font = QFont()
        license_title_font.setPointSize(12)
        license_title_font.setBold(True)
        license_title.setFont(license_title_font)
        content_layout.addWidget(license_title)
        
        license_text = QLabel(
            "OmixForge is released under the MIT License.\n\n"
            "Permission is hereby granted, free of charge, to any person obtaining a copy "
            "of this software and associated documentation files (the \"Software\"), to deal "
            "in the Software without restriction, including without limitation the rights "
            "to use, copy, modify, merge, publish, distribute, sublicense, and/or sell "
            "copies of the Software, and to permit persons to whom the Software is "
            "furnished to do so, subject to the following conditions: The above copyright "
            "notice and this permission notice shall be included in all copies or substantial "
            "portions of the Software."
        )
        license_text.setWordWrap(True)
        license_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        license_text.setStyleSheet("color: #666; font-size: 10px;")
        content_layout.addWidget(license_text)
        
        # Section: Authors
        authors_title = QLabel("Authors & Contributors")
        authors_title_font = QFont()
        authors_title_font.setPointSize(12)
        authors_title_font.setBold(True)
        authors_title.setFont(authors_title_font)
        content_layout.addWidget(authors_title)
        
        authors_text = QLabel(
            "• Mohamed Sinan M - Lead Developer <a href='https://github.com/mohdsinanm'>GitHub</a>\n"
                   )
        authors_text.setWordWrap(True)
        authors_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(authors_text)


        # Section: Resources
        resources_title = QLabel("Resources & Links")
        resources_title_font = QFont()
        resources_title_font.setPointSize(12)
        resources_title_font.setBold(True)
        resources_title.setFont(resources_title_font)
        content_layout.addWidget(resources_title)
        
        resources_text = QLabel(
            "• Project Repository: <a href='https://github.com/mohdsinanm/OmixForge'>GitHub</a>\n"
            "• Documentation: <a href='https://github.com/mohdsinanm/OmixForge/wiki'>OmixForge Docs</a>\n"
            "• Nextflow: <a href='https://www.nextflow.io'>nextflow.io</a>\n"
            "• nf-core: <a href='https://nf-co.re'>nf-co.re</a>"
        )
        resources_text.setWordWrap(True)
        resources_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        resources_text.setOpenExternalLinks(True)
        content_layout.addWidget(resources_text)
        
        
        # Section: Technologies
        tech_title = QLabel("Technologies")
        tech_title_font = QFont()
        tech_title_font.setPointSize(12)
        tech_title_font.setBold(True)
        tech_title.setFont(tech_title_font)
        content_layout.addWidget(tech_title)
        
        tech_text = QLabel(
            "• Python 3.x\n"
            "• PyQt6 - GUI Framework\n"
            "• Nextflow - Workflow Management\n"
            "• Docker - Containerization\n"
            "• nf-core - Bioinformatics Pipelines"
        )
        tech_text.setWordWrap(True)
        tech_text.setAlignment(Qt.AlignmentFlag.AlignLeft)
        content_layout.addWidget(tech_text)
        
        
        # Add stretch at the end
        content_layout.addStretch()
        
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
