import pytest
from unittest.mock import AsyncMock, patch

from immo.immo_mcp import ImmoMCP


@pytest.fixture
def mock_catalog(mocker):
    catalog = AsyncMock()
    catalog.search.return_value = [
        {
            "id": "mtl-001", "type": "condo", "city": "Montréal",
            "neighbourhood": "Plateau-Mont-Royal", "price_cad": 425_000,
            "rooms": 3, "sqft": 850, "parking": False,
            "tags": ["condo", "montreal"],
        },
    ]
    catalog.aclose = AsyncMock()
    mocker.patch("immo.immo_mcp.ImmoCatalogClient", return_value=catalog)
    return catalog


@pytest.fixture
def mcp(mock_catalog):
    return ImmoMCP(bid_engine_url="http://mock:3045")


# ── Invariants ────────────────────────────────────────────────────────────────

def test_vertical_is_immo(mcp):
    assert mcp.vertical == "immo"


def test_tool_name(mcp):
    assert mcp.tool_name == "immo_search"


# ── get_organic_results ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_organic_results_returns_listing(mcp, mock_catalog):
    results = await mcp.get_organic_results("condo montreal")
    assert len(results) == 1
    assert results[0]["city"] == "Montréal"
    assert results[0]["source"] == "organic"
    mock_catalog.search.assert_called_once_with("condo montreal")


@pytest.mark.asyncio
async def test_organic_results_empty_on_no_match(mcp, mock_catalog):
    mock_catalog.search.return_value = []
    results = await mcp.get_organic_results("unknown-city-xyz")
    assert results == []


@pytest.mark.asyncio
async def test_organic_result_fields(mcp, mock_catalog):
    results = await mcp.get_organic_results("montreal")
    r = results[0]
    assert "type" in r
    assert "city" in r
    assert "neighbourhood" in r
    assert "price_cad" in r
    assert "rooms" in r
    assert "sqft" in r
    assert "parking" in r
    assert r["source"] == "organic"


# ── get_sponsored_result ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sponsored_result_format(mcp):
    sponsor = {
        "type": "condo", "city": "Montréal", "neighbourhood": "Vieux-Port",
        "price_cad": 599_000, "cta": "Visite virtuelle disponible",
        "url": "https://example-immo.ca/listing/42",
    }
    result = await mcp.get_sponsored_result(sponsor)
    assert result["source"] == "sponsored"
    assert result["city"] == "Montréal"
    assert result["cta"] == "Visite virtuelle disponible"


@pytest.mark.asyncio
async def test_sponsored_result_missing_fields_default_empty(mcp):
    result = await mcp.get_sponsored_result({})
    assert result["type"] == ""
    assert result["price_cad"] is None
    assert result["source"] == "sponsored"


# ── execute() integration ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_organic_only(mcp):
    with patch.object(mcp, "request_bid", return_value=None):
        out = await mcp.execute("condo", cohorte_id="hash123")
    assert out["vertical"] == "immo"
    assert out["sponsored_count"] == 0
    assert len(out["results"]) == 1


@pytest.mark.asyncio
async def test_execute_with_sponsor(mcp, mock_catalog):
    sponsor = {"type": "maison", "city": "Laval", "neighbourhood": "Sainte-Rose",
               "price_cad": 650_000, "cta": "Appeler l'agent", "url": "#"}
    with patch.object(mcp, "request_bid", return_value={"sponsor": sponsor}):
        out = await mcp.execute("maison laval", cohorte_id="hash456")
    assert out["sponsored_count"] == 1
    sponsored = next(r for r in out["results"] if r.get("_sponsored"))
    assert sponsored["city"] == "Laval"


# ── close() ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_close_releases_catalog(mcp, mock_catalog):
    with patch.object(mcp, "_http") as mock_http, \
         patch.object(mcp, "_cache") as mock_cache:
        mock_http.aclose = AsyncMock()
        mock_cache.aclose = AsyncMock()
        await mcp.close()
    mock_catalog.aclose.assert_called_once()


# ── tool_schema ───────────────────────────────────────────────────────────────

def test_tool_schema(mcp):
    schema = mcp.tool_schema()
    assert schema["name"] == "immo_search"
    assert "cohorte_id" in schema["inputSchema"]["properties"]
