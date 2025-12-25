import pytest, os, sys
sys.path.append(os.getcwd())
from src.__main__ import MainWindow
from pathlib import Path
from PyQt6.QtCore import Qt


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
def window(qtbot):
    app = MainWindow()
    qtbot.addWidget(app)
    return app
