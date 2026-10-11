from pathlib import Path
from tempfile import TemporaryDirectory

import src.core.status_page.results.run_results as results_module
from src.utils.fileops.file_handle import tar_folder


def test_tar_decrypt_worker_restores_run_directory_root(monkeypatch):
    with TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source_dir = root / "source" / "demo_run"
        source_dir.mkdir(parents=True)
        (source_dir / "params.json").write_text("{}")
        source_archive = root / "source.tar.gz"
        tar_folder(str(source_dir), str(source_archive))

        run_root = root / "runs"
        run_root.mkdir()
        encrypted_archive = run_root / "demo_run.tar.gz.enc"
        encrypted_archive.write_bytes(b"encrypted-placeholder")
        restored_run_dir = run_root / "demo_run"

        def fake_decrypt(encrypted_path, _key):
            archive_path = Path(str(encrypted_path).replace(".enc", ""))
            archive_path.write_bytes(source_archive.read_bytes())
            return str(archive_path)

        monkeypatch.setattr(results_module, "decrypt_file", fake_decrypt)
        worker = results_module.TarDecryptWorker(
            "demo_run.tar.gz.enc",
            str(restored_run_dir),
            str(encrypted_archive),
            {"user": "test", "password": "test"},
        )
        finished = []
        errors = []
        worker.signals.finished.connect(finished.append)
        worker.signals.error.connect(lambda _name, message: errors.append(message))

        worker.run()

        assert not errors
        assert finished == ["demo_run.tar.gz.enc"]
        assert (restored_run_dir / "params.json").is_file()
        assert encrypted_archive.is_file()
        assert not (run_root / "demo_run.tar.gz").exists()