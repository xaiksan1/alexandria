# CryptoMCP Real Data Feed (CoinGecko) — Design Spec

## Goal

Replace the static mock dictionary in `CryptoMCP.get_organic_results()` with live data from the CoinGecko free API. On any failure the exception propagates to the bid engine; there is no silent fallback.

## Architecture

Two units with clear boundaries:

```
CryptoMCP.get_organic_results(query)
    └─→ CoinGeckoClient.search(query)       # GET /search?query=
    └─→ CoinGeckoClient.enrich(ids)         # GET /coins/markets?ids=&vs_currency=usd
         └─→ in-process TTL cache (60s, shared dict on instance)
         └─→ raises CoinGeckoError on failure
```

`CoinGeckoClient` knows nothing about MCP. `CryptoMCP` knows nothing about HTTP. Each can be tested independently.

## Components

### `coingecko_client.py` (new)

**`CoinGeckoError(Exception)`** — sentinel raised on any API failure.

**`CoinGeckoClient`**
- `httpx.AsyncClient` with 5 s connect + read timeout
- In-process TTL cache: single `dict[str, tuple[Any, float]]` on the instance, shared by both
  `search` and `enrich`. Timestamps use `time.monotonic()`. TTL = 60 s.
- `async search(query: str) -> list[dict]`
  - Cache key: `f"search:{query}"`
  - `GET https://api.coingecko.com/api/v3/search?query={query}`
  - Parse: `response.json()["coins"][:5]` → list of `{"id", "symbol", "name"}` dicts
  - Non-200 or exception → `raise CoinGeckoError(f"search failed: {status_or_exc}")`
- `async enrich(ids: list[str]) -> dict[str, dict]`
  - If `ids` is empty, return `{}` immediately (no HTTP call)
  - Cache key: `f"markets:{','.join(sorted(ids))}"`
  - `GET https://api.coingecko.com/api/v3/coins/markets?ids={ids_csv}&vs_currency=usd&per_page=50`
  - Parse: `{item["id"]: item for item in response.json()}` — response is a flat list
  - Return value includes at minimum: `{"symbol", "name", "current_price", "market_cap_rank"}`
  - Non-200 or exception → `raise CoinGeckoError(f"enrich failed: {status_or_exc}")`
- `async aclose()` — closes the httpx client (naming matches httpx convention)

### `crypto_mcp.py` (modified)

- Remove `MOCK_CRYPTO_DATA` dict and all references
- `__init__`: instantiate `self._cg = CoinGeckoClient()`
- `get_organic_results(query)`:
  ```python
  coins = await self._cg.search(query)      # raises CoinGeckoError on failure
  if not coins:
      return []                             # short-circuit: no enrich call needed
  ids = [c["id"] for c in coins]
  market = await self._cg.enrich(ids)       # raises CoinGeckoError on failure
  return [
      {
          "symbol": c["symbol"].upper(),
          "name": c["name"],
          "category": "crypto",
          "price_usd": market.get(c["id"], {}).get("current_price"),  # None if absent
          "source": "organic",
      }
      for c in coins
  ]
  ```
- `close()`: call `await super().close()` first (closes `_http` + `_cache` from base),
  then `await self._cg.aclose()`. Both resources must be closed.
- `get_sponsored_result()`: unchanged

### `close()` override contract

`AdMCPBase.close()` closes `self._http` (bid-engine client) and `self._cache` (BidCacheClient).
`CryptoMCP.close()` must not drop these:

```python
async def close(self) -> None:
    await super().close()      # closes _http + _cache
    await self._cg.aclose()   # closes CoinGeckoClient httpx session
```

## Data Flow

```
query "bitcoin"
    → search → response["coins"][:5] → [{id:"bitcoin", symbol:"btc", name:"Bitcoin"}, ...]
    → enrich(["bitcoin", ...]) → {item["id"]: item for item in list}
                               → {"bitcoin": {current_price: 67000, ...}}
    → return [{symbol:"BTC", name:"Bitcoin", category:"crypto", price_usd:67000, source:"organic"}]

query "unknown_xyz"
    → search → response["coins"][:5] → []
    → short-circuit → return []
```

