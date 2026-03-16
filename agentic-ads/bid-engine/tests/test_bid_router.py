import pytest
from bid_engine.bid_router import BidRouter, AuctionRequest


@pytest.fixture
def router():
    return BidRouter()


def test_route_returns_auction_result(router):
    req = AuctionRequest(vertical="crypto", cohorte_id="hash123")
    result = router.route(req)
    assert result.bid_id is not None
    assert result.vertical == "crypto"
    assert result.bid_amount >= 0


def test_route_bid_amount_positive(router):
    req = AuctionRequest(vertical="cloud", cohorte_id="hashxyz", V=1.0)
    result = router.route(req)
    assert result.bid_amount >= 0


def test_route_includes_sponsor_for_known_vertical(router):
    req = AuctionRequest(vertical="crypto", cohorte_id="hash")
    result = router.route(req)
    assert result.sponsor is not None
    assert "name" in result.sponsor


def test_route_sponsor_none_for_unknown_vertical(router):
    req = AuctionRequest(vertical="unknown_vertical_xyz", cohorte_id="hash")
    result = router.route(req)
    assert result.sponsor is None


def test_route_w1_w2_sum_to_one(router):
    req = AuctionRequest(vertical="crypto", cohorte_id="hash")
    result = router.route(req)
    assert abs(result.w1 + result.w2 - 1.0) < 1e-9


def test_record_outcome_updates_bid_count(router):
    router.record_outcome("crypto", won=True, bid_amount=0.5, V=1.0)
    state = router.optimizer_state("crypto")
    assert state["bid_count"] == 1


def test_record_outcome_win_increases_win_rate(router):
    router.record_outcome("crypto", won=True, bid_amount=0.5, V=1.0)
    router.record_outcome("crypto", won=True, bid_amount=0.5, V=1.0)
    state = router.optimizer_state("crypto")
    assert state["win_rate"] == 1.0


def test_optimizer_state_returns_dict(router):
    state = router.optimizer_state("crypto")
    required_keys = {"vertical", "w1", "w2", "bid_count", "win_rate", "is_reliable"}
    assert required_keys.issubset(state.keys())


def test_each_vertical_has_independent_optimizer(router):
    router.record_outcome("crypto", won=True, bid_amount=0.5, V=1.0)
    cloud_state = router.optimizer_state("cloud")
    assert cloud_state["bid_count"] == 0  # cloud not updated
