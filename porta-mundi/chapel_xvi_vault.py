#!/usr/bin/env python3
"""
ChapelXVI - Secure Communication & Protocol Vault
Part of the Alexandria Cyber-Gate

Deux moitiés :
- le journal scellé (ici) : mémoire immuable du gate, chaque entrée chaînée par hash ;
- le Sanctuaire des clés (chapel_xvi_sanctuary.py + chapel_xvi_server.py, port 6000),
  qui garde les secrets d'Alexandria et se rouvre seul avec 2 morceaux sur 3.
"""

import fcntl
import hashlib
import json
import logging
import os
import time
import urllib.request
from pathlib import Path

SANCTUARY_URL = "http://127.0.0.1:6000"
SEAL_LOG = Path.home() / ".chapel_xvi" / "sealed_records.jsonl"


class ChapelXVIVault:
    """
    The 'Sanctuary' of the Cyber-Gate.
    Journal scellé + état du Sanctuaire des clés (service sur le port interne 6000).
    """

    def __init__(self, seal_log: Path = SEAL_LOG):
        self.logger = logging.getLogger("ADAM.ChapelXVI")
        self.port = 6000
        # Journal scellé append-only, chaîné par hash (mémoire immuable du gate).
        # Plusieurs process y écrivent (cyber-gate, sanctuaire) : le dernier hash est
        # relu sous verrou à chaque scellé pour que la chaîne ne casse jamais.
        self._seal_log = seal_log
        self._seal_log.parent.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _last_hash_of(f) -> str:
        f.seek(0)
        last = "GENESIS"
        for line in f:
            line = line.strip()
            if line:
                last = json.loads(line).get("hash", last)
        return last

    def _reparer_queue(self, f) -> int:
        """Retire une fin de journal abîmée par une coupure brutale ; retourne les octets retirés.

        Une coupure de courant pendant un scellé laisse une dernière ligne faite d'octets
        nuls (la place était réservée sur le disque, les données jamais écrites) ou coupée
        net. Seule la QUEUE est concernée : on la déplace, intacte, dans
        sealed_records.residus (rien n'est effacé en silence) ; les lignes valides restent.
        """
        f.seek(0)
        brut = f.buffer.read()
        lignes = brut.split(b"\n")
        # dernière ligne valide en partant de la fin (les octets nuls ne sont pas du JSON)
        dernier = -1
        for k in range(len(lignes) - 1, -1, -1):
            if lignes[k].strip():
                try:
                    json.loads(lignes[k])
                    dernier = k
                    break
                except ValueError:
                    continue
        garder = len(b"\n".join(lignes[: dernier + 1])) + (1 if dernier >= 0 else 0)
        retire = brut[garder:]
        if retire.strip(b"\n\r\t "):
            with open(self._seal_log.with_suffix(".residus"), "ab") as r:
                r.write(f"--- {time.strftime('%Y-%m-%dT%H:%M:%S')} ({len(retire)} octets)\n".encode()
                        + retire + b"\n")
            f.truncate(garder)
            return len(retire)
        return 0

    def seal_record(self, record: dict) -> dict:
        """Scelle un record dans le journal chaîné. Chaque entrée lie prev_hash -> hash.

        Chaque scellé est forcé sur le disque (fsync) avant de rendre la main : après une
        coupure brutale, un scellé annoncé est un scellé écrit.
        """
        with open(self._seal_log, "a+", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            try:
                retire = self._reparer_queue(f)
                if retire:
                    self._ecrire(f, {"event": "journal.reparation", "octets_retires": retire,
                                     "cause": "fin de journal abîmée par une coupure brutale",
                                     "residus": str(self._seal_log.with_suffix(".residus"))})
                digest, prev = self._ecrire(f, record)
            finally:
                fcntl.flock(f, fcntl.LOCK_UN)
        return {"sealed": True, "hash": digest[:16] + "...", "prev_hash": prev[:16] + "..."}

    def _ecrire(self, f, record: dict) -> tuple[str, str]:
        prev = self._last_hash_of(f)
        entry = {"ts": time.time(), "prev_hash": prev, "record": record}
        digest = hashlib.sha256(
            (prev + json.dumps(record, sort_keys=True, default=str)).encode()
        ).hexdigest()
        entry["hash"] = digest
        f.seek(0, 2)
        f.write(json.dumps(entry, default=str) + "\n")
        f.flush()
        os.fsync(f.fileno())
        return digest, prev

    def verify_chain(self) -> dict:
        """Recalcule toute la chaîne : dit si une entrée a été modifiée ou retirée."""
        prev = "GENESIS"
        count = 0
        if not self._seal_log.exists():
            return {"intact": True, "entries": 0}
        with open(self._seal_log, encoding="utf-8") as f:
            for n, line in enumerate(f, 1):
                if not line.strip():
                    continue
                entry = json.loads(line)
                expected = hashlib.sha256(
                    (prev + json.dumps(entry["record"], sort_keys=True, default=str)).encode()
                ).hexdigest()
                if entry.get("prev_hash") != prev or entry.get("hash") != expected:
                    return {"intact": False, "entries": count, "broken_at_line": n}
                prev = entry["hash"]
                count += 1
        return {"intact": True, "entries": count}

    def sanctuary_status(self) -> dict:
        """État du Sanctuaire des clés (jamais de secret dans la réponse)."""
        try:
            with urllib.request.urlopen(f"{SANCTUARY_URL}/health", timeout=2) as r:
                return json.loads(r.read())
        except Exception:
            return {"sanctuary": "INJOIGNABLE"}

    def get_module_status(self):
        state = self.sanctuary_status().get("sanctuary", "INJOIGNABLE")
        return {
            "name": "ChapelXVI",
            "status": state,
            "port": self.port,
            "security_level": "OMEGA",
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vault = ChapelXVIVault()
    print(json.dumps({**vault.get_module_status(), "journal": vault.verify_chain()}, indent=2))
