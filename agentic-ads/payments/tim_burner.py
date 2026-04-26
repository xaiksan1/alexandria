import hashlib

# Versioned salt — change this to rotate all wallets (sponsors must be re-funded)
_SALT = "tim-burner:agentic-ads:sponsors:v1"


def derive_wallet(sponsor_id: str) -> str:
    """Return a deterministic 0x-prefixed ETH address for a sponsor.

    Mechanism: sha256(SALT:sponsorId) as private key material →
    double-sha256 pubkey approximation → rightmost 20 bytes = address.

    No external dependencies. Reproducible from sponsor_id alone.
    NOT secp256k1 — suitable for M2M ad payments, not high-value custody.
    """
    seed = f"{_SALT}:{sponsor_id}"
    priv = hashlib.sha256(seed.encode()).digest()
    pub = hashlib.sha256(priv).digest()
    addr_bytes = hashlib.sha256(pub).digest()[-20:]
    return "0x" + addr_bytes.hex()


def verify_wallet(sponsor_id: str, expected_wallet: str) -> bool:
    """Return True if expected_wallet matches the deterministic derivation."""
    return derive_wallet(sponsor_id).lower() == expected_wallet.lower()
