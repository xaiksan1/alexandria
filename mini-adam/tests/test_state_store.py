import pytest
import runner.state_store as ss
from runner.state_store import init_db, create_agent, update_agent, get_agent


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    """Each test gets its own isolated database."""
    ss.DB_PATH = tmp_path / "test_agents.db"
    await init_db()


@pytest.mark.asyncio
async def test_create_and_get():
    """Test creating and retrieving an agent."""
    await create_agent("agent-1")
    row = await get_agent("agent-1")
    assert row is not None
    assert row["agent_id"] == "agent-1"
    assert row["status"] == "PENDING"
    assert row["result"] is None
    assert row["elapsed_ms"] >= 0


@pytest.mark.asyncio
async def test_update_status_done():
    """Test updating agent status to DONE with result."""
    await create_agent("agent-2")
    await update_agent("agent-2", "DONE", "hello result")
    row = await get_agent("agent-2")
    assert row["status"] == "DONE"
    assert row["result"] == "hello result"


@pytest.mark.asyncio
async def test_update_status_error():
    """Test updating agent status to ERROR."""
    await create_agent("agent-3")
    await update_agent("agent-3", "ERROR", "something failed")
    row = await get_agent("agent-3")
    assert row["status"] == "ERROR"


@pytest.mark.asyncio
async def test_get_nonexistent_returns_none():
    """Test that getting a nonexistent agent returns None."""
    row = await get_agent("nonexistent-id")
    assert row is None


@pytest.mark.asyncio
async def test_elapsed_ms_nonnegative():
    """Test that elapsed_ms is always >= 0."""
    import asyncio
    await create_agent("agent-4")
    await asyncio.sleep(0.01)
    await update_agent("agent-4", "DONE", "ok")
    row = await get_agent("agent-4")
    assert row["elapsed_ms"] >= 0
