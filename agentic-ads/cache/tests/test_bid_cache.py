import pytest
import pytest_asyncio
import hashlib
from unittest.mock import AsyncMock, MagicMock, patch
from cache.vault import Vault
from cache.bid_cache import BidCache

@pytest.fixture
def vault():
    return Vault()

@pytest.fixture
def mock_redis():
    r = AsyncMock()
    r.setex = AsyncMock(return_value=True)
    r.get = AsyncMock(return_value=None)
    r.delete = AsyncMock(return_value=1)
    r.aclose = AsyncMock()
    return r

@pytest.fixture
def bid_cache(vault, mock_redis):
    cache = BidCache.__new__(BidCache)
    cache._redis = mock_redis
    cache._vault = vault
    return cache

@pytest.mark.asyncio
async def test_compute_context_hash_format():
    h = BidCache.compute_context_hash("cloud", "QC-CA", "desktop")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)

@pytest.mark.asyncio
async def test_compute_context_hash_no_pii_in_inputs():
    """Hash inputs contain only vertical, region, device — no user data."""
    h = BidCache.compute_context_hash("cloud", "QC-CA", "desktop")
    expected = hashlib.sha256(b"cloud|QC-CA|desktop").hexdigest()
    assert h == expected

@pytest.mark.asyncio
async def test_compute_context_hash_deterministic():
    h1 = BidCache.compute_context_hash("cloud", "QC-CA", "desktop")
    h2 = BidCache.compute_context_hash("cloud", "QC-CA", "desktop")
    assert h1 == h2

@pytest.mark.asyncio
async def test_compute_context_hash_different_inputs():
    h1 = BidCache.compute_context_hash("cloud", "QC-CA", "desktop")
    h2 = BidCache.compute_context_hash("crypto", "QC-CA", "desktop")
    assert h1 != h2

@pytest.mark.asyncio
async def test_set_calls_redis_setex(bid_cache, mock_redis):
    await bid_cache.set("abc123", "cloud", b"payload", ttl_seconds=3600)
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args.kwargs.get("name") == "abc123" or call_args.args[0] == "abc123"
    assert call_args.kwargs.get("time") == 3600 or call_args.args[1] == 3600

@pytest.mark.asyncio
async def test_set_encrypts_payload(bid_cache, mock_redis, vault):
    payload = b"sensitive_bid_response"
    await bid_cache.set("hash_xyz", "cloud", payload, ttl_seconds=600)
    stored = mock_redis.setex.call_args.kwargs.get("value") or mock_redis.setex.call_args.args[2]
    # The stored bytes should NOT be the plain payload
    assert stored != payload
    # And should be decryptable
    label = "cloud:hash_xyz"
    assert vault.decrypt(stored, label) == payload

@pytest.mark.asyncio
async def test_get_returns_none_on_miss(bid_cache, mock_redis):
    mock_redis.get.return_value = None
    result = await bid_cache.get("nonexistent", "cloud")
    assert result is None

@pytest.mark.asyncio
async def test_get_decrypts_on_hit(bid_cache, mock_redis, vault):
    payload = b"cached_response_data"
    encrypted = vault.encrypt(payload, "cloud:myhash")
    mock_redis.get.return_value = encrypted
    result = await bid_cache.get("myhash", "cloud")
    assert result == payload

@pytest.mark.asyncio
async def test_get_deletes_corrupted_entry(bid_cache, mock_redis):
    mock_redis.get.return_value = b"corrupted_garbage_data_that_wont_decrypt"
    result = await bid_cache.get("hash_abc", "cloud")
    assert result is None
    mock_redis.delete.assert_called_once_with("hash_abc")
