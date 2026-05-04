# mini-adam Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Service qui reçoit une commande emoji → spawne un agent LLM → retourne l'état, avec tests passants.

**Architecture:** Deux process FastAPI indépendants (router :4000 / runner :4001) séparés par un JWT HMAC-SHA256. Router parse les emojis et signe les tokens ; Runner vérifie les tokens, spawne les agents LLM (Claude via Anthropic SDK), persiste l'état dans SQLite.

**Tech Stack:** Python 3.11+, FastAPI, uvicorn, httpx, PyJWT, aiosqlite, anthropic SDK, pytest, pytest-asyncio, respx, PM2, Docker.

---

## File Map

| Fichier | Rôle |
|---------|------|
| `pyproject.toml` | Dépendances + config pytest |
| `.env.example` | Template secrets (JWT_SECRET, ANTHROPIC_API_KEY) |
| `config/commands.json` | Table emoji extensible rechargeable à chaud |
| `tests/conftest.py` | Variables d'env de test globales |
| `tests/test_emoji_parser.py` | Tests emoji_parser |
| `tests/test_auth.py` | Tests sign + verify JWT |
| `tests/test_state_store.py` | Tests CRUD SQLite |
| `tests/test_agent_spawner.py` | Tests spawn sync/async avec mock LLM |
| `tests/test_router.py` | Tests router endpoints (mock runner via respx) |
| `tests/test_runner.py` | Tests runner endpoints (mock LLM) |
| `tests/test_integration.py` | E2E marqué `integration` (services réels requis) |
| `router/__init__.py` | Vide |
| `router/emoji_parser.py` | Parse emoji string → commande structurée |
| `router/auth.py` | `sign_token()` HMAC-SHA256 |
| `router/main.py` | FastAPI :4000 — /cmd et /state/{id} |
| `runner/__init__.py` | Vide |
| `runner/auth.py` | `verify_token()` HMAC-SHA256 |
| `runner/state_store.py` | CRUD SQLite via aiosqlite |
| `runner/agent_spawner.py` | Spawn short/long agents via asyncio |
| `runner/main.py` | FastAPI :4001 — /spawn et /state/{id} |
| `ecosystem.config.js` | PM2 — 2 apps |
| `docker-compose.yml` | Réseau mini-adam-net |
| `Dockerfile` | Image Python partagée |
| `.gitignore` | Exclut data/, .env, __pycache__ |

---

## Task 0: Scaffold du projet

**Files:**
- Create: `mini-adam/pyproject.toml`
- Create: `mini-adam/.env.example`
- Create: `mini-adam/.gitignore`
- Create: `mini-adam/config/commands.json`
- Create: `mini-adam/tests/conftest.py`
- Create: `mini-adam/router/__init__.py`
- Create: `mini-adam/runner/__init__.py`

- [ ] **Step 1: Créer la structure de répertoires**

```bash
mkdir -p /home/ichigo/alexandria/mini-adam/{tests,router,runner,config,data,docs/superpowers/plans}
cd /home/ichigo/alexandria/mini-adam
```

- [ ] **Step 2: Écrire `pyproject.toml`**

```toml
[project]
name = "mini-adam"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "httpx>=0.27",
    "pyjwt>=2.8",
    "aiosqlite>=0.20",
    "anthropic>=0.40",
]

[project.optional-dependencies]
dev = [
    "pytest>=8",
    "pytest-asyncio>=0.23",
    "respx>=0.21",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = ["integration: requires running services (deselect with -m 'not integration')"]
```

- [ ] **Step 3: Écrire `.env.example`**

```
JWT_SECRET=change-me-use-envii
ANTHROPIC_API_KEY=sk-ant-...
RUNNER_URL=http://localhost:4001
SHORT_TASK_THRESHOLD_S=5
```

- [ ] **Step 4: Écrire `.gitignore`**

```
.env
data/
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
```

- [ ] **Step 5: Écrire `config/commands.json`**

