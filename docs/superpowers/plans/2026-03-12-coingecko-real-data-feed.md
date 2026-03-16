# CoinGecko Real Data Feed Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace `CryptoMCP`'s static mock dictionary with live CoinGecko free-API data, propagating failures to the bid engine.

**Architecture:** A new `CoinGeckoClient` wraps httpx with a 60 s in-process TTL cache; `CryptoMCP.get_organic_results()` delegates to it entirely. On any HTTP failure `CoinGeckoError` propagates — no fallback.

**Tech Stack:** Python 3.12, httpx (already in requirements.txt), pytest-asyncio, unittest.mock

---

## Chunk 1: CoinGeckoClient

### Task 1: Red tests for CoinGeckoClient

**Files:**
- Create: `mcp-servers/crypto/tests/test_coingecko_client.py`

All tests must fail before any implementation exists.

- [ ] **Step 1: Write the full test file**

`mcp-servers/crypto/tests/test_coingecko_client.py`:

```python
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
    assert "bitcoin" in call_url


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
```

- [ ] **Step 2: Run tests to verify all 7 fail**

```bash
cd /home/ichigo/alexandria/agentic-ads && python -m pytest mcp-servers/crypto/tests/test_coingecko_client.py -v 2>&1 | tail -15
```

Expected: 7 errors — `ModuleNotFoundError: No module named 'crypto.coingecko_client'`

- [ ] **Step 3: Commit the red tests**

> **Note:** Run git commands from `/home/ichigo` (repo root), not from the `agentic-ads/` subdirectory.

```bash
cd /home/ichigo
git add alexandria/agentic-ads/mcp-servers/crypto/tests/test_coingecko_client.py
git commit -m "test(crypto): 7 red tests for CoinGeckoClient"
```

---

### Task 2: Green — implement CoinGeckoClient

**Files:**
- Create: `mcp-servers/crypto/coingecko_client.py`

- [ ] **Step 1: Write the implementation**

`mcp-servers/crypto/coingecko_client.py`:

```python
import time
import httpx

BASE_URL = "https://api.coingecko.com/api/v3"
TTL = 60.0  # seconds


class CoinGeckoError(Exception):
    """Raised on any CoinGecko API failure."""


class CoinGeckoClient:
    """Async CoinGecko free-API client with in-process TTL cache.

    Cache is a single dict shared by both search() and enrich().
    Timestamps use time.monotonic() — immune to system clock adjustments.
    """

    def __init__(self) -> None:
        self._http = httpx.AsyncClient(timeout=httpx.Timeout(5.0))
        self._cache: dict[str, tuple[object, float]] = {}

    def _get_cached(self, key: str):
        entry = self._cache.get(key)
        if entry is None:
            return None
        value, ts = entry
        if time.monotonic() - ts > TTL:
            del self._cache[key]
            return None
        return value

    def _set_cached(self, key: str, value) -> None:
        self._cache[key] = (value, time.monotonic())

    async def search(self, query: str) -> list[dict]:
        """Search CoinGecko for coins matching query.

        Returns top 5 coins as list of {id, symbol, name}.
        Raises CoinGeckoError on any failure.
        """
        key = f"search:{query}"
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        try:
            resp = await self._http.get(f"{BASE_URL}/search", params={"query": query})
        except Exception as exc:
            raise CoinGeckoError(f"search failed: {exc}") from exc

        if resp.status_code != 200:
            raise CoinGeckoError(f"search failed: status {resp.status_code}")

        result = resp.json()["coins"][:5]
        self._set_cached(key, result)
        return result

    async def enrich(self, ids: list[str]) -> dict[str, dict]:
        """Fetch market data for a list of coin ids.

        Returns {id: {symbol, name, current_price, market_cap_rank, ...}}.
        Returns {} immediately if ids is empty (no HTTP call).
        Raises CoinGeckoError on any failure.
        """
        if not ids:
            return {}

        key = f"markets:{','.join(sorted(ids))}"
        cached = self._get_cached(key)
        if cached is not None:
            return cached

        ids_csv = ",".join(ids)
        try:
            resp = await self._http.get(
                f"{BASE_URL}/coins/markets",
                params={"ids": ids_csv, "vs_currency": "usd", "per_page": 50},
            )
        except Exception as exc:
            raise CoinGeckoError(f"enrich failed: {exc}") from exc

        if resp.status_code != 200:
            raise CoinGeckoError(f"enrich failed: status {resp.status_code}")

        result = {item["id"]: item for item in resp.json()}
        self._set_cached(key, result)
        return result

    async def aclose(self) -> None:
        await self._http.aclose()
```

- [ ] **Step 2: Run tests — all 7 must pass**

```bash
cd /home/ichigo/alexandria/agentic-ads && python -m pytest mcp-servers/crypto/tests/test_coingecko_client.py -v 2>&1 | tail -12
```

Expected: `7 passed`

- [ ] **Step 3: Commit**

```bash
cd /home/ichigo
git add alexandria/agentic-ads/mcp-servers/crypto/coingecko_client.py
git commit -m "feat(crypto): CoinGeckoClient with TTL cache — 7 tests green"
```

