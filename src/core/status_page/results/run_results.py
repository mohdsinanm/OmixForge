
from pathlib import Path
from src.assets.stylesheet import close_button_style
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import RUN_DIR, PIPELINES_RUNS, CONFIG_FILE
from src.utils.fileops.file_handle import list_files_in_directory, delete_directory, delete_file, untar_folder, json_read, file_exists
from src.utils.encryption.handle import generate_key, decrypt_file
from src.utils.widgets.filetree import FilesTreeWidget
from src.utils.widgets.loading import LoadingDialog
from src.utils.resource import resource_path
from src.utils.widgets.credential_popup import CredentialsDialog
from src.core.status_page.run_state import classify_run_log, is_private_run
logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton, QApplication, QMessageBox, QDialog, QSplitter
)

from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, pyqtSignal, QTimer,  QProcess, QThread, QObject,  QRunnable, QThreadPool, pyqtSlot, QObject, pyqtSignal


class TarDecryptSignals(QObject):
    finished = pyqtSignal(str)     # emits run_name on success
    error = pyqtSignal(str, str)   # emits run_name, error message


class TarDecryptWorker(QRunnable):
    def __init__(self, run_name, run_dir, tar_name, cred):
        super().__init__()
        self.run_name = run_name
        self.run_dir = run_dir
        self.tar_name = tar_name
        self.cred = cred
        self.signals = TarDecryptSignals()

    @pyqtSlot()
    def run(self):
        try:

            key = generate_key(
                f"{self.cred.get('user', '')}:{self.cred.get('password', '')}"
            )

            archive_path = decrypt_file(self.tar_name, key)
            untar_folder(archive_path, str(Path(self.run_dir).parent))
            delete_file(archive_path)

            self.signals.finished.emit(self.run_name)

        except Exception as e:
            self.signals.error.emit(self.run_name, str(e))

class PipelineDataCard(QFrame):
    clicked = pyqtSignal(str)

    def __init__(self, name: str, locked: bool = False, status: str = "Unknown"):
        super().__init__()
        self.name = name
        self.locked = locked
        self.status = status

        self.setObjectName("pipelineResultCard")
        self.setProperty("state", status.casefold())
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

        self.status_badge = QLabel(status)
        self.status_badge.setObjectName("resultStatusBadge")
        self.status_badge.setProperty("state", status.casefold())
        self.status_badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_badge.setFixedHeight(32)

        self.status_group = QWidget(self)
        self.status_group.setStyleSheet("background: transparent;")
        self.status_group_layout = QHBoxLayout(self.status_group)
        self.status_group_layout.setContentsMargins(0, 0, 0, 0)
        self.status_group_layout.setSpacing(6)
        self.status_group_layout.addWidget(self.status_badge)

        if locked:
            self.lock_icon = QSvgWidget(resource_path("src/assets/lock.svg"))
            self.lock_icon.setFixedSize(16, 16)
            self.status_group_layout.addWidget(
                self.lock_icon, 0, Qt.AlignmentFlag.AlignVCenter
            )

        layout.addWidget(self.status_group, 0, Qt.AlignmentFlag.AlignVCenter)

    
    def mousePressEvent(self, event):
        self.clicked.emit(self.name)
        event.accept()


