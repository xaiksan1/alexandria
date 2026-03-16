from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from bid_engine.bid_router import BidRouter, AuctionRequest

_router: BidRouter | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _router
    _router = BidRouter()
    yield


app = FastAPI(title="Agentic-Ads Bid Engine API", version="1.0.0", lifespan=lifespan)


class BidRequest(BaseModel):
    vertical: str
    cohorte_id: str
    geo_region: str = "QC-CA"
    device_class: str = "desktop"
    V: float = Field(default=1.0, gt=0.0, description="Estimated win value (must be > 0)")


class OutcomeRequest(BaseModel):
    vertical: str
    won: bool
    bid_amount: float = Field(ge=0.0)
    V: float = Field(gt=0.0)


def _get_router() -> BidRouter:
    if _router is None:
        raise HTTPException(status_code=503, detail="Bid engine not ready")
    return _router


@app.post("/bid")
async def place_bid(req: BidRequest):
    result = _get_router().route(AuctionRequest(
        vertical=req.vertical,
        cohorte_id=req.cohorte_id,
        geo_region=req.geo_region,
        device_class=req.device_class,
        V=req.V,
    ))
    return {
        "bid_id": result.bid_id,
        "vertical": result.vertical,
        "bid_amount": result.bid_amount,
        "w1": result.w1,
        "w2": result.w2,
        "sponsor": result.sponsor,
    }


@app.post("/bid/outcome")
async def record_outcome(req: OutcomeRequest):
    _get_router().record_outcome(
        vertical=req.vertical,
        won=req.won,
        bid_amount=req.bid_amount,
        V=req.V,
    )
    return {"ok": True}


@app.get("/optimizer/{vertical}")
async def optimizer_state(vertical: str):
    return _get_router().optimizer_state(vertical)


@app.get("/health")
async def health():
    return {"status": "ok", "port": 3045}
