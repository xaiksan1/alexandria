"""
Chapel XVI — où vivent le coffre, les morceaux de la clé maître et les jetons.

Les 3 morceaux sont volontairement à 3 endroits différents :
1. ~/.chapel_xvi/shares/share-1           — sur la machine, à côté du coffre
2. ~/.chapel_xvi-sceau/share-2            — le morceau destiné à vivre HORS de la machine
                                           (futur nœud) ; le retirer = coupe-circuit en cas de vol
3. ADAM/CLAUDE/systemd/chapel-xvi-share-3.env — gitignoré, repris par la sauvegarde envii

CHAPEL_XVI_SHARES (chemins séparés par « : ») remplace la liste, par exemple
quand le morceau 2 aura déménagé.
"""

import os
from pathlib import Path

HOME = Path.home()
STORE_PATH = Path(os.environ.get("CHAPEL_XVI_STORE", HOME / ".chapel_xvi" / "sanctuary.json"))
TOKENS_DIR = Path(os.environ.get("CHAPEL_XVI_TOKENS", HOME / ".chapel_xvi" / "tokens"))

_DEFAULT_SHARES = [
    HOME / ".chapel_xvi" / "shares" / "share-1",
    HOME / ".chapel_xvi-sceau" / "share-2",
    HOME / "alexandria" / "ADAM" / "CLAUDE" / "systemd" / "chapel-xvi-share-3.env",
]
SHARE_PATHS = (
    [Path(p) for p in os.environ["CHAPEL_XVI_SHARES"].split(":") if p]
    if os.environ.get("CHAPEL_XVI_SHARES")
    else _DEFAULT_SHARES
)
