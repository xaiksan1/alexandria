import pytest
from cache.vault import Vault


def test_derive_key_is_32_bytes():
    v = Vault()
    key = v.derive_key("test_label")
    assert len(key) == 32


def test_derive_key_deterministic():
    v = Vault()
    assert v.derive_key("label_a") == v.derive_key("label_a")


def test_derive_key_deterministic_cross_instance():
    """Two Vaults initialized with the same mnemonic produce identical keys."""
    v1 = Vault()
    phrase = v1.mnemonic_phrase
    v2 = Vault(mnemonic=phrase)
    assert v1.derive_key("label_a") == v2.derive_key("label_a")


def test_vault_env_mnemonic_persistence(monkeypatch):
    """Vault loaded from VAULT_MNEMONIC env var is deterministic across instances."""
    v_tmp = Vault()
    phrase = v_tmp.mnemonic_phrase
    monkeypatch.setenv("VAULT_MNEMONIC", phrase)
    v1 = Vault()
    v2 = Vault()
    assert v1.derive_key("vertical_cloud") == v2.derive_key("vertical_cloud")


def test_derive_key_different_labels():
    v = Vault()
    assert v.derive_key("label_a") != v.derive_key("label_b")


def test_encrypt_decrypt_roundtrip():
    v = Vault()
    plaintext = b"bid_response_payload_xyz"
    ciphertext = v.encrypt(plaintext, "vertical_cloud")
    assert v.decrypt(ciphertext, "vertical_cloud") == plaintext


def test_encrypt_produces_different_ciphertext_each_time():
    v = Vault()
    pt = b"same_payload"
    c1 = v.encrypt(pt, "lbl")
    c2 = v.encrypt(pt, "lbl")
    assert c1 != c2  # different nonce each time


def test_decrypt_wrong_label_raises():
    v = Vault()
    ct = v.encrypt(b"payload", "correct_label")
    with pytest.raises(ValueError):
        v.decrypt(ct, "wrong_label")


def test_decrypt_tampered_ciphertext_raises():
    v = Vault()
    ct = bytearray(v.encrypt(b"payload", "lbl"))
    ct[20] ^= 0xFF  # flip a bit in ciphertext body
    with pytest.raises(ValueError):
        v.decrypt(bytes(ct), "lbl")