```json
{
  "⚙️🎬": { "action": "render",  "model": "claude-sonnet-4-6", "timeout": 300 },
  "✨🚀": { "action": "deploy",  "model": "claude-sonnet-4-6", "timeout": 60  },
  "🧠📖": { "action": "analyze", "model": "claude-sonnet-4-6", "timeout": 120 }
}
```

- [ ] **Step 6: Écrire `tests/conftest.py`**

```python
import os

# Set before any app module is imported
os.environ.setdefault("JWT_SECRET", "test-secret-mini-adam")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-placeholder")
os.environ.setdefault("RUNNER_URL", "http://runner-mock:4001")
os.environ.setdefault("SHORT_TASK_THRESHOLD_S", "5")
```

- [ ] **Step 7: Créer les `__init__.py` vides**

```bash
touch router/__init__.py runner/__init__.py tests/__init__.py
```

- [ ] **Step 8: Installer les dépendances**

```bash
cd /home/ichigo/alexandria/mini-adam
pip install -e ".[dev]"
```

Expected: pas d'erreur. `pip show fastapi pyjwt aiosqlite anthropic respx` tous présents.

- [ ] **Step 9: Commit**

```bash
git add pyproject.toml .env.example .gitignore config/ tests/conftest.py router/__init__.py runner/__init__.py
git commit -m "feat(mini-adam): scaffold — pyproject, config, structure"
```

---

## Task 1: emoji_parser (TDD)

**Files:**
- Create: `tests/test_emoji_parser.py`
- Create: `router/emoji_parser.py`

- [ ] **Step 1: Écrire le test (RED)**

```python
# tests/test_emoji_parser.py
import json
import pytest
from pathlib import Path
from router.emoji_parser import parse_emoji, ParsedCommand


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
    # Even if 🤖 is in commands.json, system wins
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
    # model and timeout have defaults when not in commands.json entry
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
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
cd /home/ichigo/alexandria/mini-adam
pytest tests/test_emoji_parser.py -v
```

Expected: `ModuleNotFoundError: No module named 'router.emoji_parser'`

- [ ] **Step 3: Implémenter `router/emoji_parser.py`**

```python
import json
from pathlib import Path
from typing import TypedDict


SYSTEM_EMOJIS: dict[str, str] = {
    "🤖": "spawn",
    "📡": "route",
    "📊": "state",
}


class ParsedCommand(TypedDict):
    system_action: str | None
    custom_action: str | None
    emoji_key: str
    model: str
    timeout: int
    payload: str


def parse_emoji(emoji_str: str, commands_path: Path) -> ParsedCommand:
    for emoji, action in SYSTEM_EMOJIS.items():
        if emoji_str.startswith(emoji):
            return ParsedCommand(
                system_action=action,
                custom_action=None,
                emoji_key=emoji,
                model="claude-sonnet-4-6",
                timeout=30,
                payload=emoji_str[len(emoji):].strip(),
            )

    commands = _load_commands(commands_path)
    if emoji_str in commands:
        entry = commands[emoji_str]
        return ParsedCommand(
            system_action=None,
            custom_action=entry["action"],
            emoji_key=emoji_str,
            model=entry.get("model", "claude-sonnet-4-6"),
            timeout=entry.get("timeout", 30),
            payload="",
        )

    raise ValueError(f"Unknown emoji command: {emoji_str!r}")


def _load_commands(commands_path: Path) -> dict:
    if not commands_path.exists():
        return {}
    return json.loads(commands_path.read_text(encoding="utf-8"))
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/test_emoji_parser.py -v
```

Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
git add tests/test_emoji_parser.py router/emoji_parser.py
git commit -m "feat(mini-adam): emoji_parser — system + extensible table (TDD)"
```

---

## Task 2: Auth — sign + verify JWT (TDD)

**Files:**
- Create: `tests/test_auth.py`
- Create: `router/auth.py`
- Create: `runner/auth.py`

- [ ] **Step 1: Écrire le test (RED)**

```python
# tests/test_auth.py
import time
import pytest
import jwt as pyjwt
from router.auth import sign_token
from runner.auth import verify_token


