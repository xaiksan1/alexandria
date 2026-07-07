#!/usr/bin/env python3
"""
NMAP Scanner - Real-Time Defensive Network Reconnaissance
Part of the Alexandria Cyber-Gate (11e module de défense)

Défensif / white-hat STRICT : scanne uniquement le RÉSEAU LOCAL de l'Architecte
(plages privées RFC1918 + localhost). Toute cible publique est REFUSÉE. But : voir
en temps réel les hôtes/ports ouverts sur son propre réseau pour fermer les portes.
"""
import ipaddress
import json
import logging
import threading
import urllib.request

import nmap

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


def _is_private_target(target: str) -> bool:
    """White-hat guard : n'autorise que localhost et les plages privées RFC1918."""
    host = target.split("/")[0]
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_private or ip.is_loopback
    except ValueError:
        # nom d'hôte : on n'autorise que localhost explicite
        return host in ("localhost", "127.0.0.1", "::1")


class NmapScanner:
    """Scanner nmap défensif — réseau interne uniquement, jamais de cible publique."""

    def __init__(self):
        self.logger = logging.getLogger("ADAM.NmapScanner")
        self.scans_run = 0
        self._nm = nmap.PortScanner()

    def scan(self, target: str = "127.0.0.1", ports: str = "1-1024", ping_sweep: bool = False) -> dict:
        if not _is_private_target(target):
            _notify_phoenix("nmap_scanner", "HIGH", "policy_block",
                            f"scan REFUSÉ (cible non privée): {target}", {"target": target})
            return {"error": "refused", "reason": "white-hat: cible hors réseau privé/local",
                    "target": target}

        args = "-sn" if ping_sweep else "-sT --open"
        self.logger.info("Scan défensif %s (%s)", target, args)
        try:
            self._nm.scan(hosts=target, ports=None if ping_sweep else ports, arguments=args)
        except Exception as e:
            return {"error": str(e), "target": target}

        self.scans_run += 1
        hosts = []
        for host in self._nm.all_hosts():
            open_ports = []
            if not ping_sweep:
                for proto in self._nm[host].all_protocols():
                    for p in sorted(self._nm[host][proto].keys()):
                        if self._nm[host][proto][p]["state"] == "open":
                            open_ports.append(p)
            hosts.append({"host": host, "state": self._nm[host].state(), "open_ports": open_ports})

        result = {"target": target, "mode": "ping_sweep" if ping_sweep else "port_scan",
                  "hosts_up": len(hosts), "hosts": hosts}
        _notify_phoenix("nmap_scanner", "INFO", "network_recon",
                        f"scan interne {target}: {len(hosts)} hôte(s)",
                        {"hosts_up": len(hosts)})
        return result

    def get_module_status(self):
        return {"name": "NMAP Scanner", "status": "SCANNING", "mode": "defensive_internal_only",
                "scans_run": self.scans_run, "policy": "RFC1918 + localhost only"}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sc = NmapScanner()
    print(json.dumps(sc.scan("127.0.0.1", ports="1-1000"), indent=2))
    print("public refusé:", json.dumps(sc.scan("8.8.8.8")))
    print(json.dumps(sc.get_module_status(), indent=2))
