# Campaign Runner Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `scripts/run_campaign.py` — a synchronous CLI script that bids on every active vertical and product from `product_registry.json`, then writes an atomic run summary; fix the broken souffle target.

**Architecture:** One plain-`def run()` entry point using `httpx.Client` (synchronous). Two sequential passes: unique verticals first, then individual products. Errors accumulate in the summary rather than halting the run. Atomic write to `campaign_run_summary.json` via `.tmp → os.replace()`.

**Tech Stack:** Python 3.12, httpx (sync), pytest, unittest.mock (MagicMock + patch)

---

## Chunk 1: Red tests → Green implementation → Souffle fix

### Task 1: Write failing tests for run_campaign

**Files:**
- Create: `scripts/tests/__init__.py` (empty)
- Create: `scripts/tests/conftest.py`
- Create: `scripts/tests/test_run_campaign.py`

**Context:** The `scripts/` directory already exists (contains `flush_revenue.py`, `remediate.py`). `scripts/tests/` does not exist yet — create it first. Tests in this project follow the pattern in `mcp-servers/crypto/tests/` — plain `MagicMock` for sync HTTP, `patch.object` for method-level mocking. `pytest.ini` is at `agentic-ads/` root (`asyncio_mode = auto`). A root-level `conftest.py` also exists there — the new `scripts/tests/conftest.py` is a separate, nested conftest (no conflict). No async needed here.

- [ ] **Step 0: Create `scripts/tests/` directory**

```bash
mkdir -p /home/ichigo/alexandria/agentic-ads/scripts/tests
```

- [ ] **Step 1: Create `scripts/tests/__init__.py`**

```bash
touch /home/ichigo/alexandria/agentic-ads/scripts/tests/__init__.py
```

- [ ] **Step 2: Create `scripts/tests/conftest.py`**

```python
# scripts/tests/conftest.py
"""Add scripts/ to sys.path so run_campaign is importable as a module."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
```

- [ ] **Step 3: Write the failing tests in `scripts/tests/test_run_campaign.py`**

```python
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
```

- [ ] **Step 4: Run tests — confirm they all fail (ImportError)**