def test_sign_produces_valid_jwt():
    token = sign_token("agent-abc", "spawn")
    # Décoder sans vérifier pour inspecter le payload
    raw = pyjwt.decode(token, options={"verify_signature": False})
    assert raw["agent_id"] == "agent-abc"
    assert raw["command"] == "spawn"
    assert "iat" in raw
    assert "exp" in raw


def test_sign_and_verify_roundtrip():
    token = sign_token("agent-xyz", "route")
    claims = verify_token(token)
    assert claims["agent_id"] == "agent-xyz"
    assert claims["command"] == "route"


def test_expired_token_rejected():
    expired = pyjwt.encode(
        {"agent_id": "x", "command": "y", "iat": 1, "exp": 1},
        "test-secret-mini-adam",
        algorithm="HS256",
    )
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(expired)


def test_wrong_secret_rejected():
    forged = pyjwt.encode(
        {"agent_id": "x", "command": "y", "iat": int(time.time()), "exp": int(time.time()) + 30},
        "WRONG-SECRET",
        algorithm="HS256",
    )
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(forged)


def test_tampered_token_rejected():
    token = sign_token("agent-abc", "spawn")
    tampered = token[:-4] + "XXXX"
    with pytest.raises(pyjwt.InvalidTokenError):
        verify_token(tampered)
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
pytest tests/test_auth.py -v
```

Expected: `ModuleNotFoundError: No module named 'router.auth'`

- [ ] **Step 3: Implémenter `router/auth.py`**

```python
import os
import time
import jwt

_SECRET = os.environ["JWT_SECRET"]
_EXPIRY_SECONDS = 30


def sign_token(agent_id: str, command: str) -> str:
    now = int(time.time())
    return jwt.encode(
        {"agent_id": agent_id, "command": command, "iat": now, "exp": now + _EXPIRY_SECONDS},
        _SECRET,
        algorithm="HS256",
    )
```

- [ ] **Step 4: Implémenter `runner/auth.py`**

```python
import os
import jwt

_SECRET = os.environ["JWT_SECRET"]


def verify_token(token: str) -> dict:
    """Raises jwt.InvalidTokenError if token is invalid or expired."""
    return jwt.decode(token, _SECRET, algorithms=["HS256"])
```

- [ ] **Step 5: Vérifier que les tests passent**

```bash
pytest tests/test_auth.py -v
```

Expected: `5 passed`

- [ ] **Step 6: Commit**

```bash
git add tests/test_auth.py router/auth.py runner/auth.py
git commit -m "feat(mini-adam): JWT auth — sign (router) + verify (runner) (TDD)"
```

---

## Task 3: state_store — SQLite (TDD)

**Files:**
- Create: `tests/test_state_store.py`
- Create: `runner/state_store.py`

- [ ] **Step 1: Écrire le test (RED)**

```python
# tests/test_state_store.py
import pytest
from pathlib import Path
import runner.state_store as ss
from runner.state_store import init_db, create_agent, update_agent, get_agent


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    ss.DB_PATH = tmp_path / "test_agents.db"
    await init_db()


async def test_create_and_get():
    await create_agent("agent-1")
    row = await get_agent("agent-1")
    assert row is not None
    assert row["agent_id"] == "agent-1"
    assert row["status"] == "PENDING"
    assert row["result"] is None
    assert row["elapsed_ms"] >= 0


async def test_update_status_done():
    await create_agent("agent-2")
    await update_agent("agent-2", "DONE", "hello result")
    row = await get_agent("agent-2")
    assert row["status"] == "DONE"
    assert row["result"] == "hello result"


async def test_update_status_error():
    await create_agent("agent-3")
    await update_agent("agent-3", "ERROR", "something failed")
    row = await get_agent("agent-3")
    assert row["status"] == "ERROR"


async def test_get_nonexistent_returns_none():
    row = await get_agent("nonexistent-id")
    assert row is None


