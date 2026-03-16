import math
from dataclasses import dataclass


@dataclass
class BidParams:
    """Parameters for the U(b) utility function."""
    V: float          # estimated value of a win
    w1: float = 0.7   # profit weight (cold-start default)
    w2: float = 0.3   # cost weight (cold-start default)
    k: float = 5.0    # sigmoid steepness
    b_mid: float = 0.5  # sigmoid midpoint

    def __post_init__(self):
        self._validate()

    def _validate(self):
        if self.V < 0:
            raise ValueError(f"V must be >= 0, got {self.V}")
        if not (0 < self.w1 < 1):
            raise ValueError(f"w1 must be in (0, 1), got {self.w1}")
        # CRITICAL: enforce w1 + w2 = 1.0 invariant
        self.w2 = round(1.0 - self.w1, 4)
        assert abs(self.w1 + self.w2 - 1.0) < 1e-9, f"w1+w2 invariant broken: {self.w1}+{self.w2}"


def p_win(b: float, k: float = 5.0, b_mid: float = 0.5) -> float:
    """Win probability: sigmoid of bid amount.

    p(win|b) = 1 / (1 + exp(-k * (b - b_mid)))
    """
    return 1.0 / (1.0 + math.exp(-k * (b - b_mid)))


def utility(b: float, params: BidParams) -> float:
    """Compute U(b) = w1 * p(win|b) * (V - b) - w2 * Cost(b).

    Args:
        b: Bid amount (must be >= 0)
        params: BidParams with V, w1, w2, k, b_mid

    Returns:
        Utility value. Higher is better.
    """
    if b < 0:
        raise ValueError(f"Bid amount must be >= 0, got {b}")
    pw = p_win(b, params.k, params.b_mid)
    return params.w1 * pw * (params.V - b) - params.w2 * b


def optimal_bid(
    params: BidParams,
    b_min: float = 0.0,
    b_max: float = 1.0,
    steps: int = 1000,
) -> tuple[float, float]:
    """Find the bid amount that maximizes U(b) by grid search.

    Args:
        params: BidParams
        b_min: Minimum bid to consider
        b_max: Maximum bid to consider
        steps: Grid resolution

    Returns:
        (optimal_bid, max_utility)
    """
    if steps <= 0:
        raise ValueError(f"steps must be > 0, got {steps}")
    if b_min > b_max:
        raise ValueError(f"b_min ({b_min}) must be <= b_max ({b_max})")
    step = (b_max - b_min) / steps
    best_b = b_min
    best_u = utility(b_min, params)
    for i in range(1, steps + 1):
        b = b_min + i * step  # anchored — no float drift from accumulation
        u = utility(b, params)
        if u > best_u:
            best_u = u
            best_b = b
    return round(best_b, 6), round(best_u, 6)
