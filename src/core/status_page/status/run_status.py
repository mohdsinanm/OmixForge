
import json
from pathlib import Path

from src.assets.stylesheet import close_button_style
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import RUN_DIR, PIPELINES_RUNS, CONFIG_FILE
from src.utils.fileops.file_handle import list_files_in_directory, read_from_file, delete_directory, delete_file, json_read
from src.core.status_page.run_state import classify_run_log, is_private_run

logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton, QApplication, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QThreadPool
from PyQt6.QtGui import QFont

from src.core.dashboard.pipeline_dash_tab.local_pipeline import PipelineLocal


class PipelineCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name, background, status="UNKNOWN", pid=None):
        super().__init__()
        self.name = name

        self.setObjectName("pipelineResultCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        accent = {
            "#fcebe8": "#be5540",
            "#f0f2f1": "#778780",
            "#e5f3eb": "#19825c",
            "#fff3df": "#b87718",
        }.get(background, "#111111")
        
        self.setStyleSheet("""
            QFrame#pipelineResultCard {{
                border: 1px solid #dbe6e2;
                border-left: 4px solid {accent};
                border-radius: 8px;
                padding: 10px;
                background: {background};
                color: #263b36;
            }}
            QFrame#pipelineResultCard:hover {{
                border-color: #9db9b0;
            }}
        """.format(background=background, accent=accent))

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(5)
        name_label = QLabel(name)
        name_label.setObjectName("pipelineCardName")
        layout.addWidget(name_label)

        detail = QLabel(f"PID {pid}  ·  {status}" if pid else status)
        detail.setObjectName("pipelineCardRunStatus")
        layout.addWidget(detail)
        self.setLayout(layout)

    
    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        event.accept()


