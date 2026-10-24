
from PyQt6.QtWidgets import ( 
    QLabel, QFrame, QHBoxLayout,
)
from PyQt6.QtCore import pyqtSignal, Qt

from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()

class PipelineCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name):
        super().__init__()
        self.name = name

        self.setObjectName("pipelineCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout()
        layout.setContentsMargins(16, 14, 16, 14)
        label = QLabel(name)
        label.setObjectName("pipelineCardName")
        layout.addWidget(label)
        layout.addStretch()
        self.setLayout(layout)

    
    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        event.accept()

