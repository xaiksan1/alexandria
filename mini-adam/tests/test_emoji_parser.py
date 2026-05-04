import json
import pytest
from pathlib import Path
from router.emoji_parser import parse_emoji


def _cmd_file(tmp_path: Path, data: dict) -> Path:
    p = tmp_path / "commands.json"
    p.write_text(json.dumps(data))
    return p


def test_system_emoji_spawn(tmp_path):
    f = _cmd_file(tmp_path, {})
    result = parse_emoji("🤖", f)
    assert result["system_action"] == "spawn"
    assert result["custom_action"] is None
    assert result["model"] == "claude-sonnet-4-6"


def test_system_emoji_route(tmp_path):
    f = _cmd_file(tmp_path, {})
    result = parse_emoji("📡", f)
    assert result["system_action"] == "route"


def test_system_emoji_state(tmp_path):
    f = _cmd_file(tmp_path, {})
    result = parse_emoji("📊", f)
    assert result["system_action"] == "state"


def test_system_emoji_priority_over_custom(tmp_path):
    f = _cmd_file(tmp_path, {"🤖": {"action": "should_not_appear", "model": "x", "timeout": 1}})
    result = parse_emoji("🤖", f)
    assert result["system_action"] == "spawn"


def test_custom_emoji(tmp_path):
    f = _cmd_file(tmp_path, {"⚙️🎬": {"action": "render", "model": "claude-sonnet-4-6", "timeout": 300}})
    result = parse_emoji("⚙️🎬", f)
    assert result["system_action"] is None
    assert result["custom_action"] == "render"
    assert result["timeout"] == 300


def test_custom_emoji_defaults(tmp_path):
    f = _cmd_file(tmp_path, {"🎨": {"action": "paint"}})
    result = parse_emoji("🎨", f)
    assert result["model"] == "claude-sonnet-4-6"
    assert result["timeout"] == 30


def test_unknown_emoji_raises(tmp_path):
    f = _cmd_file(tmp_path, {})
    with pytest.raises(ValueError, match="Unknown emoji"):
        parse_emoji("❓", f)


def test_missing_commands_file_treats_as_empty(tmp_path):
    f = tmp_path / "nonexistent.json"
    with pytest.raises(ValueError, match="Unknown emoji"):
        parse_emoji("❓", f)


def test_system_emoji_payload_extracted(tmp_path):
    """Test that system emoji payload is correctly extracted (startswith behavior)."""
    f = _cmd_file(tmp_path, {})
    result = parse_emoji("🤖 run this task", f)
    assert result["system_action"] == "spawn"
    assert result["payload"] == "run this task"


def test_system_emoji_key_set(tmp_path):
    """Test that emoji_key is correctly set for system emoji."""
    f = _cmd_file(tmp_path, {})
    result = parse_emoji("🤖", f)
    assert result["emoji_key"] == "🤖"
