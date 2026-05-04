"""
Test d'intégration end-to-end.
Nécessite les deux services démarrés (PM2 ou Docker).
Lancer avec : pytest tests/test_integration.py -m integration -v

Skip automatique si ROUTER_URL non joignable.
"""
import os
import time
import pytest
import httpx

ROUTER_URL = os.environ.get("ROUTER_URL", "http://localhost:4000")
TIMEOUT = 60


@pytest.fixture(scope="session")
def services_up():
    try:
        httpx.get(f"{ROUTER_URL}/docs", timeout=3)
    except httpx.RequestError:
        pytest.skip("Services not running — start with: pm2 start ecosystem.config.js")


@pytest.mark.integration
def test_spawn_short_task_end_to_end(services_up):
    resp = httpx.post(
        f"{ROUTER_URL}/cmd",
        json={"emoji": "🤖", "payload": "Reply with exactly the word: PASSED"},
        timeout=30,
    )
    assert resp.status_code == 200, f"Unexpected: {resp.text}"
    data = resp.json()

    agent_id = data["agent_id"]
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        state = httpx.get(f"{ROUTER_URL}/state/{agent_id}").json()
        if state["status"] in ("DONE", "ERROR"):
            break
        time.sleep(1)

    assert state["status"] == "DONE", f"Agent ended with: {state}"
    assert "PASSED" in state["result"]


@pytest.mark.integration
def test_state_unknown_agent_404(services_up):
    resp = httpx.get(f"{ROUTER_URL}/state/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.integration
def test_unknown_emoji_400(services_up):
    resp = httpx.post(f"{ROUTER_URL}/cmd", json={"emoji": "❓❓❓", "payload": ""})
    assert resp.status_code == 400
