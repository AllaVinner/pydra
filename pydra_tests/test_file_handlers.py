import io
from pathlib import Path

from pytest import MonkeyPatch
from pydra.file_handlers import open_or_stderr, open_or_stdin, open_or_stdout
from contextlib import redirect_stderr, redirect_stdout


def test_open_or_stdin_file_input(tmp_path: Path):
    file = Path(tmp_path, "f.txt")
    actual_file_content = "This is a test file"
    file.write_text(actual_file_content)
    with open_or_stdin(file) as f:
        read_file_content = f.read()
    assert read_file_content == actual_file_content


def test_open_or_stdin_none_input(monkeypatch: MonkeyPatch):
    actual_file_content = "This is a test file"
    monkeypatch.setattr("sys.stdin", io.StringIO(actual_file_content))
    with open_or_stdin(None) as f:
        read_file_content = f.read()
    assert read_file_content == actual_file_content


def test_open_or_stdout_file_input(tmp_path: Path, monkeypatch: MonkeyPatch):
    file = Path(tmp_path, "f.txt")
    expected_file_content = "This is a test file"
    assert not file.exists()
    with open_or_stdout(file) as f:
        f.write(expected_file_content)
    actual_file_content = file.read_text()
    assert expected_file_content == actual_file_content


def test_open_or_stdout_none_input():
    expected_content = "This is a test file"
    with io.StringIO() as mock_stdout, redirect_stdout(mock_stdout):
        with open_or_stdout(None) as f:
            f.write(expected_content)
        actual_content = mock_stdout.getvalue()

    assert expected_content == actual_content


def test_open_or_stderr_file_input(tmp_path: Path):
    file = Path(tmp_path, "f.txt")
    expected_file_content = "This is a test file"
    assert not file.exists()
    with open_or_stderr(file) as f:
        f.write(expected_file_content)
    actual_file_content = file.read_text()
    assert expected_file_content == actual_file_content


def test_open_or_stderr_none_input(tmp_path: Path):
    expected_content = "This is a test file"
    with io.StringIO() as mock_stderr, redirect_stderr(mock_stderr):
        with open_or_stderr(None) as f:
            f.write(expected_content)
        actual_content = mock_stderr.getvalue()
    assert expected_content == actual_content
