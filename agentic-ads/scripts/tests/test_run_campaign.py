# scripts/tests/test_run_campaign.py
import json
import os
import pytest
from unittest.mock import MagicMock, patch, call

# run_campaign doesn't exist yet — these imports will fail (that's the point)
from run_campaign import load_registry, bid_for, run, RunSummary


def _make_resp(status_code: int, body: dict) -> MagicMock:
    """Build a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = body
    return resp


# ── Test 1: load_registry returns only active products ────────────────────────

def test_load_registry_returns_active_products(tmp_path):
    registry = tmp_path / "product_registry.json"
    registry.write_text(json.dumps({
        "products": [
            {"name": "btc-tracker", "vertical": "crypto", "active": True},
            {"name": "old-product", "vertical": "crypto", "active": False},
            {"name": "no-flag",     "vertical": "crypto"},            # missing active
        ]
    }))
    result = load_registry(str(registry))
    assert result == [{"name": "btc-tracker", "vertical": "crypto", "active": True}]


# ── Test 2: load_registry returns [] for missing file ─────────────────────────

def test_load_registry_missing_file_returns_empty(tmp_path):
    result = load_registry(str(tmp_path / "nonexistent.json"))
    assert result == []


# ── Test 3: load_registry raises on malformed JSON ────────────────────────────

def test_load_registry_malformed_json_raises(tmp_path):
    bad = tmp_path / "product_registry.json"
    bad.write_text("{not valid json")
    with pytest.raises(json.JSONDecodeError):
        load_registry(str(bad))


# ── Test 4: bid_for success with sponsor present ──────────────────────────────

def test_bid_for_success_sponsor_present():
    session = MagicMock()
    session.post.return_value = _make_resp(200, {
        "bid_id": "abc", "vertical": "crypto",
        "bid_amount": 0.05, "sponsor": {"name": "CoinEx"}, "w1": 1.0, "w2": 1.0,
    })
    result = bid_for(session, "crypto", "crypto", "http://localhost:3045")
    assert result["sponsor"] == {"name": "CoinEx"}
    assert result["bid_amount"] == 0.05
    session.post.assert_called_once_with(
        "http://localhost:3045/bid",
        json={
            "vertical": "crypto",
            "cohorte_id": "campaign-runner",
            "geo_region": "QC-CA",
            "device_class": "desktop",
            "V": 1.0,
        },
    )


# ── Test 5: bid_for non-200 returns error dict ────────────────────────────────

def test_bid_for_non200_returns_error_dict():
    session = MagicMock()
    session.post.return_value = _make_resp(429, {})
    result = bid_for(session, "crypto", "btc-tracker", "http://localhost:3045")
    assert "error" in result
    assert "429" in result["error"]


# ── Test 6: run counts bids_won and prospective revenue ───────────────────────

def test_run_counts_won_bids_and_revenue(tmp_path):
    registry = tmp_path / "product_registry.json"
    registry.write_text(json.dumps({
        "products": [{"name": "btc-tracker", "vertical": "crypto", "active": True}]
    }))
    summary_path = str(tmp_path / "campaign_run_summary.json")

    won_resp  = _make_resp(200, {"bid_id": "x", "vertical": "crypto",
                                  "bid_amount": 0.05, "sponsor": {"name": "Ex"},
                                  "w1": 1.0, "w2": 1.0})
    loss_resp = _make_resp(200, {"bid_id": "y", "vertical": "crypto",
                                  "bid_amount": 0.0, "sponsor": None,
                                  "w1": 1.0, "w2": 1.0})

    mock_session = MagicMock()
    # Pass 1 (vertical) wins, Pass 2 (product) loses
    mock_session.post.side_effect = [won_resp, loss_resp]
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)

    with patch("run_campaign.httpx.Client", return_value=mock_session):
        run(registry_path=str(registry),
            bid_url="http://localhost:3045",
            summary_path=summary_path)

    with open(summary_path) as f:
        data = json.load(f)

    assert data["bids_won"] == 1
    assert data["verticals_called"] == 1
    assert data["products_called"] == 1
    assert abs(data["prospective_revenue_usd"] - 0.05) < 1e-9
    assert data["errors"] == []


# ── Test 7: run writes summary atomically via tmp_path ────────────────────────

def test_run_writes_summary_atomically(tmp_path):
    registry = tmp_path / "product_registry.json"
    registry.write_text(json.dumps({"products": []}))
    summary_path = tmp_path / "campaign_run_summary.json"

    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)

    with patch("run_campaign.httpx.Client", return_value=mock_session):
        run(registry_path=str(registry),
            bid_url="http://localhost:3045",
            summary_path=str(summary_path))

    # Final file must exist
    assert summary_path.exists()
    # .tmp file must be gone (os.replace moved it)
    assert not (tmp_path / "campaign_run_summary.json.tmp").exists()
    # Content must be valid JSON
    data = json.loads(summary_path.read_text())
    assert "run_at" in data


# ── Test 8: run skips product missing vertical key ────────────────────────────

def test_run_skips_product_missing_vertical(tmp_path):
    registry = tmp_path / "product_registry.json"
    registry.write_text(json.dumps({
        "products": [
            {"name": "broken-product", "active": True},   # no vertical key
        ]
    }))
    summary_path = str(tmp_path / "campaign_run_summary.json")

    mock_session = MagicMock()
    mock_session.__enter__ = MagicMock(return_value=mock_session)
    mock_session.__exit__ = MagicMock(return_value=False)

    with patch("run_campaign.httpx.Client", return_value=mock_session):
        run(registry_path=str(registry),
            bid_url="http://localhost:3045",
            summary_path=summary_path)

    # bid_for must NOT have been called (skipped)
    mock_session.post.assert_not_called()

    with open(summary_path) as f:
        data = json.load(f)
    assert data["products_called"] == 0
    assert len(data["errors"]) == 1
    assert "missing vertical" in data["errors"][0]
