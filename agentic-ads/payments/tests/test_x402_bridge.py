import json
import os
import pytest
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from payments.x402_bridge import X402Bridge, PaymentRequest, PaymentResult


@pytest.fixture
def bridge():
    return X402Bridge(dwallstreet_url="http://mock-dws:3003")


def _mock_post(status_code: int, body: dict | None = None) -> AsyncMock:
    """Build an AsyncMock for bridge._http.post with a sync MagicMock response."""
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    if body is not None:
        mock_resp.json.return_value = body
    return AsyncMock(return_value=mock_resp)


@pytest.mark.asyncio
async def test_charge_success(bridge):
    with patch.object(bridge._http, "post", _mock_post(200, {"confirmed": True, "tx_hash": "0xabc123"})):
        result = await bridge.charge(PaymentRequest(
            bid_id="bid-001", vertical="crypto", bid_amount=0.45
        ))
    assert result.payment_confirmed is True
    assert result.tx_hash == "0xabc123"
    assert result.error == ""


@pytest.mark.asyncio
async def test_charge_http_error_returns_not_confirmed(bridge):
    with patch.object(bridge._http, "post", _mock_post(500)):
        result = await bridge.charge(PaymentRequest(
            bid_id="bid-002", vertical="cloud", bid_amount=0.3
        ))
    assert result.payment_confirmed is False
    assert "500" in result.error


@pytest.mark.asyncio
async def test_charge_timeout_returns_not_confirmed(bridge):
    import httpx
    with patch.object(bridge._http, "post", AsyncMock(side_effect=httpx.TimeoutException("timeout"))):
        result = await bridge.charge(PaymentRequest(
            bid_id="bid-003", vertical="crypto", bid_amount=0.5
        ))
    assert result.payment_confirmed is False
    assert result.error != ""


@pytest.mark.asyncio
async def test_charge_connect_error_returns_not_confirmed(bridge):
    import httpx
    with patch.object(bridge._http, "post", AsyncMock(side_effect=httpx.ConnectError("refused"))):
        result = await bridge.charge(PaymentRequest(
            bid_id="bid-004", vertical="crypto", bid_amount=0.5
        ))
    assert result.payment_confirmed is False


