import pytest
from unittest.mock import AsyncMock, patch

from cloud.cloud_mcp import CloudMCP
from cloud.cloud_catalog import CloudCatalogError


@pytest.fixture
def mock_catalog(mocker):
    catalog = AsyncMock()
    catalog.search.return_value = [
        {
            "id": "aws-ec2", "provider": "AWS", "name": "EC2 — Elastic Compute Cloud",
            "category": "compute", "price_from": "0.0116 USD/hr",
            "url": "https://aws.amazon.com/ec2/",
            "tags": ["ec2", "aws", "compute"],
        },
    ]
    catalog.aclose = AsyncMock()
    mocker.patch("cloud.cloud_mcp.CloudCatalogClient", return_value=catalog)
    return catalog


@pytest.fixture
def mcp(mock_catalog):
    return CloudMCP(bid_engine_url="http://mock:3045")


# ── Invariants ────────────────────────────────────────────────────────────────

def test_vertical_is_cloud(mcp):
    assert mcp.vertical == "cloud"


def test_tool_name(mcp):
    assert mcp.tool_name == "cloud_search"


# ── get_organic_results ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_organic_results_returns_aws(mcp, mock_catalog):
    results = await mcp.get_organic_results("aws compute")
    assert len(results) == 1
    assert results[0]["provider"] == "AWS"
    assert results[0]["source"] == "organic"
    mock_catalog.search.assert_called_once_with("aws compute")


@pytest.mark.asyncio
async def test_organic_results_empty_query(mcp, mock_catalog):
    mock_catalog.search.return_value = []
    results = await mcp.get_organic_results("nonexistent-provider-xyz")
    assert results == []


@pytest.mark.asyncio
async def test_organic_result_fields(mcp, mock_catalog):
    results = await mcp.get_organic_results("aws")
    r = results[0]
    assert "name" in r
    assert "provider" in r
    assert "category" in r
    assert "price_from" in r
    assert "url" in r
    assert r["source"] == "organic"


# ── get_sponsored_result ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sponsored_result_format(mcp):
    sponsor = {
        "name": "Hetzner Cloud",
        "provider": "Hetzner",
        "category": "compute",
        "cta": "Get 20 EUR free credit",
        "url": "https://hetzner.com",
    }
    result = await mcp.get_sponsored_result(sponsor)
    assert result["source"] == "sponsored"
    assert result["name"] == "Hetzner Cloud"
    assert result["cta"] == "Get 20 EUR free credit"


@pytest.mark.asyncio
async def test_sponsored_result_missing_fields_default_empty(mcp):
    result = await mcp.get_sponsored_result({})
    assert result["name"] == ""
    assert result["category"] == "cloud"
    assert result["source"] == "sponsored"


# ── execute() integration ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_organic_only(mcp):
    with patch.object(mcp, "request_bid", return_value=None):
        out = await mcp.execute("aws", cohorte_id="hash123")
    assert out["vertical"] == "cloud"
    assert out["sponsored_count"] == 0
    assert len(out["results"]) == 1


@pytest.mark.asyncio
async def test_execute_with_sponsor(mcp, mock_catalog):
    sponsor = {"name": "Sponsor Cloud", "provider": "X", "category": "compute",
               "cta": "Try free", "url": "#"}
    with patch.object(mcp, "request_bid", return_value={"sponsor": sponsor}):
        out = await mcp.execute("compute", cohorte_id="hash456")
    assert out["sponsored_count"] == 1
    sponsored = next(r for r in out["results"] if r.get("_sponsored"))
    assert sponsored["name"] == "Sponsor Cloud"


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
    assert schema["name"] == "cloud_search"
    assert "cohorte_id" in schema["inputSchema"]["properties"]
