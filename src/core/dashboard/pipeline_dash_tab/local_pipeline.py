from datetime import datetime
import json
from pyqtwaitingspinner import WaitingSpinner

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton, QDialog, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QProcess, QThread, QObject,  QRunnable, QThreadPool, pyqtSlot, QObject, pyqtSignal
from PyQt6.QtGui import QFont

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.subcommands.shell import run_shell_command
from src.utils.constants import CONFIG_FILE,RUN_DIR, PIPELINES_RUNS, SAMPLE_PREP_DIR
from src.utils.fileops.file_handle import ensure_directory, write_to_file, append_to_file, json_read, delete_file, delete_directory , tar_folder
from src.utils.encryption.handle import encrypt_file, decrypt_file, generate_key
from src.core.dashboard.pipeline_dash_tab.pipeline_args import PipelineArgsDialog
from src.core.dashboard.pipeline_dash_tab.pipeline_card import PipelineCard

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
            shell_out = run_shell_command(f"nextflow info {self.pipeline_name}")
            info = {}
            
            for line in shell_out.stdout.splitlines():
                if ": " in line:
                    key, value = line.split(": ", 1)
                    info[key.strip()] = value.strip()
            
            # Emit the parsed info dict
            self.info_ready.emit(info)
        except Exception as e:
            logger.error(f"Error fetching pipeline info: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()

class ZipEncryptSignals(QObject):
    finished = pyqtSignal(str, int)     # emits run_name on success
    error = pyqtSignal(str, int, str)   # emits run_name, error message


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
                self.result.emit(False, err)
        except Exception as e:
            logger.error(f"Error deleting pipeline: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()


class PipelineLocal(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        # keep references to running processes so they are not GC'd
        self.processes = {}
        self.output_displays = {}  # Store references to output display widgets by run_name
        self.current_pipeline_name = None  # Track the currently displayed pipeline
        
        self.constants = json_read(CONFIG_FILE)
        self.RUN_DIR = self.constants.get("folders",{}).get("RUN_DIR", RUN_DIR)
        self.PIPELINES_RUNS = self.constants.get("folders",{}).get("PIPELINES_RUNS", PIPELINES_RUNS)
        self.SAMPLE_PREP_DIR =  self.constants.get("folders",{}).get("SAMPLE_PREP_DIR", SAMPLE_PREP_DIR)
        
        # Worker thread and spinner for async pipeline info fetch
        self.info_worker = None
        self.info_worker_thread = None
        
        self.pipelines = []
        self.pipeline_info_lines = {}
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
        self.details_box.setObjectName("pipeline_info_box")
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
    
    def refresh_pipelines(self):
        """Refresh the local pipelines list and re-render cards."""
        logger.info("Refreshing local pipelines...")
        self.pipelines = []
        self.get_local_pipelines()
        self.render_cards()
        logger.info(f"Refreshed: found {len(self.pipelines)} pipelines")


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
            card.setMaximumHeight(200) 
            card.clicked.connect(self.on_card_clicked)

            # Add card to grid
            self.cards_grid.addWidget(card, row, col)

            # next column
            col += 1

            # wrap to next row
            if col >= columns:
                col = 0
                row += 1

    def _find_run_for_pipeline(self, pipeline_name: str):
        """Return the run_name key for a running process matching pipeline_name, or None."""
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
        
        # Clear old details
        for i in reversed(range(self.details_layout.count())):
            item = self.details_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()
        
        # Stop any existing worker thread
        if self.info_worker_thread is not None:
            try:
                # Check if thread is still alive before quitting
                if self.info_worker_thread.isRunning():
                    self.info_worker_thread.quit()
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
        # Stop spinner
        spinner.stop()
        
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
                
        self.action_section = QHBoxLayout()
        
        delete_btn = QPushButton("Delete", parent=self.details_box)
        delete_btn.setObjectName("pipeline_delete_btn")
        delete_btn.setFixedSize(60, 30)
        delete_btn.clicked.connect(self.on_delete_clicked)

        # Run and Cancel buttons
        self.run_btn = QPushButton("Run", parent=self.details_box)
        self.run_btn.setObjectName("pipeline_run_btn")
        self.run_btn.setFixedSize(60, 30)
        self.run_btn.clicked.connect(self.on_run_clicked)

        self.cancel_btn = QPushButton("Cancel", parent=self.details_box)
        self.cancel_btn.setObjectName("pipeline_cancel_btn")
        self.cancel_btn.setFixedSize(60, 30)
        self.cancel_btn.clicked.connect(self.on_cancel_clicked)

        # If this pipeline already has a running process, reflect that in the UI
        running_rn = self._find_run_for_pipeline(name)
        if running_rn:
            self.run_btn.setEnabled(False)
            self.cancel_btn.setEnabled(True)
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
    
    def _on_pipeline_info_error(self, error_msg, spinner):
        """Handle pipeline info error - show error message."""
        # Stop spinner
        spinner.stop()
        
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
        
        ensure_directory([str(run_dir), self.PIPELINES_RUNS ])

        logger.info(f"Starting pipeline: {pipeline}")
        try:
            # Write config to JSON file in run directory
            config_file = f"{run_dir}/params.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            write_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Running pipeline: {pipeline}\n")
            write_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Config: {json.dumps(config, indent=2)}\n")

            # create QProcess without parent
            proc = QProcess()
            proc.setProgram("nextflow")
            # Include -params-file to pass the JSON config
            proc.setArguments(["run", pipeline, "-profile", "docker", "-params-file", str(config_file)])
            proc.setWorkingDirectory(str(run_dir))

            # keep proc referenced
            self.processes[run_name] = {"proc": proc, "pipeline": pipeline}

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

            # connect signals
            proc.readyReadStandardOutput.connect(lambda rn=run_name: self._proc_stdout(rn))
            proc.readyReadStandardError.connect(lambda rn=run_name: self._proc_stderr(rn))
            proc.finished.connect(lambda exitCode, exitStatus, rn=run_name: self._proc_finished(rn, exitCode, exitStatus))

            proc.start()
            QMessageBox.information(self, "Pipeline Started", f"Started {pipeline}\nConfig saved to {config_file}")
        except Exception as e:
            logger.error(f"Error starting pipeline: {e}")
            append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Error starting pipeline: {e}\n")
            QMessageBox.critical(self, "Error", f"Failed to start pipeline: {e}")

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

    def on_cancel_clicked(self):
        # Cancel the currently running pipeline (if any)
        if not hasattr(self, 'current_run_name') or not self.current_run_name:
            return
        rn = self.current_run_name
        entry = self.processes.get(rn)
        if not entry:
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

    def _proc_finished(self, run_name, exitCode, exitStatus):
        try:

            try:
                app = QApplication.instance()
                if app.cred:
                    zip_name = f"{self.RUN_DIR}/{run_name.replace('.txt', '.tar.gz')}"
                    run_dir = f"{self.RUN_DIR}/{run_name.replace('.txt','')}"

                    worker = ZipEncryptWorker(run_name, run_dir, zip_name, app.cred, exitCode)

                    # Connect callbacks
                    worker.signals.finished.connect(self._on_zip_encrypt_done)
                    worker.signals.error.connect(self._on_zip_encrypt_error)

                    # Start async
                    QThreadPool.globalInstance().start(worker)
                else:
                    append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Pipeline run completed <<exit-code:{exitCode}>>.\n")
                    logger.info(f"Pipeline {run_name} finished (code={exitCode})")
            except Exception as e:
                logger.error(f"Failed to complete run - {e}")
                append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Pipeline run completed <<exit-code:{1}>>.\n")

            
        finally:
            # Clean up stored process
            entry = self.processes.pop(run_name, None)
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
            # If this finished run was the currently displayed one, update buttons
            if hasattr(self, 'current_run_name') and self.current_run_name == run_name:
                try:
                    self.run_btn.setEnabled(True)
                except Exception:
                    pass
                try:
                    self.cancel_btn.setEnabled(False)
                except Exception:
                    pass
                # clear current run tracking
                self.current_run_name = None
                self.current_pipeline = None

    def _on_zip_encrypt_done(self, run_name, exitCode):
        logger.info(f"Zip/encrypt cleanup completed for run: {run_name}")
        append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Pipeline run completed <<exit-code:{exitCode}>>.\n")
        logger.info(f"Pipeline {run_name} finished (code={exitCode})")
        # optionally update UI here


    def _on_zip_encrypt_error(self, run_name, err, exitCode):
        logger.error(f"Zip/encrypt failed for run {run_name}: {err}")
        append_to_file(f"{self.PIPELINES_RUNS}/{run_name}", f"Pipeline run completed <<exit-code:{1}>>.\n")
        logger.error(f"Pipeline {run_name} finished (code={exitCode}) , But encryption failed")
        

    def closeEvent(self, event):
        # Terminate any running processes when the widget is closed/destroyed
        for rn, entry in list(self.processes.items()):
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
        # Stop any worker threads cleanly
        try:
            if getattr(self, 'info_worker_thread', None) is not None:
                try:
                    self.info_worker_thread.quit()
                    self.info_worker_thread.wait(1000)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            if getattr(self, 'delete_thread', None) is not None:
                try:
                    self.delete_thread.quit()
                    self.delete_thread.wait(1000)
                except Exception:
                    pass
        except Exception:
            pass

        super().closeEvent(event)

