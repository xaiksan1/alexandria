import json
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add action-layer to path
sys.path.insert(0, str(Path(__file__).parent.parent))
import pinchtab_caller


@pytest.fixture(autouse=True)
def isolated_queue(tmp_path, monkeypatch):
    """Each test gets its own action_queue.json in a tmp dir."""
    queue_path = tmp_path / "action_queue.json"
    queue_path.write_text('{"pending": []}')
    monkeypatch.setattr(pinchtab_caller, "QUEUE_PATH", queue_path)
    return queue_path


def test_call_queues_when_pinchtab_missing(isolated_queue):
    """If pinchtab not installed, action is queued and False returned."""
    with patch.object(pinchtab_caller, "PINCHTAB_PATH", Path("/nonexistent/pinchtab")):
        result = pinchtab_caller.call("click", "https://example.com", button="buy")
    assert result is False
    data = json.loads(isolated_queue.read_text())
    assert len(data["pending"]) == 1
    assert data["pending"][0]["action"] == "click"
    assert data["pending"][0]["url"] == "https://example.com"


def test_call_returns_true_on_subprocess_success(isolated_queue, tmp_path):
    """Successful subprocess run returns True without queuing."""
    fake_pinchtab = tmp_path / "pinchtab"
    (fake_pinchtab / "install.sh").parent.mkdir(parents=True, exist_ok=True)
    (fake_pinchtab / "install.sh").write_text("#!/bin/bash")

    mock_result = MagicMock()
    mock_result.returncode = 0

    with patch.object(pinchtab_caller, "PINCHTAB_PATH", fake_pinchtab), \
         patch("subprocess.run", return_value=mock_result):
        result = pinchtab_caller.call("click", "https://example.com")

    assert result is True
    data = json.loads(isolated_queue.read_text())
    assert len(data["pending"]) == 0


def test_call_queues_on_subprocess_failure(isolated_queue, tmp_path):
    """Non-zero returncode queues the action and returns False."""
    fake_pinchtab = tmp_path / "pinchtab"
    (fake_pinchtab / "install.sh").parent.mkdir(parents=True, exist_ok=True)
    (fake_pinchtab / "install.sh").write_text("#!/bin/bash")

    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "command not found"

    with patch.object(pinchtab_caller, "PINCHTAB_PATH", fake_pinchtab), \
         patch("subprocess.run", return_value=mock_result):
        result = pinchtab_caller.call("click", "https://example.com")

    assert result is False
    data = json.loads(isolated_queue.read_text())
    assert len(data["pending"]) == 1


def test_call_queues_on_exception(isolated_queue, tmp_path):
    """Any exception during subprocess queues and returns False."""
    fake_pinchtab = tmp_path / "pinchtab"
    (fake_pinchtab / "install.sh").parent.mkdir(parents=True, exist_ok=True)
    (fake_pinchtab / "install.sh").write_text("#!/bin/bash")

    with patch.object(pinchtab_caller, "PINCHTAB_PATH", fake_pinchtab), \
         patch("subprocess.run", side_effect=OSError("timeout")):
        result = pinchtab_caller.call("click", "https://example.com")

    assert result is False
    data = json.loads(isolated_queue.read_text())
    assert len(data["pending"]) == 1


def test_enqueue_atomic_no_tmp_left(isolated_queue):
    """After enqueue, no .tmp file should remain."""
    pinchtab_caller._enqueue("open", "https://example.com", {})
    assert not os.path.exists(str(isolated_queue) + ".tmp")


def test_enqueue_appends_to_existing(isolated_queue):
    """Multiple enqueues accumulate without overwriting."""
    pinchtab_caller._enqueue("click", "https://a.com", {})
    pinchtab_caller._enqueue("scroll", "https://b.com", {})
    data = json.loads(isolated_queue.read_text())
    assert len(data["pending"]) == 2
    assert data["pending"][0]["action"] == "click"
    assert data["pending"][1]["action"] == "scroll"


def test_load_queue_returns_empty_on_corrupt_file(isolated_queue):
    """Corrupt queue file is handled gracefully — returns empty pending list."""
    isolated_queue.write_text("{invalid}")
    data = pinchtab_caller._load_queue()
    assert data == {"pending": []}
