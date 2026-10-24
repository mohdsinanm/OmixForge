
from pathlib import Path
from src.assets.stylesheet import close_button_style
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import PIPELINE_DIR, CONFIG_FILE
from src.utils.fileops.file_handle import list_files_in_directory, json_read, file_exists
from src.utils.widgets.filetree import FilesTreeWidget
from src.utils.resource import resource_path
logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton, QSplitter
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
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Pipeline name
        self.label = QLabel(name)
        self.label.setObjectName("pipelineCardName")
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
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        heading_layout = QHBoxLayout()
        heading = QLabel("Pipeline files")
        heading.setObjectName("dashboardSectionTitle")
        self.pipeline_count = QLabel()
        self.pipeline_count.setObjectName("dashboardCount")
        heading_layout.addWidget(heading)
        heading_layout.addWidget(self.pipeline_count)
        heading_layout.addStretch()
        main_layout.addLayout(heading_layout)

        # Cards Grid
        self.cards_grid = QGridLayout()
        self.cards_grid.setContentsMargins(12, 12, 12, 12)
        self.cards_grid.setVerticalSpacing(10)

        scroll = QScrollArea()
        scroll.setObjectName("pipelineEditorScroll")
        scroll.viewport().setStyleSheet("background: transparent;")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_widget = QWidget()
        scroll_widget.setObjectName("pipelineEditorScrollContent")
        scroll_widget.setStyleSheet("background: transparent;")
        scroll_widget.setLayout(self.cards_grid)
        scroll.setWidget(scroll_widget)

        self.details_box = QFrame()
        self.details_box.setObjectName("pipelineEditorDetails")
        self.details_box.hide()
        self.details_box.setMinimumHeight(160)
        self.details_layout = QVBoxLayout(self.details_box)

        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_splitter.setObjectName("pipelineEditorSplitter")
        self.content_splitter.setHandleWidth(8)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.addWidget(scroll)
        self.content_splitter.addWidget(self.details_box)
        self.content_splitter.setStretchFactor(0, 2)
        self.content_splitter.setStretchFactor(1, 3)
        self._details_splitter_initialized = False
        main_layout.addWidget(self.content_splitter, 1)

        self.empty_state = QLabel("No pipeline files found.", scroll_widget)
        self.empty_state.setObjectName("dashboardEmptyState")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)

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
        self.pipeline_count.setText(f"{len(self.pipeline_runs)} available")

        # Clear grid
        for i in reversed(range(self.cards_grid.count())):
            item = self.cards_grid.takeAt(i)
            if item.widget() and item.widget() is not self.empty_state:
                item.widget().deleteLater()

        if not self.pipeline_runs:
            self.cards_grid.addWidget(self.empty_state, 0, 0)
            self.empty_state.show()
            return

        self.cards_grid.removeWidget(self.empty_state)
        self.empty_state.hide()

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
        title.setObjectName("pipelineDetailTitle")

        self.action_items_top = QHBoxLayout()

        close_btn = QPushButton("X", parent=self.details_box)
        close_btn.setObjectName("close_result_details")
        close_btn.setStyleSheet(close_button_style())
        close_btn.setFixedSize(40,30)
        close_btn.clicked.connect(self._on_close_button_click)
        self.action_items_top.addWidget(title)
        self.action_items_top.addWidget(close_btn)

        self.details_layout.addLayout(self.action_items_top)

        # Open Files Tree Window
        pipeline_dir = f'{self.PIPELINE_DIR}/{name}'
        self.open_files_tree(pipeline_dir)

        # Actions
        self._show_details_pane()

    def _show_details_pane(self):
        self.details_box.show()
        if self._details_splitter_initialized:
            return
        available_height = max(self.content_splitter.height(), 400)
        detail_height = max(200, int(available_height * 0.52))
        self.content_splitter.setSizes([
            max(160, available_height - detail_height),
            detail_height,
        ])
        self._details_splitter_initialized = True

    
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