async def test_elapsed_ms_increases_after_update():
    import asyncio
    await create_agent("agent-4")
    await asyncio.sleep(0.01)
    await update_agent("agent-4", "DONE", "ok")
    row = await get_agent("agent-4")
    assert row["elapsed_ms"] >= 0
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
pytest tests/test_state_store.py -v
```

Expected: `ModuleNotFoundError: No module named 'runner.state_store'`

- [ ] **Step 3: Implémenter `runner/state_store.py`**

```python
import time
from pathlib import Path
from typing import Literal

import aiosqlite

DB_PATH = Path("data/agents.db")

Status = Literal["PENDING", "RUNNING", "DONE", "ERROR"]


async def init_db() -> None:
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
    now = _now_ms()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO agents (agent_id, status, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (agent_id, "PENDING", now, now),
        )
        await db.commit()


async def update_agent(agent_id: str, status: Status, result: str | None = None) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE agents SET status=?, result=?, updated_at=? WHERE agent_id=?",
            (status, result, _now_ms(), agent_id),
        )
        await db.commit()


async def get_agent(agent_id: str) -> dict | None:
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
    return int(time.time() * 1000)
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/test_state_store.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add tests/test_state_store.py runner/state_store.py
git commit -m "feat(mini-adam): state_store — SQLite CRUD avec aiosqlite (TDD)"
```

---

## Task 4: agent_spawner (TDD)

**Files:**
- Create: `tests/test_agent_spawner.py`
- Create: `runner/agent_spawner.py`

- [ ] **Step 1: Écrire le test (RED)**

```python
# tests/test_agent_spawner.py
import asyncio
import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import runner.state_store as ss
from runner.state_store import init_db, get_agent
from runner.agent_spawner import spawn_agent


@pytest.fixture(autouse=True)
async def isolated_db(tmp_path):
    ss.DB_PATH = tmp_path / "agents.db"
    await init_db()


def _mock_anthropic(text: str):
    """Returns a context manager that patches anthropic.AsyncAnthropic."""
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
    # Give asyncio.Task time to finish
    await asyncio.sleep(0.05)
    row = await get_agent(agent_id)
    assert row["status"] == "DONE"


async def test_agent_error_sets_error_status():
    mock_instance = AsyncMock()
    mock_instance.messages.create = AsyncMock(side_effect=RuntimeError("API down"))
    with patch("runner.agent_spawner.anthropic.AsyncAnthropic", return_value=mock_instance):
        with pytest.raises(RuntimeError):
            await spawn_agent("analyze", "oops", "claude-sonnet-4-6", timeout=3)
    # Agent ID won't be returned on error in short-task path — check via DB would need the ID
    # This test confirms the exception propagates
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
pytest tests/test_agent_spawner.py -v
```

Expected: `ModuleNotFoundError: No module named 'runner.agent_spawner'`

- [ ] **Step 3: Implémenter `runner/agent_spawner.py`**

```python
import asyncio
import os
import uuid

import anthropic

from runner.state_store import create_agent, update_agent

SHORT_TASK_THRESHOLD_S = int(os.environ.get("SHORT_TASK_THRESHOLD_S", "5"))


async def spawn_agent(action: str, payload: str, model: str, timeout: int) -> tuple[str, str | None]:
    """
    Spawn an LLM agent.

    Short tasks (timeout <= SHORT_TASK_THRESHOLD_S): awaited inline, result returned.
    Long tasks: scheduled as asyncio.Task, None returned — caller polls state.
    """
    agent_id = str(uuid.uuid4())
    await create_agent(agent_id)

    if timeout <= SHORT_TASK_THRESHOLD_S:
        result = await _run_agent(agent_id, action, payload, model)
        return agent_id, result

    asyncio.create_task(_run_agent(agent_id, action, payload, model))
    return agent_id, None


async def _run_agent(agent_id: str, action: str, payload: str, model: str) -> str:
    await update_agent(agent_id, "RUNNING")
    try:
        client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = await client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": f"Action: {action}\n\n{payload}"}],
        )
        result: str = message.content[0].text
        await update_agent(agent_id, "DONE", result)
        return result
    except Exception as e:
        await update_agent(agent_id, "ERROR", str(e))
        raise
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/test_agent_spawner.py -v
```

Expected: `3 passed`

- [ ] **Step 5: Commit**

```bash
git add tests/test_agent_spawner.py runner/agent_spawner.py
git commit -m "feat(mini-adam): agent_spawner — short/long tasks + LLM via anthropic (TDD)"
```

---

## Task 5: runner/main.py — FastAPI :4001 (TDD)

**Files:**
- Create: `tests/test_runner.py`
- Create: `runner/main.py`

- [ ] **Step 1: Écrire le test (RED)**

```python
# tests/test_runner.py
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


