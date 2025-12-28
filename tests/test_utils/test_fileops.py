import json
import zipfile
import pytest

from src.utils.fileops.file_handle import *


def test_ensure_directory_single(tmp_path):
    dir_path = tmp_path / "testdir"
    ensure_directory(str(dir_path))
    assert dir_path.exists()
    delete_directory(tmp_path)

def test_ensure_directory_list(tmp_path):
    dirs = [tmp_path / "a", tmp_path / "b"]
    ensure_directory([str(d) for d in dirs])
    assert all(d.exists() for d in dirs)
    delete_directory(tmp_path)

def test_ensure_directory_existing(tmp_path):
    assert not ensure_directory(str(tmp_path))  # should not raise
    delete_directory(tmp_path)

def test_write_and_read_file(tmp_path):
    ensure_directory(tmp_path)

    file = tmp_path / "file.txt"
    write_to_file(str(file), "hello")
    assert read_from_file(str(file)) == "hello"
    delete_directory(tmp_path)

def test_append_to_file(tmp_path):
    ensure_directory(tmp_path)
    file = tmp_path / "file.txt"
    write_to_file(str(file), "hello")
    append_to_file(str(file), " world")
    assert read_from_file(str(file)) == "hello world"
    delete_directory(tmp_path)


def test_delete_file(tmp_path):
    ensure_directory(tmp_path)
    file = tmp_path / "file.txt"
    file.write_text("x")
    delete_file(str(file))
    assert not file.exists()
    delete_directory(tmp_path)


def test_delete_file_nonexistent():
    delete_file("does_not_exist.txt")  # no exception

def test_delete_directory(tmp_path):
    ensure_directory(tmp_path)
    dir_path = tmp_path / "dir"
    dir_path.mkdir()
    delete_directory(str(dir_path))
    assert not dir_path.exists()
    delete_directory(tmp_path)


def test_list_files_in_directory(tmp_path):
    ensure_directory(tmp_path)
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    files = list_files_in_directory(str(tmp_path))
    assert len(files) == 2
    delete_directory(tmp_path)


def test_list_files_nonexistent_directory():
    assert list_files_in_directory("invalid_dir") == []

def test_file_exists(tmp_path):
    ensure_directory(tmp_path)

    file = tmp_path / "a.txt"
    file.touch()
    assert file_exists(str(file))
    delete_directory(tmp_path)

def test_get_file_size(tmp_path):
    ensure_directory(tmp_path)

    file = tmp_path / "a.txt"
    file.write_text("abc")
    assert get_file_size(str(file)) == 3
    delete_directory(tmp_path)


def test_get_file_size_nonexistent():
    assert get_file_size("missing.txt") == 0


def test_copy_file(tmp_path):
    ensure_directory(tmp_path)
    src = tmp_path / "src.txt"
    dest = tmp_path / "dest.txt"
    src.write_text("x")
    copy_file(str(src), str(dest))
    assert dest.read_text() == "x"
    delete_directory(tmp_path)



def test_move_file(tmp_path):
    ensure_directory(tmp_path)
    src = tmp_path / "src.txt"
    dest = tmp_path / "dest.txt"
    src.write_text("x")
    move_file(str(src), str(dest))
    assert dest.exists()
    assert not src.exists()
    delete_directory(tmp_path)


# -----------------------------
# JSON
# -----------------------------

def test_json_write_and_read(tmp_path):
    ensure_directory(tmp_path)
    file = tmp_path / "data.json"
    data = {"a": 1}
    json_write(str(file), data)
    assert json_read(str(file)) == data
    delete_directory(tmp_path)


def test_json_read_invalid_json(tmp_path):
    ensure_directory(tmp_path)
    file = tmp_path / "bad.json"
    file.write_text("{invalid}")
    with pytest.raises(json.JSONDecodeError):
        json_read(str(file))

    delete_directory(tmp_path)

def test_zip_folder(tmp_path):
    ensure_directory(tmp_path)

    folder = tmp_path / "folder"
    folder.mkdir()
    (folder / "a.txt").write_text("x")

    zip_path = tmp_path / "test.zip"
    zip_folder(str(folder), str(zip_path))

    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as z:
        assert "a.txt" in z.namelist()

    delete_directory(tmp_path)


def test_tar_and_untar_folder(tmp_path):
    ensure_directory(tmp_path)
    folder = tmp_path / "folder"
    folder.mkdir()
    (folder / "a.txt").write_text("x")

    tar_path = tmp_path / "test.tar.gz"
    extract_path = tmp_path / "extract"

    tar_folder(str(folder), str(tar_path))
    untar_folder(str(tar_path), str(extract_path))

    extracted = extract_path / folder.name / "a.txt"
    assert extracted.exists()
    assert extracted.read_text() == "x"
    delete_directory(tmp_path)


def test_untar_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        untar_folder("missing.tar.gz", "out")


def test_items_collector_basic(tmp_path):
    ensure_directory(tmp_path)
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.csv").touch()

    result = items_collector(str(tmp_path), [".txt"], set())
    assert len(result) == 1
    assert result[0].endswith("a.txt")
    delete_directory(tmp_path)


def test_items_collector_excludes_dirs(tmp_path):
    ensure_directory(tmp_path)
    excluded = tmp_path / "exclude"
    excluded.mkdir()
    (excluded / "a.txt").touch()

    result = items_collector(str(tmp_path), [".txt"], {"exclude"})
    assert result == []
    delete_directory(tmp_path)

def test_items_collector_no_matches(tmp_path):
    ensure_directory(tmp_path)
    (tmp_path / "a.md").touch()
    result = items_collector(str(tmp_path), [".txt"], set())
    assert result == []
    delete_directory(tmp_path)