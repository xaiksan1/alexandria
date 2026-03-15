import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import pytest
from unittest.mock import AsyncMock, patch

from ia_tools_mcp import IAToolsMCP


@pytest.fixture
def mock_catalog(mocker):
    catalog = AsyncMock()
    catalog.search.return_value = [
        {
            "id": "claude", "name": "Claude", "provider": "Anthropic",
            "category": "llm", "price_from": "Free / 20 USD/mo",
            "url": "https://claude.ai",
            "tags": ["claude", "llm", "ai"],
        },
    ]
    catalog.aclose = AsyncMock()
    mocker.patch("ia_tools_mcp.IAToolsCatalogClient", return_value=catalog)
    return catalog


@pytest.fixture
def mcp(mock_catalog):
    return IAToolsMCP(bid_engine_url="http://mock:3045")


# ── Invariants ────────────────────────────────────────────────────────────────

def test_vertical_is_ia_tools(mcp):
    assert mcp.vertical == "ia-tools"


def test_tool_name(mcp):
    assert mcp.tool_name == "ia_tools_search"


# ── get_organic_results ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_organic_results_returns_tool(mcp, mock_catalog):
    results = await mcp.get_organic_results("llm chat")
    assert len(results) == 1
    assert results[0]["name"] == "Claude"
    assert results[0]["source"] == "organic"
    mock_catalog.search.assert_called_once_with("llm chat")


@pytest.mark.asyncio
async def test_organic_results_empty_on_no_match(mcp, mock_catalog):
    mock_catalog.search.return_value = []
    results = await mcp.get_organic_results("unknown-tool-xyz")
    assert results == []


@pytest.mark.asyncio
async def test_organic_result_fields(mcp, mock_catalog):
    results = await mcp.get_organic_results("claude")
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
        "name": "SuperAI", "provider": "SuperCorp",
        "category": "coding-assistant",
        "cta": "Try free for 30 days",
        "url": "https://superai.example.com",
    }
    result = await mcp.get_sponsored_result(sponsor)
    assert result["source"] == "sponsored"
    assert result["name"] == "SuperAI"
    assert result["cta"] == "Try free for 30 days"


@pytest.mark.asyncio
async def test_sponsored_result_missing_fields_default_empty(mcp):
    result = await mcp.get_sponsored_result({})
    assert result["name"] == ""
    assert result["category"] == "ai"
    assert result["source"] == "sponsored"


# ── execute() integration ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_execute_organic_only(mcp):
    with patch.object(mcp, "request_bid", return_value=None):
        out = await mcp.execute("llm", cohorte_id="hash123")
    assert out["vertical"] == "ia-tools"
    assert out["sponsored_count"] == 0
    assert len(out["results"]) == 1


@pytest.mark.asyncio
async def test_execute_with_sponsor(mcp, mock_catalog):
    sponsor = {"name": "SponsoredAI", "provider": "SponsoCorp",
               "category": "llm", "cta": "Sign up", "url": "#"}
    with patch.object(mcp, "request_bid", return_value={"sponsor": sponsor}):
        out = await mcp.execute("coding assistant", cohorte_id="hash456")
    assert out["sponsored_count"] == 1
    sponsored = next(r for r in out["results"] if r.get("_sponsored"))
    assert sponsored["name"] == "SponsoredAI"


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
    assert schema["name"] == "ia_tools_search"
    assert "cohorte_id" in schema["inputSchema"]["properties"]
