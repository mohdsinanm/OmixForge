import pytest

from src.utils import nfcore_utils
from src.utils.nfcore_utils import *


class FakeResponse:
    status_code = 200

    def json(self):
        return {"remote_workflows": [{"name": "demo"}]}


def test_get_pipelines_json(monkeypatch):
    monkeypatch.setattr(nfcore_utils.requests, "get", lambda *args, **kwargs: FakeResponse())

    pipeline_list = NfcoreUtils().get_pipelines_json()

    assert pipeline_list["remote_workflows"][0]["name"] == "demo"


def test_get_pipelines(monkeypatch):
    monkeypatch.setattr(nfcore_utils.requests, "get", lambda *args, **kwargs: FakeResponse())

    pipeline_list = NfcoreUtils().get_pipelines()

    assert len(pipeline_list) == 1
    assert pipeline_list[0].name == "demo"


def test_get_pipelines_json_retries_transient_http_failure(monkeypatch):
    responses = [
        type("Response", (), {"status_code": 503})(),
        type("Response", (), {
            "status_code": 200,
            "json": lambda self: {"remote_workflows": []},
        })(),
    ]
    calls = []
    monkeypatch.setattr(nfcore_utils.requests, "get", lambda *args, **kwargs: calls.append(1) or responses.pop(0))
    monkeypatch.setattr(nfcore_utils.time, "sleep", lambda *_: None)

    result = NfcoreUtils().get_pipelines_json()

    assert result == {"remote_workflows": []}
    assert len(calls) == 2


def test_get_pipelines_json_raises_actionable_error_after_network_failures(monkeypatch):
    monkeypatch.setattr(
        nfcore_utils.requests,
        "get",
        lambda *args, **kwargs: (_ for _ in ()).throw(nfcore_utils.requests.Timeout("offline")),
    )
    monkeypatch.setattr(nfcore_utils.time, "sleep", lambda *_: None)

    with pytest.raises(RuntimeError, match="Check your network connection"):
        NfcoreUtils().get_pipelines_json()

