import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
import runner.state_store as ss
from runner.state_store import init_db
from router.auth import sign_token


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    ss.DB_PATH = tmp_path / "agents.db"
    await init_db()


@pytest.fixture
def token():
    return sign_token("pending", "spawn")


def _mock_gemini(text: str):
    mock_response = MagicMock()
    mock_response.text = text
    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
    return patch("runner.agent_spawner.genai.Client", return_value=mock_client)


async def test_spawn_short_task_returns_done(token):
    from runner.main import app
    with _mock_gemini("mocked result"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post(
                "/spawn",
                json={"action": "analyze", "payload": "test", "model": "claude-sonnet-4-6", "timeout": 3},
                headers={"Authorization": f"Bearer {token}"},
            )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "DONE"
    assert data["result"] == "mocked result"
    assert "agent_id" in data


async def test_spawn_missing_auth_returns_422():
    from runner.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/spawn", json={"action": "x", "payload": "", "model": "x", "timeout": 1})
    assert resp.status_code == 422


async def test_spawn_invalid_token_returns_401():
    from runner.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/spawn",
            json={"action": "x", "payload": "", "model": "x", "timeout": 1},
            headers={"Authorization": "Bearer invalid.bad.token"},
        )
    assert resp.status_code == 401


async def test_state_unknown_agent_returns_404():
    from runner.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.get("/state/does-not-exist")
    assert resp.status_code == 404


async def test_state_known_agent_returns_data(token):
    from runner.main import app
    with _mock_gemini("ok"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            spawn_resp = await ac.post(
                "/spawn",
                json={"action": "a", "payload": "b", "model": "claude-sonnet-4-6", "timeout": 3},
                headers={"Authorization": f"Bearer {token}"},
            )
            agent_id = spawn_resp.json()["agent_id"]
            state_resp = await ac.get(f"/state/{agent_id}")
    assert state_resp.status_code == 200
    assert state_resp.json()["status"] == "DONE"
