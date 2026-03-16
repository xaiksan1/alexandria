"""
Pinchtab caller — wraps @ADAM/pinchtab CLI for direct browser actions.
Non-blocking: if pinchtab is down, actions are queued in action_queue.json.
Layers 1-3 are unaffected by pinchtab availability.
"""
import json
import logging
import os
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)
QUEUE_PATH = Path(__file__).parent / "action_queue.json"
PINCHTAB_PATH = Path("/home/ichigo/alexandria/ADAM/pinchtab")


def call(action: str, url: str, **kwargs) -> bool:
    """Execute a pinchtab browser action.

    Returns True on success, False on failure (action queued for retry).
    """
    if not (PINCHTAB_PATH / "install.sh").exists():
        logger.warning("Pinchtab not found — queuing action")
        _enqueue(action, url, kwargs)
        return False

    try:
        result = subprocess.run(
            ["pinchtab", "action", action, "--url", url],
            capture_output=True, text=True, timeout=30,
            cwd=str(PINCHTAB_PATH),
        )
        if result.returncode == 0:
            return True
        logger.warning(f"Pinchtab action failed: {result.stderr}")
        _enqueue(action, url, kwargs)
        return False
    except Exception as e:
        logger.warning(f"Pinchtab call error: {e}")
        _enqueue(action, url, kwargs)
        return False


def _enqueue(action: str, url: str, kwargs: dict) -> None:
    """Atomic append to action_queue.json."""
    data = _load_queue()
    data["pending"].append({
        "action": action,
        "url": url,
        "kwargs": kwargs,
        "queued_at": time.time(),
    })
    _atomic_write(data)


def _load_queue() -> dict:
    if QUEUE_PATH.exists():
        try:
            return json.loads(QUEUE_PATH.read_text())
        except Exception:
            pass
    return {"pending": []}


def _atomic_write(data: dict) -> None:
    tmp = QUEUE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2))
    os.replace(tmp, QUEUE_PATH)
