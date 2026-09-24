#!/usr/bin/env python3
"""
Contrôle de la mémoire au démarrage — Porta-Mundi
Tourne UNE fois par démarrage (pm2, autorestart: false), puis s'arrête : aucun poids.

La carte mère remet parfois seulement 8 Go sur 16 au démarrage (vu du 10 au
20 septembre, puis le 24), et rien ne le signale : pm2 n'affiche que la mémoire
vive, et la différence part en silence dans le swap. Ce contrôle :
- lit la mémoire que Linux a reçue et la compare aux 16 Go attendus ;
- note comment le démarrage précédent s'est terminé (arrêt propre ou coupure) ;
- ajoute une ligne à ADAM/logs/memoire-par-demarrage.log ;
- prévient Phoenix (HIGH si la mémoire manque, INFO sinon — échelle de Phoenix : CRITICAL/HIGH/MEDIUM/LOW/INFO).
"""

import json
import re
import subprocess
import time
import urllib.request
from datetime import datetime
from pathlib import Path

EXPECTED_GB = 16
TOLERANCE_GB = 1.5  # le noyau et le micrologiciel se réservent toujours un peu
LOG = Path("/home/ichigo/alexandria/ADAM/logs/memoire-par-demarrage.log")
PHOENIX_URL = "http://localhost:8000/events"


def total_gb() -> float:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) / 1048576
    raise RuntimeError("MemTotal absent de /proc/meminfo")


def previous_boot_ending() -> str:
    out = subprocess.run(["journalctl", "-b", "-1", "--no-pager", "-q", "-n", "400"],
                         capture_output=True, text=True).stdout
    if not out.strip():
        return "inconnu"
    if re.search(r"systemd-shutdown|Reached target .*(Power-Off|Reboot|Shutdown|System Power Off|System Reboot)", out):
        return "arrêt propre"
    return "coupure (plantage)"


def notify_phoenix(severity: str, message: str, data: dict) -> bool:
    payload = json.dumps({"source": "memory-boot-check", "severity": severity,
                          "category": "hardware", "message": message, "data": data}).encode()
    for _ in range(24):  # Phoenix démarre en même temps : on lui laisse 2 minutes
        try:
            req = urllib.request.Request(PHOENIX_URL, data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=3)
            return True
        except Exception:
            time.sleep(5)
    return False


def main() -> None:
    gb = total_gb()
    ok = gb >= EXPECTED_GB - TOLERANCE_GB
    prev = previous_boot_ending()
    line = (f"{datetime.now():%Y-%m-%d %H:%M} | mémoire {gb:.1f} Go sur {EXPECTED_GB} attendus | "
            f"{'OK' if ok else 'MANQUE'} | démarrage précédent : {prev}")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
    print(line)
    if ok:
        message = f"Mémoire complète au démarrage : {gb:.1f} Go"
    else:
        message = (f"La carte mère n'a remis que {gb:.1f} Go sur {EXPECTED_GB} au démarrage "
                   f"(démarrage précédent : {prev})")
    sent = notify_phoenix("INFO" if ok else "HIGH", message,
                          {"total_gb": round(gb, 1), "expected_gb": EXPECTED_GB, "previous_boot": prev})
    print("Phoenix prévenu" if sent else "Phoenix injoignable")


if __name__ == "__main__":
    main()
