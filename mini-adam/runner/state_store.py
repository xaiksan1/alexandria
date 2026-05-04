"""
State store for agents using SQLite.
Manages agent lifecycle: PENDING → RUNNING → DONE/ERROR.
"""

import time
from pathlib import Path
from typing import Literal

import aiosqlite

DB_PATH = Path("data/agents.db")

Status = Literal["PENDING", "RUNNING", "DONE", "ERROR"]


async def init_db() -> None:
    """Initialize the database schema."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
                agent_id   TEXT PRIMARY KEY,
                status     TEXT NOT NULL,
                result     TEXT,
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
        """)
        await db.commit()


async def create_agent(agent_id: str) -> None:
    """Create a new agent with PENDING status."""
    now = _now_ms()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO agents (agent_id, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (agent_id, "PENDING", now, now),
        )
        await db.commit()


async def update_agent(agent_id: str, status: Status, result: str | None = None) -> None:
    """Update agent status and optional result."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE agents SET status=?, result=?, updated_at=? WHERE agent_id=?",
            (status, result, _now_ms(), agent_id),
        )
        await db.commit()


async def get_agent(agent_id: str) -> dict | None:
    """
    Retrieve an agent by ID.
    Returns dict with: agent_id, status, result, created_at, updated_at, elapsed_ms
    Or None if not found.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT agent_id, status, result, created_at, updated_at FROM agents WHERE agent_id=?",
            (agent_id,),
        ) as cursor:
            row = await cursor.fetchone()

    if row is None:
        return None

    return {
        "agent_id": row[0],
        "status": row[1],
        "result": row[2],
        "created_at": row[3],
        "updated_at": row[4],
        "elapsed_ms": row[4] - row[3],
    }


def _now_ms() -> int:
    """Get current time in milliseconds since epoch."""
    return int(time.time() * 1000)
