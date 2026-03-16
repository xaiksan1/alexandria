"""Tests for cache ↔ bid engine wiring in AdMCPBase.request_bid().

All cache interactions are mocked — no live Cache API or Bid Engine needed.
Run these first (red), then implement BidCacheClient in mcp_base.py (green).
"""
import base64
from unittest.mock import AsyncMock, MagicMock

import pytest

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mcp_base import AdMCPBase, BidCacheClient


# ---------------------------------------------------------------------------
# Minimal concrete subclass (AdMCPBase is abstract)
# ---------------------------------------------------------------------------
class FakeMCP(AdMCPBase):
    vertical = "crypto"
    tool_name = "fake"
    tool_description = "fake"

    async def get_organic_results(self, query, **kwargs):
        return []

    async def get_sponsored_result(self, sponsor_data):
        return {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _make_engine_response(is_reliable: bool = True) -> dict:
    return {
        "bid_id": "engine-bid-id",
        "vertical": "crypto",
        "bid_amount": 1.5,
        "w1": 0.7,
        "w2": 0.3,
        "sponsor": None,
        "is_reliable": is_reliable,
    }


def _encode_bytes(raw: bytes) -> str:
    return base64.b64encode(raw).decode()


# ---------------------------------------------------------------------------
# Cache hit tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cache_hit_skips_bid_engine():
    """Cache hit → bid engine never called, cache.set never called."""
    mcp = FakeMCP()
    cached_payload = _make_engine_response()

    mcp._cache.get = AsyncMock(return_value=cached_payload)
    mcp._cache.set = AsyncMock()
    mock_http = MagicMock()
    mock_http.aclose = AsyncMock()
    mcp._http = mock_http  # any call to _http.post would fail the test

    result = await mcp.request_bid("cohorte-1", "QC-CA", "desktop")

    mcp._cache.get.assert_called_once_with("cohorte-1", "crypto")
    mcp._cache.set.assert_not_called()
    mcp._http.post.assert_not_called()
    assert result is not None
    await mcp.close()


@pytest.mark.asyncio
async def test_cache_hit_returns_fresh_bid_id():
    """Two hits on same cohorte → two different bid_ids."""
    mcp = FakeMCP()
    mcp._cache.get = AsyncMock(return_value=_make_engine_response())
    mcp._cache.set = AsyncMock()

    r1 = await mcp.request_bid("cohorte-1", "QC-CA", "desktop")
    r2 = await mcp.request_bid("cohorte-1", "QC-CA", "desktop")

    assert r1["bid_id"] != r2["bid_id"]
    await mcp.close()


@pytest.mark.asyncio
async def test_cache_hit_sets_cache_hit_true():
    """Cache hit → returned dict has cache_hit=True."""
    mcp = FakeMCP()
    mcp._cache.get = AsyncMock(return_value=_make_engine_response())
    mcp._cache.set = AsyncMock()

    result = await mcp.request_bid("cohorte-1", "QC-CA", "desktop")

    assert result["cache_hit"] is True
    await mcp.close()


# ---------------------------------------------------------------------------
# Cache miss tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cache_miss_calls_bid_engine():
    """Cache miss → bid engine called, result has cache_hit=False."""
    mcp = FakeMCP()
    engine_payload = _make_engine_response(is_reliable=True)

    mcp._cache.get = AsyncMock(return_value=None)
    mcp._cache.set = AsyncMock()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=mock_resp)

    result = await mcp.request_bid("cohorte-2", "QC-CA", "desktop")

    mcp._http.post.assert_called_once()
    assert result["cache_hit"] is False
    await mcp.close()


@pytest.mark.asyncio
async def test_cache_miss_stores_result():
    """Cache miss → cache.set called with cohorte_id, vertical, and correct TTL."""
    mcp = FakeMCP()
    engine_payload = _make_engine_response(is_reliable=True)

    mcp._cache.get = AsyncMock(return_value=None)
    mcp._cache.set = AsyncMock()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=mock_resp)

    await mcp.request_bid("cohorte-2", "QC-CA", "desktop")

    mcp._cache.set.assert_called_once()
    args = mcp._cache.set.call_args[0]
    assert args[0] == "cohorte-2"   # cohorte_id
    assert args[1] == "crypto"       # vertical
    assert args[3] == 600            # ttl (is_reliable=True)
    assert args[2]["bid_id"] == "engine-bid-id"   # payload contains engine response
    await mcp.close()


