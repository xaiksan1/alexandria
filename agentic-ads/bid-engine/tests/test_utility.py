import math
import pytest
from bid_engine.utility import BidParams, p_win, utility, optimal_bid


def test_p_win_at_midpoint():
    """p(win | b_mid) should be 0.5."""
    assert abs(p_win(0.5, k=5.0, b_mid=0.5) - 0.5) < 1e-9


def test_p_win_increases_with_bid():
    assert p_win(0.8, k=5.0, b_mid=0.5) > p_win(0.3, k=5.0, b_mid=0.5)


def test_p_win_bounded():
    assert 0.0 < p_win(0.0) < 1.0
    assert 0.0 < p_win(1.0) < 1.0


def test_bid_params_w2_auto_normalized():
    """w2 must always equal round(1.0 - w1, 4)."""
    p = BidParams(V=1.0, w1=0.7)
    assert p.w2 == 0.3
    p2 = BidParams(V=1.0, w1=0.6)
    assert p2.w2 == 0.4


def test_bid_params_w1_w2_sum_to_one():
    p = BidParams(V=1.0, w1=0.7)
    assert abs(p.w1 + p.w2 - 1.0) < 1e-9


def test_bid_params_negative_V_raises():
    with pytest.raises(ValueError, match="V must be"):
        BidParams(V=-0.1, w1=0.7)


def test_bid_params_invalid_w1_raises():
    with pytest.raises(ValueError, match="w1 must be"):
        BidParams(V=1.0, w1=0.0)
    with pytest.raises(ValueError, match="w1 must be"):
        BidParams(V=1.0, w1=1.0)


def test_utility_zero_bid():
    """At b=0: p_win is near 0 (low bid), cost is 0."""
    p = BidParams(V=1.0, w1=0.7)
    u = utility(0.0, p)
    assert isinstance(u, float)


def test_utility_negative_bid_raises():
    p = BidParams(V=1.0, w1=0.7)
    with pytest.raises(ValueError, match="Bid amount"):
        utility(-0.1, p)


def test_utility_bid_above_V_is_negative():
    """Bidding more than V should produce negative utility (unprofitable)."""
    p = BidParams(V=0.5, w1=0.7)
    u = utility(0.9, p)  # b > V → loss
    assert u < 0


def test_optimal_bid_is_within_range():
    p = BidParams(V=1.0, w1=0.7)
    b_opt, u_opt = optimal_bid(p, b_min=0.0, b_max=1.0, steps=100)
    assert 0.0 <= b_opt <= 1.0


def test_optimal_bid_maximizes_utility():
    """Optimal bid utility should be >= utility at b=0 and b=1."""
    p = BidParams(V=1.0, w1=0.7)
    b_opt, u_opt = optimal_bid(p, b_min=0.0, b_max=1.0, steps=200)
    assert u_opt >= utility(0.0, p)
    assert u_opt >= utility(1.0, p)


def test_w1_w2_invariant_enforced_on_update():
    """Verify invariant holds even with w1 values that would create float drift."""
    for w1 in [0.51, 0.63, 0.75, 0.82, 0.9]:
        p = BidParams(V=1.0, w1=w1)
        assert abs(p.w1 + p.w2 - 1.0) < 1e-9, f"invariant broken for w1={w1}"


def test_optimal_bid_steps_zero_raises():
    p = BidParams(V=1.0, w1=0.7)
    with pytest.raises(ValueError, match="steps must be > 0"):
        optimal_bid(p, steps=0)


def test_optimal_bid_b_min_greater_than_b_max_raises():
    p = BidParams(V=1.0, w1=0.7)
    with pytest.raises(ValueError, match="b_min"):
        optimal_bid(p, b_min=1.0, b_max=0.0)


def test_optimal_bid_no_float_drift():
    """Grid endpoint b_max must be evaluated exactly (no accumulated drift)."""
    p = BidParams(V=2.0, w1=0.7)
    b_opt, u_opt = optimal_bid(p, b_min=0.0, b_max=1.0, steps=1000)
    # If there were drift the last point might be slightly > 1.0, raising ValueError
    assert 0.0 <= b_opt <= 1.0
