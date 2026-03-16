"""Agentic-Ads auto-remediation script.

Called by the ADAM souffle 'agentic_ads_remediate' when the Inspector detects
that agentic-ads services are down (after grace_misses exhausted).

Strategy:
  1. Check each port — skip services that are already up.
  2. Restart dead services via tmux new-window in session Z-01.
  3. Print a structured log so the Inspector can confirm in the next round.

Fines stop accumulating once services come back up (trust recovers +5/round).
"""

import socket
import subprocess
import sys
import time

BASE = "/home/ichigo/alexandria/agentic-ads"
TMUX_SESSION = "Z-01"

SERVICES = [
    {
        "name": "agentic-ads-cache",
        "port": 3044,
        "window": "ads-cache",
        "cmd": f"cd {BASE}/cache && uvicorn cache_api:app --host 0.0.0.0 --port 3044; exec bash",
    },
    {
        "name": "agentic-ads-engine",
        "port": 3045,
        "window": "ads-engine",
        "cmd": f"cd {BASE}/bid-engine && uvicorn bid_engine_api:app --host 0.0.0.0 --port 3045; exec bash",
    },
    {
        "name": "agentic-ads-ui",
        "port": 3043,
        "window": "ads-ui",
        "cmd": f"cd {BASE}/ui && bun dev --port 3043; exec bash",
    },
]


def port_open(port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def restart_in_tmux(window: str, cmd: str) -> bool:
    """Open (or replace) a tmux window in Z-01 and run cmd."""
    # Kill existing window with same name if it exists
    subprocess.run(
        ["tmux", "kill-window", "-t", f"{TMUX_SESSION}:{window}"],
        capture_output=True,
    )
    result = subprocess.run(
        ["tmux", "new-window", "-t", TMUX_SESSION, "-n", window, cmd],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def main() -> None:
    print(f"[agentic-ads remediate] Starting at {time.strftime('%Y-%m-%dT%H:%M:%S')}")
    fixed = []
    already_up = []
    failed = []

    for svc in SERVICES:
        if port_open(svc["port"]):
            already_up.append(svc["name"])
            print(f"  ✓ {svc['name']} port {svc['port']} already up — skip")
            continue

        print(f"  ✗ {svc['name']} port {svc['port']} DOWN — restarting via tmux...")
        ok = restart_in_tmux(svc["window"], svc["cmd"])
        if ok:
            fixed.append(svc["name"])
            print(f"  → {svc['name']} restart dispatched (window: {svc['window']})")
        else:
            failed.append(svc["name"])
            print(f"  ✗ {svc['name']} tmux restart FAILED — will escalate")

    print(f"\n[agentic-ads remediate] Summary:")
    print(f"  Already up:  {already_up or 'none'}")
    print(f"  Restarted:   {fixed or 'none'}")
    print(f"  Failed:      {failed or 'none'}")

    if failed:
        sys.exit(1)  # Non-zero → Inspector escalates to Michael


main()
