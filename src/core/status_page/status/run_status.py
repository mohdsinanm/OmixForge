
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.subcommands.shell import run_shell_command, run_shell_command_stream
from src.utils.constants import RUN_DIR, PIPELINES_RUNS
from src.utils.fileops.file_handle import list_files_in_directory, read_from_file, delete_directory, delete_file
import time

logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class PipelineCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name, background):
        super().__init__()
        self.name = name

        self.setObjectName("pipelineCard")
        
        self.setStyleSheet("""
            QFrame#pipelineCard {{
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 12px;
                background: {background};
                color: #444;
            }}
            QFrame#pipelineCard:hover {{
                background: #eaeaea;
            }}
            QFrame#pipelineCard:hover QLabel {{
                color: black;
            }}
        """.format(background=background))

        layout = QHBoxLayout()
        label = QLabel(name)
        
               
        label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        layout.addWidget(label)
        layout.addStretch()
        self.setLayout(layout)

    
    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        event.accept()


class PipelineRunStatus(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pipeline_runs = []
        self.get_local_pipelines_status()

        main_layout = QVBoxLayout(self)

        # GRID LAYOUT FOR CARDS
        self.cards_grid = QGridLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        # scroll only in vertical direction
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_widget = QWidget()
        scroll_widget.setLayout(self.cards_grid)
        scroll.setWidget(scroll_widget)

        main_layout.addWidget(scroll)

        # DETAILS BOX
        self.details_box = QFrame()
        self.details_box.hide()
        self.details_layout = QVBoxLayout(self.details_box)
        main_layout.addWidget(self.details_box)

        self.render_cards()


    def get_local_pipelines_status(self):

        items_collected = list_files_in_directory(PIPELINES_RUNS)
        self.pipeline_runs = items_collected


    def render_cards(self):
        columns = 3
        row = 0
        col = 0

        # Clear existing cards so re-rendering doesn't duplicate widgets
        for i in reversed(range(self.cards_grid.count())):
            item = self.cards_grid.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        for index, name in enumerate(self.pipeline_runs):
            content = read_from_file(PIPELINES_RUNS / name)

            if "error" in content.lower() or "failed" in content.lower():
                card = PipelineCard(name, "#ff4c4c")  # Red for error
            elif "completed" in content.lower():
                card = PipelineCard(name, "#4bb543")  # Green for completed
            else:
                card = PipelineCard(name, "#f0ad4e")  # Yellow for running/unknown
            
            card.clicked.connect(self.on_card_clicked)

            # Add card to grid
            self.cards_grid.addWidget(card, row, col)

            # next column
            col += 1

            # wrap to next row
            if col >= columns:
                col = 0
                row += 1
    

    def on_card_clicked(self, name):
        # Clear previous details
        
        for i in reversed(range(self.details_layout.count())):
            item = self.details_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        # Title
        self.details_layout.addWidget(QLabel(f"Details for pipeline: {name}"))

        # Read file content
        content = read_from_file(PIPELINES_RUNS / name)

        # Large content label
        content_label = QLabel(content)
        content_label.setWordWrap(True)
        content_label.setFont(QFont("Courier New", 10))

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(content_label)

        self.details_layout.addWidget(scroll)

        # Action section
        self.action_section = QHBoxLayout()

        delete_btn = QPushButton("Delete", parent=self.details_box)
        delete_btn.setFixedSize(60, 30)
        delete_btn.clicked.connect(self.on_delete_clicked)

        self.action_section.addWidget(delete_btn)
        self.details_layout.addLayout(self.action_section)

        self.details_box.show()

        
    def on_delete_clicked(self):
        try:
            file_name = self.details_layout.itemAt(0).widget().text().split(': ')[1]
            delete_file(PIPELINES_RUNS / file_name)
            delete_directory(RUN_DIR / file_name.replace(".txt",""))
            logger.info(f"Successfully deleted pipeline: {self.details_layout.itemAt(0).widget().text().split(': ')[1]}")

            # Clear the grid layout
            for i in reversed(range(self.cards_grid.count())):
                item = self.cards_grid.takeAt(i)
                if item.widget():
                    item.widget().deleteLater()
                # Refresh the local pipelines list and UI
                self.clear_details_layout()
                self.details_box.hide()
                self.pipeline_runs = []
                self.get_local_pipelines_status()
                # Re-render the cards   
            # Here you can add logic to delete the pipeline
        except Exception as e:
            logger.error(f"Error deleting pipeline: {e}")
        self.render_cards()

    def clear_details_layout(self):
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
