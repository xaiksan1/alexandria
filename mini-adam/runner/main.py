import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

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
