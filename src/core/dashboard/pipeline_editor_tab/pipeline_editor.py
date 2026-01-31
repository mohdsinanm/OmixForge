
from pathlib import Path
from src.assets.stylesheet import close_btn_red_bg
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import PIPELINE_DIR, CONFIG_FILE
from src.utils.fileops.file_handle import list_files_in_directory, json_read, file_exists
from src.utils.widgets.filetree import FilesTreeWidget
from src.utils.resource import resource_path
logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton
)

from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal, QTimer,pyqtSignal


class PipelineDataCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name: str, locked: bool = False):
        super().__init__()
        self.name = name
        self.locked = locked

        self.setObjectName("pipelineCard")

        self.setStyleSheet("""
            QFrame#pipelineCard {
                border: 1px solid #ccc;
                border-radius: 10px;
                padding: 12px;
                color: #444;
                background: white;
            }
            QFrame#pipelineCard:hover {
                background: #eaeaea;
            }
            QFrame#pipelineCard:hover QLabel {
                color: black;
            }
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Pipeline name
        self.label = QLabel(name)
        self.label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(self.label)

        layout.addStretch()

    
    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        event.accept()


class PipelineEditorTab(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pipeline_runs = []
        self.files_tree_window = None

        self.constants = json_read(CONFIG_FILE)
        self.PIPELINE_DIR = self.constants.get("folders",{}).get("PIPELINE_DIR", PIPELINE_DIR)
  

        self.get_local_pipelines_status()

        main_layout = QVBoxLayout(self)

        # Cards Grid
        self.cards_grid = QGridLayout()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_widget = QWidget()
        scroll_widget.setLayout(self.cards_grid)
        scroll.setWidget(scroll_widget)

        main_layout.addWidget(scroll, 1)

        self.details_box = QFrame()
        self.details_box.hide()
        self.details_layout = QVBoxLayout(self.details_box)
        main_layout.addWidget(self.details_box, 1)

        self.render_cards()

        # Periodic refresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self._periodic_refresh)
        self._refresh_timer.start()


    def get_local_pipelines_status(self):
        self.pipeline_runs = list_files_in_directory(self.PIPELINE_DIR)


    def render_cards(self):
        columns = 1
        row = col = 0

        # Clear grid
        for i in reversed(range(self.cards_grid.count())):
            item = self.cards_grid.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        for name in self.pipeline_runs:
            card = PipelineDataCard(name)
            card.clicked.connect(self.on_card_clicked)

            card.setMaximumHeight(150)

            self.cards_grid.addWidget(card, row, col)

            col += 1
            if col >= columns:
                col = 0
                row += 1


    def on_card_clicked(self, name: str):
        """Open file tree window + show delete action"""

        # Clear previous details
        self.clear_details_layout()

        # Title
        title = QLabel(f"Pipeline: {name}")
        title.setFont(QFont("Arial", 11, QFont.Weight.Bold))

        self.action_items_top = QHBoxLayout()

        close_btn = QPushButton("X", parent=self.details_box)
        close_btn.setObjectName("close_result_details")
        close_btn.setStyleSheet(close_btn_red_bg())
        close_btn.setFixedSize(40,30)
        close_btn.clicked.connect(self._on_close_button_click)
        self.action_items_top.addWidget(title)
        self.action_items_top.addWidget(close_btn)

        self.details_layout.addLayout(self.action_items_top)

        # Open Files Tree Window
        pipeline_dir = f'{self.PIPELINE_DIR}/{name}'
        self.open_files_tree(pipeline_dir)

        # Actions
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

    def open_files_tree(self, pipeline_dir: Path):
        """Embed file tree inside details_box"""

        if not file_exists(pipeline_dir):
            logger.warning(f"Run directory does not exist: {pipeline_dir}")
            return


        self.files_tree_window = FilesTreeWidget(
            root_dir=pipeline_dir,
            allowed_exts=[".md", ".MD", ".txt", ".nf", ".json", ".csv", ".config", ".yaml", ".yml"],
            parent=self.details_box,
            exclude_dirs=[],
        )

        self.details_layout.addWidget(self.files_tree_window)

    
    def clear_details_layout(self):
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)

            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

            layout = item.layout()
            if layout:
                self._clear_layout(layout)
    
    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

    def _periodic_refresh(self):
        try:
            self.get_local_pipelines_status()
            self.render_cards()
        except Exception:
            pass
