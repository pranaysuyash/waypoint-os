"""
Document storage abstraction — local filesystem for dev, S3-compatible target for production.

Signed URLs are keyed by document_id (never storage_key) with HMAC claims
encoding {document_id}:{operation}:{expires_timestamp}.

INTERNAL_URL_SECRET must be set in production/staging. Fails fast if missing.
"""

import hashlib
import hmac
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

DATA_DIR = Path(os.getenv("DATA_DIR", "data"))
DOCUMENTS_DIR = DATA_DIR / "documents"
_SIGNED_URL_EXPIRY_SECONDS = 900  # 15 minutes


def _get_internal_url_secret() -> str:
    """Get INTERNAL_URL_SECRET. Fails fast in production/staging."""
    secret = os.getenv("INTERNAL_URL_SECRET")
    if secret:
        return secret

    environment = os.getenv("ENVIRONMENT", os.getenv("APP_ENV", "development"))
    if environment in ("production", "staging"):
        raise RuntimeError(
            "INTERNAL_URL_SECRET must be set in production/staging. "
            "Signed URLs cannot function safely without a stable secret."
        )

    # Dev/test only: deterministic secret per process
    logger.warning("INTERNAL_URL_SECRET not set — using dev-only fallback")
    return "dev-only-internal-url-secret-do-not-use-in-prod"


_INTERNAL_URL_SECRET: Optional[str] = None


def get_internal_url_secret() -> str:
    global _INTERNAL_URL_SECRET
    if _INTERNAL_URL_SECRET is None:
        _INTERNAL_URL_SECRET = _get_internal_url_secret()
    return _INTERNAL_URL_SECRET


def _hmac_sign(document_id: str, operation: str, expires_ts: int) -> str:
    """Create HMAC-SHA256 claim for a signed URL."""
    message = f"{document_id}:{operation}:{expires_ts}"
    return hmac.new(
        get_internal_url_secret().encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


def _hmac_verify(document_id: str, operation: str, expires_ts: int, token: str) -> bool:
    """Verify HMAC-SHA256 claim for a signed URL."""
    expected = _hmac_sign(document_id, operation, expires_ts)
    return hmac.compare_digest(expected, token)


@runtime_checkable
class DocumentStorageBackend(Protocol):
    async def put(self, key: str, data: bytes) -> str: ...
    async def get_signed_url(self, document_id: str, operation: str, expires_in: int = _SIGNED_URL_EXPIRY_SECONDS) -> str: ...
    async def get(self, key: str) -> bytes: ...
    async def delete(self, key: str) -> bool: ...
    async def metadata(self, key: str) -> dict: ...


class LocalDocumentStorage:
    """Local filesystem document storage.

    Files stored under DATA_DIR/documents/{agency_id}/{trip_id}/{uuid}.{ext}.
    Signed URLs use HMAC claims keyed by document_id, not storage_key.
    Soft-delete: delete() returns True but does NOT remove the file from disk.
    """

    def __init__(self, root: Optional[Path] = None):
        self.root = root or DOCUMENTS_DIR
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        """Resolve a storage key to an absolute path, preventing traversal."""
        resolved = (self.root / key).resolve()
        if not str(resolved).startswith(str(self.root.resolve())):
            raise ValueError(f"Storage key escapes root: {key}")
        return resolved

    async def put(self, key: str, data: bytes) -> str:
        """Atomic write via temp file + rename."""
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        fd, tmp = tempfile.mkstemp(dir=str(path.parent))
        try:
            os.write(fd, data)
            os.close(fd)
            os.rename(tmp, str(path))
        except BaseException:
            try:
                os.close(fd)
            except OSError:
                pass
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise

        logger.info("Document stored: key=%s size=%d", key, len(data))
        return key

    async def get_signed_url(self, document_id: str, operation: str, expires_in: int = _SIGNED_URL_EXPIRY_SECONDS) -> str:
        """Generate a signed URL keyed by document_id + operation."""
        expires_ts = int(datetime.now(timezone.utc).timestamp()) + expires_in
        token = _hmac_sign(document_id, operation, expires_ts)
        return f"/api/internal/documents/{document_id}/{operation}?token={token}&expires={expires_ts}"

    async def get(self, key: str) -> bytes:
        """Read file bytes by storage key."""
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {key}")
        return path.read_bytes()

    async def delete(self, key: str) -> bool:
        """Soft-delete: return True but do NOT remove file from disk."""
        path = self._resolve(key)
        if not path.exists():
            return False
        logger.info("Document soft-deleted (file retained): key=%s", key)
        return True

    async def metadata(self, key: str) -> dict:
        """Return file metadata."""
        path = self._resolve(key)
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {key}")
        stat = path.stat()
        return {
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
        }


def verify_signed_url(document_id: str, operation: str, token: str, expires: str) -> bool:
    """Verify a signed URL claim. Returns True if valid and not expired."""
    try:
        expires_ts = int(expires)
    except (ValueError, TypeError):
        return False

    if expires_ts <= int(datetime.now(timezone.utc).timestamp()):
        return False

    return _hmac_verify(document_id, operation, expires_ts, token)


def get_document_storage() -> DocumentStorageBackend:
    """Factory: returns storage backend based on DOCUMENT_STORAGE_BACKEND env var."""
    backend = os.getenv("DOCUMENT_STORAGE_BACKEND", "local")
    if backend == "local":
        return LocalDocumentStorage()
    elif backend == "s3":
        raise NotImplementedError("S3 document storage not yet implemented")
    raise ValueError(f"Unknown document storage backend: {backend}")
