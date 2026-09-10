"""Filesystem path guard: canonical containment validation for file-backed stores.

Mimosa flagged 40 path-traversal sites across persistence, cache, memory,
geography, and script tooling. Most already validate trip IDs via
``persistence._validate_trip_id``; the honest fix is one canonical guard
every file-backed store uses, not 40 scattered regexes.

:func:`safe_join` resolves a candidate name against a trusted base directory
and rejects anything that escapes it (``..``, absolute paths, symlink-free
lexical check via ``os.path.realpath`` containment).
"""

from __future__ import annotations

import os
from pathlib import Path


class UnsafePathError(ValueError):
    """Raised when a candidate path escapes its trusted base directory."""


def safe_join(base: str | os.PathLike, *parts: str) -> Path:
    """Join ``parts`` under ``base`` and return the resolved path.

    Every part must be a plain name (no separators, no ``..``), and the final
    resolved path must remain inside ``base``. Raises :class:`UnsafePathError`
    otherwise, so callers can fail loudly instead of writing outside the store.
    """
    base_path = Path(base).resolve()
    for part in parts:
        if not isinstance(part, str) or not part:
            raise UnsafePathError(f"empty or non-string path part: {part!r}")
        if part in (".", "..") or "/" in part or "\\" in part or "\x00" in part:
            raise UnsafePathError(f"unsafe path part: {part!r}")

    candidate = base_path.joinpath(*parts)
    resolved = Path(os.path.realpath(candidate))
    try:
        resolved.relative_to(base_path)
    except ValueError as exc:
        raise UnsafePathError(f"path escapes base {base_path}: {resolved}") from exc
    return resolved


def validate_filename(name: str, *, label: str = "filename") -> str:
    """Validate a bare filename (no directory component) and return it."""
    if not isinstance(name, str) or not name.strip():
        raise UnsafePathError(f"empty {label}")
    stripped = name.strip()
    if (
        stripped in (".", "..")
        or "/" in stripped
        or "\\" in stripped
        or "\x00" in stripped
        or os.path.isabs(stripped)
    ):
        raise UnsafePathError(f"unsafe {label}: {name!r}")
    return stripped
