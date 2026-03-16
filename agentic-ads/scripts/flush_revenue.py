"""CLI entry point for the revenue_flush ADAM souffle.

Called every 60s by: python3 /home/ichigo/alexandria/agentic-ads/scripts/flush_revenue.py
Exits 0 on full flush, exits 1 if entries remain (souffle retries next round).
"""
import asyncio
import os
import sys

# Add payments directory to path so cortex_sync is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "payments"))

from cortex_sync import CortexSyncService


async def main() -> None:
    async with CortexSyncService() as svc:
        synced, remaining = await svc.flush_pending()
        print(f"[revenue_flush] Flushed {synced} entries, {remaining} remaining")
        if remaining:
            raise SystemExit(1)


asyncio.run(main())
