from datetime import datetime
import codecs
import json
import os
import signal
import subprocess
import csv
import time
import tempfile
from pathlib import Path
from pyqtwaitingspinner import WaitingSpinner

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton, QDialog, QMessageBox, QApplication, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QProcess, QThread, QObject, QRunnable, QThreadPool, pyqtSlot, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.subcommands.shell import run_shell_command
from src.utils.constants import CONFIG_FILE,RUN_DIR, PIPELINES_RUNS, SAMPLE_PREP_DIR
from src.utils.fileops.file_handle import ensure_directory, write_to_file, append_to_file, json_read, delete_file, delete_directory , tar_folder
from src.utils.encryption.handle import encrypt_file, decrypt_file, generate_key
from src.core.dashboard.pipeline_dash_tab.pipeline_args import PipelineArgsDialog
from src.core.dashboard.pipeline_dash_tab.pipeline_card import PipelineCard
from src.assets.stylesheet import close_button_style

logger = OmixForgeLogger.get_logger()


class PipelineInfoWorker(QObject):
    """Worker thread to fetch pipeline info without blocking UI."""
    
    finished = pyqtSignal()
    error = pyqtSignal(str)
    info_ready = pyqtSignal(dict)
    
    def __init__(self, pipeline_name):
        super().__init__()
        self.pipeline_name = pipeline_name
    
    def run(self):
        """Run the nextflow info command and parse output."""
        try:
            shell_out = run_shell_command(
                f"nextflow info {self.pipeline_name}"
            )

            info = {}
            revisions = []
            in_revisions = False

            for line in shell_out.stdout.splitlines():
                stripped = line.strip()

                if not stripped:
                    continue

                # Start of revisions section
                if stripped.startswith("revisions"):
                    in_revisions = True
                    continue

                # Parse revisions
                if in_revisions:
                    revision = stripped.lstrip("*").strip()
                    revision = revision.replace("(default)", "").strip()
                    revision = revision.replace(">", "").strip()

                    revisions.append(revision)
                    continue

                # Parse key/value information
                if ":" in line:
                    key, value = line.split(":", 1)
                    info[key.strip()] = value.strip()

            if revisions:
                info["revisions"] = revisions

            self.info_ready.emit(info)

        except Exception as e:
            logger.error(f"Error fetching pipeline info: {e}")
            self.error.emit(str(e))

        finally:
            self.finished.emit()

class ZipEncryptSignals(QObject):
    finished = pyqtSignal(str, int)     # emits run_name on success
    error = pyqtSignal(str, str, int)   # emits run_name, error message, exit code


class ZipEncryptWorker(QRunnable):
    def __init__(self, run_name, run_dir, zip_name, cred, exitCode):
        super().__init__()
        self.run_name = run_name
        self.run_dir = run_dir
        self.zip_name = zip_name
        self.cred = cred
        self.exitCode = exitCode
        self.signals = ZipEncryptSignals()

    @pyqtSlot()
    def run(self):
        try:
            tar_folder(self.run_dir, self.zip_name)

            key = generate_key(
                f"{self.cred.get('user', '')}:{self.cred.get('password', '')}"
            )

            encrypt_file(self.zip_name, key)

            delete_file(self.zip_name)
            delete_directory(self.run_dir)

            self.signals.finished.emit(self.run_name, self.exitCode)

        except Exception as e:
            self.signals.error.emit(self.run_name, str(e), self.exitCode)