```bash
cd /home/ichigo/alexandria/agentic-ads
python -m pytest scripts/tests/test_run_campaign.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'load_registry' from 'run_campaign'` (module doesn't exist yet). All 8 collected, 8 errors.

- [ ] **Step 5: Commit red tests**

```bash
cd /home/ichigo/alexandria/agentic-ads
git add scripts/tests/__init__.py scripts/tests/conftest.py scripts/tests/test_run_campaign.py
git commit -m "test(campaign-runner): red — 8 failing tests for run_campaign"
```

---

### Task 2: Implement run_campaign.py and seed product_registry.json

**Files:**
- Create: `scripts/run_campaign.py`
- Create: `product_registry.json` (at `agentic-ads/` root)
- Create: `.gitignore` (at `agentic-ads/` root — runtime outputs must not be committed)

- [ ] **Step 1: Create `.gitignore`** (agentic-ads has no .gitignore yet)

```bash
cat > /home/ichigo/alexandria/agentic-ads/.gitignore << 'EOF'
# Runtime outputs
campaign_run_summary.json
campaign_run_summary.json.tmp
pending_revenue.json.tmp
__pycache__/
*.pyc
.pytest_cache/
EOF
```

- [ ] **Step 3: Create `product_registry.json`** (agentic-ads root — source of truth for active campaigns)

```bash
cat > /home/ichigo/alexandria/agentic-ads/product_registry.json << 'EOF'
{
  "products": [
    {
      "name": "bitcoin-tracker-pro",
      "vertical": "crypto",
      "active": true
    }
  ]
}
EOF
```

- [ ] **Step 4: Create `scripts/run_campaign.py`**

```python
# scripts/run_campaign.py
"""Campaign runner — called every hour by the agentic_ads_campaign souffle.

Reads product_registry.json, calls the bid engine for each active vertical
and product, writes an atomic run summary to campaign_run_summary.json.

Called by souffle:
    python3 /home/ichigo/alexandria/agentic-ads/scripts/run_campaign.py
"""
import json
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

import httpx

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.join(_HERE, "..")

REGISTRY_PATH = os.path.join(_ROOT, "product_registry.json")
SUMMARY_PATH  = os.path.join(_ROOT, "campaign_run_summary.json")
BID_URL       = os.environ.get("BID_ENGINE_URL", "http://localhost:3045")


@dataclass
class RunSummary:
    run_at: str
    verticals_called: int
    products_called: int
    bids_won: int
    prospective_revenue_usd: float
    errors: list


def load_registry(path: str) -> list[dict]:
    """Return active products from product_registry.json.

    Raises json.JSONDecodeError on malformed JSON (failure must be visible).
    Returns [] if file is missing or has no products key.
    """
    try:
        with open(path) as f:
            data = json.load(f)          # raises JSONDecodeError if malformed
    except FileNotFoundError:
        print(f"[campaign-runner] WARNING: {path} not found", file=sys.stderr)
        return []

    products = data.get("products", [])
    if not products:
        print("[campaign-runner] WARNING: no products in registry", file=sys.stderr)

    return [p for p in products if p.get("active") is True]


def bid_for(session: httpx.Client, vertical: str, name: str, bid_url: str) -> dict:
    """POST /bid for one vertical. `name` is used only for log messages.

    Returns parsed response dict on 200.
    Returns {"error": "<detail>"} on non-200 or network error (run continues).
    """
    payload = {
        "vertical": vertical,
        "cohorte_id": "campaign-runner",
        "geo_region": "QC-CA",
        "device_class": "desktop",
        "V": 1.0,
    }
    try:
        resp = session.post(f"{bid_url}/bid", json=payload)
        if resp.status_code != 200:
            msg = f"bid failed: {resp.status_code} ({name})"
            print(f"[campaign-runner] ERROR: {msg}", file=sys.stderr)
            return {"error": msg}
        return resp.json()
    except httpx.RequestError as exc:
        msg = str(exc)
        print(f"[campaign-runner] ERROR: {msg}", file=sys.stderr)
        return {"error": msg}


def run(
    registry_path: str = REGISTRY_PATH,
    bid_url: str = BID_URL,
    summary_path: str = SUMMARY_PATH,
) -> None:
    """Main entry point — orchestrates both bid passes and writes summary."""
    products = load_registry(registry_path)

    # Unique verticals from active products (preserves order via dict)
    verticals = list({p["vertical"]: None for p in products if "vertical" in p})

    bids_won = 0
    prospective_revenue_usd = 0.0
    errors: list[str] = []
    verticals_called = 0
    products_called = 0

    with httpx.Client() as session:
        # Pass 1: one bid per unique vertical
        for vertical in verticals:
            result = bid_for(session, vertical, vertical, bid_url)
            verticals_called += 1
            if "error" in result:
                errors.append(result["error"])
            elif result.get("sponsor") is not None:
                bids_won += 1
                prospective_revenue_usd += result.get("bid_amount", 0.0)

        # Pass 2: one bid per active product
        for product in products:
            if "vertical" not in product:
                errors.append(
                    f"product '{product.get('name', '?')}' missing vertical key"
                )
                continue
            result = bid_for(session, product["vertical"], product["name"], bid_url)
            products_called += 1
            if "error" in result:
                errors.append(result["error"])
            elif result.get("sponsor") is not None:
                bids_won += 1
                prospective_revenue_usd += result.get("bid_amount", 0.0)

    summary = RunSummary(
        run_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        verticals_called=verticals_called,
        products_called=products_called,
        bids_won=bids_won,
        prospective_revenue_usd=prospective_revenue_usd,
        errors=errors,
    )

    # Atomic write — CLAUDE.md rule 3
    tmp = summary_path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(asdict(summary), f, indent=2)
    os.replace(tmp, summary_path)

    print(
        f"[campaign-runner] Done: {bids_won} bids won, "
        f"${prospective_revenue_usd:.4f} prospective",
        flush=True,
    )


if __name__ == "__main__":
    run()
```

- [ ] **Step 5: Run all 8 tests — confirm they pass**

```bash
cd /home/ichigo/alexandria/agentic-ads
python -m pytest scripts/tests/test_run_campaign.py -v
```

Expected: `8 passed`

- [ ] **Step 6: Smoke-test the CLI entry point (no bid engine needed — it will fail gracefully)**

```bash
cd /home/ichigo/alexandria/agentic-ads
BID_ENGINE_URL=http://localhost:1 python3 scripts/run_campaign.py
```

Expected output (stderr): `[campaign-runner] ERROR: ...` for each bid attempt (connection refused)
Expected output (stdout): `[campaign-runner] Done: 0 bids won, $0.0000 prospective`
Expected: `campaign_run_summary.json` created at root.

```bash
cat /home/ichigo/alexandria/agentic-ads/campaign_run_summary.json
```

Expected: valid JSON with `"bids_won": 0`, `"errors": [...]`.

- [ ] **Step 7: Commit green implementation**

```bash
cd /home/ichigo/alexandria/agentic-ads
git add .gitignore scripts/run_campaign.py product_registry.json
git commit -m "feat(campaign-runner): run_campaign.py + seed product_registry.json

Sequential bid caller: passes over unique verticals then individual products.
Atomic write to campaign_run_summary.json. 8/8 tests passing."
```

---

### Task 3: Fix the broken souffle target

**Files:**
- Modify: `souffles/agentic_ads_campaign.json`

- [ ] **Step 1: Read current souffle to confirm the broken target**

```bash
cat /home/ichigo/alexandria/agentic-ads/souffles/agentic_ads_campaign.json
```

Expected: `"action": "python3 /home/ichigo/alexandria/agentic-ads/bid-engine/bid_router.py --campaign auto"`

- [ ] **Step 2: Fix the `action` field** (edit `souffles/agentic_ads_campaign.json`)

Replace only the `action` line. Final file:

```json
{
  "name": "agentic_ads_campaign",
  "description": "Trigger autonomous ad campaigns for Alexandria products every hour",
  "trigger": "timer:3600s",
  "interval_s": 3600,
  "action": "python3 /home/ichigo/alexandria/agentic-ads/scripts/run_campaign.py",
  "relay_to": ["revenue_sync"],
  "_note": "NO file_trigger — avoids flood when Product-Spawner generates 100+ variants"
}
```

- [ ] **Step 3: Verify the JSON is valid**

```bash
cd /home/ichigo/alexandria/agentic-ads && python3 -c "import json; json.load(open('souffles/agentic_ads_campaign.json')); print('OK')"
```

Expected: `OK`

- [ ] **Step 4: Run the full test suite to confirm nothing is broken**

```bash
cd /home/ichigo/alexandria/agentic-ads
python -m pytest scripts/tests/ -v
```

Expected: `8 passed`

- [ ] **Step 5: Commit the souffle fix**

```bash
cd /home/ichigo/alexandria/agentic-ads
git add souffles/agentic_ads_campaign.json
git commit -m "fix(souffle): point agentic_ads_campaign to run_campaign.py

bid_router.py --campaign auto never existed. Now calls the real runner."
```

---

## Done

After Task 3 completes, run `superpowers:finishing-a-development-branch`.
