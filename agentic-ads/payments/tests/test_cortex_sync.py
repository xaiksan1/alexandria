"""Tests for CortexSyncService — cortex-v3 push and pending flush."""
import json
import os
from unittest.mock import AsyncMock, MagicMock

import pytest

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cortex_sync import CortexSyncService


@pytest.fixture
def tmp_pending(tmp_path):
    """Return path to a temp pending_revenue.json (empty)."""
    p = tmp_path / "pending_revenue.json"
    p.write_text(json.dumps({"pending": []}))
    return str(p)


@pytest.fixture
def svc(tmp_pending):
    s = CortexSyncService(cortex_url="http://fake-cortex", pending_path=tmp_pending)
    return s


@pytest.mark.asyncio
async def test_push_success_returns_true(svc):
    """HTTP 200 → push returns True."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    svc._http.post = AsyncMock(return_value=mock_resp)

    result = await svc.push("bid-1", "crypto", 0.05)
    assert result is True


@pytest.mark.asyncio
async def test_push_failure_returns_false(svc):
    """Any exception → push returns False and never raises."""
    svc._http.post = AsyncMock(side_effect=Exception("network error"))

    result = await svc.push("bid-1", "crypto", 0.05)
    assert result is False


@pytest.mark.asyncio
async def test_flush_clears_file_on_full_success(svc, tmp_pending):
    """All entries synced → pending list becomes empty."""
    with open(tmp_pending, "w") as f:
        json.dump({"pending": [
            {"bid_id": "a", "vertical": "crypto", "amount": 0.1},
            {"bid_id": "b", "vertical": "crypto", "amount": 0.2},
        ]}, f)

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    svc._http.post = AsyncMock(return_value=mock_resp)

    synced, remaining = await svc.flush_pending()

    assert synced == 2
    assert remaining == 0
    data = json.loads(open(tmp_pending).read())
    assert data["pending"] == []


@pytest.mark.asyncio
async def test_flush_keeps_failed_entries(svc, tmp_pending):
    """Partial success → only failed entries remain in file."""
    with open(tmp_pending, "w") as f:
        json.dump({"pending": [
            {"bid_id": "a", "vertical": "crypto", "amount": 0.1},
            {"bid_id": "b", "vertical": "crypto", "amount": 0.2},
        ]}, f)

    responses = [
        MagicMock(status_code=200),
        MagicMock(status_code=500),
    ]
    svc._http.post = AsyncMock(side_effect=responses)

    synced, remaining = await svc.flush_pending()

    assert synced == 1
    assert remaining == 1
    data = json.loads(open(tmp_pending).read())
    assert len(data["pending"]) == 1
    assert data["pending"][0]["bid_id"] == "b"


@pytest.mark.asyncio
async def test_flush_corrupt_file_resets(svc, tmp_pending):
    """Corrupt JSON → file reset to empty, returns (0, 0), no crash."""
    with open(tmp_pending, "w") as f:
        f.write("NOT JSON {{{")

    synced, remaining = await svc.flush_pending()

    assert synced == 0
    assert remaining == 0
    data = json.loads(open(tmp_pending).read())
    assert data == {"pending": []}
