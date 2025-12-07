import time
import json


from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
    QHBoxLayout, QGridLayout, QPushButton, QDialog, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, pyqtSignal, QProcess
from PyQt6.QtGui import QFont

from src.utils.logger_module.omix_logger import OmixForgeLogger
from src.utils.subcommands.shell import run_shell_command, run_shell_command_stream
from src.utils.constants import RUN_DIR, PIPELINES_RUNS, SAMPLE_PREP_DIR
from src.utils.fileops.file_handle import ensure_directory, write_to_file, append_to_file
from src.core.dashboard.pipeline_dash_tab.pipeline_args import PipelineArgsDialog
from src.core.dashboard.pipeline_dash_tab.pipeline_card import PipelineCard

logger = OmixForgeLogger.get_logger()


class PipelineLocal(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        # keep references to running processes so they are not GC'd
        self.processes = {}
        self.output_displays = {}  # Store references to output display widgets by run_name
        self.current_pipeline_name = None  # Track the currently displayed pipeline
        
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
        # Store the current pipeline name for use in on_run_clicked
        self.current_pipeline_name = name
        
        # Clear old details
        for i in reversed(range(self.details_layout.count())):
            item = self.details_layout.takeAt(i)
            if item.widget():
                item.widget().deleteLater()


        shell_out = run_shell_command(f"nextflow info {name}")
        content = ''
        for line in shell_out.stdout.splitlines():
            if ": " in line:
                key, value = line.split(": ", 1)
                self.pipeline_info_lines[key.strip()] = value.strip()
                content += f"{key.strip()}: {value.strip()}\n\n"
                
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
        delete_btn.setFixedSize(60, 30)
        delete_btn.clicked.connect(self.on_delete_clicked)

        # Run and Cancel buttons
        self.run_btn = QPushButton("Run", parent=self.details_box)
        self.run_btn.setFixedSize(60, 30)
        self.run_btn.clicked.connect(self.on_run_clicked)

        self.cancel_btn = QPushButton("Cancel", parent=self.details_box)
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
        # Get the pipeline name from stored attribute
        pipeline = self.current_pipeline_name
        if not pipeline:
            QMessageBox.warning(self, "Error", "No pipeline selected.")
            return
        
        # Show the args dialog
        dialog = PipelineArgsDialog(pipeline, self.pipeline_info_lines, parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        # Get the config
        config = dialog.get_config()
        
        # Validate mandatory args
        if not config.get("input"):
            QMessageBox.warning(self, "Missing Argument", "Please specify the input (sample sheet) file.")
            return
        
        run_name = f"{pipeline}_{time.time()}_run.txt".replace("nf-core/", "")
        run_dir = RUN_DIR / run_name.replace('.txt', '')
        ensure_directory([str(run_dir), PIPELINES_RUNS])

        logger.info(f"Starting pipeline: {pipeline}")
        try:
            # Write config to JSON file in run directory
            config_file = run_dir / "params.json"
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            write_to_file(PIPELINES_RUNS / run_name, f"Running pipeline: {pipeline}\n")
            write_to_file(PIPELINES_RUNS / run_name, f"Config: {json.dumps(config, indent=2)}\n")

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
            append_to_file(PIPELINES_RUNS / run_name, f"Error starting pipeline: {e}\n")
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
                    append_to_file(PIPELINES_RUNS / run_name, line + "\n")
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
                    append_to_file(PIPELINES_RUNS / run_name, line + "\n")
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
            append_to_file(PIPELINES_RUNS / rn, "Pipeline run cancelled by user.\n")
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
            append_to_file(PIPELINES_RUNS / run_name, "Pipeline run completed.\n")
            logger.info(f"Pipeline {run_name} finished (code={exitCode})")
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
        super().closeEvent(event)

