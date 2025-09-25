
from PyQt6.QtWidgets import QLabel, QMainWindow, QHBoxLayout, QWidget, QVBoxLayout, QTabWidget
from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtWidgets import QWidget

from core.dashboard.pipeline_import_tab.pipeline_import import PipelineImport


class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

class PipelineDashboard(QWidget):
    def __init__(self, main_window: QMainWindow):
        super().__init__()

        layout = QVBoxLayout()

        tab_widget = QTabWidget()

        # tab1 = QWidget()
        # tab1_layout = QVBoxLayout()
        # tab1_layout.addWidget(QLabel("This is Tab 1"))
        # tab1.setLayout(tab1_layout)

        pipeline_import_tab = PipelineImport().pipeline_import_tab

        tab2 = QWidget()
        tab2_layout = QVBoxLayout()
        tab2_layout.addWidget(QLabel("This is Tab 2"))
        tab2.setLayout(tab2_layout)

        tab_widget.addTab(pipeline_import_tab, "Pipeline Import")
        tab_widget.addTab(tab2, "Tab 2")


        tab2_layout.addWidget(Color("orange"))
        tab2_layout.addWidget(Color("blue"))

        layout.addWidget(tab_widget)

        widget = QWidget()
        widget.setLayout(layout)



        # Set this widget as the central widget of the main window
        main_window.setCentralWidget(widget)