class PipelineRunStatus(QWidget):

    running_jobs_count_changed = pyqtSignal(int)

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
        scroll.setObjectName("runStatusScroll")
        scroll.setWidgetResizable(True)

        # scroll only in vertical direction
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_widget = QWidget()
        scroll_widget.setObjectName("runStatusScrollContent")
        scroll_widget.setLayout(self.cards_grid)
        scroll.setWidget(scroll_widget)

        # DETAILS BOX
        self.details_box = QFrame()
        self.details_box.hide()
        self.details_box.setMinimumHeight(160)
        self.details_layout = QVBoxLayout(self.details_box)

        # A splitter lets users choose how much space the run list and log view
        # receive. The detail pane remains hidden until a run is selected.
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_splitter.setObjectName("runStatusSplitter")
        self.content_splitter.setHandleWidth(8)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.setStyleSheet("""
            QSplitter#runStatusSplitter::handle {
                background-color: #dbe6e2;
            }
            QSplitter#runStatusSplitter::handle:hover {
                background-color: #111111;
            }
        """)
        self.content_splitter.addWidget(scroll)
        self.content_splitter.addWidget(self.details_box)
        self.content_splitter.setStretchFactor(0, 2)
        self.content_splitter.setStretchFactor(1, 3)
        self._details_splitter_initialized = False
        main_layout.addWidget(self.content_splitter, 1)

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
        app = QApplication.instance()
        private_session = bool(getattr(app, "cred", None))
        self.pipeline_runs = [
            name for name in items_collected
            if private_session or not is_private_run(name, self.RUN_DIR)
        ]

    def refresh_visibility(self):
        """Immediately discard a selected private log when the session becomes public."""
        self.get_local_pipelines_status()
        selected = getattr(self, "_selected_run", None)
        if selected and selected not in self.pipeline_runs:
            self._on_close_button_click()
        self.render_cards()


    def get_running_jobs_count(self):
        # Get the number of running pipeline jobs from PipelineLocal
        return len(PipelineLocal.active_runs)


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
            status, pid = self._run_card_status(name, content)
            background = {
                "FAILED": "#fcebe8",
                "INTERRUPTED": "#fcebe8",
                "CANCELLED": "#f0f2f1",
                "COMPLETED": "#e5f3eb",
                "RUNNING": "#fff3df",
            }.get(status, "#fff3df")
            card = PipelineCard(name, background, status, pid)
            
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

    def _run_card_status(self, name, content):
        """Return the visible run state and live supervisor PID, when available."""
        metadata_path = Path(self.RUN_DIR) / name.removesuffix(".txt") / "omixforge-run.json"
        try:
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            pid = int(metadata.get("pid"))
            if PipelineLocal._pid_is_running(pid, metadata.get("process_start_token")):
                return "RUNNING", pid
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass

        log_status = classify_run_log(content)
        if log_status != "Unknown":
            return log_status.upper(), None
        return "RUNNING" if name in PipelineLocal.active_runs else "STARTING", None
    

    def on_card_clicked(self, name):
        # if same card selected again, do nothing (avoid rebuild / duplicate buttons)
        if hasattr(self, '_selected_run') and self._selected_run == name and self.details_box.isVisible():
            return

        self._selected_run = name

        # Clear previous details completely
        self.clear_layout(self.details_layout)
        self.details_box.hide()
        
        # Reset any existing timers
        if self._details_timer:
            try:
                self._details_timer.stop()
            except Exception:
                pass
            self._details_timer = None


        self.action_items_top = QHBoxLayout()

        close_btn = QPushButton("X", parent=self.details_box)
        close_btn.setObjectName("close_status_details")
        close_btn.setStyleSheet(close_button_style())
        close_btn.setFixedSize(40,30)
        close_btn.clicked.connect(self._on_close_button_click)
        self.action_items_top.addWidget(QLabel(f"Details for pipeline: {name}"))
        self.action_items_top.addWidget(close_btn)

        self.details_layout.addLayout(self.action_items_top)


        # Read file content and create a label that we will refresh periodically
        content = read_from_file(f"{self.PIPELINES_RUNS}/{name}")
        self._details_content_label = QLabel(content)
        self._details_content_label.setObjectName("runLogContent")
        self._details_content_label.setWordWrap(True)
        self._details_content_label.setFont(QFont("Courier New", 10))

        # Scroll area
        scroll = QScrollArea()
        scroll.setStyleSheet("QScrollArea { background-color: #ffffff; border: 1px solid #dbe6e2; }")
        scroll.viewport().setStyleSheet("background-color: #ffffff;")
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

        # Action section - create fresh layout each time
        action_section = QHBoxLayout()

        delete_btn = QPushButton("Delete", parent=self.details_box)
        delete_btn.setFixedSize(70, 30)
        delete_btn.clicked.connect(lambda: self.on_delete_clicked(name))

        action_section.addWidget(delete_btn)
        self.details_layout.addLayout(action_section)

        self.details_box.show()
        if not self._details_splitter_initialized:
            available_height = max(self.content_splitter.height(), 400)
            detail_height = max(220, int(available_height * 0.58))
            self.content_splitter.setSizes([
                max(160, available_height - detail_height),
                detail_height,
            ])
            self._details_splitter_initialized = True

    
    def on_delete_clicked(self,file_name):
        try:
            # Stop any running details refresh timer
            if self._details_timer:
                try:
                    self._details_timer.stop()
                except Exception:
                    pass
                self._details_timer = None

            # Hide and clear the details view
            self.details_box.hide()
            self.clear_details_layout()

            app = QApplication.instance()
            if getattr(app, "cred", False):
                try:
                    delete_file(f'{self.RUN_DIR}/{file_name.replace(".txt", ".tar.gz.enc")}')
                except Exception:
                    pass

            # Delete the run files/directories if present
            try:
                delete_file(f"{self.PIPELINES_RUNS}/{file_name}")
            except Exception:
                pass

            try:
                delete_directory(f'{self.RUN_DIR}/{file_name.replace(".txt", "")}')
            except Exception:
                pass
            try:
                (Path(self.RUN_DIR) / ".private_runs" / f"{Path(file_name).stem}.json").unlink(missing_ok=True)
            except OSError:
                pass

            logger.info(f"Successfully deleted run: {file_name}")
        except Exception as e:
            logger.error(f"Error deleting pipeline: {e}")

        # Refresh pipeline list and UI state
        self.pipeline_runs = []
        self.get_local_pipelines_status()
        self.render_cards()

    def clear_details_layout(self):
        # Fully clear widgets and nested layouts from the details area.
        self.clear_layout(self.details_layout)

    def _on_close_button_click(self):
        self.details_box.hide()
        self._selected_run = None

        if self._details_timer:
            try:
                self._details_timer.stop()
            except Exception:
                pass
            self._details_timer = None

        try:
            self.clear_details_layout()
        except Exception:
            pass

    def clear_layout(self, layout):
        if layout is None:
            return

        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            child_layout = item.layout()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            elif child_layout is not None:
                self.clear_layout(child_layout)
                child_layout.deleteLater()

    def _periodic_refresh(self):
        # Called by timer to refresh list and cards
        try:
            self.get_local_pipelines_status()
            selected = getattr(self, "_selected_run", None)
            if selected and selected not in self.pipeline_runs:
                self._on_close_button_click()
            self.render_cards()
            self.running_jobs_count_changed.emit(self.get_running_jobs_count())
        except Exception:
            pass

    def _refresh_details_content(self, name):
        try:
            content = read_from_file(f"{self.PIPELINES_RUNS}/{name}")
            if hasattr(self, '_details_content_label') and self._details_content_label:
                self._details_content_label.setText(content)
        except Exception:
            pass
