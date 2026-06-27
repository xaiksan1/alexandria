#!/usr/bin/env python3
"""
Minotaure - Dynamic Network Labyrinth & Honeypot Generator
Part of the Alexandria Cyber-Gate
"""

import json
import logging
import random
import threading
import urllib.request

_PHOENIX_URL = "http://localhost:8000/events"


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

class MinotaureGatekeeper:
    """
    Protects the Cyber-Gate by creating a dynamic 'Labyrinth' of 
    virtual network paths and honeypots to confuse attackers.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ADAM.Minotaure")
        self.active_honeypots = []

    def generate_labyrinth(self, complexity: int = 5):
        """Generate a complex set of virtual routes"""
        self.logger.info(f"Generating network labyrinth with complexity {complexity}...")
        self.active_honeypots = [f"honeypot_{i}" for i in range(complexity)]
        _notify_phoenix(
            source="minotaure",
            severity="INFO",
            category="deception",
            message=f"Labyrinth activated — {complexity} honeypot nodes deployed",
            data={"nodes": self.active_honeypots, "complexity": complexity},
        )
        return {"status": "labyrinth_active", "nodes": len(self.active_honeypots)}

    def challenge_intruder(self, ip_address: str):
        """Issue a cryptographic challenge to a suspicious IP"""
        self.logger.warning(f"Challenging intruder at {ip_address}...")
        challenge_id = random.randint(1000, 9999)
        _notify_phoenix(
            source="minotaure",
            severity="MEDIUM",
            category="honeypot",
            message=f"Intruder challenged — {ip_address} → puzzle #{challenge_id}",
            data={"ip": ip_address, "challenge_id": challenge_id, "type": "recursive_puzzle"},
        )
        return {"challenge_id": challenge_id, "type": "recursive_puzzle"}

    def get_module_status(self):
        return {
            "name": "Minotaure",
            "status": "GUARDING",
            "labyrinth_depth": len(self.active_honeypots),
            "mode": "active_deception"
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    gate = MinotaureGatekeeper()
    gate.generate_labyrinth()
    print(json.dumps(gate.get_module_status(), indent=2))
