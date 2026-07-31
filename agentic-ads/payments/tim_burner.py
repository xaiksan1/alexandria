import hashlib

# INTERNAL USE ONLY. These addresses have no real private key (sha256-derived,
# not secp256k1) and can never be spent from on a real chain. Use them for
# Alexandria's internal agent-to-agent Energon ledger accounting only — NEVER
# as the recipient_wallet passed to ADAM/dwallstreet/x402_handler.py, which
# verifies real on-chain USDC transfers. Real external settlement uses a real
# wallet (see ALEXANDRIA_WALLET / sponsors_registry.json), never a derive_wallet()
# address. See ADAM/dwallstreet/x402_handler.py's matching note.

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


# ─────────────────────────────────────────────────────────────────────────
# Agent wallets — separate from the sponsor derive_wallet() above on purpose.
#
# 2026-07-31: paper_spawner.py's larva-birth agent_id was `f"paper-slot-
# {len(name)}"` — keyed by the NAME'S LENGTH, so two different agents with
# same-length names collided on both the slot id and (once wired) the wallet.
# Michael's fix request: derive the wallet from the agent's actual NAME using
# an elliptic curve, an encoding he remembered as "base64" (Base58 is the
# real Bitcoin-style one — Base64 was never used for addresses; the two get
# mixed up easily), and reverse-endian byte order.
#
# What's implemented here and why:
#   - Reversed byte order: real, applied below.
#   - Base58Check: real Bitcoin-style encoding (not Base64) — implemented
#     below, no external dependency.
#   - Elliptic curve (secp256k1, what Bitcoin/Ethereum actually use): NOT
#     used to generate a real private key here, deliberately. A keypair
#     derived purely from a PUBLIC, guessable string (the agent's own name)
#     is a real vulnerability the moment this wallet ever holds real value —
#     anyone who knows the agent's name could recompute the identical
#     "private" key and drain it. Real EC math only adds security when the
#     seed feeding it is secret; adding an EC step here just to hash away the
#     result would be theater, not protection — the exact "looks correct but
#     isn't" failure mode this whole audit has been about. Energons have no
#     market value yet, but Michael's own plan is for that to change — the
#     correct upgrade path when it does is a BIP32 HD wallet (one securely
#     held master seed + a public per-agent derivation path/index), not a
#     name-derived keypair. Build that for real when that day comes.
#
# So this stays in the same safety envelope as derive_wallet() above: a
# deterministic, non-custodial pseudo-address, never a spendable private key.
_AGENT_SALT = "tim-burner:alexandria:agents:v1"

_BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


def _base58check_encode(payload: bytes, version: int = 0x35) -> str:
    """Bitcoin-style Base58Check: version byte + payload + 4-byte double-
    SHA256 checksum, encoded in Base58 (not Base64 — Base58 drops 0/O/I/l
    specifically because they're visually ambiguous, which is the entire
    point of using it for something a human might have to retype)."""
    versioned = bytes([version]) + payload
    checksum = hashlib.sha256(hashlib.sha256(versioned).digest()).digest()[:4]
    full = versioned + checksum
    n_leading_zeros = len(full) - len(full.lstrip(b"\x00"))
    num = int.from_bytes(full, "big")
    chars = []
    while num > 0:
        num, rem = divmod(num, 58)
        chars.append(_BASE58_ALPHABET[rem])
    return "1" * n_leading_zeros + "".join(reversed(chars))


def derive_agent_wallet(name: str) -> str:
    """Deterministic Base58Check pseudo-wallet for an Alexandria agent, keyed
    by the agent's actual NAME — not a slot index, not the name's length.

    No real private key (see module note above) — never pass this as a real
    on-chain recipient address, exactly like derive_wallet() above.
    """
    seed = f"{_AGENT_SALT}:{name}".encode()
    digest = hashlib.sha256(seed).digest()
    digest = digest[::-1]  # reverse byte order (endianness)
    payload = digest[-20:]
    return _base58check_encode(payload)
