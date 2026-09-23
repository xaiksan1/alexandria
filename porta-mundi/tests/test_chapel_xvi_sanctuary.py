"""Tests du cœur du Sanctuaire Chapel XVI (sans réseau).

Run:  ADAM/.venv/bin/python3 -m pytest porta-mundi/tests/test_chapel_xvi_sanctuary.py -q
"""
import itertools
import stat
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from chapel_xvi_sanctuary import (  # noqa: E402
    Sanctuary,
    SanctuaryError,
    Share,
    combine_shares,
    load_shares,
    split_master,
    write_private,
)


MASTER = bytes(range(32))


def test_any_two_of_three_shares_rebuild_the_master():
    shares = split_master(MASTER)
    assert len(shares) == 3
    for pair in itertools.combinations(shares, 2):
        assert combine_shares(list(pair)) == MASTER


def test_one_share_alone_is_refused():
    shares = split_master(MASTER)
    with pytest.raises(SanctuaryError):
        combine_shares([shares[0]])


def test_shares_from_two_generations_are_refused():
    a = split_master(MASTER)
    b = split_master(bytes(reversed(MASTER)))
    with pytest.raises(SanctuaryError):
        combine_shares([a[0], b[1]])


def test_share_roundtrips_through_text():
    s = split_master(MASTER)[1]
    assert Share.parse(s.serialize()) == s


def test_load_shares_skips_missing_and_garbage(tmp_path):
    shares = split_master(MASTER)
    good = tmp_path / "s1"
    good.write_text(shares[0].serialize())
    junk = tmp_path / "junk"
    junk.write_text("pas un morceau")
    loaded = load_shares([good, junk, tmp_path / "absent"])
    assert loaded == [shares[0]]


def test_write_private_is_owner_only(tmp_path):
    p = tmp_path / "d" / "f"
    write_private(p, "x")
    assert stat.S_IMODE(p.stat().st_mode) == 0o600
    assert stat.S_IMODE(p.parent.stat().st_mode) == 0o700


def test_create_then_reopen_with_two_shares(tmp_path):
    store = tmp_path / "sanctuary.json"
    sanctuary, shares = Sanctuary.create(store)
    sanctuary.put("BIFROST_ADMIN_PASSWORD", "tres-secret")
    reopened = Sanctuary(store, combine_shares([shares[0], shares[2]]))
    assert reopened.get("BIFROST_ADMIN_PASSWORD") == "tres-secret"
    assert "tres-secret" not in store.read_text()


def test_create_refuses_to_overwrite(tmp_path):
    store = tmp_path / "sanctuary.json"
    Sanctuary.create(store)
    with pytest.raises(SanctuaryError):
        Sanctuary.create(store)


def test_wrong_master_is_refused(tmp_path):
    store = tmp_path / "sanctuary.json"
    Sanctuary.create(store)
    with pytest.raises(SanctuaryError):
        Sanctuary(store, MASTER)


def test_secret_moved_under_another_name_does_not_decrypt(tmp_path):
    store = tmp_path / "sanctuary.json"
    sanctuary, _ = Sanctuary.create(store)
    sanctuary.put("A", "valeur")
    sanctuary._data["secrets"]["B"] = sanctuary._data["secrets"]["A"]
    with pytest.raises(Exception):
        sanctuary.get("B")


def test_service_sees_only_its_grants(tmp_path):
    sanctuary, _ = Sanctuary.create(tmp_path / "s.json")
    sanctuary.put("A", "1")
    sanctuary.put("B", "2")
    token = sanctuary.issue_token("energon-meter")
    sanctuary.grant("energon-meter", "A")
    assert sanctuary.authenticate(token) == "energon-meter"
    assert sanctuary.secrets_for("energon-meter") == {"A": "1"}
    assert token not in (tmp_path / "s.json").read_text()


def test_unknown_token_and_reissued_token(tmp_path):
    sanctuary, _ = Sanctuary.create(tmp_path / "s.json")
    old = sanctuary.issue_token("jarvis")
    new = sanctuary.issue_token("jarvis")
    assert sanctuary.authenticate("n'importe quoi") is None
    assert sanctuary.authenticate(old) is None
    assert sanctuary.authenticate(new) == "jarvis"


def test_grant_unknown_secret_is_refused(tmp_path):
    sanctuary, _ = Sanctuary.create(tmp_path / "s.json")
    with pytest.raises(SanctuaryError):
        sanctuary.grant("jarvis", "INEXISTANT")


def test_delete_and_revoke(tmp_path):
    sanctuary, _ = Sanctuary.create(tmp_path / "s.json")
    sanctuary.put("A", "1")
    token = sanctuary.issue_token("svc")
    sanctuary.grant("svc", "A")
    sanctuary.delete("A")
    assert sanctuary.secrets_for("svc") == {}
    sanctuary.revoke("svc")
    assert sanctuary.authenticate(token) is None
