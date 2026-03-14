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

# Bid payload constants — sentinel values for campaign-runner identity
COHORTE_ID   = "campaign-runner"
GEO_REGION   = "QC-CA"
DEVICE_CLASS = "desktop"
BID_V        = 1.0          # minimum valid value per Field(gt=0.0)


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
        "cohorte_id": COHORTE_ID,
        "geo_region": GEO_REGION,
        "device_class": DEVICE_CLASS,
        "V": BID_V,
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

    with httpx.Client(timeout=10.0) as session:
        # Pass 1: one bid per unique vertical
        for vertical in verticals:
            result = bid_for(session, vertical, vertical, bid_url)
            verticals_called += 1
            if "error" in result:
                errors.append(result["error"])
            elif result.get("sponsor") is not None:
                bids_won += 1
                # prospective only — confirmed revenue handled by flush_revenue.py
                # via cortex-v3 after payment_confirmed=TRUE in bid_history (CLAUDE.md rule 5)
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