# ---------------------------------------------------------------------------
# TTL tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_ttl_120_when_not_reliable():
    """`is_reliable=False` in engine response → cache.set called with ttl=120."""
    mcp = FakeMCP()
    engine_payload = _make_engine_response(is_reliable=False)

    mcp._cache.get = AsyncMock(return_value=None)
    mcp._cache.set = AsyncMock()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=mock_resp)

    await mcp.request_bid("cohorte-3", "QC-CA", "desktop")

    args = mcp._cache.set.call_args[0]
    assert args[3] == 120
    await mcp.close()


@pytest.mark.asyncio
async def test_ttl_600_when_reliable():
    """`is_reliable=True` → cache.set called with ttl=600."""
    mcp = FakeMCP()
    engine_payload = _make_engine_response(is_reliable=True)

    mcp._cache.get = AsyncMock(return_value=None)
    mcp._cache.set = AsyncMock()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=mock_resp)

    await mcp.request_bid("cohorte-4", "QC-CA", "desktop")

    args = mcp._cache.set.call_args[0]
    assert args[3] == 600
    await mcp.close()


# ---------------------------------------------------------------------------
# Fallback tests
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_cache_timeout_falls_back():
    """Cache raises ReadTimeout → bid engine called (fallback)."""
    import httpx as _httpx

    mcp = FakeMCP()
    mcp._cache.get = AsyncMock(side_effect=_httpx.ReadTimeout("timeout", request=None))
    mcp._cache.set = AsyncMock()

    engine_payload = _make_engine_response()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=mock_resp)

    result = await mcp.request_bid("cohorte-5", "QC-CA", "desktop")

    mcp._http.post.assert_called_once()
    assert result is not None
    await mcp.close()


@pytest.mark.asyncio
async def test_cache_down_falls_back():
    """Cache raises ConnectError → bid engine called (fallback)."""
    import httpx as _httpx

    mcp = FakeMCP()
    mcp._cache.get = AsyncMock(side_effect=_httpx.ConnectError("down"))
    mcp._cache.set = AsyncMock()

    engine_payload = _make_engine_response()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=mock_resp)

    result = await mcp.request_bid("cohorte-6", "QC-CA", "desktop")

    mcp._http.post.assert_called_once()
    assert result is not None
    await mcp.close()


@pytest.mark.asyncio
async def test_corrupt_b64_falls_back():
    """`payload_b64` is invalid base64 → BidCacheClient returns None → bid engine called."""
    mcp = FakeMCP()
    mcp._cache.set = AsyncMock()

    # Cache returns hit=true but with garbage base64
    cache_resp = MagicMock()
    cache_resp.status_code = 200
    cache_resp.json.return_value = {"hit": True, "payload_b64": "!!!not-valid-base64!!!"}
    mcp._cache._http.get = AsyncMock(return_value=cache_resp)

    # Bid engine returns a valid result
    engine_payload = _make_engine_response()
    engine_resp = MagicMock()
    engine_resp.status_code = 200
    engine_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=engine_resp)

    result = await mcp.request_bid("cohorte-7", "QC-CA", "desktop")
    mcp._http.post.assert_called_once()
    assert result is not None
    await mcp.close()


@pytest.mark.asyncio
async def test_corrupt_json_falls_back():
    """Valid base64 but invalid JSON payload → BidCacheClient returns None → bid engine called."""
    mcp = FakeMCP()
    mcp._cache.set = AsyncMock()

    # Cache returns hit=true with valid base64 but the decoded content is not valid JSON
    bad_json_b64 = _encode_bytes(b"THIS IS NOT JSON {{{")
    cache_resp = MagicMock()
    cache_resp.status_code = 200
    cache_resp.json.return_value = {"hit": True, "payload_b64": bad_json_b64}
    mcp._cache._http.get = AsyncMock(return_value=cache_resp)

    # Bid engine returns a valid result
    engine_payload = _make_engine_response()
    engine_resp = MagicMock()
    engine_resp.status_code = 200
    engine_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=engine_resp)

    result = await mcp.request_bid("cohorte-8", "QC-CA", "desktop")
    mcp._http.post.assert_called_once()
    assert result is not None
    await mcp.close()


@pytest.mark.asyncio
async def test_cache_set_failure_does_not_break_request():
    """cache.set never raises (best-effort) — result is still returned correctly."""
    mcp = FakeMCP()
    mcp._cache.get = AsyncMock(return_value=None)
    # BidCacheClient.set() guarantees never-raises; mock mirrors that contract.
    mcp._cache.set = AsyncMock()

    engine_payload = _make_engine_response()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = engine_payload
    mcp._http.post = AsyncMock(return_value=mock_resp)

    result = await mcp.request_bid("cohorte-9", "QC-CA", "desktop")
    assert result is not None
    assert result["cache_hit"] is False
    await mcp.close()
