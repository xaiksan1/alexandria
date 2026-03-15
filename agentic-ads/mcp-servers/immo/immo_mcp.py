from typing import Any

from _base.mcp_base import AdMCPBase
from immo.immo_catalog import ImmoCatalogClient


class ImmoMCP(AdMCPBase):
    vertical = "immo"
    tool_name = "immo_search"
    tool_description = (
        "Search real-estate listings in Quebec (QC-CA): condos, maisons, plex. "
        "Returns price, rooms, sqft, city, and neighbourhood."
    )

    def __init__(self, bid_engine_url: str = "http://localhost:3045") -> None:
        super().__init__(bid_engine_url=bid_engine_url)
        self._catalog = ImmoCatalogClient()

    async def get_organic_results(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Return organic real-estate listings from the static catalog."""
        items = await self._catalog.search(query)
        return [
            {
                "type": item["type"],
                "city": item["city"],
                "neighbourhood": item["neighbourhood"],
                "price_cad": item["price_cad"],
                "rooms": item["rooms"],
                "sqft": item["sqft"],
                "parking": item["parking"],
                "source": "organic",
            }
            for item in items
        ]

    async def get_sponsored_result(self, sponsor_data: dict) -> dict[str, Any]:
        """Format sponsor data as a native immo tool result."""
        return {
            "type": sponsor_data.get("type", ""),
            "city": sponsor_data.get("city", ""),
            "neighbourhood": sponsor_data.get("neighbourhood", ""),
            "price_cad": sponsor_data.get("price_cad"),
            "cta": sponsor_data.get("cta", ""),
            "url": sponsor_data.get("url", ""),
            "source": "sponsored",
        }

    async def close(self) -> None:
        await super().close()
        await self._catalog.aclose()
