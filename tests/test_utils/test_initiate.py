from pathlib import Path
from tempfile import TemporaryDirectory

from src.core import initiate as initiate_module


def _raise_network_error(_self):
    raise RuntimeError("nf-core is unavailable")


def test_startup_uses_cached_workflows_when_remote_fetch_fails(monkeypatch):
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        cache_file = temp_path / "nfcore_cache.json"
        cached_payload = {"remote_workflows": [{"name": "cached-pipeline"}]}
        cache_file.write_text('{"remote_workflows": [{"name": "cached-pipeline"}]}')

        monkeypatch.setattr(initiate_module, "INITIATE_CACHE_JSON", cache_file)
        monkeypatch.setattr(initiate_module.NfcoreUtils, "get_pipelines_json", _raise_network_error)
        app = initiate_module.InitiateApp.__new__(initiate_module.InitiateApp)

        app.load_json_data()

        assert app.cache_json_data == cached_payload


def test_startup_continues_with_empty_workflows_without_cache(monkeypatch):
    with TemporaryDirectory() as temp_dir:
        cache_file = Path(temp_dir) / "missing-cache.json"
        monkeypatch.setattr(initiate_module, "INITIATE_CACHE_JSON", cache_file)
        monkeypatch.setattr(initiate_module.NfcoreUtils, "get_pipelines_json", _raise_network_error)
        app = initiate_module.InitiateApp.__new__(initiate_module.InitiateApp)

        app.load_json_data()

        assert app.cache_json_data == {"remote_workflows": []}