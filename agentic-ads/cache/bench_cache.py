"""Phase 0 gate: cache hit must be <1ms (excluding network).

Benchmarks the AES-256-GCM encrypt+decrypt cycle for a 512-byte payload.
In production the PBKDF2 key is derived once per label and reused; this
bench isolates the per-request crypto cost (AESGCM only).

Run:
    python alexandria/agentic-ads/cache/bench_cache.py
"""

import sys
import os

# Allow running directly without PYTHONPATH set
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import warnings
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Suppress ephemeral mnemonic warning in benchmark context
warnings.filterwarnings("ignore", category=RuntimeWarning, message="VAULT_MNEMONIC not set")

from cache.vault import Vault  # noqa: E402

# ── Phase 0 gate ─────────────────────────────────────────────────────────────

def main() -> None:
    vault = Vault()
    payload = b"A" * 512  # typical bid response size
    label = "cloud:abc123hash"

    # Derive key once — mirrors production where key is cached per label
    key = vault.derive_key(label)
    aesgcm = AESGCM(key)

    # Warm-up (exclude JIT/import overhead from measurement)
    for _ in range(10):
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, payload, None)
        aesgcm.decrypt(nonce, ct, None)

    N = 1000
    t0 = time.perf_counter()
    for _ in range(N):
        nonce = os.urandom(12)
        ct = aesgcm.encrypt(nonce, payload, None)
        aesgcm.decrypt(nonce, ct, None)
    elapsed = time.perf_counter() - t0
    avg_ms = (elapsed / N) * 1000

    print(f"AES-256-GCM round-trip (encrypt+decrypt 512B): {avg_ms:.4f}ms avg over {N} iterations")
    print(f"(Key derivation PBKDF2/100k is done once per label, not per request)")

    if avg_ms < 1.0:
        print("PHASE 0 GATE PASSED: <1ms AES-GCM per-request crypto latency")
    else:
        print(f"PHASE 0 GATE FAILED: {avg_ms:.4f}ms > 1ms target")
        raise SystemExit(1)


main()
