"""Semantic Bid Cache — core competitive moat.

Cache hit <1ms, ~0 tokens. SHA256 context hashing for Loi 25 compliance,
AES-256-GCM encryption via BIP-39 vault, Redis backend with TTL.
"""

import hashlib
import redis.asyncio as aioredis
from cache.vault import Vault


class BidCache:
    """Encrypted semantic bid cache with Loi 25-compliant context hashing."""

    def __init__(self, redis_url: str, vault: Vault) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=False)
        self._vault = vault

    @staticmethod
    def compute_context_hash(
        product_vertical: str,
        geo_region_code: str,
        device_class: str,
    ) -> str:
        """SHA256 hash of vertical|region|device — Loi 25 compliant, no PII.

        Args:
            product_vertical: The product/service vertical (e.g. "cloud").
            geo_region_code: ISO region code (e.g. "QC-CA").
            device_class: Device category (e.g. "desktop", "mobile").

        Returns:
            64-character lowercase hex SHA256 digest.
        """
        raw = f"{product_vertical}|{geo_region_code}|{device_class}".encode()
        return hashlib.sha256(raw).hexdigest()

    async def set(
        self,
        cohorte_id: str,
        vertical: str,
        response_payload: bytes,
        ttl_seconds: int = 3600,
    ) -> None:
        """Encrypt payload and store in Redis with TTL.

        Args:
            cohorte_id: SHA256 context hash (privacy boundary key).
            vertical: Product vertical used to scope the encryption label.
            response_payload: Raw bytes of the bid response to cache.
            ttl_seconds: Time-to-live in seconds (default 3600).
        """
        label = f"{vertical}:{cohorte_id}"
        encrypted = self._vault.encrypt(response_payload, label)
        await self._redis.setex(name=cohorte_id, time=ttl_seconds, value=encrypted)

    async def get(self, cohorte_id: str, vertical: str) -> bytes | None:
        """Fetch and decrypt cached response. Returns None on miss.

        Args:
            cohorte_id: SHA256 context hash used as Redis key.
            vertical: Product vertical used to scope the decryption label.

        Returns:
            Decrypted payload bytes on hit, None on miss or corruption.
        """
        raw = await self._redis.get(cohorte_id)
        if raw is None:
            return None
        label = f"{vertical}:{cohorte_id}"
        try:
            return self._vault.decrypt(raw, label)
        except ValueError:
            # Corrupted or wrong key — treat as cache miss
            await self._redis.delete(cohorte_id)
            return None

    async def close(self) -> None:
        """Close the Redis connection."""
        await self._redis.aclose()
