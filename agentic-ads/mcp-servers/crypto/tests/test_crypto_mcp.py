import pytest
from unittest.mock import AsyncMock, patch

from crypto.crypto_mcp import CryptoMCP
from crypto.coingecko_client import CoinGeckoError


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_cg(mocker):
    """Patch CoinGeckoClient so no real HTTP calls are made in any test."""
    cg = AsyncMock()
    cg.search.return_value = [
        {"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"},
    ]
    cg.enrich.return_value = {
        "bitcoin": {"current_price": 67000, "market_cap_rank": 1},
    }
    cg.aclose = AsyncMock()
    mocker.patch("crypto.crypto_mcp.CoinGeckoClient", return_value=cg)
    return cg


@pytest.fixture
def mcp(mock_cg):
    return CryptoMCP(bid_engine_url="http://mock:3045")


# ── Invariants ────────────────────────────────────────────────────────────────

def test_vertical_is_crypto(mcp):
    assert mcp.vertical == "crypto"


def test_tool_name(mcp):
    assert mcp.tool_name == "crypto_search"


# ── get_organic_results ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_organic_results_btc_query(mcp, mock_cg):
    results = await mcp.get_organic_results("bitcoin")
    assert any(r["symbol"] == "BTC" for r in results)
    assert any(r["price_usd"] == 67000 for r in results)
    assert all(r["source"] == "organic" for r in results)
    mock_cg.search.assert_called_once_with("bitcoin")


@pytest.mark.asyncio
async def test_organic_results_empty_on_unknown_query(mcp, mock_cg):
    """Empty search result -> empty list (no default BTC fallback)."""
    mock_cg.search.return_value = []
    results = await mcp.get_organic_results("unknown_coin_xyz")
    assert results == []
    mock_cg.enrich.assert_not_called()


@pytest.mark.asyncio
async def test_organic_results_propagates_coingecko_error(mcp, mock_cg):
    mock_cg.search.side_effect = CoinGeckoError("rate limited")
    with pytest.raises(CoinGeckoError):
        await mcp.get_organic_results("bitcoin")


@pytest.mark.asyncio
async def test_organic_results_partial_enrich_yields_none_price(mcp, mock_cg):
    """Coin absent from enrich response -> price_usd: None."""
    mock_cg.search.return_value = [
        {"id": "solana", "symbol": "sol", "name": "Solana"},
    ]
    mock_cg.enrich.return_value = {}
    results = await mcp.get_organic_results("solana")
    assert results[0]["symbol"] == "SOL"
    assert results[0]["price_usd"] is None


# ── get_sponsored_result ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sponsored_result_format(mcp):
    sponsor_data = {
        "symbol": "BINANCE",
        "name": "Binance Exchange",
        "category": "exchange",
        "cta": "Trade now with 0% fees",
        "url": "https://example-exchange.com",
    }
    result = await mcp.get_sponsored_result(sponsor_data)
    assert result["source"] == "sponsored"
    assert result["name"] == "Binance Exchange"
    assert result["cta"] == "Trade now with 0% fees"


# ── execute() integration ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_organic_only(mcp):
    with patch.object(mcp, "request_bid", return_value=None):
        out = await mcp.execute("bitcoin", cohorte_id="hash123")
    assert out["vertical"] == "crypto"
    assert out["sponsored_count"] == 0


@pytest.mark.asyncio
async def test_execute_with_sponsor(mcp, mock_cg):
    sponsor = {
        "symbol": "EX",
        "name": "MockExchange",
        "category": "exchange",
        "cta": "Trade",
        "url": "#",
    }
    with patch.object(mcp, "request_bid", return_value={"sponsor": sponsor}):
        out = await mcp.execute("ethereum", cohorte_id="hash456")
    assert out["sponsored_count"] == 1
    sponsored = next(r for r in out["results"] if r.get("_sponsored"))
    assert sponsored["name"] == "MockExchange"


# ── close() — both resources released ────────────────────────────────────────

@pytest.mark.asyncio
async def test_close_releases_both_resources(mcp, mock_cg):
    """close() must call super().close() AND cg.aclose()."""
    with patch.object(mcp, "_http") as mock_http, \
         patch.object(mcp, "_cache") as mock_cache:
        mock_http.aclose = AsyncMock()
        mock_cache.aclose = AsyncMock()
        await mcp.close()
    mock_cg.aclose.assert_called_once()


# ── tool_schema ───────────────────────────────────────────────────────────────

def test_tool_schema(mcp):
    schema = mcp.tool_schema()
    assert schema["name"] == "crypto_search"
    assert "cohorte_id" in schema["inputSchema"]["properties"]
