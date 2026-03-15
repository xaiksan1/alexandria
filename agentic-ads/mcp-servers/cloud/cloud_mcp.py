from typing import Any

from _base.mcp_base import AdMCPBase
from cloud.cloud_catalog import CloudCatalogClient


class CloudMCP(AdMCPBase):
    vertical = "cloud"
    tool_name = "cloud_search"
    tool_description = (
        "Search for cloud infrastructure services and providers (AWS, GCP, Azure, etc.). "
        "Returns pricing, categories, and service details."
    )

    def __init__(self, bid_engine_url: str = "http://localhost:3045") -> None:
        super().__init__(bid_engine_url=bid_engine_url)
        self._catalog = CloudCatalogClient()

    async def get_organic_results(self, query: str, **kwargs) -> list[dict[str, Any]]:
        """Return organic cloud service results from the static catalog."""
        items = await self._catalog.search(query)
        return [
            {
                "name": item["name"],
                "provider": item["provider"],
                "category": item["category"],
                "price_from": item["price_from"],
                "url": item["url"],
                "source": "organic",
            }
            for item in items
        ]

    async def get_sponsored_result(self, sponsor_data: dict) -> dict[str, Any]:
        """Format sponsor data as a native cloud tool result."""
        return {
            "name": sponsor_data.get("name", ""),
            "provider": sponsor_data.get("provider", ""),
            "category": sponsor_data.get("category", "cloud"),
            "cta": sponsor_data.get("cta", ""),
            "url": sponsor_data.get("url", ""),
            "source": "sponsored",
        }

    async def close(self) -> None:
        await super().close()
        await self._catalog.aclose()
