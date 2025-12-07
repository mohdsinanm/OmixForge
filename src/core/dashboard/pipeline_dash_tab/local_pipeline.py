from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.subcommands.shell import run_shell_command, run_shell_command_stream
from src.utils.constants import RUN_DIR
from src.utils.fileops.file_handle import ensure_directory

logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


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


class PipelineLocal(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pipelines = []
        self.get_local_pipelines()

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


    def get_local_pipelines(self):
        process = run_shell_command("nextflow list")
        try:
            output = process.stdout.strip().splitlines()
            for line in output:
                if line and not line.startswith("You can run"):
                    name = line.split()[0]
                    self.pipelines.append(name)
        except Exception as e:
            logger.error(f"Error decoding nextflow list output: {e}")


    def render_cards(self):
        columns = 3
        row = 0
        col = 0

        # Clear existing cards so re-rendering doesn't duplicate widgets
        for i in reversed(range(self.cards_grid.count())):
            item = self.cards_grid.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        for index, name in enumerate(self.pipelines):
            card = PipelineCard(name)
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
        # Clear old details
        for i in reversed(range(self.details_layout.count())):
            item = self.details_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        # New content
        self.details_layout.addWidget(QLabel(f"Details for pipeline: {name}"))
        self.details_layout.addWidget(
            QLabel("Here you can show pipeline metadata, description, parameters, etc.")
        )
        self.action_section = QHBoxLayout()
        

        delete_btn = QPushButton("Delete", parent=self.details_box)
        delete_btn.setFixedSize(60, 30)
        delete_btn.clicked.connect(self.on_delete_clicked)

        run_btn = QPushButton("Run", parent=self.details_box)
        run_btn.setFixedSize(60, 30)
        run_btn.clicked.connect(self.on_run_clicked)

        self.action_section.addWidget(run_btn)
        self.action_section.addWidget(delete_btn)
        self.details_layout.addLayout(self.action_section)

        self.details_box.show()
    
    def on_delete_clicked(self):
        try:
            process_dlt = run_shell_command("nextflow drop " + self.details_layout.itemAt(0).widget().text().split(": ")[1])
            if process_dlt.returncode == 0:
                logger.info(f"Successfully deleted pipeline: {self.details_layout.itemAt(0).widget().text().split(': ')[1]}")

                # Clear the grid layout
                for i in reversed(range(self.cards_grid.count())):
                    item = self.cards_grid.takeAt(i)
                    if item.widget():
                        item.widget().deleteLater()
                # Refresh the local pipelines list and UI
                self.pipelines = []
                self.get_local_pipelines()
                # Re-render the cards   
            # Here you can add logic to delete the pipeline
        except Exception as e:
            logger.error(f"Error deleting pipeline: {e}")
        self.render_cards()

    def on_run_clicked(self):
        # Here you can add logic to run the pipeline
        logger.info(f"Running pipeline: {self.details_layout.itemAt(0).widget().text().split(': ')[1]}")
        try:
            ensure_directory(RUN_DIR)
            process_run, stream  = run_shell_command_stream(f"cd {RUN_DIR} && nextflow run " + self.details_layout.itemAt(0).widget().text().split(": ")[1] + " -profile docker")
            for line in stream:
                logger.info(line)
        except Exception as e:
            logger.error(f"Error running pipeline: {e}")

