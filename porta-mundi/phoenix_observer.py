"""
PHOENIX — Observability & Threat Detection
Porta-Mundi module #2 · Flux position 1

Ingest threat events from all modules, detect patterns, expose metrics.
REST API on port 8000.
"""
import json
import logging
import queue
import time
import threading
from collections import deque
from datetime import datetime
from dataclasses import dataclass, asdict, field
from typing import Optional
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [PHOENIX] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("PHOENIX")

PORT = 8000
MAX_EVENTS = 500

app = Flask(__name__)
CORS(app)


@dataclass
class ThreatEvent:
    id: int
    ts: float
    source: str
    severity: str        # CRITICAL / HIGH / MEDIUM / LOW / INFO
    category: str        # auth / network / code / anomaly / probe
    message: str
    data: dict = field(default_factory=dict)

    @property
    def iso(self):
        return datetime.fromtimestamp(self.ts).isoformat()


class PhoenixObserver:
    def __init__(self):
        self._events: deque[ThreatEvent] = deque(maxlen=MAX_EVENTS)
        self._counter = 0
        self._lock = threading.Lock()
        self._start_time = time.time()
        self._counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        self._subscribers: set[queue.Queue] = set()
        logger.info("Phoenix Observer initialized — watching for threats")

    def ingest(self, source: str, severity: str, category: str, message: str,
               data: Optional[dict] = None) -> ThreatEvent:
        severity = severity.upper()
        if severity not in self._counts:
            severity = "INFO"
        with self._lock:
            self._counter += 1
            ev = ThreatEvent(
                id=self._counter, ts=time.time(),
                source=source, severity=severity,
                category=category, message=message,
                data=data or {},
            )
            self._events.append(ev)
            self._counts[severity] += 1
        if severity in ("CRITICAL", "HIGH"):
            logger.warning("[%s] %s — %s", source, severity, message)
        else:
            logger.info("[%s] %s — %s", source, severity, message)

        ev_dict = {"id": ev.id, "ts": ev.iso, "source": ev.source,
                   "severity": ev.severity, "category": ev.category,
                   "message": ev.message, "data": ev.data}
        with self._lock:
            subs = list(self._subscribers)
        for q in subs:
            try:
                q.put_nowait(ev_dict)
            except queue.Full:
                pass

        return ev

    def subscribe(self) -> queue.Queue:
        q: queue.Queue = queue.Queue(maxsize=200)
        with self._lock:
            self._subscribers.add(q)
        return q

    def unsubscribe(self, q: queue.Queue) -> None:
        with self._lock:
            self._subscribers.discard(q)

    def recent(self, limit: int = 50, severity: Optional[str] = None) -> list[dict]:
        with self._lock:
            events = list(self._events)
        if severity:
            events = [e for e in events if e.severity == severity.upper()]
        return [
            {"id": e.id, "ts": e.iso, "source": e.source,
             "severity": e.severity, "category": e.category,
             "message": e.message, "data": e.data}
            for e in events[-limit:]
        ]

    def metrics_text(self) -> str:
        uptime = time.time() - self._start_time
        with self._lock:
            total = sum(self._counts.values())
            counts = dict(self._counts)
        lines = [
            "# HELP phoenix_events_total Total threat events ingested",
            "# TYPE phoenix_events_total counter",
            f'phoenix_events_total {total}',
            "# HELP phoenix_uptime_seconds Uptime in seconds",
            "# TYPE phoenix_uptime_seconds gauge",
            f'phoenix_uptime_seconds {uptime:.1f}',
        ]
        for sev, cnt in counts.items():
            lines.append(
                f'phoenix_events_by_severity{{severity="{sev}"}} {cnt}'
            )
        return "\n".join(lines) + "\n"

    def status(self) -> dict:
        with self._lock:
            total = sum(self._counts.values())
            counts = dict(self._counts)
        return {
            "module": "PHOENIX", "role": "Observability",
            "status": "ONLINE", "port": PORT,
            "uptime_s": round(time.time() - self._start_time, 1),
            "events_total": total,
            "events_by_severity": counts,
            "buffer_size": len(self._events),
            "buffer_max": MAX_EVENTS,
        }


observer = PhoenixObserver()


@app.get("/health")
def health():
    return jsonify({"status": "ok", "module": "PHOENIX", "port": PORT})


@app.get("/status")
def status():
    return jsonify(observer.status())


@app.post("/events")
def ingest_event():
    body = request.get_json(force=True, silent=True) or {}
    source = body.get("source", "unknown")
    severity = body.get("severity", "INFO")
    category = body.get("category", "generic")
    message = body.get("message", "")
    data = body.get("data", {})
    if not message:
        return jsonify({"error": "message required"}), 400
    ev = observer.ingest(source, severity, category, message, data)
    return jsonify({"id": ev.id, "ts": ev.iso, "status": "ingested"}), 201


@app.get("/events")
def get_events():
    limit = min(int(request.args.get("limit", 50)), MAX_EVENTS)
    severity = request.args.get("severity")
    return jsonify(observer.recent(limit, severity))


@app.get("/metrics")
def metrics():
    return Response(observer.metrics_text(), mimetype="text/plain")


@app.get("/events/stream")
def events_stream():
    """SSE endpoint — pushes events to connected clients in real-time."""
    q = observer.subscribe()

    def generate():
        try:
            # Replay last 30 events on connect so the UI isn't empty
            for ev in observer.recent(30):
                yield f"data: {json.dumps(ev)}\n\n"
            while True:
                try:
                    ev = q.get(timeout=25)
                    yield f"data: {json.dumps(ev)}\n\n"
                except queue.Empty:
                    yield ": ping\n\n"   # keepalive so the connection stays open
        except GeneratorExit:
            observer.unsubscribe(q)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


def get_module_status() -> dict:
    return observer.status()


if __name__ == "__main__":
    logger.info("PHOENIX igniting on port %d", PORT)
    observer.ingest("phoenix", "INFO", "system", "Phoenix Observer online — threat surveillance active")
    app.run(host="127.0.0.1", port=PORT, debug=False)