@pytest.mark.asyncio
async def test_charge_malformed_json_returns_not_confirmed(bridge):
    """resp.json() raising JSONDecodeError must not propagate — never-raises contract."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = json.JSONDecodeError("bad json", "", 0)
    with patch.object(bridge._http, "post", AsyncMock(return_value=mock_resp)):
        result = await bridge.charge(PaymentRequest(
            bid_id="bid-005", vertical="crypto", bid_amount=0.5
        ))
    assert result.payment_confirmed is False
    assert result.error != ""


@pytest.mark.asyncio
async def test_record_revenue_atomic_write(bridge, tmp_path):
    revenue_path = str(tmp_path / "pending_revenue.json")
    with patch("payments.x402_bridge.PENDING_REVENUE_PATH", revenue_path):
        await bridge.record_revenue("bid-001", "crypto", 0.45)

    with open(revenue_path) as f:
        data = json.load(f)
    assert len(data["pending"]) == 1
    assert data["pending"][0]["bid_id"] == "bid-001"
    assert data["pending"][0]["payment_confirmed"] is True


@pytest.mark.asyncio
async def test_record_revenue_appends_to_existing(bridge, tmp_path):
    revenue_path = str(tmp_path / "pending_revenue.json")
    with open(revenue_path, "w") as f:
        json.dump({"pending": [{"bid_id": "existing", "vertical": "cloud", "amount": 0.1, "payment_confirmed": True}]}, f)

    with patch("payments.x402_bridge.PENDING_REVENUE_PATH", revenue_path):
        await bridge.record_revenue("bid-002", "crypto", 0.45)

    with open(revenue_path) as f:
        data = json.load(f)
    assert len(data["pending"]) == 2


@pytest.mark.asyncio
async def test_record_revenue_no_tmp_file_left(bridge, tmp_path):
    """After atomic write, no .tmp file should remain."""
    revenue_path = str(tmp_path / "pending_revenue.json")
    with patch("payments.x402_bridge.PENDING_REVENUE_PATH", revenue_path):
        await bridge.record_revenue("bid-001", "crypto", 0.45)
    assert not os.path.exists(revenue_path + ".tmp")


@pytest.mark.asyncio
async def test_record_revenue_corrupt_file_resets(bridge, tmp_path):
    """Corrupt pending_revenue.json must not crash record_revenue — reset to empty."""
    revenue_path = str(tmp_path / "pending_revenue.json")
    with open(revenue_path, "w") as f:
        f.write("{invalid json{{")

    with patch("payments.x402_bridge.PENDING_REVENUE_PATH", revenue_path):
        await bridge.record_revenue("bid-001", "crypto", 0.45)

    with open(revenue_path) as f:
        data = json.load(f)
    assert len(data["pending"]) == 1
    assert data["pending"][0]["bid_id"] == "bid-001"


@pytest.mark.asyncio
async def test_process_win_records_revenue_on_confirmed(tmp_path):
    """payment_confirmed=True + cortex push fails → record_revenue writes file (fallback path)."""
    import asyncio as _al
    from unittest.mock import AsyncMock as _AM, MagicMock as _MM
    from cortex_sync import CortexSyncService as _CSS
    import x402_bridge as _xb

    revenue_path = str(tmp_path / "pending_revenue.json")

    mock_sync = _MM(spec=_CSS)
    mock_sync.push = _AM(return_value=False)  # push fails → fallback to record_revenue

    bridge = _xb.X402Bridge(dwallstreet_url="http://mock-dws:3003", cortex_sync=mock_sync)
    bridge._http.post = _mock_post(200, {"confirmed": True, "tx_hash": "0xdef"})

    with patch("x402_bridge.PENDING_REVENUE_PATH", revenue_path):
        result = await bridge.process_win("bid-001", "crypto", 0.45)
        assert result.payment_confirmed is True

        # Drain the event loop so the fire-and-forget create_task completes
        await _al.sleep(0)

    with open(revenue_path) as f:
        data = json.load(f)
    assert data["pending"][0]["bid_id"] == "bid-001"


@pytest.mark.asyncio
async def test_process_win_no_revenue_on_not_confirmed(bridge, tmp_path):
    """Revenue must NOT be recorded if payment_confirmed = False."""
    revenue_path = str(tmp_path / "pending_revenue.json")
    with patch.object(bridge._http, "post", _mock_post(200, {"confirmed": False})), \
         patch("payments.x402_bridge.PENDING_REVENUE_PATH", revenue_path):
        result = await bridge.process_win("bid-001", "crypto", 0.45)
    assert result.payment_confirmed is False
    assert not os.path.exists(revenue_path)  # no file created


@pytest.mark.asyncio
async def test_context_manager(tmp_path):
    """X402Bridge must support async context manager protocol."""
    async with X402Bridge(dwallstreet_url="http://mock-dws:3003") as bridge:
        assert bridge._url == "http://mock-dws:3003"


# ---------------------------------------------------------------------------
# Revenue sync integration tests (Task 2)
# ---------------------------------------------------------------------------
import asyncio as _asyncio
from unittest.mock import patch as _patch

import sys as _sys
import os as _os
_sys.path.insert(0, _os.path.join(_os.path.dirname(__file__), ".."))

from cortex_sync import CortexSyncService as _CortexSyncService


@pytest.fixture
def mock_sync():
    s = MagicMock(spec=_CortexSyncService)
    s.push = AsyncMock(return_value=True)
    return s


@pytest.fixture
def bridge_with_sync(mock_sync, tmp_path, monkeypatch):
    from x402_bridge import X402Bridge
    import x402_bridge
    pending = tmp_path / "pending_revenue.json"
    pending.write_text('{"pending": []}')
    monkeypatch.setattr(x402_bridge, "PENDING_REVENUE_PATH", str(pending))
    return X402Bridge(cortex_sync=mock_sync), mock_sync


@pytest.mark.asyncio
async def test_push_and_record_skips_record_on_success(bridge_with_sync):
    """push True → record_revenue NOT called."""
    bridge, mock_sync = bridge_with_sync
    mock_sync.push = AsyncMock(return_value=True)
    bridge.record_revenue = AsyncMock()

    await bridge._push_and_record("bid-x", "crypto", 0.5)

    mock_sync.push.assert_called_once_with("bid-x", "crypto", 0.5)
    bridge.record_revenue.assert_not_called()


@pytest.mark.asyncio
async def test_push_and_record_calls_record_on_failure(bridge_with_sync):
    """push False → record_revenue called (fallback)."""
    bridge, mock_sync = bridge_with_sync
    mock_sync.push = AsyncMock(return_value=False)
    bridge.record_revenue = AsyncMock()

    await bridge._push_and_record("bid-x", "crypto", 0.5)

    bridge.record_revenue.assert_called_once_with("bid-x", "crypto", 0.5)


@pytest.mark.asyncio
async def test_process_win_fires_create_task_on_confirm(bridge_with_sync):
    """payment_confirmed=True → create_task fired."""
    bridge, mock_sync = bridge_with_sync
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"confirmed": True, "tx_hash": "0xabc"}
    bridge._http.post = AsyncMock(return_value=mock_resp)

    with _patch("asyncio.create_task") as mock_create_task:
        result = await bridge.process_win("bid-1", "crypto", 1.5)
        mock_create_task.assert_called_once()

    assert result.payment_confirmed is True


@pytest.mark.asyncio
async def test_process_win_no_task_if_not_confirmed(bridge_with_sync):
    """payment_confirmed=False → create_task NOT called."""
    bridge, mock_sync = bridge_with_sync
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"confirmed": False, "tx_hash": ""}
    bridge._http.post = AsyncMock(return_value=mock_resp)

    with _patch("asyncio.create_task") as mock_create_task:
        result = await bridge.process_win("bid-1", "crypto", 1.5)
        mock_create_task.assert_not_called()

    assert result.payment_confirmed is False
