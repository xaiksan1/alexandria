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
        await super().close()       # closes _http (bid-engine) + _cache (BidCacheClient)
        await self._cg.aclose()    # closes CoinGeckoClient httpx session
