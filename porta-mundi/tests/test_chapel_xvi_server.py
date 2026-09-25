"""Tests du service Chapel XVI (Flask test client, coffre temporaire, sans réseau).

Run:  ADAM/.venv/bin/python3 -m pytest porta-mundi/tests/test_chapel_xvi_server.py -q
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import chapel_xvi_server  # noqa: E402
from chapel_xvi_cli import parse_env_file  # noqa: E402
from chapel_xvi_sanctuary import Sanctuary, combine_shares, load_shares, write_private  # noqa: E402
from chapel_xvi_server import SanctuaryService, create_app  # noqa: E402
from chapel_xvi_vault import ChapelXVIVault  # noqa: E402


@pytest.fixture(autouse=True)
def no_phoenix(monkeypatch):
    sent = []
    monkeypatch.setattr(chapel_xvi_server, "_notify_phoenix", lambda *a, **k: sent.append(a))
    return sent


@pytest.fixture
def world(tmp_path):
    store = tmp_path / "sanctuary.json"
    sanctuary, shares = Sanctuary.create(store)
    sanctuary.put("A", "valeur-a")
    sanctuary.put("B", "valeur-b")
    token = sanctuary.issue_token("energon-meter")
    sanctuary.grant("energon-meter", "A")
    paths = [tmp_path / f"share-{i}" for i in (1, 2, 3)]
    for share, path in zip(shares, paths):
        write_private(path, share.serialize())
    journal = ChapelXVIVault(seal_log=tmp_path / "journal.jsonl")
    return {"store": store, "paths": paths, "token": token, "journal": journal, "tmp": tmp_path}


def _client(world, paths=None):
    svc = SanctuaryService(world["store"], paths or world["paths"], world["journal"])
    svc.try_unseal()
    return svc, create_app(svc).test_client()


def test_opens_by_itself_with_two_of_three(world):
    svc, client = _client(world, world["paths"][1:])
    assert client.get("/health").json["sanctuary"] == "OUVERT"


def test_stays_sealed_with_one_share(world, no_phoenix):
    svc, client = _client(world, world["paths"][:1])
    assert client.get("/health").json["sanctuary"] == "SCELLÉ"
    r = client.get("/v1/secrets", headers={"Authorization": f"Bearer {world['token']}"})
    assert r.status_code == 503
    assert any(a[0] == "MEDIUM" for a in no_phoenix)


def test_service_gets_only_its_secrets(world):
    _, client = _client(world)
    r = client.get("/v1/secrets", headers={"Authorization": f"Bearer {world['token']}"})
    assert r.status_code == 200
    assert r.json == {"service": "energon-meter", "secrets": {"A": "valeur-a"}}
    one = client.get("/v1/secrets/A", headers={"Authorization": f"Bearer {world['token']}"})
    assert one.json["value"] == "valeur-a"
    forbidden = client.get("/v1/secrets/B", headers={"Authorization": f"Bearer {world['token']}"})
    assert forbidden.status_code == 403


def test_bad_tokens_are_refused_then_escalated(world, no_phoenix):
    _, client = _client(world)
    assert client.get("/v1/secrets").status_code == 401
    for _ in range(5):
        assert client.get("/v1/secrets", headers={"Authorization": "Bearer faux"}).status_code == 401
    critical = [a for a in no_phoenix if a[0] == "CRITICAL"]
    assert critical and critical[0][3]["user"] == "chapel-xvi:jeton-inconnu"


def test_every_access_is_sealed_without_values(world):
    _, client = _client(world)
    client.get("/v1/secrets", headers={"Authorization": f"Bearer {world['token']}"})
    client.get("/v1/secrets", headers={"Authorization": "Bearer faux"})
    text = (world["tmp"] / "journal.jsonl").read_text()
    assert "sanctuary.read" in text and "sanctuary.refused" in text
    assert "valeur-a" not in text and world["token"] not in text
    assert world["journal"].verify_chain() == {"intact": True, "entries": 3}


def test_picks_up_changes_made_by_the_cli(world):
    _, client = _client(world)
    # le CLI rouvre le coffre avec ses propres morceaux, dans un autre process
    cli_view = Sanctuary(world["store"], combine_shares(load_shares(world["paths"])))
    cli_view.grant("energon-meter", "B")
    r = client.get("/v1/secrets/B", headers={"Authorization": f"Bearer {world['token']}"})
    assert r.status_code == 200 and r.json["value"] == "valeur-b"


def test_journal_detects_tampering(world):
    j = world["journal"]
    j.seal_record({"event": "un"})
    j.seal_record({"event": "deux"})
    log = world["tmp"] / "journal.jsonl"
    log.write_text(log.read_text().replace('"un"', '"UN"'))
    assert j.verify_chain()["intact"] is False


def test_parse_env_file_handles_quotes_and_comments():
    text = "# commentaire\nBIFROST_ADMIN_USER=Michael\nBIFROST_ADMIN_PASSWORD='a b$c'\nexport X=\"y\"\nVIDE=\n"
    assert parse_env_file(text) == {
        "BIFROST_ADMIN_USER": "Michael",
        "BIFROST_ADMIN_PASSWORD": "a b$c",
        "X": "y",
        "VIDE": "",
    }


def _journal(tmp_path):
    j = ChapelXVIVault(seal_log=tmp_path / "j.jsonl")
    j.seal_record({"event": "un"})
    j.seal_record({"event": "deux"})
    return j


def test_journal_se_repare_apres_coupure_octets_nuls(tmp_path):
    # Cas réel du 2026-09-25 : 284 octets nuls en fin de journal après une coupure.
    j = _journal(tmp_path)
    with open(j._seal_log, "ab") as f:
        f.write(b"\x00" * 284)
    j.seal_record({"event": "trois"})
    lignes = j._seal_log.read_text().splitlines()
    assert json.loads(lignes[-2])["record"]["event"] == "journal.reparation"
    assert json.loads(lignes[-1])["record"]["event"] == "trois"
    assert j.verify_chain() == {"intact": True, "entries": 4}
    assert b"\x00" * 284 in j._seal_log.with_suffix(".residus").read_bytes()


def test_journal_se_repare_apres_ligne_coupee(tmp_path):
    j = _journal(tmp_path)
    with open(j._seal_log, "a") as f:
        f.write('{"ts": 1, "prev_hash": "abc", "rec')
    j.seal_record({"event": "trois"})
    assert j.verify_chain()["intact"] is True


def test_journal_sain_nest_pas_touche(tmp_path):
    j = _journal(tmp_path)
    j.seal_record({"event": "trois"})
    assert not j._seal_log.with_suffix(".residus").exists()
    assert j.verify_chain() == {"intact": True, "entries": 3}
