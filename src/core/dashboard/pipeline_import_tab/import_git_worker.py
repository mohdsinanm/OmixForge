import os
import re
import shutil
from PyQt6.QtCore import QObject, pyqtSignal
from src.utils.subcommands.shell import run_shell_command
from src.utils.logger_module.omix_logger import OmixForgeLogger

logger = OmixForgeLogger.get_logger()


class PipelineGitImportWorker(QObject):
    """Worker to clone a GitHub repository and verify nf-core compliance."""

    finished = pyqtSignal()
    error = pyqtSignal(str)
    import_ready = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, repo_url, target_root=None):
        super().__init__()
        self.repo_url = repo_url
        # Default target is the user's .nextflow assets nf-core folder
        if target_root is None:
            target_root = os.path.expanduser("~/.nextflow/assets/nf-core")
        self.target_root = target_root

    def _repo_name_from_url(self):
        # Extract repo name from URL
        m = re.search(r"/([^/]+?)(?:\.git)?$", self.repo_url)
        if m:
            return m.group(1)
        return None

    def run(self):
        try:
            repo_name = self._repo_name_from_url()
            if not repo_name:
                msg = "Could not parse repository name from URL"
                logger.error(msg)
                self.import_ready.emit(False, msg)
                return

            os.makedirs(self.target_root, exist_ok=True)
            dest = os.path.join(self.target_root, repo_name)

            if os.path.exists(dest):
                msg = "Repository already exists at target location"
                logger.error(msg)
                self.import_ready.emit(False, msg)
                return

            # Clone repository
            clone_cmd = f"git clone {self.repo_url} {dest}"
            clone_proc = run_shell_command(clone_cmd)
            if clone_proc is None or clone_proc.returncode != 0:
                stderr = clone_proc.stderr if clone_proc is not None else "git clone failed"
                msg = f"Git clone failed: {stderr}"
                logger.error(msg)
                # cleanup partial dest
                if os.path.exists(dest):
                    try:
                        shutil.rmtree(dest)
                    except Exception:
                        pass
                self.import_ready.emit(False, msg)
                return

            # Verify nf-core compliance using nf-core lint if available
            which_nfcore = run_shell_command("which nf-core")
            lint_ok = False
            if which_nfcore is not None:
                lint_cmd = f"nf-core lint {dest}"
                lint_proc = run_shell_command(lint_cmd)
                if lint_proc is not None and lint_proc.returncode == 0:
                    lint_ok = True
                else:
                    logger.warning(f"nf-core lint reported issues for {repo_name}: {getattr(lint_proc, 'stderr', '')}")

            # Fallback simple check: presence of main.nf and nextflow.config
            if not lint_ok:
                main_nf = os.path.join(dest, "main.nf")
                nextflow_cfg = os.path.join(dest, "nextflow.config")
                if os.path.exists(main_nf) and os.path.exists(nextflow_cfg):
                    lint_ok = True
                else:
                    logger.warning(f"Repository {repo_name} missing main.nf or nextflow.config; not nf-core compliant")

            if not lint_ok:
                # Not compliant: log and remove
                msg = "Repository is not nf-core compliant; removing cloned copy"
                try:
                    shutil.rmtree(dest)
                except Exception as e:
                    logger.error(f"Failed to remove non-compliant repo at {dest}: {e}")
                logger.warning(msg)
                self.import_ready.emit(False, msg)
                return

            # Success
            logger.info(f"Successfully cloned and verified repository: {repo_name}")
            self.import_ready.emit(True, f"Cloned and verified: {repo_name}")

        except Exception as e:
            logger.error(f"Error during git import: {e}")
            self.error.emit(str(e))
        finally:
            self.finished.emit()
