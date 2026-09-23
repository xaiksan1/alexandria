#!/usr/bin/env python3
"""
Chapel XVI — le Sanctuaire des clés (cœur, sans réseau)
Part of the Alexandria Cyber-Gate (Porta-Mundi)

Garde toutes les clés d'Alexandria, chiffrées au repos, et se rouvre seul.

- Clé maître de 32 octets, jamais écrite nulle part en entier.
- Coupée en 3 morceaux (partage de Shamir) : 2 morceaux sur 3 suffisent à la
  reconstruire, un morceau seul ne révèle rien. C'est la trinité AKER/KHEPER/EVE
  appliquée aux clés : « la boule au centre du triangle ».
- Les morceaux vivent à des endroits différents. Au démarrage le sanctuaire
  réunit ceux qu'il trouve ; s'il en a 2, il se rouvre sans personne. Retirer un
  morceau hors de la machine = coupe-circuit en cas de vol.
- Chaque secret est chiffré en AES-256-GCM, lié à son nom (données associées) :
  un secret déplacé sous un autre nom ne se déchiffre plus.
- Chaque service a son propre jeton ; il ne lit que les secrets qu'on lui a
  accordés. Seule l'empreinte SHA-256 du jeton est gardée.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path

from Crypto.Protocol.SecretSharing import Shamir
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

SHARE_HEADER = "CHAPEL-XVI-SHARE"
SHARE_VERSION = "v1"
THRESHOLD = 2
SHARE_COUNT = 3
_CHECK_PLAINTEXT = b"CHAPEL-XVI-SANCTUAIRE"
_CHECK_AAD = b"chapel-xvi:check"


class SanctuaryError(Exception):
    """Erreur du sanctuaire (scellé, morceaux insuffisants, accès refusé...)."""


# ─────────────────────────────────────────────────────────
# Morceaux de la clé maître (Shamir 2 sur 3)
# ─────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Share:
    index: int
    data: bytes  # 32 octets : morceau de la 1re moitié + morceau de la 2e moitié
    key_id: str  # empreinte courte de la clé maître, pour ne pas mêler deux générations

    def serialize(self) -> str:
        return f"{SHARE_HEADER} {SHARE_VERSION} {self.index} {self.data.hex()} {self.key_id}\n"

    @classmethod
    def parse(cls, text: str) -> "Share":
        parts = text.strip().split()
        if len(parts) != 5 or parts[0] != SHARE_HEADER or parts[1] != SHARE_VERSION:
            raise SanctuaryError("morceau illisible")
        data = bytes.fromhex(parts[3])
        if len(data) != 32:
            raise SanctuaryError("morceau de mauvaise taille")
        return cls(index=int(parts[2]), data=data, key_id=parts[4])


def key_id(master: bytes) -> str:
    return hashlib.sha256(b"chapel-xvi:key-id" + master).hexdigest()[:12]


def split_master(master: bytes) -> list[Share]:
    """Coupe la clé maître en 3 morceaux, 2 suffisent.

    Shamir de pycryptodome travaille sur 16 octets : chaque moitié de la clé est
    coupée séparément, avec les mêmes numéros de morceau.
    """
    if len(master) != 32:
        raise SanctuaryError("la clé maître doit faire 32 octets")
    kid = key_id(master)
    first = dict(Shamir.split(THRESHOLD, SHARE_COUNT, master[:16]))
    second = dict(Shamir.split(THRESHOLD, SHARE_COUNT, master[16:]))
    return [Share(i, first[i] + second[i], kid) for i in sorted(first)]


def combine_shares(shares: list[Share]) -> bytes:
    """Reconstruit la clé maître à partir d'au moins 2 morceaux de la même génération."""
    by_index = {s.index: s for s in shares}
    if len(by_index) < THRESHOLD:
        raise SanctuaryError(f"{len(by_index)} morceau(x) trouvé(s), il en faut {THRESHOLD}")
    kids = {s.key_id for s in by_index.values()}
    if len(kids) != 1:
        raise SanctuaryError("morceaux de générations différentes")
    chosen = list(by_index.values())[:THRESHOLD]
    first = Shamir.combine([(s.index, s.data[:16]) for s in chosen])
    second = Shamir.combine([(s.index, s.data[16:]) for s in chosen])
    master = first + second
    if key_id(master) != kids.pop():
        raise SanctuaryError("les morceaux ne reconstruisent pas la bonne clé")
    return master


def write_private(path: Path, text: str) -> None:
    """Écrit un fichier lisible par son propriétaire seulement (0600), dossier 0700."""
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        os.write(fd, text.encode())
    finally:
        os.close(fd)
    os.chmod(path, 0o600)


def load_shares(paths: list[Path]) -> list[Share]:
    """Lit les morceaux présents ; un endroit vide ou illisible est simplement ignoré."""
    found = []
    for p in paths:
        try:
            found.append(Share.parse(p.read_text()))
        except (OSError, ValueError, SanctuaryError):
            continue
    return found


