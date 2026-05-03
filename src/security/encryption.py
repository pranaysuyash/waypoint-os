"""
Encryption utilities for Waypoint OS.
"""

import os
from functools import lru_cache
from cryptography.fernet import Fernet
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
        if os.getenv("DATA_PRIVACY_MODE") == "production":
            raise ValueError("ENCRYPTION_KEY must be set in production mode")
        key_raw = 'v-k_y8Y5C8h7_5x6pQWzD9T-4G_MvR_Wf-1h-K_N-P8='
    else:
        key_raw = key_raw.encode() if isinstance(key_raw, str) else key_raw

    if isinstance(key_raw, str):
        key_raw = key_raw.encode()
    return Fernet(key_raw)


def _clear_fernet_cache() -> None:
    _get_fernet.cache_clear()


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
    except Exception as e:
        logger.warning(f"Decryption failed: {e}")
        return token  # Fallback to original if decryption fails (might be plaintext from old data)
