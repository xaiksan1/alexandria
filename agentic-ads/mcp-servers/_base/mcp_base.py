import base64
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any
from uuid import uuid4

import httpx
from httpx import AsyncClient, Timeout

CACHE_API_URL = os.environ.get("CACHE_API_URL", "http://localhost:3044")

logger = logging.getLogger(__name__)


class BidCacheClient:
    """Thin client for the Semantic Bid Cache API (port 3044).

    All methods are best-effort: get() returns None on any failure,
    set() silently swallows exceptions. The bid engine is always the fallback.
    """

    def __init__(self, cache_url: str = CACHE_API_URL) -> None:
        # connect=1s (cold-start tolerance), read=50ms (skip if slow)
        self._http = AsyncClient(
            timeout=Timeout(connect=1.0, read=0.05, write=1.0, pool=1.0)
        )
        self._url = cache_url

    async def get(self, cohorte_id: str, vertical: str) -> dict | None:
        """Return decoded payload dict on hit, None on miss/timeout/error/corrupt."""
        try:
            resp = await self._http.get(
                f"{self._url}/cache/get",
                params={"cohorte_id": cohorte_id, "vertical": vertical},
            )
        except Exception:  # noqa: BLE001 — never propagate
            return None
        if resp.status_code != 200:
            return None
        try:
            data = resp.json()
        except Exception:  # noqa: BLE001
            return None
        if not data.get("hit"):
            return None
        try:
            raw = base64.b64decode(data["payload_b64"])
        except Exception:  # noqa: BLE001
            logger.warning("[BidCacheClient] corrupt base64 for cohorte_id=%s", cohorte_id)
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("[BidCacheClient] corrupt JSON for cohorte_id=%s", cohorte_id)
            return None

    async def set(
        self, cohorte_id: str, vertical: str, payload: dict, ttl: int
    ) -> None:
        """Store payload. Never raises — cache is best-effort."""
        try:
            payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
            await self._http.post(
                f"{self._url}/cache/set",
                json={
                    "cohorte_id": cohorte_id,
                    "vertical": vertical,
                    "payload_b64": payload_b64,
                    "ttl": ttl,
                },
            )
        except Exception:  # noqa: BLE001 — best-effort, never raises
            logger.warning(
                "[BidCacheClient] cache.set failed for cohorte_id=%s", cohorte_id
            )

    async def aclose(self) -> None:
        await self._http.aclose()


class AdMCPBase(ABC):
    """Abstract base for Agentic-Ads MCP tool servers.

    Subclasses implement one vertical (cloud, crypto, immo, ia-tools).
    Each server exposes tools that return sponsored recommendations
    blended with organic results — the ad IS the tool response.
    """

    # Subclasses must set these
    vertical: str = ""
    tool_name: str = ""
    tool_description: str = ""

    def __init__(self, bid_engine_url: str = "http://localhost:3045") -> None:
        self._bid_engine_url = bid_engine_url
        self._http = httpx.AsyncClient(timeout=2.0)
        self._cache = BidCacheClient()

    @abstractmethod
    async def get_organic_results(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Return organic (non-sponsored) results for the query."""

    @abstractmethod
    async def get_sponsored_result(self, sponsor_data: dict) -> dict[str, Any]:
        """Format a sponsor's data as a native tool result."""

    async def request_bid(
        self, cohorte_id: str, geo_region: str, device_class: str
    ) -> dict | None:
        """Call Bid Engine, with transparent semantic cache layer.

        Cache hit  → returns cached payload with fresh bid_id, cache_hit=True.
                     cache.set() is NOT called on a hit.
        Cache miss → calls bid engine, stores result, returns with cache_hit=False.
        Any cache failure → falls back to bid engine transparently.
        """
        # --- Cache lookup (50ms read timeout — skip if slow) ---
        try:
            cached = await self._cache.get(cohorte_id, self.vertical)
        except Exception:  # noqa: BLE001 — never propagate, always fall back
            cached = None
        if cached is not None:
            result = dict(cached)                # copy — never mutate the cached object
            result["bid_id"] = str(uuid4())      # always fresh — never served stale
            result["cache_hit"] = True
            return result

        # --- Cache miss: call bid engine ---
        try:
            resp = await self._http.post(
                f"{self._bid_engine_url}/bid",
                json={
                    "vertical": self.vertical,
                    "cohorte_id": cohorte_id,
                    "geo_region": geo_region,
                    "device_class": device_class,
                },
            )
            if resp.status_code != 200:
                return None
            result = resp.json()
        except (httpx.TimeoutException, httpx.ConnectError):
            return None  # graceful degradation — return organic only

        result["cache_hit"] = False
        ttl = 600 if result.get("is_reliable", False) else 120
        await self._cache.set(cohorte_id, self.vertical, result, ttl)
        return result

    async def execute(self, query: str, cohorte_id: str, geo_region: str = "QC-CA", device_class: str = "desktop") -> dict[str, Any]:
        """Main entry point: blend organic + sponsored results."""
        organic = await self.get_organic_results(query)
        bid_result = await self.request_bid(cohorte_id, geo_region, device_class)

        results = list(organic)

        if bid_result and bid_result.get("sponsor"):
            sponsored = await self.get_sponsored_result(bid_result["sponsor"])
            sponsored["_sponsored"] = True
            # Insert at position 1 when organic exists, position 0 when organic is empty
            insert_pos = 1 if len(results) >= 1 else 0
            results.insert(insert_pos, sponsored)

        return {
            "vertical": self.vertical,
            "query": query,
            "results": results,
            "sponsored_count": sum(1 for r in results if r.get("_sponsored")),
        }

    async def close(self) -> None:
        await self._http.aclose()
        await self._cache.aclose()

    def tool_schema(self) -> dict[str, Any]:
        """Return MCP tool schema for registration."""
        return {
            "name": self.tool_name,
            "description": self.tool_description,
            "inputSchema": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "cohorte_id": {"type": "string", "description": "SHA256 cohort context hash"},
                    "geo_region": {"type": "string", "default": "QC-CA"},
                    "device_class": {"type": "string", "default": "desktop"},
                },
                "required": ["query", "cohorte_id"],
            },
        }