class PipelineDeleteWorker(QObject):
    """Worker to delete a pipeline (nextflow drop) without blocking UI."""
    finished = pyqtSignal()
    error = pyqtSignal(str)
    result = pyqtSignal(bool, str)  # success, message
    # Emitted when a failure requires user confirmation to force-delete the local assets folder
    requires_confirmation = pyqtSignal(str, str)  # (pipeline_dir, error_message)

    def __init__(self, pipeline_name):
        super().__init__()
        self.pipeline_name = pipeline_name

    def run(self):
        try:
            proc = run_shell_command(f"nextflow drop {self.pipeline_name}")
            # If the helper returns an object with returncode and stderr
            rc = getattr(proc, 'returncode', 0)
            if rc == 0:
                self.result.emit(True, "Deleted")
            else:
                err = getattr(proc, 'stderr', '') or str(proc)
                # Detect the specific Nextflow message about uncommitted changes and request confirmation
                try:
                    from pathlib import Path as _Path
                    assets_dir = str(_Path.home() / ".nextflow" / "assets" / self.pipeline_name)
                except Exception:
                    assets_dir = str(self.pipeline_name)

                low_err = err.lower()
                # Detect known Nextflow refusal reasons: uncommitted changes or corrupted repo
                if (
                    'uncommitted changes' in low_err
                    or "won't drop" in low_err
                    or 'local project repository contains uncommitted changes' in low_err
                    or "can't find git repository config file" in low_err
                    or 'repository may be corrupted' in low_err
                ):
                    # Ask the GUI to request user confirmation before force-deleting the folder
                    self.requires_confirmation.emit(assets_dir, err)
                    # Inform caller that deletion did not occur but requires force delete
                    self.result.emit(False, f"RequiresForceDelete:{assets_dir}:{err}")
                else:
                    self.result.emit(False, err)
        except Exception as e:
            logger.error(f"Error deleting pipeline: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class PipelineLocal(QWidget):

    active_runs = set()

    def __init__(self, parent=None):
        super().__init__(parent)
        # keep references to running processes so they are not GC'd
        self.processes = {}
        self.run_credentials = {}
        self._log_decoders = {}
        self.completed_detached_runs = {}
        self._encrypting_runs = set()
        self.output_displays = {}  # Store references to output display widgets by run_name
        self.current_pipeline_name = None  # Track the currently displayed pipeline
        
        self.constants = json_read(CONFIG_FILE)
        self.RUN_DIR = self.constants.get("folders",{}).get("RUN_DIR", RUN_DIR)
        self.PIPELINES_RUNS = self.constants.get("folders",{}).get("PIPELINES_RUNS", PIPELINES_RUNS)
        self.SAMPLE_PREP_DIR =  self.constants.get("folders",{}).get("SAMPLE_PREP_DIR", SAMPLE_PREP_DIR)
        
        # Worker thread and spinner for async pipeline info fetch
        self.info_worker = None
        self.info_worker_thread = None
        self.active_spinner = None  # Track the active spinner to prevent accessing deleted ones
        self.remote_run_name = None
        
        self.pipelines = []
        self.pipeline_info_lines = {}
        self.get_local_pipelines()
        self._recover_detached_runs()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(18, 16, 18, 16)
        main_layout.setSpacing(12)

        heading_layout = QHBoxLayout()
        heading_layout.setSpacing(10)
        heading = QLabel("Installed pipelines")
        heading.setObjectName("dashboardSectionTitle")
        self.pipeline_count = QLabel()
        self.pipeline_count.setObjectName("dashboardCount")
        heading_layout.addWidget(heading)
        heading_layout.addWidget(self.pipeline_count)
        heading_layout.addStretch()
        refresh_button = QPushButton("Refresh")
        refresh_button.setObjectName("refresh_local_pipelines")
        refresh_button.clicked.connect(self.refresh_pipelines)
        heading_layout.addWidget(refresh_button)
        main_layout.addLayout(heading_layout)

        # GRID LAYOUT FOR CARDS
        self.cards_grid = QGridLayout()
        self.cards_grid.setContentsMargins(12, 12, 12, 12)
        self.cards_grid.setHorizontalSpacing(12)
        self.cards_grid.setVerticalSpacing(12)

        self.cards_scroll = QScrollArea()
        self.cards_scroll.setObjectName("localPipelineScroll")
        self.cards_scroll.viewport().setStyleSheet("background-color: #f3f7f6;")
        self.cards_scroll.setWidgetResizable(True)

        # scroll only in vertical direction
        self.cards_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.cards_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.cards_scroll.setMaximumHeight(16777215)

        scroll_widget = QWidget()
        scroll_widget.setObjectName("localPipelineScrollContent")
        scroll_widget.setStyleSheet("background-color: #f3f7f6;")
        self.cards_content = scroll_widget
        scroll_widget.setLayout(self.cards_grid)
        self.empty_state = QLabel("No installed pipelines yet.", scroll_widget)
        self.empty_state.setObjectName("dashboardEmptyState")
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cards_scroll.setWidget(scroll_widget)

        # DETAILS BOX
        self.details_box = QFrame()
        self.details_box.hide()
        self.details_box.setObjectName("pipeline_info_box")
        self.details_box.setMinimumHeight(160)
        self.details_layout = QVBoxLayout(self.details_box)

        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        self.content_splitter.setObjectName("pipelineInfoSplitter")
        self.content_splitter.setHandleWidth(8)
        self.content_splitter.setChildrenCollapsible(False)
        self.content_splitter.addWidget(self.cards_scroll)
        self.content_splitter.addWidget(self.details_box)
        self.content_splitter.setStretchFactor(0, 2)
        self.content_splitter.setStretchFactor(1, 3)
        self.content_splitter.setStyleSheet("""
            QSplitter#pipelineInfoSplitter::handle { background-color: #dbe6e2; }
            QSplitter#pipelineInfoSplitter::handle:hover { background-color: #111111; }
        """)
        self._details_splitter_initialized = False
        main_layout.addWidget(self.content_splitter, 1)

        self.render_cards()

        self._run_monitor_timer = QTimer(self)
        self._run_monitor_timer.setInterval(1500)
        self._run_monitor_timer.timeout.connect(self._monitor_detached_runs)
        self._run_monitor_timer.start()


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

    def _run_metadata_path(self, run_name):
        run_dir = Path(self.RUN_DIR) / run_name.removesuffix(".txt")
        return run_dir / "omixforge-run.json"

    def _run_exit_path(self, run_name):
        run_dir = Path(self.RUN_DIR) / run_name.removesuffix(".txt")
        return run_dir / "omixforge-run.exit"

    @staticmethod
    def _process_start_token(pid):
        """Return Linux /proc start time to guard against PID reuse."""
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
            fields_after_name = stat[stat.rfind(")") + 1:].split()
            return fields_after_name[19]
        except (OSError, IndexError, ValueError):
            return None

    @classmethod
    def _pid_is_running(cls, pid, start_token=None):
        if not pid:
            return False
        try:
            os.kill(int(pid), 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            pass
        except (OSError, ValueError, TypeError):
            return False
        try:
            stat = Path(f"/proc/{int(pid)}/stat").read_text()
            fields_after_name = stat[stat.rfind(")") + 1:].split()
            if fields_after_name[0] == "Z":
                return False
            current_token = fields_after_name[19]
        except OSError:
            # Some confined builds restrict /proc reads; kill(pid, 0) already
            # confirmed that a process with this PID exists.
            return True
        except (IndexError, ValueError):
            return False
        return current_token == start_token if start_token is not None else current_token is not None

    def _read_run_exit_code(self, run_name):
        try:
            value = self._run_exit_path(run_name).read_text().strip()
            return int(value) if value != "interrupted" else value
        except (OSError, ValueError):
            return None

    def _recover_detached_runs(self):
        """Restore run state from detached supervisors left by a previous app session."""
        run_root = Path(self.RUN_DIR)
        if not run_root.exists():
            return
        for metadata_path in run_root.glob("*/omixforge-run.json"):
            try:
                metadata = json.loads(metadata_path.read_text())
                run_name = metadata["run_name"]
                pid = int(metadata["pid"])
                start_token = metadata.get("process_start_token")
                exit_code = self._read_run_exit_code(run_name)
                if exit_code is not None:
                    # If the plaintext run folder remains, encryption either did
                    # not start or was interrupted. Rebuild the archive after login.
                    if metadata.get("encrypted") and metadata_path.parent.exists():
                        self.completed_detached_runs[run_name] = (metadata, exit_code)
                    continue
                if self._pid_is_running(pid, start_token):
                    self.processes[run_name] = {
                        "proc": None,
                        "pipeline": metadata.get("pipeline"),
                        "detached": True,
                        "pid": pid,
                        "process_start_token": start_token,
                        "metadata": metadata,
                    }
                    PipelineLocal.active_runs.add(run_name)
                    continue

                log_path = Path(metadata.get("log_path", Path(self.PIPELINES_RUNS) / run_name))
                with log_path.open("a", encoding="utf-8") as log_file:
                    log_file.write(
                        "\nPipeline supervisor stopped before recording an exit code. "
                        "The run may have been interrupted while OmixForge was closed.\n"
                        "Pipeline run completed <<exit-code:interrupted>>.\n"
                    )
                self._run_exit_path(run_name).write_text("interrupted\n")
                if metadata.get("encrypted") and metadata_path.parent.exists():
                    self.completed_detached_runs[run_name] = (metadata, "interrupted")
            except (OSError, ValueError, KeyError, TypeError) as exc:
                logger.warning(f"Could not restore detached run from {metadata_path}: {exc}")

    def get_active_run_names(self):
        return [
            run_name for run_name, entry in self.processes.items()
            if entry.get("detached")
            and (
                entry["proc"].poll() is None
                if entry.get("proc") is not None
                else self._pid_is_running(entry.get("pid"), entry.get("process_start_token"))
            )
        ]

    def _monitor_detached_runs(self):
        for run_name, entry in list(self.processes.items()):
            if not entry.get("detached"):
                continue
            popen = entry.get("proc")
            if popen is not None:
                exit_code = popen.poll()
                if exit_code is not None:
                    self._finish_detached_run(run_name, exit_code)
            elif not self._pid_is_running(entry.get("pid"), entry.get("process_start_token")):
                exit_code = self._read_run_exit_code(run_name)
                if exit_code is None:
                    self._record_interrupted_run(run_name, entry.get("metadata", {}))
                    exit_code = "interrupted"
                self._finish_detached_run(run_name, exit_code)

    def _record_interrupted_run(self, run_name, metadata):
        log_path = Path(metadata.get("log_path", Path(self.PIPELINES_RUNS) / run_name))
        try:
            with log_path.open("a", encoding="utf-8") as log_file:
                log_file.write(
                    "\nPipeline supervisor stopped before recording an exit code. "
                    "The run may have been interrupted while OmixForge was closed.\n"
                    "Pipeline run completed <<exit-code:interrupted>>.\n"
                )
            self._run_exit_path(run_name).write_text("interrupted\n")
        except OSError as exc:
            logger.error(f"Could not record interrupted run {run_name}: {exc}")

    def _finish_detached_run(self, run_name, exit_code):
        entry = self.processes.pop(run_name, {})
        metadata = entry.get("metadata") or {}
        if not metadata:
            try:
                metadata = json.loads(self._run_metadata_path(run_name).read_text())
            except (OSError, ValueError):
                metadata = {}
        PipelineLocal.active_runs.discard(run_name)
        self._restore_run_controls_after_finish(run_name, metadata.get("pipeline"))
        self.completed_detached_runs[run_name] = (metadata, exit_code)
        credential = self.run_credentials.pop(run_name, None)
        if metadata.get("encrypted"):
            if credential:
                self._start_run_encryption(run_name, exit_code, credential)
        else:
            self.completed_detached_runs.pop(run_name, None)

    def _restore_run_controls_after_finish(self, run_name, pipeline_name=None):
        """Release the Run button when its run ends, without changing another pipeline's controls."""
        if getattr(self, "current_run_name", None) != run_name:
            return

        # The details pane can be switched while a pipeline runs. Only update the
        # visible buttons when they still belong to the pipeline that just ended.
        same_pipeline_is_visible = (
            not pipeline_name
            or getattr(self, "current_pipeline_name", None) == pipeline_name
        )
        if same_pipeline_is_visible:
            for button, enabled in (
                (getattr(self, "run_btn", None), True),
                (getattr(self, "cancel_btn", None), False),
            ):
                try:
                    if button is not None:
                        button.setEnabled(enabled)
                except RuntimeError:
                    # The details pane may have been rebuilt while the run was active.
                    pass

        self.current_run_name = None
        self.current_pipeline = None

    def attach_private_credentials(self, credential):
        """Use the just-authenticated credentials to finish encrypted background runs."""
        if not isinstance(credential, dict):
            return
        for run_name, entry in self.processes.items():
            if entry.get("metadata", {}).get("encrypted"):
                self.run_credentials[run_name] = dict(credential)
        for run_name, (metadata, exit_code) in list(self.completed_detached_runs.items()):
            if metadata.get("encrypted"):
                self._start_run_encryption(run_name, exit_code, dict(credential))

    def _start_run_encryption(self, run_name, exit_code, credential):
        if run_name in self._encrypting_runs:
            return
        base_name = run_name.removesuffix(".txt")
        archive_path = Path(self.RUN_DIR) / f"{base_name}.tar.gz.enc"
        run_dir = Path(self.RUN_DIR) / base_name
        if not run_dir.exists():
            self.completed_detached_runs.pop(run_name, None)
            return
        self._encrypting_runs.add(run_name)
        worker = ZipEncryptWorker(
            run_name, str(run_dir), str(archive_path.with_suffix("")), credential,
            exit_code if isinstance(exit_code, int) else 1,
        )
        worker.signals.finished.connect(self._on_zip_encrypt_done)
        worker.signals.error.connect(self._on_zip_encrypt_error)
        QThreadPool.globalInstance().start(worker)

    def _cancel_detached_run(self, run_name, message="Pipeline run cancelled by user."):
        entry = self.processes.get(run_name)
        if not entry or not entry.get("detached"):
            return False
        pid = entry.get("pid")
        token = entry.get("process_start_token")
        exit_path = self._run_exit_path(run_name)
        log_path = Path(entry.get("metadata", {}).get("log_path", Path(self.PIPELINES_RUNS) / run_name))
        if self._pid_is_running(pid, token):
            try:
                os.killpg(int(pid), signal.SIGTERM)
            except OSError as exc:
                logger.warning(f"Could not signal pipeline run {run_name}: {exc}")
            deadline = time.monotonic() + 4
            while time.monotonic() < deadline and self._pid_is_running(pid, token):
                time.sleep(0.1)
            if self._pid_is_running(pid, token):
                try:
                    os.killpg(int(pid), signal.SIGKILL)
                except OSError as exc:
                    logger.warning(f"Could not force-stop pipeline run {run_name}: {exc}")

        if not exit_path.exists():
            try:
                with log_path.open("a", encoding="utf-8") as log_file:
                    log_file.write(f"\n{message} <<exit-code:143>>.\n")
                exit_path.write_text("143\n")
            except OSError as exc:
                logger.error(f"Could not record cancellation for {run_name}: {exc}")

        proc = entry.get("proc")
        if proc is not None:
            try:
                proc.wait(timeout=0.2)
            except (subprocess.TimeoutExpired, OSError):
                pass
        self.processes.pop(run_name, None)
        self.run_credentials.pop(run_name, None)
        self.completed_detached_runs.pop(run_name, None)
        PipelineLocal.active_runs.discard(run_name)
        return True
    
    def refresh_pipelines(self):
        """Refresh the local pipelines list and re-render cards."""
        logger.info("Refreshing local pipelines...")
        self.pipelines = []
        self.get_local_pipelines()
        self.render_cards()
        logger.info(f"Refreshed: found {len(self.pipelines)} pipelines")


    def render_cards(self):
        columns = 3
        card_height = 70
        row = 0
        col = 0
        self.pipeline_count.setText(f"{len(self.pipelines)} available")

        if len(self.pipelines) > 15:
            margins = self.cards_grid.contentsMargins()
            visible_rows = 5
            self.cards_scroll.setMaximumHeight(
                visible_rows * card_height
                + (visible_rows - 1) * self.cards_grid.verticalSpacing()
                + margins.top()
                + margins.bottom()
                + 2 * self.cards_scroll.frameWidth()
            )
        else:
            self.cards_scroll.setMaximumHeight(16777215)

        # Clear existing cards so re-rendering doesn't duplicate widgets
        for i in reversed(range(self.cards_grid.count())):
            item = self.cards_grid.takeAt(i)
            if item.widget() and item.widget() is not self.empty_state:
                item.widget().deleteLater()

        if not self.pipelines:
            self.cards_grid.addWidget(self.empty_state, 0, 0, 1, columns)
            self.empty_state.show()
            self.cards_content.setMinimumHeight(0)
            return

        self.cards_grid.removeWidget(self.empty_state)
        self.empty_state.hide()

        for index, name in enumerate(self.pipelines):
            card = PipelineCard(name)
            card.setMaximumHeight(200) 
            card.setMinimumHeight(70)
            card.clicked.connect(self.on_card_clicked)

            # Add card to grid
            self.cards_grid.addWidget(card, row, col)

            # next column
            col += 1

            # wrap to next row
            if col >= columns:
                col = 0
                row += 1

        margins = self.cards_grid.contentsMargins()
        rows = (len(self.pipelines) + columns - 1) // columns
        content_height = (
            rows * card_height
            + (rows - 1) * self.cards_grid.verticalSpacing()
            + margins.top()
            + margins.bottom()
        )
        self.cards_content.setMinimumHeight(content_height)

    def _find_run_for_pipeline(self, pipeline_name: str):
        """Return the run_name key for a running process matching pipeline_name, or None."""
        remote_run_name = getattr(self, "remote_run_name", None)
        if remote_run_name and getattr(self, "remote_pipeline", None) == pipeline_name:
            return remote_run_name
        for rn, entry in self.processes.items():
            try:
                p_name = entry.get('pipeline')
                if p_name and (pipeline_name == p_name or pipeline_name == p_name.replace('nf-core/', '')):
                    return rn
                proc = entry.get('proc')
                args = proc.arguments() if proc else []
                if pipeline_name in args:
                    return rn
                short = pipeline_name.replace("nf-core/", "")
                if short in args:
                    return rn
            except Exception:
                continue
        return None


    def on_card_clicked(self, name):
        """Handle pipeline card click - start async info fetch with spinner."""
        # Store the current pipeline name for use in on_run_clicked
        self.current_pipeline_name = name
        
        # Clear old details (includes nested layouts and widgets)
        self.clear_layout(self.details_layout)
        # Clear the old spinner reference so signals from old workers are ignored
        self.active_spinner = None
        
        # Stop any existing worker thread - ensure it fully stops before proceeding
        if self.info_worker_thread is not None:
            try:
                # Check if thread is still alive before quitting
                if self.info_worker_thread.isRunning():
                    self.info_worker_thread.quit()
                    # Wait up to 3 seconds for graceful shutdown
                    if not self.info_worker_thread.wait(3000):
                        # If thread didn't stop gracefully, force kill it
                        logger.warning("Worker thread didn't stop gracefully, forcing termination")
                        # Note: terminate() is more forceful than quit()
                        # We already called quit(), so just wait a bit longer
                        self.info_worker_thread.wait(1000)
            except (RuntimeError, AttributeError):
                # Thread was already deleted or is invalid
                pass
            finally:
                self.info_worker_thread = None
                self.info_worker = None
        
        # Create and show spinner
        spinner = WaitingSpinner(self.details_box)
        spinner.start()
        self.active_spinner = spinner  # Store reference to active spinner
        spinner_label = QLabel("Loading pipeline info...")
        spinner_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.details_layout.addWidget(spinner)
        self.details_layout.addWidget(spinner_label)
        self.details_box.show()
        
        # Create worker thread
        self.info_worker = PipelineInfoWorker(name)
        self.info_worker_thread = QThread()
        self.info_worker.moveToThread(self.info_worker_thread)
        
        # Connect signals
        self.info_worker_thread.started.connect(self.info_worker.run)
        self.info_worker.info_ready.connect(lambda info: self._on_pipeline_info_ready(info, name, spinner))
        self.info_worker.error.connect(lambda err: self._on_pipeline_info_error(err, spinner))
        # ensure thread quits when worker finishes and clean up objects
        self.info_worker.finished.connect(self.info_worker_thread.quit)
        self.info_worker.finished.connect(self.info_worker.deleteLater)
        # Note: do NOT call deleteLater on QThread itself; it causes "wrapped C/C++ object has been deleted" errors
        
        # Start the thread
        self.info_worker_thread.start()
    
    def _on_pipeline_info_ready(self, info, name, spinner):
        """Handle pipeline info ready signal - replace spinner with info."""
        # Ignore signal if this spinner is no longer active (user clicked another card)
        if spinner is not self.active_spinner:
            logger.debug(f"Ignoring info_ready signal for stale spinner (current pipeline: {self.current_pipeline_name})")
            return
        
        # Stop spinner
        try:
            spinner.stop()
        except RuntimeError:
            # Spinner was already deleted
            logger.debug("Spinner already deleted, skipping stop()")
            return
        
        # Update stored info
        self.pipeline_info_lines = info
        
        # Clear spinner and label
        for i in reversed(range(self.details_layout.count())):
            item = self.details_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # Build content from info
        content = ''
        for key, value in info.items():
            content += f"{key}: {value}\n\n"

        self.action_items_top = QHBoxLayout()

        close_btn = QPushButton("X", parent=self.details_box)
        close_btn.setObjectName("close_pipeline_details")
        close_btn.setStyleSheet(close_button_style())
        close_btn.setFixedSize(40,30)
        close_btn.clicked.connect(self._on_close_button_click)
        self.action_items_top.addStretch()
        self.action_items_top.addWidget(close_btn)

        self.details_layout.addLayout(self.action_items_top)

        self._details_content_label = QLabel(content)
        self._details_content_label.setObjectName("pipelineInfoLog")
        self._details_content_label.setWordWrap(True)
        self._details_content_label.setFont(QFont("Courier New", 10))

        # Scroll area
        scroll = QScrollArea()
        scroll.viewport().setStyleSheet("background-color: #ffffff;")
        scroll.setWidgetResizable(True)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setWidget(self._details_content_label)

        self.details_layout.addWidget(scroll)
                
        self.action_section = QHBoxLayout()
        
        delete_btn = QPushButton("Delete", parent=self.details_box)
        delete_btn.setObjectName("pipeline_delete_btn")
        delete_btn.setFixedSize(70, 30)
        delete_btn.clicked.connect(self.on_delete_clicked)

        # Run and Cancel buttons
        self.run_btn = QPushButton("Run", parent=self.details_box)
        self.run_btn.setObjectName("pipeline_run_btn")
        self.run_btn.setFixedSize(60, 30)
        self.run_btn.clicked.connect(self.on_run_clicked)

        self.cancel_btn = QPushButton("Cancel", parent=self.details_box)
        self.cancel_btn.setObjectName("pipeline_cancel_btn")
        self.cancel_btn.setFixedSize(70, 30)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)

        # If this pipeline already has a running process, reflect that in the UI
        running_rn = self._find_run_for_pipeline(name)
        if running_rn:
            self.run_btn.setEnabled(False)
            self.cancel_btn.setEnabled(running_rn != getattr(self, "remote_run_name", None))
            # set current run tracking so cancel will refer to the right process
            self.current_run_name = running_rn
            self.current_pipeline = name
        else:
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)

        self.action_section.addWidget(self.run_btn)
        self.action_section.addWidget(self.cancel_btn)
        self.action_section.addWidget(delete_btn)
        self.details_layout.addLayout(self.action_section)
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

    def _on_pipeline_info_error(self, error_msg, spinner):
        """Handle pipeline info error - show error message."""
        # Ignore signal if this spinner is no longer active (user clicked another card)
        if spinner is not self.active_spinner:
            logger.debug(f"Ignoring info_error signal for stale spinner (current pipeline: {self.current_pipeline_name})")
            return
        
        # Stop spinner
        try:
            spinner.stop()
        except RuntimeError:
            # Spinner was already deleted
            logger.debug("Spinner already deleted, skipping stop()")
            return
        
        # Clear spinner and label
        for i in reversed(range(self.details_layout.count())):
            item = self.details_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # Show error
        error_label = QLabel(f"Error loading pipeline info:\n{error_msg}")
        error_label.setStyleSheet("color: red;")
        error_label.setWordWrap(True)
        self.details_layout.addWidget(error_label)
    
    def on_delete_clicked(self):
        """Asynchronously delete a pipeline using PipelineDeleteWorker and show a spinner.

        This replaces the previous synchronous `nextflow drop` call so the UI remains responsive.
        """
        try:
            # Determine pipeline name (prefer stored current_pipeline_name)
            pipeline = getattr(self, 'current_pipeline_name', None)

            if not pipeline and isinstance(self.pipeline_info_lines, dict):
                pipeline = self.pipeline_info_lines.get('name') or self.pipeline_info_lines.get('Name')

            if not pipeline:
                # last-resort scan for a QLabel containing a "Key: value" pattern
                for i in range(self.details_layout.count()):
                    item = self.details_layout.itemAt(i)
                    w = item.widget() if item is not None else None
                    if w and isinstance(w, QLabel) and hasattr(w, 'text'):
                        txt = w.text()
                        if ": " in txt:
                            pipeline = txt.split(": ", 1)[1].strip()
                            break

            if not pipeline:
                logger.error("Could not determine pipeline name to delete")
                return

            # Confirm deletion with the user
            resp = QMessageBox.question(
                self,
                "Confirm Delete",
                f"Delete pipeline {pipeline}? This will remove the local pipeline.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if resp != QMessageBox.StandardButton.Yes:
                return

            # Show spinner and label in the details pane
            spinner = WaitingSpinner(self.details_box)
            spinner.start()
            deleting_label = QLabel("Deleting pipeline...")
            deleting_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.details_layout.addWidget(spinner)
            self.details_layout.addWidget(deleting_label)

            # Setup worker and thread
            delete_worker = PipelineDeleteWorker(pipeline)
            delete_thread = QThread()
            delete_worker.moveToThread(delete_thread)

            # Connect a handler for cases where nextflow reports uncommitted changes
            def _handle_requires_confirmation(pipeline_dir, error_msg):
                try:
                    # Ask user if they want to force-delete the local assets folder
                    resp2 = QMessageBox.question(
                        self,
                        "Force Delete Pipeline",
                        f"Nextflow could not drop the pipeline due to local repository issues:\n{error_msg}\n\nForcefully delete the local pipeline folder at:\n{pipeline_dir}?\nThis will permanently remove the pipeline assets.",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    )
                    if resp2 != QMessageBox.StandardButton.Yes:
                        try:
                            err_label = QLabel("Delete aborted by user. Pipeline not removed.")
                            err_label.setStyleSheet("color: red;")
                            err_label.setWordWrap(True)
                            self.details_layout.addWidget(err_label)
                        except Exception:
                            pass
                        return

                    # User confirmed - attempt to remove the directory
                    try:
                        delete_directory(pipeline_dir)
                        # Clean up spinner and deleting label if present
                        try:
                            spinner.stop()
                        except Exception:
                            pass
                        try:
                            for j in reversed(range(self.details_layout.count())):
                                it = self.details_layout.itemAt(j)
                                w = it.widget() if it is not None else None
                                if w is spinner or w is deleting_label:
                                    try:
                                        self.details_layout.removeWidget(w)
                                    except Exception:
                                        pass
                                    try:
                                        w.deleteLater()
                                    except Exception:
                                        pass
                        except Exception:
                            pass

                        # Refresh UI
                        try:
                            self.refresh_pipelines()
                        except Exception:
                            pass
                        try:
                            self.details_box.hide()
                        except Exception:
                            pass
                        QMessageBox.information(self, "Deleted", f"Pipeline folder removed: {pipeline_dir}")
                    except Exception as e:
                        logger.error(f"Force delete failed for {pipeline_dir}: {e}")
                        QMessageBox.critical(self, "Force Delete Failed", f"Failed to remove {pipeline_dir}: {e}")
                except Exception as e:
                    logger.error(f"Error in force-delete confirmation handler: {e}")

            delete_worker.requires_confirmation.connect(_handle_requires_confirmation)

            # retain references so they are not garbage-collected while running
            self.delete_worker = delete_worker
            self.delete_thread = delete_thread

            def _cleanup_spinner_and_widgets():
                try:
                    spinner.stop()
                except Exception:
                    pass
                try:
                    # remove spinner and deleting_label if still present
                    for j in reversed(range(self.details_layout.count())):
                        it = self.details_layout.itemAt(j)
                        w = it.widget() if it is not None else None
                        if w is spinner or w is deleting_label:
                            try:
                                self.details_layout.removeWidget(w)
                            except Exception:
                                pass
                            try:
                                w.deleteLater()
                            except Exception:
                                pass
                except Exception:
                    pass

            def _on_delete_result(success, message):
                _cleanup_spinner_and_widgets()
                if success:
                    logger.info(f"Successfully deleted pipeline: {pipeline}")
                    try:
                        # Refresh pipelines and UI
                        self.refresh_pipelines()
                        # Aggressively clear details pane: remove all widgets and layouts
                        while self.details_layout.count() > 0:
                            it = self.details_layout.takeAt(0)
                            if it is not None:
                                # Handle widgets
                                w = it.widget()
                                if w is not None:
                                    try:
                                        self.details_layout.removeWidget(w)
                                    except Exception:
                                        pass
                                    try:
                                        w.deleteLater()
                                    except Exception:
                                        pass
                                # Handle nested layouts
                                else:
                                    sub_layout = it.layout()
                                    if sub_layout is not None:
                                        while sub_layout.count() > 0:
                                            sub_it = sub_layout.takeAt(0)
                                            if sub_it and sub_it.widget():
                                                try:
                                                    sub_it.widget().deleteLater()
                                                except Exception:
                                                    pass
                        self.details_box.hide()
                    except Exception as e:
                        logger.error(f"Error clearing details after delete: {e}")
                else:
                    logger.error(f"Failed to delete pipeline {pipeline}: {message}")
                    try:
                        err_label = QLabel(f"Delete failed: {message}")
                        err_label.setStyleSheet("color: red;")
                        err_label.setWordWrap(True)
                        self.details_layout.addWidget(err_label)
                    except Exception:
                        pass
                try:
                    delete_thread.quit()
                except Exception:
                    pass

            def _on_delete_error(err):
                _cleanup_spinner_and_widgets()
                logger.error(f"Error deleting pipeline: {err}")
                try:
                    err_label = QLabel(f"Delete error: {err}")
                    err_label.setStyleSheet("color: red;")
                    err_label.setWordWrap(True)
                    self.details_layout.addWidget(err_label)
                except Exception:
                    pass
                try:
                    delete_thread.quit()
                except Exception:
                    pass

            delete_worker.result.connect(_on_delete_result)
            delete_worker.error.connect(_on_delete_error)
            delete_worker.finished.connect(delete_thread.quit)
            # ensure proper cleanup of worker (NOT thread; threads shouldn't be deleteLater'd)
            delete_worker.finished.connect(delete_worker.deleteLater)
            # when thread finishes, clear our references
            def _on_delete_thread_finished():
                try:
                    self.delete_worker = None
                except Exception:
                    pass
                try:
                    self.delete_thread = None
                except Exception:
                    pass
            delete_thread.finished.connect(_on_delete_thread_finished)
            delete_thread.started.connect(delete_worker.run)

            # Start deletion thread
            delete_thread.start()

        except Exception as e:
            logger.error(f"Error deleting pipeline: {e}")
            try:
                QMessageBox.critical(self, "Delete Error", f"Failed to delete pipeline: {e}")
            except Exception:
                pass

    def on_run_clicked(self):
        # Get the pipeline name from stored attribute
        pipeline = self.current_pipeline_name
        if not pipeline:
            QMessageBox.warning(self, "Error", "No pipeline selected.")
            return

        # Guard against stale button state and rapid repeated clicks.
        existing_run = self._find_run_for_pipeline(pipeline)
        if existing_run:
            self.run_btn.setEnabled(False)
            self.cancel_btn.setEnabled(existing_run != getattr(self, "remote_run_name", None))
            self.current_run_name = existing_run
            self.current_pipeline = pipeline
            return
        
        
        run_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        run_name = f"{pipeline}_{run_time}_run.txt".replace("nf-core/", "")
        run_dir = f"{self.RUN_DIR}/{run_name.replace('.txt', '')}"

        # Show the args dialog
        dialog = PipelineArgsDialog(pipeline, str(run_dir), self.pipeline_info_lines, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get the config
        config = dialog.get_config()
        
        # Validate mandatory args
        if not config.get("input"):
            QMessageBox.warning(self, "Missing Argument", "Please specify the input (sample sheet) file.")
            return

        if config.get("submit_to_server"):
            ssh_server = config.get("ssh_server")
            if not ssh_server:
                QMessageBox.warning(self, "SSH config", "Please select a valid configured SSH server.")
                return

            # Create worker and thread for remote submission
            self.remote_worker = RemotePipelineWorker(pipeline, run_dir, config, ssh_server, run_name, self.PIPELINES_RUNS, self.RUN_DIR)
            self.remote_thread = QThread()
            self.remote_worker.moveToThread(self.remote_thread)

            # Track remote submission as an active run for badge counting
            self.remote_run_name = run_name
            self.remote_pipeline = pipeline
            self.current_run_name = run_name
            self.current_pipeline = pipeline
            PipelineLocal.active_runs.add(run_name)
            self.run_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)

            # Connect signals
            self.remote_worker.progress.connect(self._on_remote_progress)
            self.remote_worker.finished.connect(self._on_remote_finished)
            self.remote_worker.error.connect(self._on_remote_error)
            self.remote_thread.started.connect(self.remote_worker.run)
            self.remote_worker.finished.connect(self.remote_thread.quit)
            self.remote_worker.error.connect(self.remote_thread.quit)
            self.remote_worker.finished.connect(self.remote_worker.deleteLater)
            self.remote_worker.error.connect(self.remote_worker.deleteLater)
            self.remote_thread.finished.connect(self.remote_thread.deleteLater)

            # Start the thread
            self.remote_thread.start()
            QMessageBox.information(self, "Pipeline Submitted", f"Submitting pipeline to {ssh_server.get('name', ssh_server.get('host'))}...")
            return

        ensure_directory([str(run_dir), self.PIPELINES_RUNS ])

        logger.info(f"Starting pipeline: {pipeline}")
        try:
            app = QApplication.instance()
            credential = getattr(app, "cred", None) if app is not None else None
            if isinstance(credential, dict) and credential:
                # Write the marker before creating any shared log output so a
                # public session never sees a private run during startup.
                private_marker = Path(self.RUN_DIR) / ".private_runs" / f"{Path(run_name).stem}.json"
                private_marker.parent.mkdir(parents=True, exist_ok=True)
                private_marker.write_text(json.dumps({"run_name": run_name}), encoding="utf-8")
                try:
                    private_marker.chmod(0o600)
                    private_marker.parent.chmod(0o700)
                except OSError:
                    pass

            # Write config to JSON file in run directory
            config_file = f"{run_dir}/params.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            write_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Running pipeline: {pipeline}\n")
            write_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Config: {json.dumps(config, indent=2)}\n")

            selected_revision = config.get("rev", "master")
            nextflow_args = [
                "run",
                pipeline,
                "-revision",
                selected_revision,
                "-profile",
                "docker",
                "-params-file",
                str(config_file),
            ]

            log_path = str(Path(self.PIPELINES_RUNS) / run_name)
            exit_path = str(self._run_exit_path(run_name))
            supervisor = (
                'log_file="$1"; exit_file="$2"; shift 2; '
                'on_signal() { '
                'printf "\\nPipeline run cancelled by user. <<exit-code:143>>.\\n" >>"$log_file"; '
                'printf "143\\n" >"$exit_file"; exit 143; }; '
                'trap on_signal TERM INT HUP; '
                'nextflow "$@" >>"$log_file" 2>&1; exit_code=$?; '
                'printf "\\nPipeline run completed <<exit-code:%s>>.\\n" "$exit_code" >>"$log_file"; '
                'printf "%s\\n" "$exit_code" >"$exit_file"; exit "$exit_code"'
            )
            proc = subprocess.Popen(
                ["/bin/sh", "-c", supervisor, "omixforge-runner", log_path, exit_path, *nextflow_args],
                cwd=str(run_dir),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )

            metadata = {
                "run_name": run_name,
                "pipeline": pipeline,
                "pid": proc.pid,
                "process_start_token": self._process_start_token(proc.pid),
                "started_at": datetime.now().isoformat(timespec="seconds"),
                "log_path": log_path,
                "exit_path": exit_path,
                "encrypted": isinstance(credential, dict) and bool(credential),
            }
            try:
                metadata_path = self._run_metadata_path(run_name)
                metadata_path.parent.mkdir(parents=True, exist_ok=True)
                temporary_metadata = metadata_path.with_suffix(".tmp")
                temporary_metadata.write_text(json.dumps(metadata, indent=2))
                temporary_metadata.replace(metadata_path)
            except Exception:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except OSError:
                    pass
                proc.wait(timeout=3)
                raise

            self.processes[run_name] = {
                "proc": proc,
                "pipeline": pipeline,
                "detached": True,
                "pid": proc.pid,
                "process_start_token": metadata["process_start_token"],
                "metadata": metadata,
            }
            self.run_credentials[run_name] = dict(credential) if isinstance(credential, dict) else None
            PipelineLocal.active_runs.add(run_name)

            # mark current run/pipeline
            self.current_run_name = run_name
            self.current_pipeline = pipeline
            # disable the run button and enable cancel
            try:
                self.run_btn.setEnabled(False)
            except Exception:
                pass
            try:
                self.cancel_btn.setEnabled(True)
            except Exception:
                pass

            QMessageBox.information(self, "Pipeline Started", f"Started {pipeline}\nConfig saved to {config_file}")
        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")
            append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Error starting pipeline: {e}\n")
            QMessageBox.critical(self, "Error", f"Failed to start pipeline: {e}")

    def _proc_stdout(self, run_name):
        self._drain_process_stream(run_name, "stdout")

    def _proc_stderr(self, run_name):
        self._drain_process_stream(run_name, "stderr")

    def _drain_process_stream(self, run_name, stream_name, final=False):
        entry = self.processes.get(run_name)
        if not entry:
            return
        proc = entry.get('proc')
        if not proc:
            return
        try:
            read_output = (
                proc.readAllStandardOutput
                if stream_name == "stdout"
                else proc.readAllStandardError
            )
            raw_output = read_output().data()
            decoder = self._log_decoders.setdefault(run_name, {}).get(stream_name)
            if decoder is None:
                decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
                self._log_decoders[run_name][stream_name] = decoder
            text = decoder.decode(raw_output, final=final)
            if text:
                append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", text)
                if stream_name == "stderr":
                    logger.error(text.rstrip())
                else:
                    logger.info(text.rstrip())
        except Exception as e:
            logger.error(f"Error reading {stream_name} for {run_name}: {e}")

    def on_cancel_clicked(self):
        # Cancel the currently running pipeline (if any)
        if not hasattr(self, 'current_run_name') or not self.current_run_name:
            return
        rn = self.current_run_name
        entry = self.processes.get(rn)
        if not entry:
            return
        if entry.get("detached"):
            self._cancel_detached_run(rn)
            self.current_run_name = None
            self.current_pipeline = None
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
            return
        proc = entry.get('proc')
        if not proc:
            return
        try:
            append_to_file(f"{self.PIPELINES_RUNS}/{rn}", "Pipeline run cancelled by user.\n")
            logger.info(f"Cancelling pipeline run: {rn}")
            if proc.state() != QProcess.ProcessState.NotRunning:
                proc.terminate()
                proc.waitForFinished(2000)
                if proc.state() != QProcess.ProcessState.NotRunning:
                    proc.kill()
                    proc.waitForFinished(1000)
        except Exception as e:
            logger.error(f"Error cancelling pipeline {rn}: {e}")
        finally:
            # clean up and update UI
            try:
                proc.deleteLater()
            except Exception:
                pass
            self.processes.pop(rn, None)
            self.run_credentials.pop(rn, None)
            PipelineLocal.active_runs.discard(rn)
            try:
                self.run_btn.setEnabled(True)
            except Exception:
                pass
            try:
                self.cancel_btn.setEnabled(False)
            except Exception:
                pass
            self.current_run_name = None
            self.current_pipeline = None

    def cancel_active_runs(self):
        """Stop every local pipeline process before leaving the workspace."""
        run_names = list(self.processes)
        for run_name, entry in list(self.processes.items()):
            if entry.get("detached"):
                self._cancel_detached_run(
                    run_name,
                    "Pipeline run cancelled by user during logout.",
                )
                continue
            proc = entry.get("proc") if entry else None
            if proc is None:
                continue
            try:
                self._proc_stdout(run_name)
                self._proc_stderr(run_name)
                for signal in (
                    proc.readyReadStandardOutput,
                    proc.readyReadStandardError,
                    proc.finished,
                ):
                    try:
                        signal.disconnect()
                    except (TypeError, RuntimeError):
                        pass
                if proc.state() != QProcess.ProcessState.NotRunning:
                    proc.terminate()
                    if not proc.waitForFinished(2000):
                        proc.kill()
                        proc.waitForFinished(1000)
                self._drain_process_stream(run_name, "stdout", final=True)
                self._drain_process_stream(run_name, "stderr", final=True)
                append_to_file(
                    f"{self.PIPELINES_RUNS}/{run_name}",
                    "Pipeline run cancelled by user during logout.\n",
                )
            except Exception as exc:
                logger.error(f"Error cancelling pipeline {run_name} during logout: {exc}")
            finally:
                try:
                    proc.deleteLater()
                except Exception:
                    pass
                self.processes.pop(run_name, None)
                self.run_credentials.pop(run_name, None)
                self._log_decoders.pop(run_name, None)
                PipelineLocal.active_runs.discard(run_name)

        if getattr(self, "current_run_name", None) in run_names:
            self.current_run_name = None
            self.current_pipeline = None
        try:
            self.run_btn.setEnabled(True)
            self.cancel_btn.setEnabled(False)
        except Exception:
            pass

    def _on_remote_progress(self, message):
        logger.info(f"Remote pipeline progress: {message}")

    def _on_remote_finished(self, success, message):
        run_name = getattr(self, "remote_run_name", None)
        pipeline = getattr(self, "remote_pipeline", None)
        if success:
            logger.info(f"Remote pipeline finished: {message}")
            QMessageBox.information(self, "Remote Pipeline", message)
        else:
            logger.error(f"Remote pipeline failed: {message}")
            QMessageBox.critical(self, "Remote Pipeline Error", message)

        if run_name:
            PipelineLocal.active_runs.discard(run_name)
            self._restore_run_controls_after_finish(run_name, pipeline)
        self.remote_run_name = None
        self.remote_pipeline = None

        # Clean up references
        self.remote_worker = None
        self.remote_thread = None

    def _on_remote_error(self, error_msg):
        run_name = getattr(self, "remote_run_name", None)
        pipeline = getattr(self, "remote_pipeline", None)
        logger.error(f"Remote pipeline error: {error_msg}")
        QMessageBox.critical(self, "Remote Pipeline Error", f"Remote submission failed: {error_msg}")

        if run_name:
            PipelineLocal.active_runs.discard(run_name)
            self._restore_run_controls_after_finish(run_name, pipeline)
        self.remote_run_name = None
        self.remote_pipeline = None

        # Clean up references
        self.remote_worker = None
        self.remote_thread = None

    def _proc_finished(self, run_name, exitCode, exitStatus):
        try:
            self._drain_process_stream(run_name, "stdout", final=True)
            self._drain_process_stream(run_name, "stderr", final=True)
            run_credential = self.run_credentials.get(run_name)
            if run_credential:
                zip_name = f"{self.RUN_DIR}/{run_name.replace('.txt', '.tar.gz')}"
                run_dir = f"{self.RUN_DIR}/{run_name.replace('.txt','')}"
                worker = ZipEncryptWorker(run_name, run_dir, zip_name, run_credential, exitCode)
                worker.signals.finished.connect(self._on_zip_encrypt_done)
                worker.signals.error.connect(self._on_zip_encrypt_error)
                QThreadPool.globalInstance().start(worker)
            else:
                append_to_file(
                    f"{self.PIPELINES_RUNS}/{run_name}",
                    f"Pipeline run completed <<exit-code:{exitCode}>>.\n",
                )
                logger.info(f"Pipeline {run_name} finished (code={exitCode})")
        except Exception as e:
            logger.error(f"Failed to complete run - {e}")
            append_to_file(
                f"{self.PIPELINES_RUNS}/{run_name}",
                "Pipeline run completed <<exit-code:1>>.\n",
            )

        finally:
            # Clean up stored process
            entry = self.processes.pop(run_name, None)
            self.run_credentials.pop(run_name, None)
            self._log_decoders.pop(run_name, None)
            PipelineLocal.active_runs.discard(run_name)
            proc = None
            if entry:
                proc = entry.get('proc')
                try:
                    # ensure process is not running
                    if proc and proc.state() != QProcess.ProcessState.NotRunning:
                        proc.kill()
                        proc.waitForFinished(2000)
                except Exception:
                    pass
                try:
                    if proc:
                        proc.deleteLater()
                except Exception:
                    pass
            self._restore_run_controls_after_finish(
                run_name,
                entry.get("pipeline") if entry else None,
            )

    def _on_zip_encrypt_done(self, run_name, exitCode):
        logger.info(f"Zip/encrypt cleanup completed for run: {run_name}")
        self._encrypting_runs.discard(run_name)
        self.completed_detached_runs.pop(run_name, None)
        logger.info(f"Pipeline {run_name} finished (code={exitCode})")


    def _on_zip_encrypt_error(self, run_name, err, exitCode):
        self._encrypting_runs.discard(run_name)
        logger.error(f"Zip/encrypt failed for run {run_name}: {err}")
        append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Pipeline run completed <<exit-code:{1}>>.\n")
        logger.error(f"Pipeline {run_name} finished (code={exitCode}) , But encryption failed")
        

    def closeEvent(self, event):
        # Detached supervisors outlive OmixForge; only legacy QProcesses are stopped here.
        if getattr(self, "_run_monitor_timer", None):
            self._run_monitor_timer.stop()
        for rn, entry in list(self.processes.items()):
            if entry.get("detached"):
                self.processes.pop(rn, None)
                self.run_credentials.pop(rn, None)
                continue
            proc = entry.get('proc') if entry else None
            try:
                if proc and proc.state() != QProcess.ProcessState.NotRunning:
                    proc.terminate()
                    proc.waitForFinished(2000)
                    if proc.state() != QProcess.ProcessState.NotRunning:
                        proc.kill()
                        proc.waitForFinished(1000)
            except Exception:
                pass
            try:
                if proc:
                    proc.deleteLater()
            except Exception:
                pass
            self.processes.pop(rn, None)
            self.run_credentials.pop(rn, None)
        
        # Stop any worker threads cleanly
        try:
            if getattr(self, 'info_worker_thread', None) is not None:
                if self.info_worker_thread.isRunning():
                    self.info_worker_thread.quit()
                    # Wait longer to ensure thread stops
                    if not self.info_worker_thread.wait(3000):
                        logger.warning("Info worker thread didn't stop in time during closeEvent")
                self.info_worker_thread = None
                self.info_worker = None
        except Exception as e:
            logger.error(f"Error stopping info worker thread: {e}")

        try:
            if getattr(self, 'delete_thread', None) is not None:
                if self.delete_thread.isRunning():
                    self.delete_thread.quit()
                    # Wait longer to ensure thread stops
                    if not self.delete_thread.wait(3000):
                        logger.warning("Delete worker thread didn't stop in time during closeEvent")
                self.delete_thread = None
                self.delete_worker = None
        except Exception as e:
            logger.error(f"Error stopping delete worker thread: {e}")

        try:
            if getattr(self, 'remote_thread', None) is not None:
                if self.remote_thread.isRunning():
                    self.remote_thread.quit()
                    # Wait longer to ensure thread stops
                    if not self.remote_thread.wait(3000):
                        logger.warning("Remote worker thread didn't stop in time during closeEvent")
                self.remote_thread = None
                self.remote_worker = None
        except Exception as e:
            logger.error(f"Error stopping remote worker thread: {e}")

        super().closeEvent(event)

