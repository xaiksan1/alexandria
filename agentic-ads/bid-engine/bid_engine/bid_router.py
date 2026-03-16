import uuid
from dataclasses import dataclass
from typing import Any
from bid_engine.utility import BidParams, optimal_bid
from bid_engine.rl_optimizer import RLOptimizer


@dataclass
class AuctionRequest:
    vertical: str
    cohorte_id: str
    geo_region: str = "QC-CA"
    device_class: str = "desktop"
    V: float = 1.0   # estimated value of a win


@dataclass
class AuctionResult:
    bid_id: str       # UUID for this auction round
    vertical: str
    cohorte_id: str
    bid_amount: float
    w1: float
    w2: float
    sponsor: dict[str, Any] | None  # None if no sponsors available
    won: bool = False  # updated after auction settles


class BidRouter:
    """Routes auction requests to optimal bids per vertical.

    Maintains one RLOptimizer per vertical, shared across requests.
    """

    def __init__(self) -> None:
        self._optimizers: dict[str, RLOptimizer] = {}
        # Mock sponsor registry (Phase 2 will use DB)
        self._sponsors: dict[str, list[dict]] = {
            "crypto": [
                {"name": "MockExchange", "symbol": "EX", "cta": "Trade now", "url": "#"},
            ],
            "cloud": [
                {"name": "MockCloud", "tier": "pro", "cta": "Start free trial", "url": "#"},
            ],
        }

    def _get_optimizer(self, vertical: str) -> RLOptimizer:
        # setdefault is atomic at CPython dict level — safe under concurrent workers
        self._optimizers.setdefault(vertical, RLOptimizer())
        return self._optimizers[vertical]

    def route(self, request: AuctionRequest) -> AuctionResult:
        """Execute one auction round: compute optimal bid, select sponsor."""
        bid_id = str(uuid.uuid4())
        optimizer = self._get_optimizer(request.vertical)
        params = optimizer.state.to_bid_params(V=request.V)
        b_opt, _ = optimal_bid(params, b_min=0.0, b_max=request.V, steps=200)

        # Select first available sponsor for this vertical (Phase 2: DB query)
        sponsors = self._sponsors.get(request.vertical, [])
        sponsor = sponsors[0] if sponsors else None

        return AuctionResult(
            bid_id=bid_id,
            vertical=request.vertical,
            cohorte_id=request.cohorte_id,
            bid_amount=b_opt,
            w1=optimizer.state.w1,
            w2=optimizer.state.w2,
            sponsor=sponsor,
        )

    def record_outcome(self, vertical: str, won: bool, bid_amount: float, V: float) -> None:
        """Feed auction result back to the RL optimizer for the vertical."""
        optimizer = self._get_optimizer(vertical)
        optimizer.update(won=won, bid_amount=bid_amount, V=V)

    def optimizer_state(self, vertical: str) -> dict:
        """Get current optimizer state for a vertical."""
        opt = self._get_optimizer(vertical)
        return {
            "vertical": vertical,
            "w1": opt.state.w1,
            "w2": opt.state.w2,
            "bid_count": opt.state.bid_count,
            "win_rate": opt.win_rate(),
            "is_reliable": opt.state.is_reliable,
        }
