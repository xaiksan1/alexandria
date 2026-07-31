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
# Agent wallets — separate from the sponsor derive_wallet() above on purpose
# (sponsors_registry.json has real, already-communicated addresses pinned to
# that function; a real external partner's wallet doesn't get to move because
# an unrelated bug got fixed).
#
# 2026-07-31, real BIP32/BIP44 secp256k1 HD wallets, not a pseudo-address.
# First pass here used sha256 + Base58Check — deliberately not a real keypair,
# reasoning that Alexandria's energon has no market value yet so a real
# private key wasn't warranted. Michael's correction, and he's right: a test
# is supposed to be exercised against real conditions so real bugs surface
# while the stakes are small — "wait for the final version" isn't a policy,
# it's an excuse that never actually arrives. Fix it in the system that
# exists now; that fix IS what makes the eventual mature version secure.
#
# Real security model: ONE master BIP39 mnemonic, generated once, stored at
# ~/.tim_burner/master_mnemonic.txt (0600, never in the repo) — same pattern
# already established in this codebase for Aegis's signing key
# (porta-mundi/aegis.py, ~/.aegis/aegis_ed25519.key). Each agent's real
# keypair is derived via the standard BIP44 path m/44'/60'/0'/0/{index},
# where `index` is a public, deterministic function of the agent's name
# (sha256(name) reduced into the valid BIP32 index range). The agent's name
# being public is fine under this model — the index only says WHICH child
# key to derive; without the secret master mnemonic, no one can derive the
# private key from the name alone. That's the actual difference between real
# EC security and the "looks like crypto" trap from the first pass: the
# secret is the master seed, never anything derivable from public data.
import os
import stat
from pathlib import Path

from eth_account import Account

Account.enable_unaudited_hdwallet_features()

_MASTER_SEED_DIR = Path.home() / ".tim_burner"
_MASTER_SEED_PATH = _MASTER_SEED_DIR / "master_mnemonic.txt"
_BIP44_COIN_TYPE = 60  # Ethereum, per SLIP-44 — matches x402_handler.py's ETH/Polygon settlement


def _load_or_create_master_mnemonic() -> str:
    if _MASTER_SEED_PATH.exists():
        return _MASTER_SEED_PATH.read_text().strip()
    _MASTER_SEED_DIR.mkdir(parents=True, exist_ok=True)
    _, mnemonic = Account.create_with_mnemonic()
    _MASTER_SEED_PATH.write_text(mnemonic)
    os.chmod(_MASTER_SEED_PATH, stat.S_IRUSR | stat.S_IWUSR)  # 0600, owner only
    return mnemonic


def _agent_derivation_index(name: str) -> int:
    """Deterministic, public BIP32 index for an agent's name. Reduced modulo
    2**31 - 1 to stay in the valid non-hardened index range."""
    return int(hashlib.sha256(name.encode()).hexdigest(), 16) % (2**31 - 1)


def derive_agent_wallet(name: str) -> str:
    """Real secp256k1 address for an Alexandria agent, via BIP44 HD
    derivation from the shared master mnemonic — keyed by the agent's actual
    NAME (not a slot index, not the name's length, so no collision between
    agents with same-length or same-derived-slot names).

    This IS a real, spendable address once the corresponding private key is
    used — unlike the sponsor derive_wallet() above. The private key itself
    is never returned or logged here; only the public address is.
    """
    mnemonic = _load_or_create_master_mnemonic()
    index = _agent_derivation_index(name)
    account = Account.from_mnemonic(mnemonic, account_path=f"m/44'/{_BIP44_COIN_TYPE}'/0'/0/{index}")
    return account.address
