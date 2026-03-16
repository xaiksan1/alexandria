import asyncio
import json
import os
import httpx
from dataclasses import dataclass

try:
    from payments.cortex_sync import CortexSyncService
except ModuleNotFoundError:
    from cortex_sync import CortexSyncService

DWALLSTREET_URL = os.environ.get("DWALLSTREET_URL", "http://localhost:3003")
PENDING_REVENUE_PATH = os.environ.get(
    "PENDING_REVENUE_PATH",
    os.path.join(os.path.dirname(__file__), "..", "pending_revenue.json")
)


@dataclass
class PaymentRequest:
    bid_id: str
    vertical: str
    bid_amount: float
    sponsor_id: str = ""


@dataclass
class PaymentResult:
    bid_id: str
    payment_confirmed: bool
    tx_hash: str = ""
    error: str = ""


class X402Bridge:
    """Client wrapper for the dwallstreet x402 M2M payment API.

    Never reimplements x402 — calls dwallstreet as client only.
    Revenue is credited ONLY after payment_confirmed = True.
    """

    _background_tasks: "set[asyncio.Task]" = set()

    def __init__(
        self,
        dwallstreet_url: str = DWALLSTREET_URL,
        cortex_sync: "CortexSyncService | None" = None,
    ) -> None:
        self._url = dwallstreet_url
        self._http = httpx.AsyncClient(timeout=10.0)
        self._sync = cortex_sync or CortexSyncService()

    async def __aenter__(self) -> "X402Bridge":
        return self

    async def __aexit__(self, *_) -> None:
        await self._http.aclose()

    async def charge(self, request: PaymentRequest) -> PaymentResult:
        """Submit a payment request to dwallstreet x402 API.

        Returns PaymentResult with payment_confirmed=True on success.
        Never raises — returns PaymentResult(payment_confirmed=False, error=...) on any failure.
        """
        try:
            resp = await self._http.post(
                f"{self._url}/x402/charge",
                json={
                    "bid_id": request.bid_id,
                    "amount": request.bid_amount,
                    "vertical": request.vertical,
                    "sponsor_id": request.sponsor_id,
                },
            )
            if resp.status_code == 200:
                data = resp.json()  # may raise json.JSONDecodeError — caught below
                return PaymentResult(
                    bid_id=request.bid_id,
                    payment_confirmed=data.get("confirmed", False),
                    tx_hash=data.get("tx_hash", ""),
                )
            return PaymentResult(
                bid_id=request.bid_id,
                payment_confirmed=False,
                error=f"HTTP {resp.status_code}",
            )
        except Exception as e:  # noqa: BLE001 — "never raises" contract
            return PaymentResult(
                bid_id=request.bid_id,
                payment_confirmed=False,
                error=str(e),
            )

    async def record_revenue(self, bid_id: str, vertical: str, amount: float) -> None:
        """Atomically append a confirmed revenue record to pending_revenue.json.

        Uses .tmp -> os.replace() pattern (atomic write — NEVER write directly).
        Only call after payment_confirmed = True.
        """
        revenue_path = os.path.abspath(PENDING_REVENUE_PATH)

        # Read existing data — treat corrupt file as empty to avoid dropping revenue
        if os.path.exists(revenue_path):
            try:
                with open(revenue_path, "r") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {"pending": []}
        else:
            data = {"pending": []}

        data["pending"].append({
            "bid_id": bid_id,
            "vertical": vertical,
            "amount": amount,
            "payment_confirmed": True,
        })

        # Atomic write: .tmp -> os.replace()
        tmp_path = revenue_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, revenue_path)

    async def _push_and_record(self, bid_id: str, vertical: str, kwh: float) -> None:
        """Try cortex-v3 push; fallback to pending_revenue.json ONLY on failure."""
        ok = await self._sync.push(bid_id, vertical, kwh)
        if not ok:
            await self.record_revenue(bid_id, vertical, kwh)  # durable fallback

    async def process_win(
        self,
        bid_id: str,
        vertical: str,
        bid_amount: float,
        sponsor_id: str = "",
    ) -> PaymentResult:
        """Full win payment flow: charge -> confirm -> async revenue push.

        Revenue sync is fire-and-forget (create_task) — zero latency added.
        Revenue only recorded if payment_confirmed = True.
        """
        result = await self.charge(PaymentRequest(
            bid_id=bid_id,
            vertical=vertical,
            bid_amount=bid_amount,
            sponsor_id=sponsor_id,
        ))
        if result.payment_confirmed:
            task = asyncio.create_task(self._push_and_record(bid_id, vertical, bid_amount))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        return result

    async def close(self) -> None:
        await self._http.aclose()