---

## Chunk 2: CryptoMCP update

### Task 3: Red — update CryptoMCP tests

**Files:**
- Modify: `mcp-servers/crypto/tests/test_crypto_mcp.py`

Replace the entire file so all CoinGeckoClient calls are mocked and the old mock-data assumptions are removed.

- [ ] **Step 1: Write the updated test file**

`mcp-servers/crypto/tests/test_crypto_mcp.py`:

```python
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
    """Empty search result → empty list (no default BTC fallback)."""
    mock_cg.search.return_value = []
    results = await mcp.get_organic_results("unknown_coin_xyz")
    assert results == []
    mock_cg.enrich.assert_not_called()  # short-circuit: enrich never called


@pytest.mark.asyncio
async def test_organic_results_propagates_coingecko_error(mcp, mock_cg):
    mock_cg.search.side_effect = CoinGeckoError("rate limited")
    with pytest.raises(CoinGeckoError):
        await mcp.get_organic_results("bitcoin")


@pytest.mark.asyncio
async def test_organic_results_partial_enrich_yields_none_price(mcp, mock_cg):
    """Coin in search result absent from enrich response → price_usd: None."""
    mock_cg.search.return_value = [
        {"id": "solana", "symbol": "sol", "name": "Solana"},
    ]
    mock_cg.enrich.return_value = {}  # solana absent
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
    """close() must call super().close() (base resources) AND cg.aclose()."""
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
```

- [ ] **Step 2: Run tests — expect failures** (CryptoMCP still uses mock data)

```bash
cd /home/ichigo/alexandria/agentic-ads && python -m pytest mcp-servers/crypto/tests/test_crypto_mcp.py -v 2>&1 | tail -20
```

Expected: several failures — `price_usd` key missing, `CoinGeckoError` not raised, etc.

- [ ] **Step 3: Commit the updated tests**

```bash
git add alexandria/agentic-ads/mcp-servers/crypto/tests/test_crypto_mcp.py
git commit -m "test(crypto): update CryptoMCP tests for CoinGecko integration (red)"
```

---

### Task 4: Green — wire CoinGeckoClient into CryptoMCP

**Files:**
- Modify: `mcp-servers/crypto/crypto_mcp.py`

- [ ] **Step 1: Write the updated implementation**

Replace the entire file:

```python
from typing import Any

from _base.mcp_base import AdMCPBase
# IMPORTANT: use `from ... import` form (not `import crypto.coingecko_client`).
# The mocker.patch("crypto.crypto_mcp.CoinGeckoClient") target relies on
# CoinGeckoClient being bound by name in this module's namespace.
from crypto.coingecko_client import CoinGeckoClient


class CryptoMCP(AdMCPBase):
    vertical = "crypto"
    tool_name = "crypto_search"
    tool_description = (
        "Search for cryptocurrency information, DeFi protocols, and blockchain projects. "
        "Returns up-to-date market data and project details."
    )

    def __init__(self, bid_engine_url: str = "http://localhost:3045") -> None:
        super().__init__(bid_engine_url=bid_engine_url)
        self._cg = CoinGeckoClient()

    async def get_organic_results(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Return live organic crypto results from CoinGecko.

        Raises CoinGeckoError on any API failure — no silent fallback.
        """
        coins = await self._cg.search(query)
        if not coins:
            return []
        ids = [c["id"] for c in coins]
        market = await self._cg.enrich(ids)
        return [
            {
                "symbol": c["symbol"].upper(),
                "name": c["name"],
                "category": "crypto",
                "price_usd": market.get(c["id"], {}).get("current_price"),
                "source": "organic",
            }
            for c in coins
        ]

    async def get_sponsored_result(self, sponsor_data: dict) -> dict[str, Any]:
        """Format sponsor data as a native crypto tool result."""
        return {
            "symbol": sponsor_data.get("symbol", ""),
            "name": sponsor_data.get("name", ""),
            "category": sponsor_data.get("category", "exchange"),
            "cta": sponsor_data.get("cta", ""),
            "url": sponsor_data.get("url", ""),
            "source": "sponsored",
        }

    async def close(self) -> None:
        await super().close()        # closes _http (bid-engine) + _cache (BidCacheClient)
        await self._cg.aclose()     # closes CoinGeckoClient httpx session
```

- [ ] **Step 2: Run all crypto tests — all must pass**

```bash
cd /home/ichigo/alexandria/agentic-ads && python -m pytest mcp-servers/crypto/ -v 2>&1 | tail -20
```

Expected: all tests pass (7 client + 10 MCP = 17 total)

- [ ] **Step 3: Run the full test suite — no regressions**

```bash
cd /home/ichigo/alexandria/agentic-ads && python -m pytest -v 2>&1 | tail -10
```

Expected: all existing tests still pass

- [ ] **Step 4: Commit**

```bash
cd /home/ichigo
git add alexandria/agentic-ads/mcp-servers/crypto/crypto_mcp.py
git commit -m "feat(crypto): wire CoinGeckoClient into CryptoMCP — live data, 17 tests green"
```
