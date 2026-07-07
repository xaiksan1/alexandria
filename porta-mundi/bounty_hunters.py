#!/usr/bin/env python3
"""
Bounty Hunters - Threat Tracking & Counter-Intelligence
Part of the Alexandria Cyber-Gate (module du flux: AEGIS -> Bounty Hunters -> Chapel XVI)

Défensif / white-hat : maintient un registre des indicateurs de compromission (IOC)
observés, ouvre des "primes" de suivi, corrèle les menaces récurrentes. Aucune action
offensive / hack-back — uniquement traçage, corrélation et signalement.
"""
import json
import logging
import threading
import time
import urllib.request

_PHOENIX_URL = "http://localhost:8000/events"


def _notify_phoenix(source, severity, category, message, data=None):
    def _send():
        try:
            payload = json.dumps({"source": source, "severity": severity,
                                  "category": category, "message": message,
                                  "data": data or {}}).encode()
            req = urllib.request.Request(_PHOENIX_URL, data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


class BountyHunters:
    """Traqueurs — registre d'IOC et corrélation défensive des menaces récurrentes."""

    def __init__(self):
        self.logger = logging.getLogger("ADAM.BountyHunters")
        self.bounties = {}   # ioc -> {count, first_seen, last_seen, severity, status}

    def track_ioc(self, ioc: str, severity: str = "LOW", context: dict | None = None) -> dict:
        """Enregistre/incrémente un indicateur de compromission (IP, hash, domaine)."""
        now = time.time()
        entry = self.bounties.get(ioc)
        if entry:
            entry["count"] += 1
            entry["last_seen"] = now
            if entry["count"] >= 3 and entry["status"] == "watch":
                entry["status"] = "bounty_open"   # menace récurrente -> prime ouverte
                _notify_phoenix("bounty_hunters", severity, "counter_intel",
                                f"prime ouverte sur IOC récurrent: {ioc} (x{entry['count']})",
                                {"ioc": ioc, "count": entry["count"]})
        else:
            entry = {"ioc": ioc, "count": 1, "first_seen": now, "last_seen": now,
                     "severity": severity, "status": "watch", "context": context or {}}
            self.bounties[ioc] = entry
        return dict(entry)

    def open_bounty(self, ioc: str, reason: str) -> dict:
        """Ouvre explicitement une prime de suivi sur un IOC (traçage renforcé)."""
        entry = self.bounties.setdefault(
            ioc, {"ioc": ioc, "count": 1, "first_seen": time.time(),
                  "last_seen": time.time(), "severity": "HIGH", "status": "watch", "context": {}})
        entry["status"] = "bounty_open"
        entry["reason"] = reason
        _notify_phoenix("bounty_hunters", "HIGH", "counter_intel",
                        f"prime ouverte: {ioc} — {reason}", {"ioc": ioc})
        return dict(entry)

    def list_bounties(self, status: str | None = None) -> list:
        vals = list(self.bounties.values())
        return [b for b in vals if status is None or b["status"] == status]

    def get_module_status(self):
        open_count = sum(1 for b in self.bounties.values() if b["status"] == "bounty_open")
        return {"name": "Bounty Hunters", "status": "HUNTING", "mode": "counter_intel",
                "tracked_iocs": len(self.bounties), "open_bounties": open_count}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    bh = BountyHunters()
    for _ in range(3):
        bh.track_ioc("192.0.2.66", "HIGH", {"note": "scan répété"})
    print(json.dumps(bh.list_bounties("bounty_open"), indent=2, default=str))
    print(json.dumps(bh.get_module_status(), indent=2))