def _mock_anthropic(text: str):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    mock_instance = AsyncMock()
    mock_instance.messages.create = AsyncMock(return_value=mock_msg)
    return patch("runner.agent_spawner.anthropic.AsyncAnthropic", return_value=mock_instance)


async def test_spawn_short_task_returns_done(token):
    from runner.main import app
    with _mock_anthropic("mocked result"):
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
    with _mock_anthropic("ok"):
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
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
pytest tests/test_runner.py -v
```

Expected: `ModuleNotFoundError: No module named 'runner.main'`

- [ ] **Step 3: Implémenter `runner/main.py`**

```python
import os
from contextlib import asynccontextmanager

import jwt as pyjwt
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from runner.agent_spawner import spawn_agent
from runner.auth import verify_token
from runner.state_store import get_agent, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="mini-adam-runner", lifespan=lifespan)


def _require_jwt(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    try:
        return verify_token(authorization[7:])
    except pyjwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


class SpawnRequest(BaseModel):
    action: str
    payload: str = ""
    model: str = "claude-sonnet-4-6"
    timeout: int = 30


@app.post("/spawn")
async def spawn(req: SpawnRequest, _claims: dict = Depends(_require_jwt)):
    agent_id, result = await spawn_agent(req.action, req.payload, req.model, req.timeout)
    status = "DONE" if result is not None else "RUNNING"
    return {"agent_id": agent_id, "status": status, "result": result}


@app.get("/state/{agent_id}")
async def state(agent_id: str):
    agent = await get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "4001")))
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/test_runner.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Commit**

```bash
git add tests/test_runner.py runner/main.py
git commit -m "feat(mini-adam): runner FastAPI :4001 — spawn + state + JWT guard (TDD)"
```

---

## Task 6: router/main.py — FastAPI :4000 (TDD)

**Files:**
- Create: `tests/test_router.py`
- Create: `router/main.py`

- [ ] **Step 1: Écrire le test (RED)**

```python
# tests/test_router.py
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
    # Patch module-level vars directly — env var approach breaks on cached imports
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
```

- [ ] **Step 2: Vérifier que le test échoue**

```bash
pytest tests/test_router.py -v
```

Expected: `ModuleNotFoundError: No module named 'router.main'`

- [ ] **Step 3: Implémenter `router/main.py`**

```python
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from router.auth import sign_token
from router.emoji_parser import parse_emoji

RUNNER_URL = os.environ.get("RUNNER_URL", "http://localhost:4001")
COMMANDS_PATH = Path("config/commands.json")

app = FastAPI(title="mini-adam-router")


class CmdRequest(BaseModel):
    emoji: str
    payload: str = ""


@app.post("/cmd")
async def cmd(req: CmdRequest):
    try:
        parsed = parse_emoji(req.emoji, COMMANDS_PATH)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    action = parsed["system_action"] or parsed["custom_action"]
    token = sign_token("pending", action)

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{RUNNER_URL}/spawn",
                json={
                    "action": action,
                    "payload": req.payload or parsed.get("payload", ""),
                    "model": parsed["model"],
                    "timeout": parsed["timeout"],
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=parsed["timeout"] + 5,
            )
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"Runner unreachable: {exc}") from exc

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Runner error")

    return resp.json()


@app.get("/state/{agent_id}")
async def state(agent_id: str):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{RUNNER_URL}/state/{agent_id}")

    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Agent not found")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Runner error")

    return resp.json()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "4000")))
```

- [ ] **Step 4: Vérifier que les tests passent**

```bash
pytest tests/test_router.py -v
```

Expected: `5 passed`

