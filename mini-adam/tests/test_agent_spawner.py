import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import runner.state_store as ss
from runner.state_store import init_db, get_agent
from runner.agent_spawner import spawn_agent


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    ss.DB_PATH = tmp_path / "agents.db"
    await init_db()


def _mock_anthropic(text: str):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    mock_instance = AsyncMock()
    mock_instance.messages.create = AsyncMock(return_value=mock_msg)
    return patch("runner.agent_spawner.anthropic.AsyncAnthropic", return_value=mock_instance)


async def test_short_task_returns_result_immediately():
    with _mock_anthropic("short result"):
        agent_id, result = await spawn_agent("analyze", "hello", "claude-sonnet-4-6", timeout=3)
    assert result == "short result"
    row = await get_agent(agent_id)
    assert row["status"] == "DONE"


async def test_long_task_returns_none_immediately():
    with _mock_anthropic("long result"):
        agent_id, result = await spawn_agent("render", "big job", "claude-sonnet-4-6", timeout=10)
        assert result is None  # caller must poll
        # sleep inside the mock context so the background task can run with the mock still active
        await asyncio.sleep(0.05)
    row = await get_agent(agent_id)
    assert row["status"] == "DONE"


async def test_agent_error_sets_error_status():
    mock_instance = AsyncMock()
    mock_instance.messages.create = AsyncMock(side_effect=RuntimeError("API down"))
    with patch("runner.agent_spawner.anthropic.AsyncAnthropic", return_value=mock_instance):
        with pytest.raises(RuntimeError):
            await spawn_agent("analyze", "oops", "claude-sonnet-4-6", timeout=3)
