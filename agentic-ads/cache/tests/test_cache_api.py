"""Unit tests for Cache API (port 3044).

Uses FastAPI TestClient with mocked Redis + Vault globals so no real
infrastructure is required.
"""

import base64
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    mock_cache = AsyncMock()
    mock_cache.set = AsyncMock()
    mock_cache.get = AsyncMock(return_value=None)
    mock_cache.close = AsyncMock()

    mock_vault = MagicMock()

    # Patch Vault + BidCache constructors so the lifespan doesn't touch real
    # Redis/keys, AND patch the module-level globals so endpoints use our mocks.
    # We do NOT replace the BidCache *class* itself so that its static method
    # compute_context_hash remains callable via BidCache.compute_context_hash().
    mock_bid_cache_cls = MagicMock(return_value=mock_cache)
    mock_bid_cache_cls.compute_context_hash = staticmethod(
        __import__("cache.bid_cache", fromlist=["BidCache"]).BidCache.compute_context_hash
    )

    with patch("cache.cache_api.Vault", return_value=mock_vault), \
         patch("cache.cache_api.BidCache", mock_bid_cache_cls), \
         patch("cache.cache_api._cache", mock_cache), \
         patch("cache.cache_api._vault", mock_vault):
        from cache.cache_api import app
        with TestClient(app, raise_server_exceptions=True) as c:
            yield c, mock_cache


def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["port"] == 3044


def test_cache_set_ok(client):
    c, mock_cache = client
    payload = base64.b64encode(b"bid_response").decode()
    r = c.post("/cache/set", json={
        "cohorte_id": "abc123",
        "vertical": "cloud",
        "payload_b64": payload,
        "ttl": 3600,
    })
    assert r.status_code == 200
    assert r.json()["ok"] is True
    mock_cache.set.assert_called_once_with("abc123", "cloud", b"bid_response", 3600)


def test_cache_set_invalid_b64(client):
    c, _ = client
    r = c.post("/cache/set", json={
        "cohorte_id": "abc",
        "vertical": "cloud",
        "payload_b64": "NOT_VALID_B64!!!",
        "ttl": 3600,
    })
    assert r.status_code == 400


def test_cache_get_miss(client):
    c, mock_cache = client
    mock_cache.get.return_value = None
    r = c.get("/cache/get", params={"cohorte_id": "missing", "vertical": "cloud"})
    assert r.status_code == 200
    assert r.json() == {"hit": False}


def test_cache_get_hit(client):
    c, mock_cache = client
    mock_cache.get.return_value = b"decrypted_payload"
    r = c.get("/cache/get", params={"cohorte_id": "abc123", "vertical": "cloud"})
    assert r.status_code == 200
    data = r.json()
    assert data["hit"] is True
    assert base64.b64decode(data["payload_b64"]) == b"decrypted_payload"


def test_cache_hash_format(client):
    c, _ = client
    r = c.get("/cache/hash", params={"vertical": "cloud", "region": "QC-CA", "device": "desktop"})
    assert r.status_code == 200
    h = r.json()["context_hash"]
    assert len(h) == 64
    assert all(ch in "0123456789abcdef" for ch in h)
