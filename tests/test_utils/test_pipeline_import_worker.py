from types import SimpleNamespace

from src.core.dashboard.pipeline_import_tab import import_worker


def test_import_worker_retries_transient_pull_failure(monkeypatch):
    commands = []
    pull_results = [
        SimpleNamespace(returncode=1, stdout="", stderr="Temporary failure in name resolution"),
        SimpleNamespace(returncode=0, stdout="", stderr=""),
    ]

    def fake_run(command):
        commands.append(command)
        if command == "nextflow list":
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return pull_results.pop(0)

    monkeypatch.setattr(import_worker, "run_shell_command", fake_run)
    monkeypatch.setattr(import_worker.time, "sleep", lambda *_: None)
    worker = import_worker.PipelineImportWorker("rnaseq")
    results = []
    worker.import_ready.connect(lambda success, message: results.append((success, message)))

    worker.run()

    assert results == [(True, "Imported successfully")]
    assert commands.count("nextflow pull nf-core/rnaseq") == 2


def test_import_worker_reports_actionable_non_transient_failure(monkeypatch):
    def fake_run(command):
        if command == "nextflow list":
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="", stderr="Unknown workflow")

    monkeypatch.setattr(import_worker, "run_shell_command", fake_run)
    worker = import_worker.PipelineImportWorker("unknown")
    results = []
    worker.import_ready.connect(lambda success, message: results.append((success, message)))

    worker.run()

    assert results[0][0] is False
    assert "Verify the workflow name" in results[0][1]


def test_import_worker_emits_error_and_records_traceback(monkeypatch):
    log_calls = []

    class LoggerSpy:
        def exception(self, message):
            log_calls.append(message)

    def failed_command(_command):
        raise RuntimeError("worker failed")

    monkeypatch.setattr(import_worker, "logger", LoggerSpy())
    monkeypatch.setattr(import_worker, "run_shell_command", failed_command)
    worker = import_worker.PipelineImportWorker("rnaseq")
    errors = []
    worker.error.connect(errors.append)

    worker.run()

    assert errors == ["worker failed"]
    assert log_calls == ["Error importing pipeline: worker failed"]