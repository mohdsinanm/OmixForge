import pytest, os, sys
sys.path.append(os.getcwd())
from src.__main__ import MainWindow
from pathlib import Path
from unittest.mock import MagicMock


@pytest.fixture
def get_test_files():
    return {"file_path" : "tests/test_files/text.txt"}

@pytest.fixture
def get_lock_key():
    return {"lock" : "LHDhK3oGRvkiefQnx7OOczTY5Tic_xZ6HcMOc_gmtoM=", "key": "key"}

@pytest.fixture
def tmp_path():
    return Path("tests/test_files/tmp")

@pytest.fixture
def sidebar_items():
    return ["Pipeline Dashboard", "Sample Prep", "Pipeline Status", "Settings"]


@pytest.fixture
def mock_initiate():
    """Mock InitiateApp so tests don't hit filesystem/network/system bins."""
    mock = MagicMock(name="InitiateAppMock")

    # What your MainWindow likely expects:
    mock.cache_json_data = {"pipelines": []}
    mock.docker_installed = True
    mock.nextflow_installed = True
    mock.constants = {"SOME_CONST": "value"}

    # If your MainWindow ever calls these:
    mock.load_json_data.return_value = None
    mock.check_docker_installed.return_value = True
    mock.check_nextflow_installed.return_value = True

    return mock

@pytest.fixture
def window(qtbot, mock_initiate):
    app = MainWindow(mock_initiate)
    qtbot.addWidget(app)
    return app
