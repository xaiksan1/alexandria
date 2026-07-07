#!/usr/bin/env python3
"""
ChapelXVI - Secure Communication & Protocol Vault
Part of the Alexandria Cyber-Gate
"""

import hashlib
import json
import logging
import time
from pathlib import Path

class ChapelXVIVault:
    """
    The 'Sanctuary' of the Cyber-Gate. 
    Manages secure keys, encrypted protocols, and high-level authorization.
    Operates on internal Port 6000.
    """
    
    def __init__(self):
        self.logger = logging.getLogger("ADAM.ChapelXVI")
        self.port = 6000
        self.is_sealed = True
        # Journal scellé append-only, chaîné par hash (mémoire immuable du gate).
        self._seal_log = Path.home() / ".chapel_xvi" / "sealed_records.jsonl"
        self._seal_log.parent.mkdir(parents=True, exist_ok=True)
        self._last_hash = self._load_last_hash()

    def _load_last_hash(self) -> str:
        if self._seal_log.exists():
            lines = self._seal_log.read_text(encoding="utf-8").strip().splitlines()
            if lines:
                return json.loads(lines[-1]).get("hash", "GENESIS")
        return "GENESIS"

    def seal_record(self, record: dict) -> dict:
        """Scelle un record dans le journal chaîné. Chaque entrée lie prev_hash -> hash."""
        entry = {"ts": time.time(), "prev_hash": self._last_hash, "record": record}
        digest = hashlib.sha256(
            (self._last_hash + json.dumps(record, sort_keys=True, default=str)).encode()
        ).hexdigest()
        entry["hash"] = digest
        with open(self._seal_log, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
        self._last_hash = digest
        return {"sealed": True, "hash": digest[:16] + "...", "prev_hash": entry["prev_hash"][:16] + "..."}

    def open_sanctuary(self, master_key: str):
        """Unseal the vault using the master key"""
        if master_key == "ALEXANDRIA_OMEGA":
            self.is_sealed = False
            self.logger.info("ChapelXVI Sanctuary UNSEALED.")
            return True
        return False

    def get_secure_protocol(self, protocol_id: str):
        """Retrieve an encrypted protocol definition"""
        if self.is_sealed:
            return {"error": "Vault is sealed"}
        return {"protocol": protocol_id, "encryption": "AES-256-GCM"}

    def get_module_status(self):
        return {
            "name": "ChapelXVI",
            "status": "SEALED" if self.is_sealed else "OPEN",
            "port": self.port,
            "security_level": "OMEGA"
        }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    vault = ChapelXVIVault()
    print(json.dumps(vault.get_module_status(), indent=2))
