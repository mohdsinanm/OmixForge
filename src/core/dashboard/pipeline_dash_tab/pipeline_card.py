
from PyQt6.QtWidgets import ( 
    QLabel, QFrame, QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class PipelineCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name):
        super().__init__()
        self.name = name

        self.setObjectName("pipelineCard")
        self.setStyleSheet("""
            QFrame#pipelineCard {
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 12px;
                background: #fafafa;
                color: #444;
            }
            QFrame#pipelineCard:hover {
                background: #eaeaea;
            }
            QFrame#pipelineCard:hover QLabel {
                color: black;
            }
        """)

        layout = QHBoxLayout()
        label = QLabel(name)
        
               
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(label)
        layout.addStretch()
        self.setLayout(layout)

    
    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        event.accept()

