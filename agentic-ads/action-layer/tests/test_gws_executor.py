# action-layer/tests/test_gws_executor.py
"""Unit tests for GWSExecutor.

Google API clients are mocked at construction time — no real credentials needed.
GWSConfigError must propagate on missing env vars or unknown tools.
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from gws_executor import GWSConfigError, GWSExecutor


# ── helpers ────────────────────────────────────────────────────────────────────

def _make_executor(tmp_path: Path) -> GWSExecutor:
    """Return a GWSExecutor with mocked Google API clients.

    Uses __new__ to bypass __init__ (which requires real credentials and
    google-api-python-client), injecting mock clients directly.
    """
    exec_ = GWSExecutor.__new__(GWSExecutor)
    exec_._chat   = MagicMock()
    exec_._sheets = MagicMock()
    return exec_


def _write_recipe(recipes_dir: Path, name: str, steps: list) -> None:
    recipes_dir.mkdir(parents=True, exist_ok=True)
    (recipes_dir / f"{name}.json").write_text(json.dumps({"steps": steps}))


# ── __init__ ──────────────────────────────────────────────────────────────────

class TestGWSExecutorInit:
    def test_raises_if_creds_env_missing(self):
        env = {k: v for k, v in os.environ.items() if k != "GOOGLE_APPLICATION_CREDENTIALS"}
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(GWSConfigError, match="GOOGLE_APPLICATION_CREDENTIALS"):
                GWSExecutor()

    def test_raises_if_creds_file_missing(self, tmp_path):
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": str(tmp_path / "nope.json")}):
            with pytest.raises(GWSConfigError, match="not found"):
                GWSExecutor()

    def test_raises_if_google_libs_not_installed(self, tmp_path):
        creds_file = tmp_path / "sa.json"
        creds_file.write_text("{}")
        with patch.dict(os.environ, {"GOOGLE_APPLICATION_CREDENTIALS": str(creds_file)}):
            with patch.dict(sys.modules, {"google.oauth2": None, "googleapiclient.discovery": None}):
                with pytest.raises((GWSConfigError, ImportError)):
                    GWSExecutor()


# ── _resolve ──────────────────────────────────────────────────────────────────

class TestResolve:
    def test_string_substitution(self, tmp_path):
        ex = _make_executor(tmp_path)
        assert ex._resolve("{foo} bar {baz}", {"foo": "hello", "baz": "world"}) == "hello bar world"

    def test_list_substitution(self, tmp_path):
        ex = _make_executor(tmp_path)
        assert ex._resolve(["{a}", "{b}"], {"a": "x", "b": "y"}) == ["x", "y"]

    def test_dict_substitution(self, tmp_path):
        ex = _make_executor(tmp_path)
        result = ex._resolve({"k": "{v}"}, {"v": "val"})
        assert result == {"k": "val"}

    def test_missing_var_raises(self, tmp_path):
        ex = _make_executor(tmp_path)
        with pytest.raises(GWSConfigError, match="not provided"):
            ex._resolve("{missing}", {})

    def test_passthrough_non_string(self, tmp_path):
        ex = _make_executor(tmp_path)
        assert ex._resolve(42, {}) == 42


# ── _chat_send ────────────────────────────────────────────────────────────────

class TestChatSend:
    def test_calls_chat_api(self, tmp_path):
        ex = _make_executor(tmp_path)
        ex._chat_send({"space": "MY_SPACE", "message": "hello"})
        ex._chat.spaces().messages().create.assert_called_once_with(
            parent="spaces/MY_SPACE",
            body={"text": "hello"},
        )
        ex._chat.spaces().messages().create().execute.assert_called_once()


# ── _sheets_append ────────────────────────────────────────────────────────────

class TestSheetsAppend:
    def test_calls_sheets_api(self, tmp_path):
        ex = _make_executor(tmp_path)
        ex._sheets_append({
            "spreadsheet_id": "SHEET_ID",
            "range": "Sheet1!A:C",
            "values": ["a", "b", "c"],
        })
        ex._sheets.spreadsheets().values().append.assert_called_once_with(
            spreadsheetId="SHEET_ID",
            range="Sheet1!A:C",
            valueInputOption="USER_ENTERED",
            body={"values": [["a", "b", "c"]]},
        )


# ── execute ───────────────────────────────────────────────────────────────────

class TestExecute:
    def test_chat_recipe_dispatched(self, tmp_path, monkeypatch):
        ex = _make_executor(tmp_path)
        # Point RECIPES_DIR to tmp
        import gws_executor
        monkeypatch.setattr(gws_executor, "RECIPES_DIR", tmp_path)
        _write_recipe(tmp_path, "test_chat", [
            {"tool": "gws-chat-send", "params": {"space": "OPS", "message": "hi {name}"}},
        ])
        monkeypatch.setenv("GWS_REVENUE_SHEET_ID", "SHEET123")

        ex.execute("test_chat", {"name": "world"})
        ex._chat.spaces().messages().create.assert_called_once()

    def test_sheets_recipe_dispatched(self, tmp_path, monkeypatch):
        ex = _make_executor(tmp_path)
        import gws_executor
        monkeypatch.setattr(gws_executor, "RECIPES_DIR", tmp_path)
        _write_recipe(tmp_path, "test_sheet", [
            {
                "tool": "gws-sheets-append",
                "params": {
                    "spreadsheet_id": "{REVENUE_SHEET_ID}",
                    "range": "A:B",
                    "values": ["{date}", "{amount}"],
                },
            },
        ])
        monkeypatch.setenv("GWS_REVENUE_SHEET_ID", "SHEET_XYZ")

        ex.execute("test_sheet", {"date": "2026-01-01", "amount": "9.99"})
        ex._sheets.spreadsheets().values().append.assert_called_once()

    def test_unknown_tool_raises(self, tmp_path, monkeypatch):
        ex = _make_executor(tmp_path)
        import gws_executor
        monkeypatch.setattr(gws_executor, "RECIPES_DIR", tmp_path)
        _write_recipe(tmp_path, "bad_tool", [
            {"tool": "unknown-tool", "params": {}},
        ])
        monkeypatch.setenv("GWS_REVENUE_SHEET_ID", "X")

        with pytest.raises(GWSConfigError, match="Unknown GWS tool"):
            ex.execute("bad_tool", {})

    def test_missing_recipe_raises(self, tmp_path, monkeypatch):
        ex = _make_executor(tmp_path)
        import gws_executor
        monkeypatch.setattr(gws_executor, "RECIPES_DIR", tmp_path)

        with pytest.raises(FileNotFoundError):
            ex.execute("nonexistent", {})

    def test_missing_revenue_sheet_id_raises(self, tmp_path, monkeypatch):
        ex = _make_executor(tmp_path)
        import gws_executor
        monkeypatch.setattr(gws_executor, "RECIPES_DIR", tmp_path)
        _write_recipe(tmp_path, "needs_sheet", [
            {
                "tool": "gws-sheets-append",
                "params": {
                    "spreadsheet_id": "{REVENUE_SHEET_ID}",
                    "range": "A:B",
                    "values": [],
                },
            },
        ])
        monkeypatch.delenv("GWS_REVENUE_SHEET_ID", raising=False)

        with pytest.raises(GWSConfigError, match="GWS_REVENUE_SHEET_ID"):
            ex.execute("needs_sheet", {})
