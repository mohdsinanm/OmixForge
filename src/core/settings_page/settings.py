from PyQt6.QtWidgets import QLabel


class SettingsPage():
    def __init__(self, main_window):
        
        label = QLabel("Settings")
        main_window.setCentralWidget(label)