# ─────────────────────────────────────────────────────────
# Le coffre chiffré
# ─────────────────────────────────────────────────────────

def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Sanctuary:
    """Coffre des secrets. Ouvert seulement avec la clé maître reconstruite."""

    def __init__(self, store_path: Path, master: bytes):
        self.store_path = store_path
        self._aead = AESGCM(master)
        self._data = self._read()
        self._verify_master()

    # --- création ---------------------------------------------------------
    @classmethod
    def create(cls, store_path: Path) -> tuple["Sanctuary", list[Share]]:
        """Nouveau sanctuaire vide : retourne le coffre et ses 3 morceaux (à disperser)."""
        if store_path.exists():
            raise SanctuaryError(f"un sanctuaire existe déjà : {store_path}")
        master = secrets.token_bytes(32)
        aead = AESGCM(master)
        nonce = secrets.token_bytes(12)
        data = {
            "version": 1,
            "key_id": key_id(master),
            "check": {"nonce": nonce.hex(),
                      "ct": aead.encrypt(nonce, _CHECK_PLAINTEXT, _CHECK_AAD).hex()},
            "secrets": {},
            "services": {},
        }
        write_private(store_path, json.dumps(data, indent=2))
        return cls(store_path, master), split_master(master)

    # --- lecture / écriture du fichier -----------------------------------
    def _read(self) -> dict:
        try:
            return json.loads(self.store_path.read_text())
        except (OSError, ValueError) as e:
            raise SanctuaryError(f"coffre illisible : {e}") from e

    def _save(self) -> None:
        tmp = self.store_path.with_suffix(".tmp")
        write_private(tmp, json.dumps(self._data, indent=2))
        os.replace(tmp, self.store_path)

    def _verify_master(self) -> None:
        c = self._data["check"]
        try:
            plain = self._aead.decrypt(bytes.fromhex(c["nonce"]), bytes.fromhex(c["ct"]), _CHECK_AAD)
        except Exception as e:
            raise SanctuaryError("clé maître incorrecte pour ce coffre") from e
        if plain != _CHECK_PLAINTEXT:
            raise SanctuaryError("clé maître incorrecte pour ce coffre")

    # --- secrets ----------------------------------------------------------
    def put(self, name: str, value: str) -> None:
        if not name or "/" in name:
            raise SanctuaryError("nom de secret invalide")
        nonce = secrets.token_bytes(12)
        ct = self._aead.encrypt(nonce, value.encode(), f"chapel-xvi:secret:{name}".encode())
        self._data["secrets"][name] = {"nonce": nonce.hex(), "ct": ct.hex()}
        self._save()

    def get(self, name: str) -> str:
        entry = self._data["secrets"].get(name)
        if entry is None:
            raise SanctuaryError(f"secret inconnu : {name}")
        return self._aead.decrypt(bytes.fromhex(entry["nonce"]), bytes.fromhex(entry["ct"]),
                                  f"chapel-xvi:secret:{name}".encode()).decode()

    def delete(self, name: str) -> None:
        self._data["secrets"].pop(name, None)
        for svc in self._data["services"].values():
            if name in svc["grants"]:
                svc["grants"].remove(name)
        self._save()

    def secret_names(self) -> list[str]:
        return sorted(self._data["secrets"])

    # --- services ---------------------------------------------------------
    def issue_token(self, service: str) -> str:
        """Crée (ou remplace) le jeton d'un service. L'ancien jeton cesse de marcher."""
        token = secrets.token_urlsafe(32)
        svc = self._data["services"].setdefault(service, {"grants": []})
        svc["token_sha256"] = token_digest(token)
        self._save()
        return token

    def grant(self, service: str, name: str) -> None:
        if name not in self._data["secrets"]:
            raise SanctuaryError(f"secret inconnu : {name}")
        svc = self._data["services"].setdefault(service, {"grants": []})
        if name not in svc["grants"]:
            svc["grants"].append(name)
            svc["grants"].sort()
        self._save()

    def revoke(self, service: str, name: str | None = None) -> None:
        """Retire un secret à un service, ou tout le service (jeton compris) si name est None."""
        if name is None:
            self._data["services"].pop(service, None)
        elif service in self._data["services"]:
            grants = self._data["services"][service]["grants"]
            if name in grants:
                grants.remove(name)
        self._save()

    def services(self) -> dict[str, list[str]]:
        return {k: list(v["grants"]) for k, v in sorted(self._data["services"].items())}

    def authenticate(self, token: str) -> str | None:
        """Retourne le service propriétaire du jeton, ou None. Comparaison à temps constant."""
        digest = token_digest(token)
        found = None
        for name, svc in self._data["services"].items():
            if hmac.compare_digest(svc.get("token_sha256", ""), digest):
                found = name
        return found

    def secrets_for(self, service: str) -> dict[str, str]:
        grants = self._data["services"].get(service, {}).get("grants", [])
        return {n: self.get(n) for n in grants}

    def reload(self) -> None:
        """Relit le fichier (après une modification par la ligne de commande)."""
        self._data = self._read()
        self._verify_master()
