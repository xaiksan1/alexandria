"""CortexSyncService — push confirmed ad revenue to cortex-v3.

cortex-v3 API contract:
  POST http://localhost:3003/api/energon/collect
  {"worker_id": "agentic-ads:{vertical}", "egn_generated": float,
   "hashrate": null, "status": "confirmed"}

Never writes to energon_ledger.json directly (CLAUDE.md rule 1).
Atomic writes to pending_revenue.json use .tmp -> os.replace() (rule 3).
"""
import json
import logging
import os

import httpx

CORTEX_URL = os.environ.get("CORTEX_URL", "http://localhost:3003")
PENDING_REVENUE_PATH = os.environ.get(
    "PENDING_REVENUE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "pending_revenue.json"),
)

logger = logging.getLogger(__name__)


class CortexSyncService:
    def __init__(
        self,
        cortex_url: str = CORTEX_URL,
        pending_path: str = PENDING_REVENUE_PATH,
    ) -> None:
        self._url = cortex_url
        self._pending_path = pending_path
        self._http = httpx.AsyncClient(timeout=3.0)

    async def __aenter__(self) -> "CortexSyncService":
        return self

    async def __aexit__(self, *_) -> None:
        await self._http.aclose()

    async def push(self, bid_id: str, vertical: str, kwh: float) -> bool:
        """POST revenue to cortex-v3. Returns True on success. Never raises."""
        try:
            resp = await self._http.post(
                f"{self._url}/api/energon/collect",
                json={
                    "worker_id": f"agentic-ads:{vertical}",
                    "egn_generated": kwh,
                    "hashrate": None,
                    "status": "confirmed",
                },
            )
            return resp.status_code == 200
        except Exception:  # noqa: BLE001 — never raises
            return False

    async def flush_pending(self) -> tuple[int, int]:
        """Flush pending_revenue.json entries to cortex-v3.

        Returns (synced_count, remaining_count).
        On corrupt file: reset to {"pending": []}, log warning, return (0, 0).
        On partial failure: atomic-write remaining entries.
        """
        revenue_path = os.path.abspath(self._pending_path)

        try:
            with open(revenue_path, "r") as f:
                data = json.load(f)
            entries = data.get("pending", [])
            if not isinstance(entries, list):
                raise ValueError("pending is not a list")
        except (json.JSONDecodeError, OSError, ValueError):
            logger.warning("[CortexSyncService] corrupt pending_revenue.json — resetting")
            self._atomic_write(revenue_path, {"pending": []})
            return (0, 0)

        synced: list[dict] = []
        failed: list[dict] = []
        for entry in entries:
            ok = await self.push(
                bid_id=entry.get("bid_id", ""),
                vertical=entry.get("vertical", ""),
                kwh=entry.get("amount", 0.0),  # field rename: amount → egn_generated
            )
            if ok:
                synced.append(entry)
            else:
                failed.append(entry)

        self._atomic_write(revenue_path, {"pending": failed})
        return (len(synced), len(failed))

    def _atomic_write(self, path: str, data: dict) -> None:
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp, path)
