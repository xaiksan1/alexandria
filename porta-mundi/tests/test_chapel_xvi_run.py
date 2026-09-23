"""Tests du lanceur Chapel XVI : un vrai Sanctuaire temporaire, un vrai programme lancé.

Run:  ADAM/.venv/bin/python3 -m pytest porta-mundi/tests/test_chapel_xvi_run.py -q
"""
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest
from werkzeug.serving import make_server

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import chapel_xvi_server  # noqa: E402
from chapel_xvi_run import build_env, parse_args  # noqa: E402
from chapel_xvi_sanctuary import Sanctuary, write_private  # noqa: E402
from chapel_xvi_server import SanctuaryService, create_app  # noqa: E402
from chapel_xvi_vault import ChapelXVIVault  # noqa: E402


def test_parse_args_with_aliases():
    service, aliases, cmd = parse_args(["jarvis", "--as", "BIFROST_API_KEY=BIFROST_VK_INTERNAL", "--", "echo", "hi"])
    assert service == "jarvis"
    assert aliases == {"BIFROST_API_KEY": "BIFROST_VK_INTERNAL"}
    assert cmd == ["echo", "hi"]


def test_parse_args_requires_a_command():
    with pytest.raises(SystemExit):
        parse_args(["jarvis", "--"])
    with pytest.raises(SystemExit):
        parse_args(["jarvis", "echo"])


def test_build_env_refuses_an_alias_to_a_secret_not_granted():
    with pytest.raises(SystemExit):
        build_env({}, {"A": "1"}, {"X": "B"})
    assert build_env({"PATH": "p"}, {"A": "1"}, {"X": "A"}) == {"PATH": "p", "A": "1", "X": "1"}


@pytest.fixture
def live_sanctuary(tmp_path, monkeypatch):
    monkeypatch.setattr(chapel_xvi_server, "_notify_phoenix", lambda *a, **k: None)
    store = tmp_path / "sanctuary.json"
    sanctuary, shares = Sanctuary.create(store)
    sanctuary.put("BIFROST_VK_INTERNAL", "vk-secrete")
    token = sanctuary.issue_token("jarvis")
    sanctuary.grant("jarvis", "BIFROST_VK_INTERNAL")
    paths = [tmp_path / f"s{i}" for i in (1, 2)]
    for share, path in zip(shares, paths):
        write_private(path, share.serialize())
    tokens = tmp_path / "tokens"
    write_private(tokens / "jarvis.token", token + "\n")
    svc = SanctuaryService(store, paths, ChapelXVIVault(seal_log=tmp_path / "j.jsonl"))
    svc.try_unseal()
    server = make_server("127.0.0.1", 0, create_app(svc))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield {"url": f"http://127.0.0.1:{server.server_port}", "tokens": tokens}
    server.shutdown()


def test_program_receives_its_secret_under_the_alias(live_sanctuary):
    env = {**os.environ, "CHAPEL_XVI_URL": live_sanctuary["url"], "CHAPEL_XVI_TOKENS": str(live_sanctuary["tokens"])}
    out = subprocess.run(
        [sys.executable, str(HERE / "chapel_xvi_run.py"), "jarvis", "--as", "BIFROST_API_KEY=BIFROST_VK_INTERNAL",
         "--", sys.executable, "-c", "import os; print(os.environ['BIFROST_API_KEY'])"],
        env=env, capture_output=True, text=True, timeout=30,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "vk-secrete"


def test_wrong_token_stops_without_waiting(live_sanctuary):
    write_private(live_sanctuary["tokens"] / "intrus.token", "faux\n")
    env = {**os.environ, "CHAPEL_XVI_URL": live_sanctuary["url"], "CHAPEL_XVI_TOKENS": str(live_sanctuary["tokens"])}
    out = subprocess.run(
        [sys.executable, str(HERE / "chapel_xvi_run.py"), "intrus", "--", "true"],
        env=env, capture_output=True, text=True, timeout=20,
    )
    assert out.returncode != 0
    assert "refusé" in out.stderr
