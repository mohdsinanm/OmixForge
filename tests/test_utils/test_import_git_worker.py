import os
import types
from unittest.mock import Mock
import pytest

from src.core.dashboard.pipeline_import_tab import import_git_worker as gitmod


class FakeCompleted:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def test_git_not_installed(monkeypatch):
    # Simulate which git not found
    def fake_run(cmd):
        if cmd.startswith("which git"):
            return None
        return FakeCompleted(0)

    monkeypatch.setattr(gitmod, 'run_shell_command', fake_run)

    w = gitmod.PipelineGitImportWorker('https://github.com/owner/repo.git')

    results = []

    def cb(success, message):
        results.append((success, message))

    w.import_ready.connect(cb)
    w.run()

    assert results, "import_ready should have been emitted"
    assert results[0][0] is False
    assert 'git is not installed' in results[0][1].lower()


def test_successful_clone_and_lint(monkeypatch, tmp_path):
    dest_root = str(tmp_path / 'assets')
    repo_name = 'repo'
    dest = os.path.join(dest_root, repo_name)

    # Track calls and emulate filesystem
    exists_calls = set()

    def fake_exists(path):
        # dest does not exist initially, after clone we simulate it exists
        if path == dest:
            return True
        # any file checks for main.nf/nextflow.config return False (not used because lint passes)
        return False

    # Fake run_shell_command behavior
    def fake_run(cmd):
        if cmd.startswith('which git'):
            return FakeCompleted(0)
        if cmd.startswith('git clone'):
            return FakeCompleted(0)
        if cmd.startswith('which nf-core'):
            return FakeCompleted(0)
        if cmd.startswith('nf-core lint'):
            return FakeCompleted(0)
        if cmd.startswith('git -C'):
            return FakeCompleted(0)
        return FakeCompleted(0)

    monkeypatch.setattr(gitmod, 'run_shell_command', fake_run)
    monkeypatch.setattr(os, 'path', os.path)  # ensure attribute exists
    monkeypatch.setattr(os.path, 'exists', fake_exists)
    monkeypatch.setattr(os, 'makedirs', lambda *a, **k: None)

    # Prevent actual rmtree
    monkeypatch.setattr(gitmod, 'shutil', gitmod.shutil)
    monkeypatch.setattr(gitmod.shutil, 'rmtree', lambda *a, **k: None)

    w = gitmod.PipelineGitImportWorker('https://github.com/owner/repo.git', target_root=dest_root)
    results = []

    def cb(success, message):
        results.append((success, message))

    w.import_ready.connect(cb)
    w.run()

    assert results, "import_ready should have been emitted"
    assert results[0][0] is True


def test_non_compliant_repo_removal(monkeypatch, tmp_path):
    dest_root = str(tmp_path / 'assets')
    repo_name = 'badrepo'
    dest = os.path.join(dest_root, repo_name)

    # Emulate dest exists after clone
    def fake_exists(path):
        if path == dest:
            return True
        # main.nf and nextflow.config missing
        return False

    # Emulate commands: git present, clone ok, nf-core present but lint fails
    def fake_run(cmd):
        if cmd.startswith('which git'):
            return FakeCompleted(0)
        if cmd.startswith('git clone'):
            return FakeCompleted(0)
        if cmd.startswith('which nf-core'):
            return FakeCompleted(0)
        if cmd.startswith('nf-core lint'):
            return FakeCompleted(1, stderr='lint issues')
        if cmd.startswith('git -C'):
            return FakeCompleted(0)
        return FakeCompleted(0)

    removed = {'called': False}

    def fake_rmtree(path, onerror=None):
        removed['called'] = True

    monkeypatch.setattr(gitmod, 'run_shell_command', fake_run)
    monkeypatch.setattr(os.path, 'exists', fake_exists)
    monkeypatch.setattr(os, 'makedirs', lambda *a, **k: None)
    monkeypatch.setattr(gitmod.shutil, 'rmtree', fake_rmtree)

    w = gitmod.PipelineGitImportWorker('https://github.com/owner/badrepo.git', target_root=dest_root)
    results = []

    def cb(success, message):
        results.append((success, message))

    w.import_ready.connect(cb)
    w.run()

    assert results, "import_ready should have been emitted"
    assert results[0][0] is False
    assert removed['called'] is True