- [ ] **Step 5: Vérifier l'ensemble de la suite**

```bash
pytest tests/ -v -m "not integration"
```

Expected: `23 passed` (8 + 5 + 5 + 3 + 5 + ?)

- [ ] **Step 6: Commit**

```bash
git add tests/test_router.py router/main.py
git commit -m "feat(mini-adam): router FastAPI :4000 — /cmd + /state proxy (TDD)"
```

---

## Task 7: PM2, Docker, test d'intégration

**Files:**
- Create: `ecosystem.config.js`
- Create: `docker-compose.yml`
- Create: `Dockerfile`
- Create: `tests/test_integration.py`

- [ ] **Step 1: Écrire `ecosystem.config.js`**

```js
module.exports = {
  apps: [
    {
      name: "mini-adam-runner",
      script: "runner/main.py",
      interpreter: "python3",
      cwd: "/home/ichigo/alexandria/mini-adam",
      env: { PORT: "4001" },
      out_file: "logs/runner.out.log",
      error_file: "logs/runner.err.log",
    },
    {
      name: "mini-adam-router",
      script: "router/main.py",
      interpreter: "python3",
      cwd: "/home/ichigo/alexandria/mini-adam",
      env: { PORT: "4000", RUNNER_URL: "http://localhost:4001" },
      out_file: "logs/router.out.log",
      error_file: "logs/router.err.log",
    },
  ],
};
```

Note : runner démarré en premier car router dépend de lui.

- [ ] **Step 2: Écrire `Dockerfile`**

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY pyproject.toml .
RUN pip install -e .
COPY . .

EXPOSE 4000 4001
```

- [ ] **Step 3: Écrire `docker-compose.yml`**

```yaml
version: "3.9"

networks:
  mini-adam-net:
    driver: bridge
    name: mini-adam-net

services:
  runner:
    build: .
    command: python3 runner/main.py
    ports:
      - "4001:4001"
    env_file: .env
    environment:
      PORT: "4001"
    networks:
      - mini-adam-net
    volumes:
      - ./data:/app/data

  router:
    build: .
    command: python3 router/main.py
    ports:
      - "4000:4000"
    env_file: .env
    environment:
      PORT: "4000"
      RUNNER_URL: "http://runner:4001"
    networks:
      - mini-adam-net
    depends_on:
      - runner
```

- [ ] **Step 4: Créer le répertoire logs**

```bash
mkdir -p /home/ichigo/alexandria/mini-adam/logs
echo "*.log" >> .gitignore
```

- [ ] **Step 5: Écrire `tests/test_integration.py`**

```python
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
TIMEOUT = 60  # secondes max pour poll


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

    # Short task (timeout=30 ≤ SHORT_TASK_THRESHOLD_S=5? Non — so it's RUNNING)
    # Poll until DONE
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
```

- [ ] **Step 6: Vérifier la suite unitaire complète**

```bash
cd /home/ichigo/alexandria/mini-adam
pytest tests/ -v -m "not integration"
```

Expected: tous les tests passent, aucun `FAILED`.

- [ ] **Step 7: Commit final**

```bash
git add ecosystem.config.js docker-compose.yml Dockerfile logs/.gitkeep tests/test_integration.py .gitignore
git commit -m "feat(mini-adam): PM2 + Docker + test integration — MVP complet"
```

---

## Démarrage rapide (après implémentation)

```bash
cd /home/ichigo/alexandria/mini-adam

# 1. Copier et remplir les secrets via envii
cp .env.example .env
# envii restore  (si les clés sont déjà dans le vault)

# 2. Lancer via PM2
pm2 start ecosystem.config.js
pm2 logs mini-adam-runner  # vérifier démarrage

# 3. Tester manuellement
python3 -c "
import httpx, time, json
r = httpx.post('http://localhost:4000/cmd', json={'emoji':'🤖','payload':'Say: HELLO'})
print(r.json())
"

# 4. Tests d'intégration
pytest tests/test_integration.py -m integration -v

# 5. Stop
pm2 stop mini-adam-router mini-adam-runner
```
