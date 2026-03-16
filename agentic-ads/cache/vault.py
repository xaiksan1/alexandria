"""BIP-39 Autonomous Key Derivation Vault for Semantic Bid Cache.

Provides deterministic AES-256-GCM encryption keys using BIP-39 mnemonics
and PBKDF2-HMAC-SHA256 key derivation.

Usage:
    export VAULT_MNEMONIC="word1 word2 ... word24"   # 24-word BIP-39 phrase
    vault = Vault()   # loads from env; deterministic across restarts

    # Ephemeral mode (testing only — keys lost on restart):
    vault = Vault(mnemonic="word1 word2 ... word24")
"""

import os
import warnings
from mnemonic import Mnemonic
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag


class Vault:
    """BIP-39 autonomous key derivation vault for encrypted bid caching.

    The vault derives per-label AES-256-GCM keys from a BIP-39 mnemonic seed
    using PBKDF2-HMAC-SHA256. The mnemonic is loaded from the VAULT_MNEMONIC
    environment variable to ensure cross-restart determinism. The mnemonic is
    never written to disk by this class.
    """

    def __init__(self, mnemonic: str | None = None, entropy_bits: int = 256) -> None:
        """Initialize the vault.

        Args:
            mnemonic: Optional BIP-39 mnemonic phrase (24 words). If None,
                      loads from VAULT_MNEMONIC env var. If env var is also
                      absent, generates a random ephemeral mnemonic and warns.
            entropy_bits: Used only when generating an ephemeral mnemonic.
        """
        self._mnemo = Mnemonic("english")

        if mnemonic is not None:
            self._mnemonic_phrase = mnemonic
        else:
            env_mnemonic = os.environ.get("VAULT_MNEMONIC")
            if env_mnemonic:
                self._mnemonic_phrase = env_mnemonic
            else:
                warnings.warn(
                    "VAULT_MNEMONIC not set — generating ephemeral mnemonic. "
                    "Encrypted cache entries will be unreadable after restart. "
                    "Set VAULT_MNEMONIC in production.",
                    RuntimeWarning,
                    stacklevel=2,
                )
                entropy = os.urandom(entropy_bits // 8)
                self._mnemonic_phrase = self._mnemo.to_mnemonic(entropy)

        self._seed_bytes = self._mnemo.to_seed(self._mnemonic_phrase)
        self._key_cache: dict[str, bytes] = {}  # label → derived key (PBKDF2 is expensive)

    @property
    def mnemonic_phrase(self) -> str:
        """Return the BIP-39 mnemonic phrase (for secure backup/export only)."""
        return self._mnemonic_phrase

    def derive_key(self, label: str) -> bytes:
        """Derive a 32-byte AES key for the given label using PBKDF2-HMAC-SHA256.

        The label serves as a KDF domain-separation context (not a random salt).
        Keys are deterministic given the same mnemonic seed + label.

        Args:
            label: Domain-separation string (e.g. "vertical_cloud:hash_abc").

        Returns:
            32-byte key suitable for AES-256 encryption.
        """
        if label not in self._key_cache:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=label.encode(),
                iterations=100_000,
                backend=default_backend(),
            )
            self._key_cache[label] = kdf.derive(self._seed_bytes)
        return self._key_cache[label]

    def encrypt(self, plaintext: bytes, label: str) -> bytes:
        """AES-256-GCM encrypt plaintext using derived key.

        Args:
            plaintext: Data to encrypt.
            label: Domain-separation label for key derivation.

        Returns:
            nonce(12 bytes) + ciphertext + GCM tag(16 bytes).
        """
        key = self.derive_key(label)
        nonce = os.urandom(12)
        ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
        return nonce + ciphertext

    def decrypt(self, ciphertext: bytes, label: str) -> bytes:
        """AES-256-GCM decrypt.

        Args:
            ciphertext: nonce(12) + ciphertext + GCM tag(16).
            label: Must match the label used during encryption.

        Returns:
            Decrypted plaintext.

        Raises:
            ValueError: On authentication failure (wrong label, tampered data).
        """
        if len(ciphertext) < 28:  # 12 nonce + 16 tag minimum
            raise ValueError("Ciphertext too short (minimum 28 bytes)")

        nonce = ciphertext[:12]
        body = ciphertext[12:]
        key = self.derive_key(label)

        try:
            return AESGCM(key).decrypt(nonce, body, None)
        except InvalidTag as e:
            raise ValueError("Decryption failed: authentication tag mismatch") from e
