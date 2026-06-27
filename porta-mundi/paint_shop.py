#!/usr/bin/env python3
"""
PAINT SHOP — Threat Enrichment & Response Renderer
Porta-Mundi module #14 · Threat Flux position 3

Threat → Phoenix → Sentinelle → [PAINT SHOP] → AEGIS → Bounty Hunters → Chapel XVI

Takes raw threat events from Phoenix, enriches them with a threat score,
action tag, and response directive, then renders them action-ready for AEGIS.
Also tracks every render as a pixel-watermark for pipeline traceability.
"""

import hashlib
import json
import logging
import threading
import time
import urllib.request
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

_PHOENIX_URL = "http://localhost:8000/events"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PAINT-SHOP] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PAINT_SHOP")


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

_renders: list[dict] = []
_lock = threading.Lock()
_start_time = time.time()
_last_phoenix_id = 0
_counters = {"total": 0, "by_action": {"SEAL": 0, "SHIELD": 0, "MONITOR": 0, "LOG": 0}}

# ── Enrichment logic ─────────────────────────────────────────────────────────

_SEVERITY_SCORE = {"CRITICAL": 100, "HIGH": 75, "MEDIUM": 50, "LOW": 25, "INFO": 0}

_CATEGORY_VECTOR = {
    "access_control": "INTRUSION",
    "white_hat":      "POLICY",
    "rate_limit":     "FLOOD",
    "honeypot":       "RECON",
    "deception":      "TRAP",
    "containment":    "QUARANTINE",
    "oracle":         "INTELLIGENCE",
    "intel":          "EXFIL",
    "scout":          "NETWORK",
    "system":         "INFRA",
    "test":           "TEST",
}

_ACTION_MATRIX = {
    # (severity_score, vector) → action
    100: "SEAL",    # CRITICAL → Tartarus
    75:  "SHIELD",  # HIGH → AEGIS
    50:  "MONITOR", # MEDIUM → Sentinelle loop
    25:  "LOG",     # LOW → Chapel XVI
    0:   "LOG",     # INFO → Chapel XVI
}


def _score(severity: str) -> int:
    return _SEVERITY_SCORE.get(severity.upper(), 0)


def _action(score: int) -> str:
    if score >= 100: return "SEAL"
    if score >= 75:  return "SHIELD"
    if score >= 50:  return "MONITOR"
    return "LOG"


def _watermark(event_id, source, ts) -> str:
    raw = f"{event_id}:{source}:{ts}"
    return "PS-" + hashlib.sha1(raw.encode()).hexdigest()[:10].upper()


def _render_event(ev: dict) -> dict:
    severity = ev.get("severity", "INFO")
    source = ev.get("source", "unknown")
    category = ev.get("category", "system")
    message = ev.get("message", "")
    ts = ev.get("ts", datetime.now(timezone.utc).isoformat())
    event_id = ev.get("id", 0)

    score = _score(severity)
    vector = _CATEGORY_VECTOR.get(category, "UNKNOWN")
    action = _action(score)
    wm = _watermark(event_id, source, ts)

    rendered = {
        "watermark":    wm,
        "event_id":     event_id,
        "source":       source,
        "severity":     severity,
        "threat_score": score,
        "vector":       vector,
        "action":       action,
        "directive":    _directive(action, source, message),
        "message":      message,
        "category":     category,
        "rendered_at":  datetime.now(timezone.utc).isoformat(),
    }

    with _lock:
        _renders.append(rendered)
        if len(_renders) > 500:
            _renders.pop(0)
        _counters["total"] += 1
        _counters["by_action"][action] = _counters["by_action"].get(action, 0) + 1

    logger.info("[%s] score=%d action=%s wm=%s — %s", severity, score, action, wm, message[:60])
    _notify_phoenix(
        source="paint-shop",
        severity="INFO",
        category="render",
        message=f"Threat rendered [{action}] — {source} score={score}",
        data={"watermark": wm, "action": action, "score": score, "vector": vector},
    )
    return rendered


def _directive(action: str, source: str, message: str) -> str:
    directives = {
        "SEAL":    f"→ TARTARUS: quarantine entity from {source}. Freeze access, log sealed entry.",
        "SHIELD":  f"→ AEGIS: activate defensive shielding against {source}. Reinforce perimeter.",
        "MONITOR": f"→ SENTINELLE: flag {source} for enhanced monitoring. Raise watch level.",
        "LOG":     f"→ CHAPEL XVI: archive event. Encrypt and seal in vault.",
    }
    return directives.get(action, "→ LOG: record event.")


# ── Background: auto-render HIGH/CRITICAL Phoenix events ─────────────────────

def _poll_and_render() -> None:
    global _last_phoenix_id
    time.sleep(5)  # let Phoenix stabilize first
    while True:
        try:
            req = urllib.request.Request("http://localhost:8000/events?limit=50")
            with urllib.request.urlopen(req, timeout=5) as resp:
                events = json.loads(resp.read())
            if events:
                new_max = max(e["id"] for e in events)
                to_render = [
                    e for e in events
                    if e["id"] > _last_phoenix_id
                    and e.get("source") not in ("paint-shop", "tartarus")
                    and _score(e.get("severity", "INFO")) >= 75
                ]
                _last_phoenix_id = new_max
                for ev in to_render:
                    _render_event(ev)
        except Exception:
            pass
        time.sleep(8)


# ── API ───────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/status")
def status():
    with _lock:
        total = _counters["total"]
        by_action = dict(_counters["by_action"])
    return jsonify({
        "module":     "PAINT SHOP",
        "role":       "Threat Enrichment & Response Renderer",
        "flux":       3,
        "status":     "RENDERING",
        "uptime_s":   round(time.time() - _start_time),
        "renders":    total,
        "by_action":  by_action,
    })


@app.post("/render")
def render_endpoint():
    """Manually render a threat event."""
    body = request.get_json(force=True, silent=True) or {}
    if not body:
        return jsonify({"error": "event body required"}), 400
    rendered = _render_event(body)
    return jsonify(rendered), 201


@app.get("/renders")
def list_renders():
    limit = min(int(request.args.get("limit", 50)), 500)
    action_filter = request.args.get("action", "").upper()
    with _lock:
        items = list(_renders)
    if action_filter:
        items = [r for r in items if r["action"] == action_filter]
    return jsonify(items[-limit:][::-1])  # newest first


@app.get("/metrics")
def metrics():
    with _lock:
        total = _counters["total"]
        by_action = dict(_counters["by_action"])
    lines = [
        "# HELP paint_shop_renders_total Total threat events rendered",
        "# TYPE paint_shop_renders_total counter",
        f"paint_shop_renders_total {total}",
    ]
    for action, count in by_action.items():
        lines.append(f'paint_shop_renders_by_action{{action="{action}"}} {count}')
    lines.append(f"paint_shop_uptime_seconds {round(time.time() - _start_time)}")
    return Response("\n".join(lines) + "\n", mimetype="text/plain")


if __name__ == "__main__":
    PORT = 4141
    threading.Thread(target=_poll_and_render, daemon=True).start()
    _notify_phoenix(
        source="paint-shop",
        severity="INFO",
        category="system",
        message="Paint Shop online — threat enrichment pipeline active",
        data={"port": PORT, "flux_position": 3},
    )
    logger.info("PAINT SHOP online — port %d — flux position 3", PORT)
    app.run(host="0.0.0.0", port=PORT, debug=False)
