# Campaign Runner — Design Spec

## Goal

Replace the broken souffle target (`bid_router.py --campaign auto`) with a working
`scripts/run_campaign.py` that sequentially calls the bid engine for every active
vertical and every active product found in `product_registry.json`.

## Architecture

```
souffle (timer:3600s)
    └─→ scripts/run_campaign.py
            ├─→ lit product_registry.json
            ├─→ passe 1: itère verticals uniques  → POST /bid (bid engine :3045)
            ├─→ passe 2: itère produits actifs    → POST /bid (bid engine :3045)
            ├─→ accumule résultats
            └─→ écrit campaign_run_summary.json (atomic: .tmp → os.replace)
```

Two sequential passes per run: one per unique vertical, one per active product.
Each call is independent — a failure on one does not block the others.
Uses `httpx.Client` (synchronous) — no asyncio, no concurrency, no gather.

## Product Registry Format

`product_registry.json` lives at `agentic-ads/product_registry.json` (not Product-Spawner's).
It is the agentic-ads source of truth for active campaigns.

```json
{
  "products": [
    {
      "name": "bitcoin-tracker-pro",
      "vertical": "crypto",
      "active": true
    }
  ]
}
```

**Active filter**: a product is active if and only if `product["active"] is True`.
Products missing the `active` key are treated as inactive (skipped, no warning needed).

## Components

### `scripts/run_campaign.py` (new)

**`load_registry(path: str) -> list[dict]`**
- Reads `product_registry.json`; parses `data["products"]`
- Returns only products where `product.get("active") is True`
- Returns `[]` if file missing or `"products"` key absent (logs warning)
- Raises `json.JSONDecodeError` on malformed JSON — failure must be visible

**`bid_for(session: httpx.Client, vertical: str, name: str, bid_url: str) -> dict`**
- Single function for both vertical-level and product-level bids (DRY)
- POST `{bid_url}/bid` with:
  ```json
  {
    "vertical": "<vertical>",
    "cohorte_id": "campaign-runner",
    "geo_region": "QC-CA",
    "device_class": "desktop",
    "V": 1.0
  }
  ```
- `name` is used only for logging (the bid engine does not receive it)
- Returns parsed JSON response dict on 200
- On non-200 or `httpx.RequestError`: logs error, returns `{"error": "<detail>"}`

**`run(registry_path: str, bid_url: str, summary_path: str) -> None`**
- Main entry point (called by souffle via `python3 scripts/run_campaign.py`)
- All three params default to module-level constants (`REGISTRY_PATH`, `BID_URL`, `SUMMARY_PATH`)
- `bid_url` defaults to `os.environ.get("BID_ENGINE_URL", "http://localhost:3045")`
- `summary_path` defaults to `campaign_run_summary.json` at project root; overridable in tests via `tmp_path`
- Opens one `httpx.Client` session for all calls
- Calls `load_registry(registry_path)`
- Extracts unique verticals from active products
- Pass 1: sequential `bid_for(session, vertical, vertical, bid_url)` per unique vertical (in Pass 1 `name` == `vertical`, for log readability only)
- Pass 2: sequential `bid_for(session, product["vertical"], product["name"], bid_url)` per product
- `verticals_called` = number of `bid_for` calls made in Pass 1
- `products_called` = number of `bid_for` calls made in Pass 2 (products skipped for missing `vertical` key are NOT counted)
- Counts `bids_won`: responses where `result.get("sponsor") is not None` — both passes contribute to the same counter
- Sums `prospective_revenue_usd`: sum of `result.get("bid_amount", 0.0)` for won bids — both passes contribute to the same accumulator
- Writes `RunSummary` atomically to `campaign_run_summary.json`

**`RunSummary` (dataclass)**
```python
@dataclass
class RunSummary:
    run_at: str               # datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    verticals_called: int
    products_called: int
    bids_won: int
    prospective_revenue_usd: float  # sum of bid_amount for won bids — NOT confirmed revenue
    errors: list[str]
```

Note: `prospective_revenue_usd` is the raw auction outcome. Confirmed revenue (after
`payment_confirmed = TRUE` in bid_history) is managed separately by `cortex_sync` /
`flush_revenue.py` via cortex-v3 port 3003. The campaign runner does NOT write to
`pending_revenue.json` or cortex.

### `souffles/agentic_ads_campaign.json` (modified)

Change the broken `action` target (key is `action`, absolute path required):
```json
// before (broken):
"action": "python3 /home/ichigo/alexandria/agentic-ads/bid-engine/bid_router.py --campaign auto"

// after:
"action": "python3 /home/ichigo/alexandria/agentic-ads/scripts/run_campaign.py"
```

Keep all other fields unchanged (`timer:3600s`, `interval_s`, `relay_to`, `_note`).

## Data Flow

```
product_registry.json → [{"name": "bitcoin-tracker-pro", "vertical": "crypto", "active": true}]
    → active products: [bitcoin-tracker-pro]
    → unique verticals: ["crypto"]

Pass 1 (verticals):
    POST /bid {"vertical":"crypto","cohorte_id":"campaign-runner","geo_region":"QC-CA","device_class":"desktop","V":1.0}
    → {"bid_id":"abc","vertical":"crypto","bid_amount":0.05,"sponsor":{"name":"..."},...}
    → bids_won += 1, prospective_revenue_usd += 0.05

Pass 2 (products):
    POST /bid {"vertical":"crypto","cohorte_id":"campaign-runner",...}  (name used for log only)
    → {"bid_id":"def","vertical":"crypto","bid_amount":0.02,"sponsor":null,...}
    → sponsor is null → not a win, no revenue added

RunSummary → campaign_run_summary.json (atomic write)
```

## Error Handling

| Failure | Behaviour |
|---------|-----------|
| Bid engine down / network error | Log error per call, add to `errors[]`, continue |
| Non-200 from bid engine | Log `"bid failed: {status}"`, add to `errors[]`, continue |
| Product missing `vertical` key | Skip product, log warning, add to `errors[]` |
| `product_registry.json` missing | Return `[]`, log warning, write empty summary |
| `product_registry.json` malformed JSON | Raise `json.JSONDecodeError` — run fails visibly |
| `campaign_run_summary.json` write failure | Raise — data loss must be visible |

## Output File

**`campaign_run_summary.json`** — separate from `pending_revenue.json` (which uses
`{"pending": []}` format for `cortex_sync`). This file is for observability only.

Atomic write protocol (CLAUDE.md rule 3):
```python
tmp = path + ".tmp"
with open(tmp, "w") as f:
    json.dump(asdict(summary), f, indent=2)
os.replace(tmp, path)
```

Output format:
```json
{
  "run_at": "2026-03-12T14:00:00Z",
  "verticals_called": 1,
  "products_called": 1,
  "bids_won": 1,
  "prospective_revenue_usd": 0.05,
  "errors": []
}
```

## Constraints

- `httpx.Client` (synchronous) — not `AsyncClient`; `run()` is plain `def`
- Sequential calls only — no `asyncio.gather()` (user constraint: avoid latency/engorgement)
- `cohorte_id`: sentinel value `"campaign-runner"` for all calls
- `V`: default `1.0` (bid engine minimum, valid per `Field(gt=0.0)`)
- Bid engine URL: `http://localhost:3045` — overridable via `BID_ENGINE_URL` env var
- `product_registry.json` path: `agentic-ads/product_registry.json` — overridable as CLI arg
- Do NOT write to `pending_revenue.json` or call cortex-v3 — that is `flush_revenue.py`'s job
- Souffle timer `timer:3600s` stays unchanged (CLAUDE.md rule 4)

## Files

| Action | Path |
|--------|------|
| Create | `scripts/run_campaign.py` |
| Create | `product_registry.json` (seed with one example product) |
| Create | `scripts/tests/test_run_campaign.py` |
| Modify | `souffles/agentic_ads_campaign.json` |

## Tests

### `scripts/tests/test_run_campaign.py` (new — 8 tests)

All tests mock `httpx.Client` — no real HTTP calls.

1. `test_load_registry_returns_active_products` — valid JSON with mixed active/inactive → only active returned
2. `test_load_registry_missing_file_returns_empty` — missing file → `[]` (no raise)
3. `test_load_registry_malformed_json_raises` — corrupted JSON → `json.JSONDecodeError` propagates
4. `test_bid_for_success_sponsor_present` — 200 response with non-null sponsor → result dict returned
5. `test_bid_for_non200_returns_error_dict` — 429 → returns `{"error": "bid failed: 429"}`
6. `test_run_counts_won_bids_and_revenue` — sponsor present → `bids_won==1`, `prospective_revenue_usd==0.05`
7. `test_run_writes_summary_atomically` — uses pytest `tmp_path` fixture; verifies output file exists and `.tmp` temp file is gone after `run()` completes
8. `test_run_skips_product_missing_vertical` — product without `vertical` key → skip + error logged
