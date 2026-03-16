import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from _base.mcp_base import AdMCPBase


class ConcreteAdMCP(AdMCPBase):
    vertical = "test_vertical"
    tool_name = "test_tool"
    tool_description = "Test MCP tool for unit tests"

    async def get_organic_results(self, query: str, **kwargs):
        return [{"title": f"Organic result for {query}", "url": "https://example.com"}]

    async def get_sponsored_result(self, sponsor_data: dict):
        return {"title": sponsor_data.get("name", "Sponsor"), "url": sponsor_data.get("url", "#")}


@pytest.fixture
def mcp():
    return ConcreteAdMCP(bid_engine_url="http://mock-engine:3045")


@pytest.mark.asyncio
async def test_execute_organic_only_on_no_bid(mcp):
    """When bid engine returns None, only organic results returned."""
    with patch.object(mcp, "request_bid", return_value=None):
        result = await mcp.execute("test query", cohorte_id="abc123")
    assert result["vertical"] == "test_vertical"
    assert result["sponsored_count"] == 0
    assert len(result["results"]) == 1


@pytest.mark.asyncio
async def test_execute_blends_sponsored_result(mcp):
    """When bid engine returns a sponsor, it's inserted at position 1."""
    bid_response = {"sponsor": {"name": "ACME Corp", "url": "https://acme.com"}}
    with patch.object(mcp, "request_bid", return_value=bid_response):
        result = await mcp.execute("test query", cohorte_id="abc123")
    assert result["sponsored_count"] == 1
    # Position 1 is the sponsored result (after first organic)
    sponsored = next(r for r in result["results"] if r.get("_sponsored"))
    assert sponsored["title"] == "ACME Corp"


@pytest.mark.asyncio
async def test_execute_graceful_on_bid_timeout(mcp):
    """Bid engine timeout → organic only, no error raised."""
    with patch.object(mcp, "request_bid", return_value=None):
        result = await mcp.execute("query", cohorte_id="hash")
    assert result["sponsored_count"] == 0
    assert len(result["results"]) >= 1


def test_tool_schema_structure(mcp):
    schema = mcp.tool_schema()
    assert schema["name"] == "test_tool"
    assert "inputSchema" in schema
    assert "query" in schema["inputSchema"]["properties"]
    assert "cohorte_id" in schema["inputSchema"]["properties"]
    assert "query" in schema["inputSchema"]["required"]


@pytest.mark.asyncio
async def test_request_bid_returns_none_on_connection_error(mcp):
    """Connection error to bid engine → None (graceful degradation)."""
    import httpx
    with patch.object(mcp._http, "post", side_effect=httpx.ConnectError("refused")):
        result = await mcp.request_bid("abc", "QC-CA", "desktop")
    assert result is None


@pytest.mark.asyncio
async def test_request_bid_returns_none_on_timeout(mcp):
    """Timeout on bid engine → None (graceful degradation)."""
    import httpx
    with patch.object(mcp._http, "post", side_effect=httpx.TimeoutException("timed out")):
        result = await mcp.request_bid("abc", "QC-CA", "desktop")
    assert result is None
