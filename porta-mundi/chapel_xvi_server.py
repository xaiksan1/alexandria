#!/usr/bin/env python3
"""
CHAPEL XVI — le Sanctuaire des clés (service, 127.0.0.1:6000)
Part of the Alexandria Cyber-Gate (Porta-Mundi)

Se rouvre seul : au démarrage, puis toutes les 30 s tant qu'il est scellé, il
cherche ses morceaux ; dès qu'il en réunit 2 sur 3, il s'ouvre, sans personne.

- Un service présente son jeton (Authorization: Bearer) et ne reçoit que ses secrets.
- Chaque accès, réussi ou refusé, est scellé dans le journal Chapel XVI (sans valeur).
- Un jeton refusé prévient Phoenix ; 5 refus en 60 s = CRITICAL, que Tartarus met
  en quarantaine. Un morceau manquant prévient aussi Phoenix.
- Jamais exposé au réseau, jamais appelé par un navigateur : pas de CORS.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.request
from collections import deque

from flask import Flask, jsonify, request

from chapel_xvi_paths import SHARE_PATHS, STORE_PATH
from chapel_xvi_sanctuary import Sanctuary, SanctuaryError, combine_shares, load_shares
from chapel_xvi_vault import ChapelXVIVault

PORT = 6000
_PHOENIX_URL = "http://localhost:8000/events"
_RETRY_SECONDS = 30
_ALERT_WINDOW = 60
_ALERT_THRESHOLD = 5

logging.basicConfig(level=logging.INFO, format="%(asctime)s [CHAPEL-XVI] %(levelname)s: %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")
logger = logging.getLogger("CHAPEL-XVI")


def _notify_phoenix(severity: str, category: str, message: str, data: dict | None = None) -> None:
    def _send():
        try:
            payload = json.dumps({"source": "chapel-xvi", "severity": severity, "category": category,
                                  "message": message, "data": data or {}}).encode()
            req = urllib.request.Request(_PHOENIX_URL, data=payload,
                                         headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=2)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


class SanctuaryService:
    def __init__(self, store_path=STORE_PATH, share_paths=SHARE_PATHS, journal: ChapelXVIVault | None = None):
        self.store_path = store_path
        self.share_paths = share_paths
        self.journal = journal or ChapelXVIVault()
        self.sanctuary: Sanctuary | None = None
        self.shares_found = 0
        self._mtime = 0.0
        self._lock = threading.Lock()
        self._failures: deque[float] = deque()

    # --- ouverture autonome ------------------------------------------------
    def try_unseal(self) -> bool:
        shares = load_shares(self.share_paths)
        self.shares_found = len(shares)
        if not self.store_path.exists():
            logger.warning("aucun coffre à %s (lancer chapel_xvi_cli.py init)", self.store_path)
            return False
        try:
            sanctuary = Sanctuary(self.store_path, combine_shares(shares))
        except SanctuaryError as e:
            logger.warning("reste scellé : %s", e)
            _notify_phoenix("WARNING", "sanctuary", f"Sanctuaire scellé : {e}",
                            {"shares_found": len(shares)})
            return False
        with self._lock:
            self.sanctuary = sanctuary
            self._mtime = self.store_path.stat().st_mtime
        self.journal.seal_record({"event": "sanctuary.unsealed", "shares_found": len(shares)})
        if len(shares) < len(self.share_paths):
            _notify_phoenix("WARNING", "sanctuary",
                            f"Sanctuaire ouvert avec {len(shares)} morceaux sur {len(self.share_paths)}",
                            {"shares_found": len(shares)})
        logger.info("Sanctuaire OUVERT (%d morceaux trouvés)", len(shares))
        return True

    def unseal_loop(self) -> None:
        while self.sanctuary is None:
            if self.try_unseal():
                return
            time.sleep(_RETRY_SECONDS)

    def _fresh(self) -> Sanctuary | None:
        """Relit le coffre si la ligne de commande l'a modifié depuis."""
        with self._lock:
            if self.sanctuary is None:
                return None
            try:
                mtime = self.store_path.stat().st_mtime
                if mtime != self._mtime:
                    self.sanctuary.reload()
                    self._mtime = mtime
            except (OSError, SanctuaryError) as e:
                logger.error("relecture du coffre impossible : %s", e)
            return self.sanctuary

    # --- accès -------------------------------------------------------------
    def _refused(self, reason: str) -> None:
        now = time.time()
        self._failures.append(now)
        while self._failures and now - self._failures[0] > _ALERT_WINDOW:
            self._failures.popleft()
        self.journal.seal_record({"event": "sanctuary.refused", "reason": reason,
                                  "peer": request.remote_addr})
        if len(self._failures) >= _ALERT_THRESHOLD:
            _notify_phoenix("CRITICAL", "intrusion",
                            f"{len(self._failures)} jetons refusés en {_ALERT_WINDOW} s au Sanctuaire",
                            {"user": "chapel-xvi:jeton-inconnu", "reason": reason})
            self._failures.clear()
        else:
            _notify_phoenix("WARNING", "access_denied", f"Sanctuaire : accès refusé ({reason})")

    def authorize(self):
        sanctuary = self._fresh()
        if sanctuary is None:
            return None, (jsonify({"error": "sanctuaire scellé"}), 503)
        auth = request.headers.get("Authorization", "")
        token = auth[7:] if auth.startswith("Bearer ") else ""
        service = sanctuary.authenticate(token) if token else None
        if service is None:
            self._refused("jeton absent" if not token else "jeton inconnu")
            return None, (jsonify({"error": "accès refusé"}), 401)
        return (sanctuary, service), None


def create_app(service: SanctuaryService) -> Flask:
    app = Flask(__name__)

    @app.get("/health")
    def health():
        s = service._fresh()
        return jsonify({
            "status": "ok",
            "sanctuary": "OUVERT" if s else "SCELLÉ",
            "shares_found": service.shares_found,
            "shares_expected": len(service.share_paths),
            "secrets": len(s.secret_names()) if s else None,
            "services": len(s.services()) if s else None,
        })

    @app.get("/v1/secrets")
    def all_secrets():
        ok, err = service.authorize()
        if err:
            return err
        sanctuary, svc = ok
        values = sanctuary.secrets_for(svc)
        service.journal.seal_record({"event": "sanctuary.read", "service": svc, "names": sorted(values)})
        return jsonify({"service": svc, "secrets": values})

    @app.get("/v1/secrets/<name>")
    def one_secret(name: str):
        ok, err = service.authorize()
        if err:
            return err
        sanctuary, svc = ok
        if name not in sanctuary.services().get(svc, []):
            service.journal.seal_record({"event": "sanctuary.forbidden", "service": svc, "name": name})
            _notify_phoenix("WARNING", "access_denied", f"{svc} a demandé {name} sans y avoir droit",
                            {"user": svc})
            return jsonify({"error": "secret non accordé à ce service"}), 403
        service.journal.seal_record({"event": "sanctuary.read", "service": svc, "names": [name]})
        return jsonify({"name": name, "value": sanctuary.get(name)})

    return app


if __name__ == "__main__":
    svc = SanctuaryService()
    threading.Thread(target=svc.unseal_loop, daemon=True).start()
    _notify_phoenix("INFO", "system", "Chapel XVI — Sanctuaire en ligne", {"port": PORT})
    logger.info("CHAPEL XVI en ligne — 127.0.0.1:%d", PORT)
    create_app(svc).run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
