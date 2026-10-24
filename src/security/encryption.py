"""
Encryption utilities for Waypoint OS.
"""

import os
from functools import lru_cache
from cryptography.fernet import Fernet, InvalidToken
import logging

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_fernet() -> Fernet:
    """Lazily initialise Fernet from ENCRYPTION_KEY env var.

    Read at call time so tests can monkeypatch without importlib.reload.
    Uses a stable development key in non-production modes.
    """
    key_raw = os.getenv("ENCRYPTION_KEY")

    if not key_raw:
        env = os.getenv("ENVIRONMENT", os.getenv("NODE_ENV", "development")).lower().strip()
        if os.getenv("DATA_PRIVACY_MODE") == "production" or env in ("production", "staging"):
            raise ValueError("ENCRYPTION_KEY must be set in production and staging environments")
        logger.warning(
            "ENCRYPTION_KEY not set — using static dev key. "
            "This is INSECURE for any environment with real data. "
            "Set ENCRYPTION_KEY in production, staging, and shared dev environments."
        )
        key_raw = 'v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8='
    else:
        key_raw = key_raw.encode() if isinstance(key_raw, str) else key_raw

    if isinstance(key_raw, str):
        key_raw = key_raw.encode()
    return Fernet(key_raw)


def _clear_fernet_cache() -> None:
    _get_fernet.cache_clear()
    _active_key_fingerprint.cache_clear()


def _active_key_bytes() -> bytes:
    key_raw = os.getenv("ENCRYPTION_KEY")
    if key_raw:
        return key_raw.encode() if isinstance(key_raw, str) else key_raw
    return b"v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8="


@lru_cache(maxsize=1)
def _active_key_fingerprint() -> str:
    import hashlib

    return hashlib.sha256(_active_key_bytes()).hexdigest()[:16]


def key_fingerprint() -> str:
    """Non-secret identifier of the active key (sha256 prefix).

    Stored alongside ciphertext (FND-0327) so a read under a different key can
    say *which* key it needs instead of crashing or returning garbage.
    """
    return _active_key_fingerprint()


def looks_like_fernet_token(value: str) -> bool:
    """Fernet tokens are urlsafe-base64 and start with the version byte 0x80
    ("gAAAAA" once encoded); plaintext never does."""
    return isinstance(value, str) and value.startswith("gAAAAA") and len(value) >= 60


def decrypt_strict(token: str) -> str:
    """Decrypt or raise ``InvalidToken`` — no plaintext fallback.

    Use when the caller must distinguish a foreign-key ciphertext from legacy
    plaintext (``decrypt`` deliberately blurs the two for pre-migration rows).
    """
    if not token:
        return token
    return _get_fernet().decrypt(token.encode()).decode()


def encrypt(data: str) -> str:
    """Encrypt a string and return base64 string."""
    if not data:
        return data
    return _get_fernet().encrypt(data.encode()).decode()


def decrypt(token: str) -> str:
    """Decrypt a base64 string."""
    if not token:
        return token
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except InvalidToken as e:
        logger.warning("Decryption failed: %s", e)
        return token  # Fallback to original if decryption fails (might be plaintext from old data)
