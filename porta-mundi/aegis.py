#!/usr/bin/env python3
"""
Aegis - Cryptographic Defense & Signing
Part of the Alexandria Cyber-Gate (module du flux: Paint Shop -> AEGIS -> Bounty Hunters)

Défensif / white-hat : signe et vérifie les artefacts (preuves forensiques, SealedBatch
d'energon), co-signe avec AKER/KHEPER/EVE. Ed25519. Ne détient aucune clé de wallet ;
la clé de signature est locale et éphémère (ou persistée hors du repo).
"""
import json
import logging
import threading
import urllib.request
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives import serialization

_PHOENIX_URL = "http://localhost:8000/events"
_KEY_PATH = Path.home() / ".aegis" / "aegis_ed25519.key"


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


class Aegis:
    """Bouclier cryptographique — signe/vérifie les artefacts défensifs (Ed25519)."""

    def __init__(self):
        self.logger = logging.getLogger("ADAM.Aegis")
        self._key = self._load_or_create_key()
        self.signatures = 0

    def _load_or_create_key(self) -> Ed25519PrivateKey:
        # Clé de signature défensive locale, hors du repo (~/.aegis, 0600).
        if _KEY_PATH.exists():
            return serialization.load_pem_private_key(_KEY_PATH.read_bytes(), password=None)
        key = Ed25519PrivateKey.generate()
        _KEY_PATH.parent.mkdir(parents=True, exist_ok=True)
        _KEY_PATH.write_bytes(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()))
        _KEY_PATH.chmod(0o600)
        return key

    def public_key_hex(self) -> str:
        return self._key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw).hex()

    def sign(self, payload: dict) -> dict:
        """Signe un artefact. Retourne signature hex + clé publique pour vérification."""
        message = json.dumps(payload, sort_keys=True).encode()
        signature = self._key.sign(message).hex()
        self.signatures += 1
        _notify_phoenix("aegis", "INFO", "crypto_signing",
                        f"artefact signé (#{self.signatures})",
                        {"pubkey": self.public_key_hex()[:16] + "..."})
        return {"signature": signature, "pubkey": self.public_key_hex(), "algo": "ed25519"}

    def verify(self, payload: dict, signature_hex: str) -> bool:
        from cryptography.exceptions import InvalidSignature
        try:
            message = json.dumps(payload, sort_keys=True).encode()
            self._key.public_key().verify(bytes.fromhex(signature_hex), message)
            return True
        except InvalidSignature:
            return False

    def cosign_batch(self, batch_id: str) -> dict:
        """Co-signature d'un SealedBatch (avec AKER/KHEPER/EVE côté RAM)."""
        sig = self.sign({"batch_id": batch_id, "validator": "aegis"})
        return {"batch_id": batch_id, "validator": "aegis", "signature": sig["signature"]}

    def get_module_status(self):
        return {"name": "Aegis", "status": "ARMED", "mode": "crypto_defense",
                "algo": "ed25519", "signatures": self.signatures,
                "pubkey": self.public_key_hex()[:16] + "..."}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    a = Aegis()
    s = a.sign({"artifact": "forensic-001", "hash": "abc123"})
    print("sign:", s["signature"][:32], "...")
    print("verify ok:", a.verify({"artifact": "forensic-001", "hash": "abc123"}, s["signature"]))
    print("verify tampered:", a.verify({"artifact": "forensic-001", "hash": "TAMPERED"}, s["signature"]))
    print(json.dumps(a.get_module_status(), indent=2))
