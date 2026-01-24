from PyQt6.QtWidgets import  QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QFont

class RequirementsNotSatisfied():
    def __init__(self, main_layout, docker_installed, nextflow_installed):
        """Initialize the requirements not satisfied widget with status indicators."""
        # --- Title ---
        title = QLabel("Oops — Requirements Missing")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        main_layout.addWidget(title)

        # --- Requirements layout ---
        req_layout = QVBoxLayout()

        
        req_layout.addLayout(self.requirement_row("Docker", docker_installed))
        req_layout.addLayout(self.requirement_row("Nextflow", nextflow_installed))

        main_layout.addLayout(req_layout)

        # --- Documentation button ---
        doc_btn = QPushButton("Open Documentation")
        doc_btn.setFixedSize(180, 32)

        doc_btn.clicked.connect(self.open_docs)
        doc_btn.setCursor(Qt.CursorShape.PointingHandCursor)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(doc_btn)
        btn_row.addStretch()

        main_layout.addLayout(btn_row)

    def requirement_row(self, name, installed):
        """Create a requirement status row with label and status indicator.
        
        Parameters
        ----------
        name : str
            Name of the requirement (e.g., 'Docker', 'Nextflow').
        installed : bool
            Whether the requirement is installed.
        
        Returns
        -------
        QHBoxLayout
            Layout containing requirement label and status indicator.
        """
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)

        pair = QHBoxLayout()
        pair.setSpacing(6)   # gap between label + mark

        mark = "✔" if installed else "✖"
        color = "green" if installed else "red"

        label = QLabel(f"<b>{name}</b>")
        status = QLabel(f"<span style='color:{color}; font-size:16px'>{mark}</span>")

        pair.addWidget(label)
        pair.addWidget(status)

        # add left stretch → center → right stretch
        row.addStretch()
        row.addLayout(pair)
        row.addStretch()

        return row
    
    def open_docs(self):
        """Open the documentation URL in the default web browser."""
        QDesktopServices.openUrl(
            QUrl("https://github.com/mohdsinanm/OmixForge/wiki/Dependency-installation")
        )