## Error Handling

| Failure | Behaviour |
|---------|-----------|
| CoinGecko non-200 | `raise CoinGeckoError(f"search/enrich failed: {status}")` |
| Network timeout / ConnectError | `raise CoinGeckoError(str(exc))` |
| Cache hit | Return cached value, no HTTP call |
| Empty search results | `return []` — short-circuit before `enrich` call |
| Coin in search but absent from enrich | `price_usd: None` (graceful via `.get()`) |

No silent fallback to mock data. The bid engine already handles empty/error organic results gracefully.

## Rate Limiting

CoinGecko free tier: ~30 req/min. Mitigated by:
- 60 s in-process TTL cache keyed per query (using `time.monotonic()`)
- Two calls per `get_organic_results` invocation (search + enrich), both independently cached

No retry logic — on rate limit (429) raise `CoinGeckoError` immediately.

## Files

| Action | Path |
|--------|------|
| Create | `mcp-servers/crypto/coingecko_client.py` |
| Modify | `mcp-servers/crypto/crypto_mcp.py` |
| Create | `mcp-servers/crypto/tests/test_coingecko_client.py` |
| Modify | `mcp-servers/crypto/tests/test_crypto_mcp.py` |

## Tests

### `test_coingecko_client.py` (new — 7 tests)

All tests mock `httpx.AsyncClient` — no real HTTP calls.

1. `test_search_returns_parsed_coins` — 200 response with `{"coins": [...]}` → list of top-5 coin dicts
2. `test_enrich_returns_price_map` — 200 response with flat list → `{id: {current_price, ...}}`
3. `test_enrich_empty_ids_returns_empty_dict` — `enrich([])` → `{}` with zero HTTP calls
4. `test_cache_hit_skips_http` — second `search()` call with same query → cache hit, HTTP called once total
5. `test_non_200_raises_coingecko_error` — 429 response → `CoinGeckoError`
6. `test_network_error_raises_coingecko_error` — `httpx.ConnectError` → `CoinGeckoError`
7. `test_partial_enrich_response_yields_none_price` — coin in search result absent from enrich response → `price_usd: None`

### `test_crypto_mcp.py` (modified — existing 8 tests updated)

The `mcp` fixture must patch `CoinGeckoClient` so no HTTP calls are made anywhere —
including in `test_execute_organic_only` and `test_execute_with_sponsor`.

Recommended fixture pattern:
```python
@pytest.fixture
def mock_cg(mocker):
    cg = AsyncMock()
    cg.search.return_value = [{"id": "bitcoin", "symbol": "btc", "name": "Bitcoin"}]
    cg.enrich.return_value = {"bitcoin": {"current_price": 67000}}
    cg.aclose = AsyncMock()
    mocker.patch("crypto.crypto_mcp.CoinGeckoClient", return_value=cg)
    return cg

@pytest.fixture
def mcp(mock_cg):
    return CryptoMCP(bid_engine_url="http://mock:3045")
```

Test changes:
- `test_organic_results_btc_query` → assert `symbol == "BTC"` and `price_usd == 67000`
- `test_organic_results_default_on_unknown_query` → rename to `test_organic_results_empty_on_unknown_query`;
  mock `search` returns `[]`; assert `results == []` (old default-BTC fallback is removed)
- `test_organic_results_propagates_coingecko_error` (new) → mock `search` raises `CoinGeckoError` → propagates
- `test_execute_organic_only`, `test_execute_with_sponsor` — already covered by `mock_cg` fixture, no changes needed
- `test_vertical_is_crypto`, `test_tool_name`, `test_sponsored_result_format`, `test_tool_schema` — unchanged

## Constraints

- NEVER call CoinGecko in tests (mock httpx in client tests; mock `CoinGeckoClient` in MCP tests)
- No API key required (free tier)
- Base URL: `https://api.coingecko.com/api/v3` — hardcoded, no env var needed
- `httpx` already in `requirements.txt`
- TTL cache uses `time.monotonic()` not `time.time()` (immune to system clock adjustments)
- `CoinGeckoClient.aclose()` naming matches httpx convention; `CryptoMCP.close()` matches base class
