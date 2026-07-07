#!/usr/bin/env python3
"""
Sentinelle - AI Threat Analysis & Classification
Part of the Alexandria Cyber-Gate (module du flux: Phoenix -> Sentinelle -> Paint Shop)

Défensif / white-hat : analyse les événements collectés par Phoenix, classe la menace
(sévérité + catégorie + score), recommande une action. Ne mène aucune action offensive.
"""
import json
import logging
import threading
import urllib.request

_PHOENIX_URL = "http://localhost:8000/events"

# Signatures défensives connues -> catégorie de menace (détection, pas exploitation).
THREAT_SIGNATURES = {
    "sql injection": "injection", "union select": "injection", "' or '1'='1": "injection",
    "../": "path_traversal", "etc/passwd": "path_traversal",
    "<script": "xss", "javascript:": "xss", "onerror=": "xss",
    "ddos": "dos", "syn flood": "dos", "amplification": "dos",
    "brute force": "credential", "password spray": "credential",
    "nmap": "recon", "masscan": "recon", "shodan": "recon",
    "ransomware": "malware", "c2": "malware", "reverse shell": "malware",
}
SEVERITY_WEIGHT = {"injection": "HIGH", "malware": "CRITICAL", "dos": "HIGH",
                   "path_traversal": "MEDIUM", "xss": "MEDIUM",
                   "credential": "HIGH", "recon": "LOW"}


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


class Sentinelle:
    """Gardien analytique — classe les menaces observées et recommande une réponse."""

    def __init__(self):
        self.logger = logging.getLogger("ADAM.Sentinelle")
        self.analyzed = 0
        self.threats_found = 0

    def analyze_threat(self, event: dict) -> dict:
        """Analyse un événement (dict libre). Retourne une évaluation de menace."""
        self.analyzed += 1
        blob = json.dumps(event).lower()
        hits = {cat for sig, cat in THREAT_SIGNATURES.items() if sig in blob}

        if not hits:
            return {"threat": False, "severity": "NONE", "categories": [],
                    "score": 0.0, "recommended_action": "allow"}

        self.threats_found += 1
        severities = [SEVERITY_WEIGHT.get(c, "LOW") for c in hits]
        rank = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        top = max(severities, key=lambda s: rank[s])
        score = round(min(1.0, rank[top] / 4 + 0.1 * (len(hits) - 1)), 3)
        action = "quarantine" if top in ("HIGH", "CRITICAL") else "monitor"

        assessment = {"threat": True, "severity": top, "categories": sorted(hits),
                      "score": score, "recommended_action": action}
        _notify_phoenix("sentinelle", top, "threat_analysis",
                        f"menace détectée: {', '.join(sorted(hits))} -> {action}",
                        assessment)
        self.logger.warning("Menace %s: %s -> %s", top, sorted(hits), action)
        return assessment

    def get_module_status(self):
        return {"name": "Sentinelle", "status": "WATCHING", "mode": "ai_threat_analysis",
                "analyzed": self.analyzed, "threats_found": self.threats_found}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    s = Sentinelle()
    print(json.dumps(s.analyze_threat({"payload": "GET /admin?q=' UNION SELECT * FROM users"}), indent=2))
    print(json.dumps(s.analyze_threat({"payload": "GET /index.html"}), indent=2))
    print(json.dumps(s.get_module_status(), indent=2))
