
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import RUN_DIR, PIPELINES_RUNS, CONFIG_FILE
from src.utils.fileops.file_handle import list_files_in_directory, read_from_file, delete_directory, delete_file, json_read

logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


class PipelineCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name, background):
        super().__init__()
        self.name = name

        self.setObjectName("pipelineResultCard")
        
        self.setStyleSheet("""
            QFrame#pipelineResultCard {{
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 12px;
                background: {background};
                color: #444;
            }}
            QFrame#pipelineResultCard:hover {{
                background: #eaeaea;
            }}
            QFrame#pipelineResultCard:hover QLabel {{
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

        self.constants = json_read(CONFIG_FILE)
        self.RUN_DIR = self.constants.get("folders",{}).get("RUN_DIR", RUN_DIR)
        self.PIPELINES_RUNS = self.constants.get("folders",{}).get("PIPELINES_RUNS", PIPELINES_RUNS)
       
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

        # Periodically refresh the run list so status updates while processes write logs
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self._periodic_refresh)
        self._refresh_timer.start()

        # Timer used to refresh the details content when a run is selected
        self._details_timer = None


    def get_local_pipelines_status(self):

        items_collected = list_files_in_directory(self.PIPELINES_RUNS )
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
            content = read_from_file(f"{self.PIPELINES_RUNS}/{name}")

            if "<<exit-code:1>>" in content.lower():
                card = PipelineCard(name, "#ff4c4c")
            elif "cancelled" in content.lower():
                card = PipelineCard(name, "#6c70dc")  # Red for error
            elif "<<exit-code:0>>" in content.lower():
                card = PipelineCard(name, "#4bb543")  # Green for completed
            else:
                card = PipelineCard(name, "#f0ad4e")  # Yellow for running/unknown
            
            card.clicked.connect(self.on_card_clicked)

            card.setMaximumHeight(200)
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


        self.action_items_top = QHBoxLayout()

        close_btn = QPushButton("X", parent=self.details_box)
        close_btn.setObjectName("close_status_details")
        close_btn.setFixedSize(30,30)
        close_btn.clicked.connect(self._on_close_button_click)
        self.action_items_top.addWidget(QLabel(f"Details for pipeline: {name}"))
        self.action_items_top.addWidget(close_btn)

        self.details_layout.addLayout(self.action_items_top)


        # Read file content and create a label that we will refresh periodically
        content = read_from_file(f"{self.PIPELINES_RUNS}/{name}")
        self._details_content_label = QLabel(content)
        self._details_content_label.setWordWrap(True)
        self._details_content_label.setFont(QFont("Courier New", 10))

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(self._details_content_label)

        self.details_layout.addWidget(scroll)

        # start a short timer to refresh the contents of the details view
        if self._details_timer:
            try:
                self._details_timer.stop()
            except Exception:
                pass
        self._details_timer = QTimer(self)
        self._details_timer.setInterval(1000)
        self._details_timer.timeout.connect(lambda: self._refresh_details_content(name))
        self._details_timer.start()

        # Action section
        self.action_section = QHBoxLayout()

        delete_btn = QPushButton("Delete", parent=self.details_box)
        delete_btn.setFixedSize(60, 30)
        delete_btn.clicked.connect(self.on_delete_clicked)

        self.action_section.addWidget(delete_btn)
        self.details_layout.addLayout(self.action_section)

        self.details_box.show()

    
    def clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                child_layout = item.layout()

                if widget is not None:
                    widget.deleteLater()

                elif child_layout is not None:
                    self.clear_layout(child_layout)

    def _on_close_button_click(self):
        self.details_box.hide()

        try:
            self.clear_layout(self.details_layout)
        except:
            pass

        
    def on_delete_clicked(self):
        try:
            file_name = self.details_layout.itemAt(0).widget().text().split(': ')[1]
            try:
                app = QApplication.instance()
                if app.cred:
                    delete_file(f'{self.RUN_DIR}/{file_name.replace(".txt",".zip.enc")}')
                    delete_file(f"{self.PIPELINES_RUNS}/{file_name}")
                    
                logger.info(f"Successfully deleted pipeline: {self.details_layout.itemAt(0).widget().text().split(': ')[1]}")


            except Exception as e:
                try:
                    delete_file(f"{self.PIPELINES_RUNS}/{file_name}")
                    delete_directory(f'{self.RUN_DIR}/{file_name.replace(".txt","")}')
                    logger.info(f"Successfully deleted pipeline: {self.details_layout.itemAt(0).widget().text().split(': ')[1]}")
                except:
                    logger.error(f"Failed to delete run {file_name}")
                
            # Clear the grid layout
            for i in reversed(range(self.cards_grid.count())):
                item = self.cards_grid.takeAt(i)
                if item.widget():
                    item.widget().deleteLater()
                # Refresh the local pipelines list and UI
                self.clear_details_layout()
                self.details_box.hide()
                if self._details_timer:
                    try:
                        self._details_timer.stop()
                    except Exception:
                        pass
                    self._details_timer = None
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

    def _periodic_refresh(self):
        # Called by timer to refresh list and cards
        try:
            self.get_local_pipelines_status()
            self.render_cards()
        except Exception:
            pass

    def _refresh_details_content(self, name):
        try:
            content = read_from_file(f"{self.PIPELINES_RUNS}/{name}")
            if hasattr(self, '_details_content_label') and self._details_content_label:
                self._details_content_label.setText(content)
        except Exception:
            pass
