from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
    QMenu
)
import sys
import os
import subprocess

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OmixForge")

        label = QLabel("Hello!")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.setCentralWidget(label)

        toolbar = QToolBar("My main toolbar")
        toolbar.setIconSize(QSize(16, 16))
        self.addToolBar(toolbar)

        button_action = QAction(QIcon("/home/sinan/Projects/OmixForge/OmixForge/omixforge.png"), "Your button", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.toolbar_button_clicked)
        button_action.setCheckable(True)
        toolbar.addAction(button_action)

        self.setStatusBar(QStatusBar(self))

        

    def toolbar_button_clicked(self, s):
        if s:
            label = QLabel(os.getcwd())
            self.setCentralWidget(label)
            
        print(subprocess.run("docker images", shell=True,capture_output=True))
        print("click", os.getcwd())

app = QApplication(sys.argv)

window = MainWindow()
window.setFixedHeight(500)
window.setFixedWidth(1000)
window.show()

app.exec()