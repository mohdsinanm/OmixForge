from PyQt6.QtWidgets import QLabel


class PipelineStatus():
    def __init__(self, main_window):
        
        label = QLabel("Pipeline Status")
        main_window.setCentralWidget(label)
