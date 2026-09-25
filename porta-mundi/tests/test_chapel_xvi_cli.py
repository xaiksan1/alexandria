"""« reveler » ne doit jamais écrire une valeur ailleurs que dans un vrai terminal.

Run:  ADAM/.venv/bin/python3 -m pytest porta-mundi/tests/test_chapel_xvi_cli.py -q
"""
import subprocess
import sys
from pathlib import Path

CLI = Path(__file__).resolve().parent.parent / "chapel_xvi_cli.py"


def test_reveler_refuses_when_output_is_captured(tmp_path):
    # Coffre et morceaux inexistants : si le refus n'arrivait pas AVANT l'ouverture,
    # l'erreur serait différente (morceaux introuvables).
    env = {"PATH": "/usr/bin:/bin", "HOME": str(tmp_path),
           "CHAPEL_XVI_STORE": str(tmp_path / "absent.json"),
           "CHAPEL_XVI_SHARES": str(tmp_path / "s1")}
    out = subprocess.run([sys.executable, str(CLI), "reveler", "N_IMPORTE_QUOI"],
                         capture_output=True, text=True, env=env, timeout=30)
    assert out.returncode == 1
    assert out.stdout == ""
    assert "vrai terminal" in out.stderr
