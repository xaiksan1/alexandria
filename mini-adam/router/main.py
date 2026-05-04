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
