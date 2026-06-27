#!/usr/bin/env python3
"""
FLOATILLA — External Communication Network & Scout Relay
Porta-Mundi module #13

Alexandria's distributed intelligence bridge.
Scout outposts relay external intelligence through Porta-Mundi to ADAM.
"""

import json
import logging
import os
import threading
import time
import urllib.request
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

_PHOENIX_URL = "http://localhost:8000/events"
_PORTA_DIR = os.path.dirname(os.path.abspath(__file__))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [FLOATILLA] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("FLOATILLA")


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

_scouts: dict[str, dict] = {}
_relays: list[dict] = []
_lock = threading.Lock()
_start_time = time.time()


def _load_config() -> dict:
    path = os.path.join(_PORTA_DIR, "FLOATILLA.json")
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def _seed_scouts() -> None:
    """Populate registry from FLOATILLA_SCOUTS.json (non-TODO entries only)."""
    path = os.path.join(_PORTA_DIR, "FLOATILLA_SCOUTS.json")
    try:
        with open(path) as f:
            data = json.load(f)
        outposts = data.get("financial_intelligence_squad_outposts", {})
        for k, v in outposts.items():
            if "TODO" in str(v.get("status", "TODO")):
                continue
            sid = v.get("id", k)
            _scouts[sid] = {
                "id": sid,
                "name": v.get("name", sid),
                "location": v.get("location", "UNKNOWN"),
                "status": "registered",
                "last_relay": None,
                "relays_count": 0,
            }
    except Exception:
        pass


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/status")
def status():
    cfg = _load_config()
    with _lock:
        active = sum(1 for s in _scouts.values() if s["status"] == "active")
        total_scouts = len(_scouts)
        total_relays = len(_relays)
    return jsonify({
        "module": "FLOATILLA",
        "version": cfg.get("floatilla", {}).get("version", "1.0.0"),
        "status": "OPERATIONAL",
        "uptime_s": round(time.time() - _start_time),
        "scouts_total": total_scouts,
        "scouts_active": active,
        "relays_received": total_relays,
        "bridge": cfg.get("playlists", {}).get("main_bridge", {}).get("status", "UNKNOWN"),
    })


@app.get("/scouts")
def list_scouts():
    with _lock:
        return jsonify(list(_scouts.values()))


@app.post("/scouts/register")
def register_scout():
    body = request.get_json(force=True, silent=True) or {}
    sid = (body.get("id") or "").strip()
    name = body.get("name", sid)
    location = body.get("location", "UNKNOWN")
    if not sid:
        return jsonify({"error": "id required"}), 400

    entry = {
        "id": sid,
        "name": name,
        "location": location,
        "status": "registered",
        "last_relay": None,
        "relays_count": 0,
    }
    with _lock:
        _scouts[sid] = entry

    logger.info("Scout registered: %s @ %s", name, location)
    _notify_phoenix(
        source="floatilla",
        severity="INFO",
        category="scout",
        message=f"Scout registered — {name} @ {location}",
        data={"scout_id": sid, "location": location},
    )
    return jsonify(entry), 201


@app.post("/relay")
def relay():
    """Intelligence relay endpoint — scouts POST their data here."""
    body = request.get_json(force=True, silent=True) or {}
    sid = body.get("scout_id", "unknown")
    payload = body.get("payload", {})
    classification = body.get("classification", "INTEL")
    ts = datetime.now(timezone.utc).isoformat()

    entry = {
        "scout_id": sid,
        "classification": classification,
        "payload": payload,
        "ts": ts,
        "relay_ip": request.remote_addr,
    }

    with _lock:
        _relays.append(entry)
        if len(_relays) > 200:
            _relays.pop(0)
        if sid in _scouts:
            _scouts[sid]["status"] = "active"
            _scouts[sid]["last_relay"] = ts
            _scouts[sid]["relays_count"] = _scouts[sid].get("relays_count", 0) + 1

    logger.info("Relay from %s — %s", sid, classification)
    _notify_phoenix(
        source="floatilla",
        severity="INFO",
        category="intel",
        message=f"Intel relay received — {sid} [{classification}]",
        data={"scout_id": sid, "classification": classification},
    )
    return jsonify({"status": "relayed", "ts": ts})


@app.get("/relay")
def list_relays():
    limit = min(int(request.args.get("limit", 50)), 200)
    scout_filter = request.args.get("scout")
    with _lock:
        items = list(_relays)
    if scout_filter:
        items = [r for r in items if r["scout_id"] == scout_filter]
    return jsonify(items[-limit:][::-1])  # newest first


if __name__ == "__main__":
    PORT = 4242
    _seed_scouts()
    _notify_phoenix(
        source="floatilla",
        severity="INFO",
        category="system",
        message="Floatilla Bridge online — scout network operational",
        data={"port": PORT, "scouts_loaded": len(_scouts)},
    )
    logger.info("FLOATILLA online — port %d — %d scouts seeded", PORT, len(_scouts))
    app.run(host="0.0.0.0", port=PORT, debug=False)
