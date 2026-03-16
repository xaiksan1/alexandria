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
