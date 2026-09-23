#!/usr/bin/env python3
"""
Chapel XVI — lanceur : démarre un programme avec ses secrets pris au Sanctuaire.

  chapel_xvi_run.py SERVICE [--as NOM_ENV=SECRET ...] -- commande args...

Demande au Sanctuaire (127.0.0.1:6000) les secrets accordés à SERVICE, avec le
jeton ~/.chapel_xvi/tokens/SERVICE.token, les place dans l'environnement puis
remplace ce process par la commande (même PID : pm2 suit le vrai programme).
Les secrets ne sont donc jamais dans la config pm2 ni dans son dump.

--as renomme un secret pour ce programme (ex. BIFROST_API_KEY=BIFROST_VK_INTERNAL).
Au démarrage de la machine le Sanctuaire peut n'être pas encore ouvert : le
lanceur réessaie pendant 90 s, puis sort en erreur et pm2 le relancera.
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

SANCTUARY_URL = os.environ.get("CHAPEL_XVI_URL", "http://127.0.0.1:6000")
TOKENS_DIR = Path(os.environ.get("CHAPEL_XVI_TOKENS", Path.home() / ".chapel_xvi" / "tokens"))
WAIT_SECONDS = 90


def parse_args(argv: list[str]) -> tuple[str, dict[str, str], list[str]]:
    if "--" not in argv or argv.index("--") < 1:
        raise SystemExit("usage : chapel_xvi_run.py SERVICE [--as ENV=SECRET ...] -- commande args...")
    split = argv.index("--")
    head, command = argv[:split], argv[split + 1:]
    if not command:
        raise SystemExit("chapel_xvi_run : commande manquante après --")
    service, rest = head[0], head[1:]
    aliases: dict[str, str] = {}
    while rest:
        if rest[0] != "--as" or len(rest) < 2 or "=" not in rest[1]:
            raise SystemExit(f"chapel_xvi_run : argument inattendu {rest[0]!r}")
        env_name, secret = rest[1].split("=", 1)
        aliases[env_name] = secret
        rest = rest[2:]
    return service, aliases, command


def fetch_secrets(service: str, wait: float = WAIT_SECONDS) -> dict[str, str]:
    token = (TOKENS_DIR / f"{service}.token").read_text().strip()
    deadline = time.monotonic() + wait
    while True:
        try:
            req = urllib.request.Request(f"{SANCTUARY_URL}/v1/secrets")
            req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req, timeout=5) as resp:
                return json.load(resp)["secrets"]
        except urllib.error.HTTPError as e:
            if e.code != 503:  # 401/403 : inutile d'insister, c'est le jeton
                raise SystemExit(f"chapel_xvi_run : Sanctuaire a refusé {service} ({e.code})")
        except OSError:
            pass
        if time.monotonic() >= deadline:
            raise SystemExit(f"chapel_xvi_run : Sanctuaire injoignable ou scellé après {wait:.0f} s")
        time.sleep(3)


def build_env(base: dict[str, str], secrets: dict[str, str], aliases: dict[str, str]) -> dict[str, str]:
    env = dict(base)
    env.update(secrets)
    for env_name, secret in aliases.items():
        if secret not in secrets:
            raise SystemExit(f"chapel_xvi_run : secret {secret} non accordé à ce service")
        env[env_name] = secrets[secret]
    return env


def main(argv: list[str]) -> None:
    service, aliases, command = parse_args(argv)
    env = build_env(dict(os.environ), fetch_secrets(service), aliases)
    os.execvpe(command[0], command, env)


if __name__ == "__main__":
    main(sys.argv[1:])
