
from pathlib import Path
from src.assets.stylesheet import close_btn_red_bg
from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.constants import RUN_DIR, CONFIG_FILE
from src.utils.fileops.file_handle import list_files_in_directory, delete_directory, delete_file, untar_folder, json_read, file_exists
from src.utils.encryption.handle import generate_key, decrypt_file
from src.utils.widgets.filetree import FilesTreeWidget
from src.utils.widgets.loading import LoadingDialog
from src.utils.resource import resource_path
from src.utils.widgets.credential_popup import CredentialsDialog
logger = OmixForgeLogger.get_logger()

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton, QApplication, QMessageBox, QDialog
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

            decrypt_file(self.tar_name, key)
            untar_folder( self.tar_name.replace(".enc","") ,self.run_dir)
            delete_file(self.tar_name.replace(".enc",""))

            self.signals.finished.emit(self.run_name)

        except Exception as e:
            self.signals.error.emit(self.run_name, str(e))

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

        # Lock icon
        self.lock_label = QLabel()
        self.lock_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        if locked:
            self.lock_icon = QSvgWidget(resource_path("src/assets/lock.svg"))
            self.lock_icon.setFixedSize(16, 16)
            layout.addWidget(self.lock_icon)

        else:
            self.lock_label.setVisible(False)

    
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

        main_layout.addWidget(scroll)

        self.details_box = QFrame()
        self.details_box.hide()
        self.details_layout = QVBoxLayout(self.details_box)
        main_layout.addWidget(self.details_box)

        self.render_cards()

        # Periodic refresh
        self._refresh_timer = QTimer(self)
        self._refresh_timer.setInterval(2000)
        self._refresh_timer.timeout.connect(self._periodic_refresh)
        self._refresh_timer.start()


    def get_local_pipelines_status(self):
        self.pipeline_runs = list_files_in_directory(self.RUN_DIR )


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
            card = PipelineDataCard(name, locked)
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
        run_dir = f'{self.RUN_DIR}/{name.replace(".tar.gz.enc", "")}'
        self.open_files_tree(run_dir)

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

    def open_files_tree(self, run_dir: Path):
        """Embed file tree inside details_box"""

        if not file_exists(run_dir):
            logger.warning(f"Run directory does not exist: {run_dir}")
            return


        self.files_tree_window = FilesTreeWidget(
            root_dir=run_dir,
            allowed_exts=[".pdf", ".html", ".svg", ".txt"],
            parent=self.details_box
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

            # Cleanup UI
            self.clear_details_layout()
            self.details_box.hide()

            self.get_local_pipelines_status()
            self.render_cards()

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
            self.render_cards()
        except Exception:
            pass