class RemotePipelineWorker(QObject):
    """Worker to run pipeline on remote server asynchronously."""
    
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)  # success, message
    error = pyqtSignal(str)
    
    def __init__(self, pipeline, run_dir, config, ssh_server, run_name, pipelines_runs_dir, run_dir_base):
        super().__init__()
        self.pipeline = pipeline
        self.run_dir = run_dir
        self.config = config
        self.ssh_server = ssh_server
        self.run_name = run_name
        self.pipelines_runs_dir = pipelines_runs_dir
        self.run_dir_base = run_dir_base
    
    def run(self):
        try:
            # build paths - remove .txt extension from run_name for remote directory
            remote_base = f"/tmp/omixforge_runs/{self.run_name.replace(' ', '_').replace('.txt', '')}"
            host = self.ssh_server.get('host')
            user = self.ssh_server.get('username')
            port = self.ssh_server.get('port', "")
            if port == "":
                port = None
            key_path = self.ssh_server.get('key_path')
            if not all([host, user, key_path]):
                raise ValueError("Incomplete SSH server configuration")

            # ensure local run_dir exists and config stored
            ensure_directory([str(self.run_dir), self.pipelines_runs_dir])
            config_file = f"{self.run_dir}/params.json"
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)

            # Create initial log file
            local_log = f"{self.pipelines_runs_dir}/{self.run_name}"
            write_to_file(local_log, f"Remote pipeline submission started for {self.pipeline} on {self.ssh_server.get('host')}\n")

            sample_sheet = self.config.get('input')
            if not sample_sheet:
                raise ValueError("Sample sheet path missing")

            self.progress.emit("Creating remote directory...")
            append_to_file(local_log, "Creating remote directory...\n")
            # create remote directory
            if port is None:
                proc = subprocess.run(["ssh", "-i", key_path, f"{user}@{host}", f"mkdir -p {remote_base}"], 
                                    capture_output=True, text=True)
            else:
                proc = subprocess.run(["ssh", "-i", key_path, "-p", str(port), f"{user}@{host}", f"mkdir -p {remote_base}"], 
                                    capture_output=True, text=True)
            if proc.returncode != 0:
                append_to_file(local_log, f"Error: Failed to create remote directory <<exit-code:1>>: {proc.stderr}\n")
                raise RuntimeError(f"Failed to create remote dir: {proc.stderr}")

            self.progress.emit("Copying sample sheet...")
            append_to_file(local_log, "Copying sample sheet...\n")
            # copy sample sheet
            sample_sheet_name = Path(sample_sheet).name
            remote_sample_sheet = f"{remote_base}/{sample_sheet_name}"
            if port is None:
                proc = subprocess.run(["scp", "-i", key_path, sample_sheet, f"{user}@{host}:{remote_sample_sheet}"], 
                                capture_output=True, text=True)
            else:
                proc = subprocess.run(["scp", "-i", key_path, "-P", str(port), sample_sheet, f"{user}@{host}:{remote_sample_sheet}"], 
                                capture_output=True, text=True)
            if proc.returncode != 0:
                append_to_file(local_log, f"Error: Failed to copy sample sheet <<exit-code:1>>: {proc.stderr}\n")
                raise RuntimeError(f"Failed to copy sample sheet: {proc.stderr}")

            # Copy data files and collect filenames for remote path replacement
            self.progress.emit("Copying data files to remote...")
            append_to_file(local_log, "Copying data files to remote...\n")
            data_files_copied = []
            with open(sample_sheet, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    for key, value in row.items():
                        if key.startswith('fastq') and value:
                            file_path = Path(value).expanduser()
                            if file_path.exists():
                                filename = file_path.name
                                remote_file = f"{remote_base}/{filename}"
                                append_to_file(local_log, f"Copying data file: {file_path} -> {remote_file}\n")
                                if port is None:
                                    proc = subprocess.run(["scp", "-i", key_path, str(file_path), f"{user}@{host}:{remote_file}"], 
                                                        capture_output=True, text=True)
                                else:
                                    proc = subprocess.run(["scp", "-i", key_path, "-P", str(port), str(file_path), f"{user}@{host}:{remote_file}"], 
                                                        capture_output=True, text=True)
                                if proc.returncode != 0:
                                    error_msg = f"Failed to copy data file {file_path}: {proc.stderr}"
                                    append_to_file(local_log, f"Error: {error_msg}\n")
                                    raise RuntimeError(error_msg)
                                data_files_copied.append((str(file_path), remote_file))
                            else:
                                error_msg = f"Data file not found: {file_path}"
                                append_to_file(local_log, f"Warning: {error_msg}\n")
                                logger.warning(error_msg)

            # Create remote script to update sample sheet paths on the server
            self.progress.emit("Updating sample sheet paths on remote server...")
            append_to_file(local_log, "Updating sample sheet paths on remote server...\n")
            remote_script = f"{remote_base}/update_samplesheet.py"
            script_content = f"""#!/usr/bin/env python3
import csv
import sys

sample_sheet = "{remote_sample_sheet}"
remote_base = "{remote_base}"

# Mapping of original paths to remote paths
path_mapping = {{
{chr(10).join([f'    "{local}": "{remote}",' for local, remote in data_files_copied])}
}}

try:
    # Read sample sheet
    with open(sample_sheet, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames
    
    # Update paths
    for row in rows:
        for key in row:
            if key.startswith('fastq') and row[key]:
                if row[key] in path_mapping:
                    row[key] = path_mapping[row[key]]
    
    # Write updated sample sheet back
    with open(sample_sheet, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"Updated sample sheet: {{sample_sheet}}")
except Exception as e:
    print(f"Error updating sample sheet: {{e}}", file=sys.stderr)
    sys.exit(1)
"""
            
            # Write script to local temp location and copy to remote
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.py') as tmp:
                tmp.write(script_content)
                tmp_script_path = tmp.name
            
            try:
                if port is None:
                    proc = subprocess.run(["scp", "-i", key_path, tmp_script_path, f"{user}@{host}:{remote_script}"], 
                                        capture_output=True, text=True)
                else:
                    proc = subprocess.run(["scp", "-i", key_path, "-P", str(port), tmp_script_path, f"{user}@{host}:{remote_script}"], 
                                        capture_output=True, text=True)
                if proc.returncode != 0:
                    append_to_file(local_log, f"Error: Failed to copy update script <<exit-code:1>>: {proc.stderr}\n")
                    raise RuntimeError(f"Failed to copy update script: {proc.stderr}")
                
                # Execute remote script
                if port is None:
                    proc = subprocess.run(["ssh", "-i", key_path, f"{user}@{host}", f"python3 {remote_script}"], 
                                        capture_output=True, text=True)
                else:
                    proc = subprocess.run(["ssh", "-i", key_path, "-p", str(port), f"{user}@{host}", f"python3 {remote_script}"], 
                                            capture_output=True, text=True)
                if proc.returncode != 0:
                    error_msg = f"Failed to update sample sheet on remote: {proc.stderr}"
                    append_to_file(local_log, f"Error: <<exit-code:1>> {error_msg}\n")
                    raise RuntimeError(error_msg)
                append_to_file(local_log, f"Remote script output: {proc.stdout}\n")
            finally:
                # Clean up temp script
                try:
                    Path(tmp_script_path).unlink()
                except Exception:
                    pass

            # Update config with remote paths
            self.config['input'] = remote_sample_sheet
            if 'outdir' in self.config:
                self.config['outdir'] = remote_base

            self.progress.emit("Copying pipeline config...")
            append_to_file(local_log, "Copying pipeline config...\n")
            # rewrite config with updated paths and copy to remote
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            if port is None:
                proc = subprocess.run(["scp", "-i", key_path, config_file, f"{user}@{host}:{remote_base}/params.json"], 
                                    capture_output=True, text=True)
            else:
                proc = subprocess.run(["scp", "-i", key_path, "-P", str(port), config_file, f"{user}@{host}:{remote_base}/params.json"], 
                                    capture_output=True, text=True)
            if proc.returncode != 0:
                append_to_file(local_log, f"Error: Failed to copy updated config <<exit-code:1>>: {proc.stderr}\n")
                raise RuntimeError(f"Failed to copy updated config: {proc.stderr}")

            # Copy pipeline directory to remote nextflow assets
            pipeline_local_dir = Path.home() / ".nextflow" / "assets" / self.pipeline
            logger.info(f"Looking for local pipeline directory at: {pipeline_local_dir}")
            if pipeline_local_dir.exists():
                self.progress.emit("Copying pipeline directory...")
                append_to_file(local_log, "Copying pipeline directory...\n")

                # Get the assets base directory
                assets_base = Path.home() / ".nextflow" / "assets"
                
                # Remote paths - use explicit expansion
                remote_assets_base = f"/home/{user}/.nextflow/assets"
                remote_pipeline_dir = f"{remote_assets_base}/{self.pipeline}"
                
                # Create remote directory structure
                if port is None:
                    proc = subprocess.run(["ssh", "-i", key_path, f"{user}@{host}", 
                                          f"mkdir -p {remote_assets_base}"],
                                        capture_output=True, text=True)
                else:
                    proc = subprocess.run(["ssh", "-i", key_path, "-p", str(port), f"{user}@{host}", 
                                          f"mkdir -p {remote_assets_base}"],
                                        capture_output=True, text=True)
                if proc.returncode != 0:
                    append_to_file(local_log, f"Warning: Failed to create remote nextflow assets dir : {proc.stderr}\n")

                try:
                    # Use tar to copy with git directory preserved
                    # Tar from assets base directory to preserve the full pipeline path (e.g., nf-core/demo)
                    tar_proc = subprocess.run(
                        ["tar", "-C", str(assets_base), "-czf", "-", self.pipeline],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    if tar_proc.returncode != 0:
                        raise RuntimeError(tar_proc.stderr.decode("utf-8", errors="ignore") or "tar failed")

                    # Extract on remote in assets base directory to recreate full structure
                    if port is None:
                        ssh_cmd = ["ssh", "-i", key_path, f"{user}@{host}", 
                                   f"mkdir -p {remote_assets_base} && cd {remote_assets_base} && tar -xzf -"]
                    else:
                        ssh_cmd = ["ssh", "-i", key_path, "-p", str(port), f"{user}@{host}", 
                                   f"mkdir -p {remote_assets_base} && cd {remote_assets_base} && tar -xzf -"]
                    ssh_proc = subprocess.run(
                        ssh_cmd,
                        input=tar_proc.stdout,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                    )
                    if ssh_proc.returncode != 0:
                        raise RuntimeError(ssh_proc.stderr.decode("utf-8", errors="ignore") or "remote tar extract failed")
                    
                    logger.info(f"Successfully copied pipeline to {remote_pipeline_dir} via tar/ssh")
                    append_to_file(local_log, f"Successfully copied pipeline to {remote_pipeline_dir} via tar/ssh\n")
                except Exception as exc:
                    append_to_file(local_log, f"Warning: Failed to copy pipeline dir: {exc}\n")
                    logger.warning(f"Failed to copy pipeline dir: {exc}")

            self.progress.emit("Starting remote pipeline...")
            append_to_file(local_log, "Starting remote pipeline...\n")
            # run pipeline remotely and save remote logs
            remote_log = f"{remote_base}/run.log"
            selected_revision = self.config.get("rev", "master")
            nextflow_cmd = f"cd {remote_base} && bash -l -c 'nextflow run {self.pipeline} -revision {selected_revision} -profile docker -params-file params.json > run.log 2>&1'"
            
            # Start the pipeline process
            if port is None:
                ssh_proc = subprocess.Popen(
                    ["ssh", "-i", key_path, f"{user}@{host}", nextflow_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
            else:
                ssh_proc = subprocess.Popen(
                    ["ssh", "-i", key_path, "-p", str(port), f"{user}@{host}", nextflow_cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

            # Poll the remote log file every 30 seconds while the process runs
            last_fetched_size = 0
            poll_interval = 30  # seconds
            
            while ssh_proc.poll() is None:  # While process is still running
                time.sleep(poll_interval)
                
                # Fetch new content from remote log using tail
                try:
                    tail_cmd = f"tail -c +{last_fetched_size + 1} {remote_log} 2>/dev/null || true"
                    if port is None:
                        tail_proc = subprocess.run(
                            ["ssh", "-i", key_path, f"{user}@{host}", tail_cmd],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                    else:
                        tail_proc = subprocess.run(
                            ["ssh", "-i", key_path, "-p", str(port), f"{user}@{host}", tail_cmd],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                    
                    if tail_proc.returncode == 0 and tail_proc.stdout:
                        new_content = tail_proc.stdout
                        # Emit progress with new log lines
                        for line in new_content.splitlines():
                            if line.strip():
                                self.progress.emit(f"Remote: {line}")
                        append_to_file(local_log, f"[Remote log update] {new_content}\n")
                        last_fetched_size += len(new_content.encode('utf-8'))
                except Exception as poll_exc:
                    logger.warning(f"Error polling remote log: {poll_exc}")
                    append_to_file(local_log, f"Warning: Error polling remote log: {poll_exc}\n")
            
            # Process has finished, get final return code
            return_code = ssh_proc.wait()
            
            # Fetch any remaining log content
            try:
                if port is None:
                    final_log_proc = subprocess.run(
                        ["ssh", "-i", key_path, f"{user}@{host}", f"cat {remote_log}"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                else:
                    final_log_proc = subprocess.run(
                        ["ssh", "-i", key_path, "-p", str(port), f"{user}@{host}", f"cat {remote_log}"],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                if final_log_proc.returncode == 0:
                    final_content = final_log_proc.stdout
                    append_to_file(local_log, f"\n--- Final Remote Pipeline Log ---\n{final_content}\n")
            except Exception as final_exc:
                logger.warning(f"Error fetching final log: {final_exc}")
            
            # Check if pipeline succeeded
            if return_code != 0:
                error_msg = f"Remote run failed <<exit-code:{return_code}>>"
                append_to_file(local_log, f"Error: {error_msg}\n")
                raise RuntimeError(error_msg)

            self.progress.emit("Syncing results back to local...")
            append_to_file(local_log, "Syncing results back to local...\n")
            # sync the entire remote run directory back to local
            if port is None:
                proc = subprocess.run(["scp", "-i", key_path, "-r", f"{user}@{host}:{remote_base}", str(Path(self.run_dir).parent)], 
                                    capture_output=True, text=True)
            else:
                proc = subprocess.run(["scp", "-i", key_path, "-P", str(port), "-r", f"{user}@{host}:{remote_base}", str(Path(self.run_dir).parent)], 
                                    capture_output=True, text=True)
            if proc.returncode != 0:
                append_to_file(local_log, f"Warning: Failed to sync results: {proc.stderr}\n")
                logger.warning(f"Failed to sync remote results: {proc.stderr}")

            self.progress.emit("Fetching remote log...")
            append_to_file(local_log, "Fetching remote log...\n")
            # pull log to local run registry for visibility (now from synced directory)
            local_run_log = Path(self.run_dir) / "run.log"
            if local_run_log.exists():
                try:
                    with open(local_run_log, 'r') as f:
                        remote_content = f.read()
                    append_to_file(local_log, f"\n--- Remote Pipeline Output ---\n{remote_content}\n")
                except Exception as e:
                    append_to_file(local_log, f"Error reading synced remote log: {e}\n")
            else:
                append_to_file(local_log, "Warning: Remote log not found in synced results.\n")

            append_to_file(local_log, f"Remote job finished, log fetched from {host}:{remote_log} <<exit-code:{proc.returncode}>>\n")
            self.finished.emit(True, f"Pipeline finished successfully on {host}")
            
        except Exception as e:
            self.error.emit(str(e))

    def _proc_stdout(self, run_name):
        # lookup the live process by run_name (proc may have been deleted)
        entry = self.processes.get(run_name)
        if not entry:
            return
        proc = entry.get('proc')
        if not proc:
            return
        try:
            out = proc.readAllStandardOutput().data().decode('utf-8', errors='ignore')
            if out:
                for line in out.splitlines():
                    append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", line + "\n")
                    logger.info(line)
        except Exception as e:
            logger.error(f"Error reading stdout for {run_name}: {e}")

    def _proc_stderr(self, run_name):
        entry = self.processes.get(run_name)
        if not entry:
            return
        proc = entry.get('proc')
        if not proc:
            return
        try:
            err = proc.readAllStandardError().data().decode('utf-8', errors='ignore')
            if err:
                for line in err.splitlines():
                    append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", line + "\n")
                    logger.error(line)
        except Exception as e:
            logger.error(f"Error reading stderr for {run_name}: {e}")

    def _on_remote_progress(self, message):
        logger.info(f"Remote pipeline progress: {message}")

    def _on_remote_finished(self, success, message):
        if success:
            logger.info(f"Remote pipeline finished: {message}")
            QMessageBox.information(self, "Remote Pipeline", message)
        else:
            logger.error(f"Remote pipeline failed: {message}")
            QMessageBox.critical(self, "Remote Pipeline Error", message)

        if getattr(self, 'remote_run_name', None):
            PipelineLocal.active_runs.discard(self.remote_run_name)
            self.remote_run_name = None

        # Clean up references
        self.remote_worker = None
        self.remote_thread = None

    def _on_remote_error(self, error_msg):
        logger.error(f"Remote pipeline error: {error_msg}")
        QMessageBox.critical(self, "Remote Pipeline Error", f"Remote submission failed: {error_msg}")

        if getattr(self, 'remote_run_name', None):
            PipelineLocal.active_runs.discard(self.remote_run_name)
            self.remote_run_name = None

