"""Cache API — FastAPI app on port 3044.

Endpoints:
    POST /cache/set      — encrypt and store a bid response
    GET  /cache/get      — retrieve and decrypt a cached response
    GET  /cache/hash     — compute Loi 25-compliant context hash
    GET  /health         — liveness check
"""

import os
import base64
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from cache.vault import Vault
from cache.bid_cache import BidCache

_vault: Vault | None = None
_cache: BidCache | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _vault, _cache
    _vault = Vault()
    _cache = BidCache(
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6380"),
        vault=_vault,
    )
    yield
    if _cache:
        await _cache.close()


app = FastAPI(title="Agentic-Ads Cache API", lifespan=lifespan)


class SetRequest(BaseModel):
    cohorte_id: str
    vertical: str
    payload_b64: str
    ttl: int = 3600


@app.post("/cache/set")
async def cache_set(req: SetRequest):
    try:
        payload = base64.b64decode(req.payload_b64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 payload")
    await _cache.set(req.cohorte_id, req.vertical, payload, req.ttl)
    return {"ok": True}


@app.get("/cache/get")
async def cache_get(cohorte_id: str, vertical: str):
    result = await _cache.get(cohorte_id, vertical)
    if result is None:
        return {"hit": False}
    return {"hit": True, "payload_b64": base64.b64encode(result).decode()}


@app.get("/cache/hash")
async def cache_hash(vertical: str, region: str, device: str):
    h = BidCache.compute_context_hash(vertical, region, device)
    return {"context_hash": h}


@app.get("/health")
async def health():
    return {"status": "ok", "port": 3044}
