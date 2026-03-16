import time
import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from crypto.coingecko_client import CoinGeckoClient, CoinGeckoError


def _make_response(status_code: int, json_data) -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@pytest.fixture
async def client():
    """Async fixture — closes httpx client after each test (prevents ResourceWarning)."""
    c = CoinGeckoClient()
    yield c
    await c.aclose()


# ── Test 1: search returns parsed coins ───────────────────────────────────────

@pytest.mark.asyncio
async def test_search_returns_parsed_coins(client):
    payload = {
        "coins": [
            {"id": "bitcoin",  "symbol": "btc", "name": "Bitcoin"},
            {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
        ]
    }
    with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_response(200, payload)
        result = await client.search("bitcoin")

    assert result == [
        {"id": "bitcoin",  "symbol": "btc", "name": "Bitcoin"},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum"},
    ]
    mock_get.assert_called_once()
    call_url = mock_get.call_args[0][0]
    assert "search" in call_url
    # query param is passed via params= kwarg, not embedded in URL
    assert mock_get.call_args[1]["params"]["query"] == "bitcoin"


# ── Test 2: enrich returns price map ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_enrich_returns_price_map(client):
    payload = [
        {"id": "bitcoin",  "symbol": "btc", "name": "Bitcoin",
         "current_price": 67000, "market_cap_rank": 1},
        {"id": "ethereum", "symbol": "eth", "name": "Ethereum",
         "current_price": 3500,  "market_cap_rank": 2},
    ]
    with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_response(200, payload)
        result = await client.enrich(["bitcoin", "ethereum"])

    assert result["bitcoin"]["current_price"] == 67000
    assert result["ethereum"]["current_price"] == 3500
    assert result["bitcoin"]["market_cap_rank"] == 1


# ── Test 3: enrich([]) short-circuits — zero HTTP calls ──────────────────────

@pytest.mark.asyncio
async def test_enrich_empty_ids_returns_empty_dict(client):
    with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
        result = await client.enrich([])

    assert result == {}
    mock_get.assert_not_called()


# ── Test 4: cache hit skips HTTP on second call ───────────────────────────────

@pytest.mark.asyncio
async def test_cache_hit_skips_http(client):
    payload = {"coins": [{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}]}
    with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_response(200, payload)
        await client.search("bitcoin")
        await client.search("bitcoin")  # second call — should hit cache

    assert mock_get.call_count == 1  # HTTP called only once


# ── Test 5: non-200 raises CoinGeckoError ────────────────────────────────────

@pytest.mark.asyncio
async def test_non_200_raises_coingecko_error(client):
    with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_response(429, {})
        with pytest.raises(CoinGeckoError):
            await client.search("bitcoin")


# ── Test 6: network error raises CoinGeckoError ──────────────────────────────

@pytest.mark.asyncio
async def test_network_error_raises_coingecko_error(client):
    with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("connection refused")
        with pytest.raises(CoinGeckoError):
            await client.search("bitcoin")


# ── Test 7: partial enrich response → price_usd None ─────────────────────────

@pytest.mark.asyncio
async def test_partial_enrich_response_yields_missing_id(client):
    """Coin present in ids list but absent from enrich response → key missing from result."""
    payload = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin",
         "current_price": 67000, "market_cap_rank": 1},
    ]
    with patch.object(client._http, "get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = _make_response(200, payload)
        result = await client.enrich(["bitcoin", "solana"])  # solana absent from response

    assert "bitcoin" in result
    assert "solana" not in result  # absent — caller uses .get(id, {})
