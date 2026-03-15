# immo/immo_catalog.py
"""Static real-estate catalog (QC-CA) — organic data source for ImmoMCP.

Fictional but realistic listings for the Quebec market.
Keyword search against type, city, neighbourhood, and tags.
"""
from __future__ import annotations

_CATALOG: list[dict] = [
    {
        "id": "mtl-001", "type": "condo", "city": "Montréal",
        "neighbourhood": "Plateau-Mont-Royal", "price_cad": 425_000,
        "rooms": 3, "sqft": 850, "parking": False,
        "tags": ["condo", "montreal", "plateau", "mtl", "appartement"],
    },
    {
        "id": "mtl-002", "type": "maison", "city": "Montréal",
        "neighbourhood": "Rosemont–La Petite-Patrie", "price_cad": 895_000,
        "rooms": 5, "sqft": 1_650, "parking": True,
        "tags": ["maison", "montreal", "rosemont", "mtl", "house"],
    },
    {
        "id": "mtl-003", "type": "duplex", "city": "Montréal",
        "neighbourhood": "Villeray", "price_cad": 680_000,
        "rooms": 6, "sqft": 2_100, "parking": True,
        "tags": ["duplex", "montreal", "villeray", "mtl", "plex", "investissement"],
    },
    {
        "id": "mtl-004", "type": "condo", "city": "Montréal",
        "neighbourhood": "Mile-End", "price_cad": 510_000,
        "rooms": 2, "sqft": 720, "parking": False,
        "tags": ["condo", "montreal", "mile-end", "mtl"],
    },
    {
        "id": "mtl-005", "type": "triplex", "city": "Montréal",
        "neighbourhood": "Hochelaga-Maisonneuve", "price_cad": 820_000,
        "rooms": 9, "sqft": 3_000, "parking": True,
        "tags": ["triplex", "montreal", "hochelaga", "plex", "investissement", "locatif"],
    },
    {
        "id": "lav-001", "type": "maison", "city": "Laval",
        "neighbourhood": "Sainte-Rose", "price_cad": 650_000,
        "rooms": 4, "sqft": 1_800, "parking": True,
        "tags": ["maison", "laval", "sainte-rose", "banlieue", "house"],
    },
    {
        "id": "lav-002", "type": "condo", "city": "Laval",
        "neighbourhood": "Chomedey", "price_cad": 340_000,
        "rooms": 2, "sqft": 780, "parking": True,
        "tags": ["condo", "laval", "chomedey", "appartement"],
    },
    {
        "id": "qc-001", "type": "maison", "city": "Québec",
        "neighbourhood": "Sainte-Foy", "price_cad": 520_000,
        "rooms": 4, "sqft": 1_600, "parking": True,
        "tags": ["maison", "quebec", "sainte-foy", "ville de quebec", "house"],
    },
    {
        "id": "qc-002", "type": "condo", "city": "Québec",
        "neighbourhood": "Vieux-Québec", "price_cad": 390_000,
        "rooms": 2, "sqft": 700, "parking": False,
        "tags": ["condo", "quebec", "vieux-quebec", "vieille-ville", "appartement"],
    },
    {
        "id": "longueuil-001", "type": "maison", "city": "Longueuil",
        "neighbourhood": "Saint-Hubert", "price_cad": 575_000,
        "rooms": 4, "sqft": 1_550, "parking": True,
        "tags": ["maison", "longueuil", "saint-hubert", "rive-sud", "banlieue"],
    },
    {
        "id": "brossard-001", "type": "condo", "city": "Brossard",
        "neighbourhood": "Solar Uniquartier", "price_cad": 480_000,
        "rooms": 3, "sqft": 1_000, "parking": True,
        "tags": ["condo", "brossard", "rive-sud", "solar", "nouveau"],
    },
    {
        "id": "sherbrooke-001", "type": "maison", "city": "Sherbrooke",
        "neighbourhood": "Mont-Bellevue", "price_cad": 380_000,
        "rooms": 4, "sqft": 1_400, "parking": True,
        "tags": ["maison", "sherbrooke", "estrie", "maison"],
    },
]


class ImmoCatalogError(Exception):
    """Raised on any catalog fault."""


class ImmoCatalogClient:
    """In-memory real-estate catalog — no HTTP, no rate limits.

    search() does case-insensitive substring matching against type, city,
    neighbourhood, and tags.
    aclose() is a no-op.
    """

    async def search(self, query: str) -> list[dict]:
        """Return listings whose type, city, neighbourhood, or tags match any query token."""
        tokens = query.lower().split()
        results = []
        for item in _CATALOG:
            haystack = (
                item["type"].lower()
                + " " + item["city"].lower()
                + " " + item["neighbourhood"].lower()
                + " " + " ".join(item["tags"])
            )
            if any(tok in haystack for tok in tokens):
                results.append(item)
        return results

    async def aclose(self) -> None:
        pass
