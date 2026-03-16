"""Compliance smoke tests — verify all required files exist and are non-empty."""
import os
import json

BASE = os.path.join(os.path.dirname(__file__))

def test_privacy_md_exists():
    path = os.path.join(BASE, "privacy.md")
    assert os.path.exists(path), "privacy.md missing"
    assert os.path.getsize(path) > 100, "privacy.md suspiciously short"

def test_officer_json_exists_and_valid():
    path = os.path.join(BASE, "officer.json")
    assert os.path.exists(path), "officer.json missing"
    with open(path) as f:
        data = json.load(f)
    assert "role" in data
    assert "law" in data
    assert "jurisdiction" in data

def test_efvp_exists():
    path = os.path.join(BASE, "EFVP.md")
    assert os.path.exists(path), "EFVP.md missing"
    assert os.path.getsize(path) > 100, "EFVP.md suspiciously short"

def test_officer_json_review_cycle():
    path = os.path.join(BASE, "officer.json")
    with open(path) as f:
        data = json.load(f)
    assert data.get("review_cycle_days") == 365

def test_privacy_md_mentions_loi25():
    path = os.path.join(BASE, "privacy.md")
    with open(path) as f:
        content = f.read()
    assert "Loi 25" in content or "Law 25" in content

def test_efvp_mentions_sha256():
    path = os.path.join(BASE, "EFVP.md")
    with open(path) as f:
        content = f.read()
    assert "SHA256" in content
