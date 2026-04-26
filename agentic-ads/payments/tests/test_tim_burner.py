import pytest

try:
    from payments.tim_burner import derive_wallet, verify_wallet
except ModuleNotFoundError:
    from tim_burner import derive_wallet, verify_wallet


# Ground truth — generated in session 2026-04-25, verified against sponsors_registry.json
KNOWN_WALLETS = {
    "ledger":           "0xfad4b71b9d92cb0e9c7a586c01af10bddfb699e2",
    "kraken":           "0x53e8ebbfc459fa22d7b42110ed7ca811649c7199",
    "coingecko-pro":    "0x59dac225913b1b47c728f0e280f13c5099de5937",
    "flyio":            "0x08ff740dd609d452bd466d4d65d1a91fa3b0f140",
    "vercel":           "0x91b4db3406f4f01427d833902daea35d3f7f13dd",
    "digitalocean":     "0xc95a178ad4f48780d939310d1f4d58ac9a3b0b7c",
    "duproprio":        "0x1cc58b60e3b982b0ed6a504f19bd658fad8490d4",
    "royallepage-qc":   "0x2b811e6a0d16040e8032d72fa8ce1c6ca66f2e87",
    "multi-prets":      "0xb3ca77b08462444cfb65cf1adf5efd0e1adb50fb",
    "huggingface-pro":  "0x739f67ce582b49505ace4152774427391776ca63",
    "together-ai":      "0x8b6bb9325c0e1bbf82b10fa7ef0d840c8dd069d5",
    "openrouter":       "0x99be1ed7765f99466fb209960dc1d040a02cd17c",
}


@pytest.mark.parametrize("sponsor_id,expected", KNOWN_WALLETS.items())
def test_derive_wallet_known(sponsor_id, expected):
    assert derive_wallet(sponsor_id) == expected


def test_derive_wallet_deterministic():
    w1 = derive_wallet("ledger")
    w2 = derive_wallet("ledger")
    assert w1 == w2


def test_derive_wallet_format():
    w = derive_wallet("test-sponsor")
    assert w.startswith("0x")
    assert len(w) == 42  # 0x + 40 hex chars


def test_derive_wallet_unique():
    wallets = [derive_wallet(sid) for sid in KNOWN_WALLETS]
    assert len(wallets) == len(set(wallets)), "collision detected"


def test_verify_wallet_match():
    assert verify_wallet("ledger", "0xfad4b71b9d92cb0e9c7a586c01af10bddfb699e2")


def test_verify_wallet_case_insensitive():
    assert verify_wallet("ledger", "0xFAD4B71B9D92CB0E9C7A586C01AF10BDDFB699E2")


def test_verify_wallet_mismatch():
    assert not verify_wallet("ledger", "0x0000000000000000000000000000000000000000")
