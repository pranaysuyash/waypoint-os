"""Shared encryption helpers for private field storage.

Used by confirmation_service, extraction_service, and any future module
that needs to encrypt/decrypt JSON blobs or single string fields at rest.

Encryption format: {"__encrypted_blob": True, "v": 1, "ciphertext": <Fernet token>}
"""

import json
from typing import Optional

from src.security.encryption import encrypt, decrypt


def encrypt_blob(data: dict) -> Optional[dict]:
    """Encrypt a JSON dict as a single Fernet token."""
    if data is None:
        return None
    serialized = json.dumps(data, default=str)
    token = encrypt(serialized)
    return {"__encrypted_blob": True, "v": 1, "ciphertext": token}


def decrypt_blob(data: dict) -> Optional[dict]:
    """Decrypt a blob-encrypted JSON dict back to original form."""
    if data is None:
        return None
    if isinstance(data, dict) and data.get("__encrypted_blob"):
        token = data.get("ciphertext", "")
        serialized = decrypt(token)
        return json.loads(serialized)
    return data


def encrypt_field(value: Optional[str]) -> Optional[dict]:
    """Encrypt a single string field as a blob."""
    if not value:
        return None
    return encrypt_blob({"value": value.strip()})


def decrypt_field(blob: Optional[dict]) -> Optional[str]:
    """Decrypt a single string field from a blob."""
    if not blob:
        return None
    decrypted = decrypt_blob(blob)
    return decrypted.get("value") if decrypted else None
