from dataclasses import dataclass, field
from bid_engine.utility import BidParams


@dataclass
class RLOptimizerState:
    """State for the RL weight optimizer."""
    w1: float = 0.7          # cold-start default
    w2: float = 0.3          # auto-computed, never set directly
    alpha: float = 0.01      # learning rate
    bid_count: int = 0        # number of bids seen
    win_count: int = 0        # number of wins seen

    def __post_init__(self):
        if not (0 < self.alpha <= 0.5):
            raise ValueError(f"alpha must be in (0, 0.5], got {self.alpha}")
        # Enforce invariant on creation
        self.w2 = round(1.0 - self.w1, 4)
        assert abs(self.w1 + self.w2 - 1.0) < 1e-9

    @property
    def is_reliable(self) -> bool:
        """True after 50 bids — enough data to trust weights."""
        return self.bid_count >= 50

    def to_bid_params(self, V: float, **kwargs) -> "BidParams":
        """Create a BidParams from current optimizer state."""
        return BidParams(V=V, w1=self.w1, **kwargs)


class RLOptimizer:
    """Online RL optimizer for bid weights w1/w2.

    Updates weights based on auction win/loss feedback.
    Enforces w1 + w2 = 1.0 invariant after every update.
    """

    W1_MIN = 0.1   # never go below (prevent degenerate all-cost bidding)
    W1_MAX = 0.95  # never go above (prevent degenerate ignore-cost bidding)

    def __init__(self, state: RLOptimizerState | None = None) -> None:
        self.state = state or RLOptimizerState()

    def update(self, won: bool, bid_amount: float, V: float) -> RLOptimizerState:
        """Update weights based on auction outcome.

        Args:
            won: True if this bid won the auction
            bid_amount: The bid amount placed
            V: Estimated value of a win

        Returns:
            Updated state (also mutates self.state)
        """
        self.state.bid_count += 1

        if won:
            self.state.win_count += 1
            # Won: increase w1 (profit motive was appropriate)
            new_w1 = self.state.w1 + self.state.alpha
        else:
            # Lost: decrease w1 (cost was too high, be more conservative)
            new_w1 = self.state.w1 - self.state.alpha

        # Clamp to safe range
        new_w1 = max(self.W1_MIN, min(self.W1_MAX, new_w1))

        # CRITICAL: enforce w1 + w2 = 1.0 invariant
        self.state.w1 = round(new_w1, 4)
        self.state.w2 = round(1.0 - self.state.w1, 4)
        assert abs(self.state.w1 + self.state.w2 - 1.0) < 1e-9, (
            f"Invariant broken: w1={self.state.w1} + w2={self.state.w2} = {self.state.w1 + self.state.w2}"
        )

        return self.state

    def win_rate(self) -> float:
        """Current win rate. Returns 0.0 if no bids yet."""
        if self.state.bid_count == 0:
            return 0.0
        return self.state.win_count / self.state.bid_count

    def reset(self) -> None:
        """Reset to cold-start state."""
        self.state = RLOptimizerState()
