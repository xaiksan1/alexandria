import json
import pytest
import respx
import httpx
from fastapi.testclient import TestClient


@pytest.fixture
def cmd_file(tmp_path):
    data = {
        "🧠📖": {"action": "analyze", "model": "claude-sonnet-4-6", "timeout": 120},
    }
    p = tmp_path / "commands.json"
    p.write_text(json.dumps(data))
    return p


@pytest.fixture
def router_app(cmd_file, monkeypatch):
    import router.main as rm
    monkeypatch.setattr(rm, "RUNNER_URL", "http://runner-mock:4001")
    monkeypatch.setattr(rm, "COMMANDS_PATH", cmd_file)
    return rm.app


@respx.mock
def test_cmd_system_emoji_spawn(router_app):
    respx.post("http://runner-mock:4001/spawn").mock(
        return_value=httpx.Response(200, json={"agent_id": "abc", "status": "DONE", "result": "hello"})
    )
    client = TestClient(router_app)
    resp = client.post("/cmd", json={"emoji": "🤖", "payload": "do something"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["agent_id"] == "abc"
    assert data["status"] == "DONE"


@respx.mock
def test_cmd_custom_emoji(router_app):
    respx.post("http://runner-mock:4001/spawn").mock(
        return_value=httpx.Response(200, json={"agent_id": "xyz", "status": "RUNNING", "result": None})
    )
    client = TestClient(router_app)
    resp = client.post("/cmd", json={"emoji": "🧠📖", "payload": "analyze this"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "RUNNING"


def test_cmd_unknown_emoji_returns_400(router_app):
    client = TestClient(router_app)
    resp = client.post("/cmd", json={"emoji": "❓", "payload": ""})
    assert resp.status_code == 400


@respx.mock
def test_state_proxied(router_app):
    respx.get("http://runner-mock:4001/state/abc").mock(
        return_value=httpx.Response(200, json={
            "agent_id": "abc", "status": "DONE", "result": "ok", "elapsed_ms": 500
        })
    )
    client = TestClient(router_app)
    resp = client.get("/state/abc")
    assert resp.status_code == 200
    assert resp.json()["elapsed_ms"] == 500


@respx.mock
def test_state_not_found_proxied(router_app):
    respx.get("http://runner-mock:4001/state/missing").mock(
        return_value=httpx.Response(404, json={"detail": "Agent not found"})
    )
    client = TestClient(router_app)
    resp = client.get("/state/missing")
    assert resp.status_code == 404
