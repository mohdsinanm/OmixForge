from PyQt6.QtWidgets import QLabel,QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class PipelineImport():
    def __init__(self):

        self.pipeline_import_tab = QWidget()
        tab1_layout = QVBoxLayout()
        tab1_layout.addWidget(QLabel("This Pipeline import tab"))

        self.pipeline_import_tab.setLayout(tab1_layout)

        tab1_layout.addWidget(Color("red"))
        tab1_layout.addWidget(Color("green"))

