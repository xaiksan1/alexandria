#!/usr/bin/env python3
"""
TARTARUS — Threat Containment & Quarantine Engine
Porta-Mundi module #12

The deep abyss. CRITICAL threats detected by Phoenix are automatically
sealed here — quarantine list, containment log, manual release control.
"""

import json
import logging
import threading
import time
import urllib.request
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

_PHOENIX_URL = "http://localhost:8000/events"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [TARTARUS] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("TARTARUS")


def _notify_phoenix(source: str, severity: str, category: str, message: str, data: dict = None) -> None:
    def _send():
        try:
            payload = json.dumps({
                "source": source, "severity": severity,
                "category": category, "message": message,
                "data": data or {},
            }).encode()
            req = urllib.request.Request(
                _PHOENIX_URL, data=payload,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


app = Flask(__name__)
CORS(app)

_quarantine: dict[str, dict] = {}
_lock = threading.Lock()
_seq = 0
_start_time = time.time()
_last_phoenix_id = 0


def _next_id() -> str:
    global _seq
    _seq += 1
    return f"QTN-{_seq:04d}"


def _seal(entity: str, reason: str, trigger_source: str = "manual", severity: str = "CRITICAL") -> dict:
    qid = _next_id()
    entry = {
        "id": qid,
        "entity": entity,
        "reason": reason,
        "trigger_source": trigger_source,
        "severity": severity,
        "sealed_at": datetime.now(timezone.utc).isoformat(),
        "released": False,
        "released_at": None,
    }
    with _lock:
        _quarantine[qid] = entry
    logger.warning("SEALED %s → %s | %s", entity, qid, reason[:70])
    _notify_phoenix(
        source="tartarus",
        severity="INFO",
        category="containment",
        message=f"Entity sealed in Tartarus — {entity}",
        data={"qid": qid, "reason": reason[:100], "trigger": trigger_source},
    )
    return entry


def _poll_phoenix() -> None:
    """Auto-seal CRITICAL events arriving from Phoenix."""
    global _last_phoenix_id
    while True:
        try:
            req = urllib.request.Request("http://localhost:8000/events?limit=50")
            with urllib.request.urlopen(req, timeout=5) as resp:
                events = json.loads(resp.read())
            if events:
                new_max = max(e["id"] for e in events)
                criticals = [
                    e for e in events
                    if e["id"] > _last_phoenix_id
                    and e["severity"] == "CRITICAL"
                    and e.get("source") != "tartarus"
                ]
                _last_phoenix_id = new_max
                for ev in criticals:
                    data = ev.get("data", {})
                    entity = (
                        data.get("user")
                        or data.get("ip")
                        or ev.get("source", "unknown")
                    )
                    _seal(
                        entity=str(entity),
                        reason=ev.get("message", "CRITICAL event"),
                        trigger_source=ev.get("source", "phoenix"),
                        severity="CRITICAL",
                    )
        except Exception:
            pass
        time.sleep(10)


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/status")
def status():
    with _lock:
        active = [e for e in _quarantine.values() if not e["released"]]
        total = len(_quarantine)
    return jsonify({
        "module": "TARTARUS",
        "status": "ACTIVE",
        "uptime_s": round(time.time() - _start_time),
        "sealed": len(active),
        "released": total - len(active),
        "total": total,
    })


@app.get("/quarantine")
def list_quarantine():
    include_released = request.args.get("released", "false").lower() == "true"
    with _lock:
        items = [
            e for e in _quarantine.values()
            if include_released or not e["released"]
        ]
    items.sort(key=lambda x: x["sealed_at"], reverse=True)
    return jsonify(items)


@app.post("/quarantine")
def add_quarantine():
    body = request.get_json(force=True, silent=True) or {}
    entity = (body.get("entity") or "").strip()
    reason = body.get("reason", "manual containment")
    if not entity:
        return jsonify({"error": "entity required"}), 400
    entry = _seal(entity, reason, trigger_source="manual")
    return jsonify(entry), 201


@app.delete("/quarantine/<qid>")
def release_quarantine(qid):
    with _lock:
        entry = _quarantine.get(qid)
        if not entry:
            return jsonify({"error": "not found"}), 404
        if entry["released"]:
            return jsonify({"error": "already released"}), 409
        entry["released"] = True
        entry["released_at"] = datetime.now(timezone.utc).isoformat()

    logger.info("RELEASED %s (%s)", entry["entity"], qid)
    _notify_phoenix(
        source="tartarus",
        severity="INFO",
        category="containment",
        message=f"Entity released from Tartarus — {entry['entity']}",
        data={"qid": qid, "entity": entry["entity"]},
    )
    return jsonify(entry)


if __name__ == "__main__":
    PORT = 4343
    threading.Thread(target=_poll_phoenix, daemon=True).start()
    _notify_phoenix(
        source="tartarus",
        severity="INFO",
        category="system",
        message="Tartarus Prison online — containment layer active",
        data={"port": PORT},
    )
    logger.info("TARTARUS online — port %d — polling Phoenix every 10s", PORT)
    app.run(host="127.0.0.1", port=PORT, debug=False)
