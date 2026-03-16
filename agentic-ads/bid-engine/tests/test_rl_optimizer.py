import pytest
from bid_engine.rl_optimizer import RLOptimizer, RLOptimizerState
from bid_engine.utility import BidParams


def test_cold_start_weights():
    opt = RLOptimizer()
    assert opt.state.w1 == 0.7
    assert opt.state.w2 == 0.3


def test_invariant_on_init():
    state = RLOptimizerState()
    assert abs(state.w1 + state.w2 - 1.0) < 1e-9


def test_invariant_after_win():
    opt = RLOptimizer()
    state = opt.update(won=True, bid_amount=0.5, V=1.0)
    assert abs(state.w1 + state.w2 - 1.0) < 1e-9


def test_invariant_after_loss():
    opt = RLOptimizer()
    state = opt.update(won=False, bid_amount=0.5, V=1.0)
    assert abs(state.w1 + state.w2 - 1.0) < 1e-9


def test_w1_increases_on_win():
    opt = RLOptimizer()
    initial_w1 = opt.state.w1
    opt.update(won=True, bid_amount=0.5, V=1.0)
    assert opt.state.w1 > initial_w1


def test_w1_decreases_on_loss():
    opt = RLOptimizer()
    initial_w1 = opt.state.w1
    opt.update(won=False, bid_amount=0.5, V=1.0)
    assert opt.state.w1 < initial_w1


def test_w1_never_below_min():
    opt = RLOptimizer()
    # Force many losses
    for _ in range(200):
        opt.update(won=False, bid_amount=0.5, V=1.0)
    assert opt.state.w1 >= RLOptimizer.W1_MIN


def test_w1_never_above_max():
    opt = RLOptimizer()
    # Force many wins
    for _ in range(200):
        opt.update(won=True, bid_amount=0.5, V=1.0)
    assert opt.state.w1 <= RLOptimizer.W1_MAX


def test_bid_count_increments():
    opt = RLOptimizer()
    opt.update(won=True, bid_amount=0.5, V=1.0)
    opt.update(won=False, bid_amount=0.3, V=1.0)
    assert opt.state.bid_count == 2


def test_win_count_increments():
    opt = RLOptimizer()
    opt.update(won=True, bid_amount=0.5, V=1.0)
    opt.update(won=False, bid_amount=0.3, V=1.0)
    assert opt.state.win_count == 1


def test_not_reliable_before_50_bids():
    opt = RLOptimizer()
    for _ in range(49):
        opt.update(won=True, bid_amount=0.5, V=1.0)
    assert not opt.state.is_reliable


def test_reliable_after_50_bids():
    opt = RLOptimizer()
    for _ in range(50):
        opt.update(won=True, bid_amount=0.5, V=1.0)
    assert opt.state.is_reliable


def test_win_rate():
    opt = RLOptimizer()
    opt.update(won=True, bid_amount=0.5, V=1.0)
    opt.update(won=True, bid_amount=0.5, V=1.0)
    opt.update(won=False, bid_amount=0.5, V=1.0)
    assert abs(opt.win_rate() - 2/3) < 1e-9


def test_win_rate_zero_before_bids():
    opt = RLOptimizer()
    assert opt.win_rate() == 0.0


def test_reset_restores_cold_start():
    opt = RLOptimizer()
    for _ in range(20):
        opt.update(won=True, bid_amount=0.5, V=1.0)
    opt.reset()
    assert opt.state.w1 == 0.7
    assert opt.state.bid_count == 0


def test_invariant_never_broken_over_100_updates():
    """Stress test: invariant holds across 100 mixed updates."""
    opt = RLOptimizer()
    for i in range(100):
        won = i % 3 != 0  # roughly 2/3 wins
        opt.update(won=won, bid_amount=0.5, V=1.0)
        assert abs(opt.state.w1 + opt.state.w2 - 1.0) < 1e-9, (
            f"Invariant broken at step {i}: w1={opt.state.w1} w2={opt.state.w2}"
        )


def test_to_bid_params():
    opt = RLOptimizer()
    params = opt.state.to_bid_params(V=1.0)
    assert params.V == 1.0
    assert params.w1 == opt.state.w1
    assert params.w2 == opt.state.w2


def test_alpha_zero_raises():
    with pytest.raises(ValueError, match="alpha"):
        RLOptimizerState(alpha=0.0)


def test_alpha_too_large_raises():
    with pytest.raises(ValueError, match="alpha"):
        RLOptimizerState(alpha=0.6)


def test_alpha_boundary_valid():
    s = RLOptimizerState(alpha=0.5)
    assert s.alpha == 0.5
