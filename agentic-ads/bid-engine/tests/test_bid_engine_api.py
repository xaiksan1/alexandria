import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    mock_router = MagicMock()
    mock_router.route.return_value = MagicMock(
        bid_id="test-bid-uuid",
        vertical="crypto",
        bid_amount=0.45,
        w1=0.7,
        w2=0.3,
        sponsor={"name": "MockExchange"},
    )
    mock_router.record_outcome.return_value = None
    mock_router.optimizer_state.return_value = {
        "vertical": "crypto",
        "w1": 0.7,
        "w2": 0.3,
        "bid_count": 5,
        "win_rate": 0.6,
        "is_reliable": False,
    }
    from bid_engine_api import app
    import bid_engine_api as _api_module
    # Start the test client (lifespan runs, sets _router to a real BidRouter).
    # Then overwrite _router with the mock so all requests use it.
    with TestClient(app, raise_server_exceptions=True) as c:
        _api_module._router = mock_router
        yield c, mock_router


def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["port"] == 3045


def test_place_bid(client):
    c, mock_router = client
    r = c.post("/bid", json={
        "vertical": "crypto",
        "cohorte_id": "abc123hash",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["bid_id"] == "test-bid-uuid"
    assert data["bid_amount"] == 0.45
    assert data["w1"] == 0.7
    assert data["w2"] == 0.3
    assert data["sponsor"]["name"] == "MockExchange"


def test_record_outcome(client):
    c, mock_router = client
    r = c.post("/bid/outcome", json={
        "vertical": "crypto",
        "won": True,
        "bid_amount": 0.45,
        "V": 1.0,
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_optimizer_state(client):
    c, mock_router = client
    r = c.get("/optimizer/crypto")
    assert r.status_code == 200
    data = r.json()
    assert data["w1"] == 0.7
    assert data["bid_count"] == 5
