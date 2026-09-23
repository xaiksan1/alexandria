#!/usr/bin/env python3
"""
Chapel XVI — gestion du Sanctuaire des clés en ligne de commande (sur la machine).

  init                      crée le coffre et disperse les 3 morceaux de la clé maître
  status                    état : morceaux trouvés, secrets, services (jamais de valeur)
  put NOM                   range un secret ; la valeur est lue sur l'entrée standard
  import-env FICHIER        range chaque NOM=valeur d'un fichier .env
  grant SERVICE NOM...      accorde des secrets à un service
  token SERVICE             (re)crée le jeton du service dans ~/.chapel_xvi/tokens/SERVICE.token
  revoke SERVICE [NOM]      retire un secret à un service, ou tout le service
  delete NOM                détruit un secret
  verify-journal            recalcule la chaîne du journal scellé

Les valeurs ne sont jamais affichées ni passées en argument de commande.
"""

from __future__ import annotations

import argparse
import shlex
import sys
from pathlib import Path

from chapel_xvi_paths import SHARE_PATHS, STORE_PATH, TOKENS_DIR
from chapel_xvi_sanctuary import Sanctuary, SanctuaryError, combine_shares, load_shares, write_private
from chapel_xvi_vault import ChapelXVIVault


def _open() -> Sanctuary:
    return Sanctuary(STORE_PATH, combine_shares(load_shares(SHARE_PATHS)))


def parse_env_file(text: str) -> dict[str, str]:
    """Lit des lignes NOM=valeur (guillemets du shell acceptés, commentaires ignorés)."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line[7:]
        name, raw = line.split("=", 1)
        parts = shlex.split(raw, comments=False) if raw.strip() else [""]
        out[name.strip()] = parts[0] if parts else ""
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="chapel_xvi_cli.py", description="Sanctuaire Chapel XVI")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")
    sub.add_parser("status")
    sp = sub.add_parser("put"); sp.add_argument("name")
    sp = sub.add_parser("import-env"); sp.add_argument("file")
    sp = sub.add_parser("grant"); sp.add_argument("service"); sp.add_argument("names", nargs="+")
    sp = sub.add_parser("token"); sp.add_argument("service")
    sp = sub.add_parser("revoke"); sp.add_argument("service"); sp.add_argument("name", nargs="?")
    sp = sub.add_parser("delete"); sp.add_argument("name")
    sub.add_parser("verify-journal")
    args = p.parse_args(argv)
    journal = ChapelXVIVault()

    try:
        if args.cmd == "init":
            _, shares = Sanctuary.create(STORE_PATH)
            for share, path in zip(shares, SHARE_PATHS):
                write_private(path, share.serialize())
                print(f"morceau {share.index} → {path}")
            journal.seal_record({"event": "sanctuary.created", "shares": len(shares)})
            print(f"coffre créé : {STORE_PATH}")

        elif args.cmd == "status":
            found = load_shares(SHARE_PATHS)
            print(f"morceaux trouvés : {len(found)}/{len(SHARE_PATHS)}")
            for path in SHARE_PATHS:
                print(f"  {'✓' if load_shares([path]) else '✗'} {path}")
            s = _open()
            print(f"secrets ({len(s.secret_names())}) : {', '.join(s.secret_names()) or '—'}")
            for svc, grants in s.services().items():
                print(f"service {svc} : {', '.join(grants) or '—'}")

        elif args.cmd == "put":
            value = sys.stdin.read().rstrip("\n")
            if not value:
                raise SanctuaryError("valeur vide sur l'entrée standard")
            _open().put(args.name, value)
            journal.seal_record({"event": "sanctuary.put", "name": args.name})
            print(f"rangé : {args.name}")

        elif args.cmd == "import-env":
            values = parse_env_file(Path(args.file).read_text())
            s = _open()
            for name, value in values.items():
                s.put(name, value)
            journal.seal_record({"event": "sanctuary.import", "names": sorted(values)})
            print(f"rangés : {', '.join(sorted(values))}")

        elif args.cmd == "grant":
            s = _open()
            for name in args.names:
                s.grant(args.service, name)
            journal.seal_record({"event": "sanctuary.grant", "service": args.service, "names": args.names})
            print(f"{args.service} ← {', '.join(args.names)}")

        elif args.cmd == "token":
            token = _open().issue_token(args.service)
            path = TOKENS_DIR / f"{args.service}.token"
            write_private(path, token + "\n")
            journal.seal_record({"event": "sanctuary.token", "service": args.service})
            print(f"jeton de {args.service} → {path}")

        elif args.cmd == "revoke":
            _open().revoke(args.service, args.name)
            if args.name is None:
                (TOKENS_DIR / f"{args.service}.token").unlink(missing_ok=True)
            journal.seal_record({"event": "sanctuary.revoke", "service": args.service, "name": args.name})
            print(f"retiré : {args.service}{' / ' + args.name if args.name else ' (service entier)'}")

        elif args.cmd == "delete":
            _open().delete(args.name)
            journal.seal_record({"event": "sanctuary.delete", "name": args.name})
            print(f"détruit : {args.name}")

        elif args.cmd == "verify-journal":
            print(journal.verify_chain())

    except SanctuaryError as e:
        print(f"Chapel XVI : {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