class PipelineResultsPage(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.pipeline_runs = []
        self.files_tree_window = None

        self.constants = json_read(CONFIG_FILE)
        self.RUN_DIR = self.constants.get("folders",{}).get("RUN_DIR", RUN_DIR)
        self.PIPELINES_RUNS = self.constants.get("folders",{}).get("PIPELINES_RUNS", PIPELINES_RUNS)
  

        self.get_local_pipelines_status()

        main_layout = QVBoxLayout(self)

        # Cards Grid
        self.cards_grid = QGridLayout()

        scroll = QScrollArea()
        scroll.setObjectName("runResultsScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        scroll_widget = QWidget()
        scroll_widget.setObjectName("runResultsScrollContent")
        scroll_widget.setLayout(self.cards_grid)
        scroll.setWidget(scroll_widget)

        self.details_box = QFrame()
        self.details_box.hide()
        self.details_box.setMinimumHeight(160)
        self.details_layout = QVBoxLayout(self.details_box)

        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_splitter.setObjectName("runResultsSplitter")
        self.content_splitter.setHandleWidth(8)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.addWidget(scroll)
        self.content_splitter.addWidget(self.details_box)
        self.content_splitter.setStretchFactor(0, 2)
        self.content_splitter.setStretchFactor(1, 3)
        self.content_splitter.setStyleSheet("""
            QSplitter#runResultsSplitter::handle { background-color: #dbe6e2; }
            QSplitter#runResultsSplitter::handle:hover { background-color: #111111; }
        """)
        self._details_splitter_initialized = False
        main_layout.addWidget(self.content_splitter, 1)

        self.render_cards()

        # Periodic refresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self._periodic_refresh)
        self._refresh_timer.start()


    def get_local_pipelines_status(self):
        items = list_files_in_directory(self.RUN_DIR)
        app = QApplication.instance()
        private_session = bool(getattr(app, "cred", None))
        self.pipeline_runs = [
            name for name in items
            if name != ".private_runs"
            and (private_session or not is_private_run(name, self.RUN_DIR))
        ]

    def refresh_visibility(self):
        self.get_local_pipelines_status()
        selected = getattr(self, "_selected_run", None)
        if selected and selected not in self.pipeline_runs:
            self._on_close_button_click()
        self.render_cards()


    def render_cards(self):
        columns = 1
        row = col = 0

        # Clear grid
        for i in reversed(range(self.cards_grid.count())):
            item = self.cards_grid.takeAt(i)
            if item.widget():
                item.widget().deleteLater()

        for name in self.pipeline_runs:
            locked = name.endswith(".tar.gz.enc")
            card = PipelineDataCard(name, locked, self._get_run_status(name, locked))
            card.clicked.connect(self.on_card_clicked)

            card.setMaximumHeight(150)

            self.cards_grid.addWidget(card, row, col)

            col += 1
            if col >= columns:
                col = 0
                row += 1

    def _get_run_status(self, name: str, locked: bool = False) -> str:
        run_name = name.removesuffix(".tar.gz.enc") if locked else name
        log_path = Path(self.PIPELINES_RUNS) / f"{run_name}.txt"
        try:
            log_content = log_path.read_text(encoding="utf-8", errors="ignore").casefold()
        except OSError:
            return "Encrypted" if locked else "Unknown"

        status = classify_run_log(log_content)
        if status != "Unknown":
            return status
        if locked:
            return "Encrypted"
        return "Unknown"


    def on_card_clicked(self, name: str):
        """Open file tree window + show delete action"""
        if name not in self.pipeline_runs:
            return
        app = QApplication.instance()
        if not getattr(app, "cred", None) and is_private_run(name, self.RUN_DIR):
            return
        self._selected_run = name

        # Clear previous details
        self.clear_details_layout()

        # Title
        title = QLabel(f"Pipeline: {name}")
        title.setFont(QFont("Noto Sans", 11, QFont.Weight.Bold))

        self.action_items_top = QHBoxLayout()

        close_btn = QPushButton("X", parent=self.details_box)
        close_btn.setObjectName("close_result_details")
        close_btn.setStyleSheet(close_button_style())
        close_btn.setFixedSize(40,30)
        close_btn.clicked.connect(self._on_close_button_click)
        self.action_items_top.addWidget(title)
        self.action_items_top.addWidget(close_btn)

        self.details_layout.addLayout(self.action_items_top)

        if name.endswith(".tar.gz.enc"):
            notice = QLabel("This run is encrypted. Decrypt it to browse its files.")
            notice.setObjectName("encryptedRunNotice")
            notice.setWordWrap(True)
            self.details_layout.addWidget(notice)
        else:
            self.open_files_tree(Path(self.RUN_DIR) / name)

        # Actions
        actions = QHBoxLayout()
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedSize(80, 32)
        delete_btn.clicked.connect(lambda: self.on_delete_clicked(name))

        decrept_btn = QPushButton("Decrypt")
        decrept_btn.setFixedSize(80, 32)
        decrept_btn.clicked.connect(lambda: self.on_decrypt_clicked(name))

        actions.addStretch()
        if ".tar.gz.enc" in name:
            app = QApplication.instance()
            try:
                if app.cred and ".tar.gz.enc" in name:
                    actions.addWidget(decrept_btn)
                    actions.addWidget(delete_btn)
            except:
                pass
        else:
            actions.addWidget(delete_btn)

        self.details_layout.addLayout(actions)
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
        self._selected_run = None

        try:
            self.clear_layout(self.details_layout)
        except:
            pass

    def open_files_tree(self, run_dir: Path):
        """Embed file tree inside details_box"""

        if not file_exists(run_dir):
            logger.warning(f"Run directory does not exist: {run_dir}")
            return


        self.files_tree_window = FilesTreeWidget(
            root_dir=run_dir,
            allowed_exts=[".md", ".MD", ".txt", ".json", ".csv", ".config", ".yaml", ".yml"],
            parent=self.details_box,
            exclude_dirs=[".nextflow", "work",]
        )

        self.details_layout.addWidget(self.files_tree_window)

    def on_decrypt_clicked(self, name: str):
        try:
            dialog = CredentialsDialog(self)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return  # user cancelled

            username, password = dialog.get_credentials()

            if not username or not password:
                QMessageBox.warning(self, "Error", "Username and password required")
                return

            # Store credentials safely (example)
            app = QApplication.instance()
            
            cred = {
                "user": username,
                "password": password
            }
            if app.cred == cred:
                tar_name = f"{self.RUN_DIR}/{name}"
                run_dir = f"{self.RUN_DIR}/{name.replace('.tar.gz.enc','')}"

                self.loading_dialog = LoadingDialog(
                    message="Decrypting pipeline…",
                    parent=self
                )
                self.loading_dialog.show()

                worker = TarDecryptWorker(name, run_dir, tar_name, cred)

                # Connect callbacks
                worker.signals.finished.connect(self._on_tar_decrypt_done)
                worker.signals.error.connect(self._on_tar_decrypt_error)

                # Start async
                QThreadPool.globalInstance().start(worker)

            else:
                logger.error(app.cred)
                logger.error(cred)
                QMessageBox.warning(self, "Error", "Credentials does not match")

        except Exception as e:
            logger.error(f"Error decrypting pipeline {name}: {e}")

    def _on_tar_decrypt_done(self, runname):
        if hasattr(self, "loading_dialog"):
            self.loading_dialog.close()
            self.loading_dialog.deleteLater()
            self.loading_dialog = None

        QMessageBox.information(
            self,
            "Decryption Complete",
            f"{runname} decrypted successfully")
        self.clear_details_layout()
        self.details_box.hide()
        self.get_local_pipelines_status()
        self.render_cards()

    def _on_tar_decrypt_error(self, runname, e):
        if hasattr(self, "loading_dialog"):
            self.loading_dialog.close()
            self.loading_dialog.deleteLater()
            self.loading_dialog = None

            QMessageBox.critical(
                self,
                "Decryption Failed",
                f"{runname} failed to decrypt:\n{e}"
            )

    def on_delete_clicked(self, name: str):

        try:

            if name.endswith(".tar.gz.enc"):
                delete_file(f"{self.RUN_DIR}/{name}")
            else:
                delete_directory(f"{self.RUN_DIR}/{name}")
            logger.info(f"Deleted pipeline: {name}")

            # Cleanup UI
            self.clear_details_layout()
            self.details_box.hide()

            self.get_local_pipelines_status()
            self.render_cards()

        except Exception as e:
            logger.error(f"Error deleting pipeline {name}: {e}")

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
            selected = getattr(self, "_selected_run", None)
            if selected and selected not in self.pipeline_runs:
                self._on_close_button_click()
            self.render_cards()
        except Exception:
            pass
