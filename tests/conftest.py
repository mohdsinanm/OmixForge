import pytest
import os 

@pytest.fixture
def get_test_files():
    return {"file_path" : "tests/test_files/text.txt"}

@pytest.fixture
def get_lock_key():
    return {"lock" : "LHDhK3oGRvkiefQnx7OOczTY5Tic_xZ6HcMOc_gmtoM=", "key": "key"}