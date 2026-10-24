"""
tools/reencrypt_trip_rows.py — re-encrypt trip rows from one ENCRYPTION_KEY to another.

FND-0327: ciphertext carries a key id (``kid``) since Sim #4, and reads under a
different key surface an explicit unreadable marker instead of a 500 — but the
rows still need a path back to readability. This is that path: a dry-run by
default, key-rotation tool that decrypts every encrypted field of the selected
trips with the OLD key and re-encrypts it with the NEW key, row by row, inside
one transaction per row.

Scope of fields mirrors spine_api.persistence.SQLTripStore exactly:
  - blob fields (_PRIVATE_BLOB_FIELDS): whole-object Fernet tokens with ``kid``
  - PII-key fields (_PII_KEY_FIELDS): JSON objects whose string values at
    _PII_FIELDS keys are individually encrypted

Legacy plaintext values are left untouched. Rows whose ciphertext the OLD key
cannot open are reported, never modified.

Usage (dry-run):
    .venv/bin/python tools/reencrypt_trip_rows.py --from-key <fernet> --to-key <fernet> \
        --ids trip_a,trip_b            # or --agency <agency_id> [--limit N]
Apply:
    ... --apply

Keys may also be passed via env: REENCRYPT_FROM_KEY / REENCRYPT_TO_KEY.
DATABASE_URL is read from the environment (the ``+asyncpg`` scheme is accepted).
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from spine_api.persistence import SQLTripStore  # noqa: E402
from src.security.encryption import looks_like_fernet_token  # noqa: E402

BLOB_FIELDS = sorted(SQLTripStore._PRIVATE_BLOB_FIELDS)
PII_KEY_FIELDS = sorted(SQLTripStore._PII_KEY_FIELDS)
PII_FIELDS = {k.lower() for k in SQLTripStore._PII_FIELDS}


def _kid(key: bytes) -> str:
    import hashlib

    return hashlib.sha256(key).hexdigest()[:16]


class RotationReport:
    def __init__(self) -> None:
        self.rows_seen = 0
        self.rows_changed = 0
        self.fields_rotated = 0
        self.fields_legacy_plain = 0
        self.unreadable: list[tuple[str, str]] = []  # (trip_id, field)

    def as_dict(self) -> dict:
        return {
            "rows_seen": self.rows_seen,
            "rows_changed": self.rows_changed,
            "fields_rotated": self.fields_rotated,
            "fields_legacy_plain": self.fields_legacy_plain,
            "unreadable": self.unreadable,
        }


def rotate_blob(value: Any, old: Fernet, new: Fernet, new_kid: str, report: RotationReport, trip_id: str, field: str) -> Any:
    """Pure transform for a blob field. Returns the new storage value (or the input, unchanged)."""
    if not (isinstance(value, dict) and value.get("__encrypted_blob")):
        if value is not None:
            report.fields_legacy_plain += 1
        return value
    try:
        plain = old.decrypt(str(value.get("ciphertext", "")).encode())
    except InvalidToken:
        report.unreadable.append((trip_id, field))
        return value
    report.fields_rotated += 1
    return {"__encrypted_blob": True, "v": 2, "kid": new_kid, "ciphertext": new.encrypt(plain).decode()}


def rotate_pii(value: Any, old: Fernet, new: Fernet, report: RotationReport, trip_id: str, field: str) -> Any:
    """Pure transform for a PII-key JSON object: rotate every encrypted string at a PII key."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if k.lower() in PII_FIELDS and isinstance(v, str) and looks_like_fernet_token(v):
                try:
                    plain = old.decrypt(v.encode())
                except InvalidToken:
                    report.unreadable.append((trip_id, f"{field}.{k}"))
                    out[k] = v
                    continue
                report.fields_rotated += 1
                out[k] = new.encrypt(plain).decode()
            else:
                out[k] = rotate_pii(v, old, new, report, trip_id, field)
        return out
    if isinstance(value, list):
        return [rotate_pii(i, old, new, report, trip_id, field) for i in value]
    return value


def rotate_row(row: dict, old: Fernet, new: Fernet, new_kid: str, report: RotationReport) -> dict:
    """Return {field: new_value} for every field that changed."""
    trip_id = row["id"]
    changes: dict[str, Any] = {}
    for field in BLOB_FIELDS:
        before = row.get(field)
        after = rotate_blob(before, old, new, new_kid, report, trip_id, field)
        if after is not before and after != before:
            changes[field] = after
    for field in PII_KEY_FIELDS:
        before = row.get(field)
        after = rotate_pii(before, old, new, report, trip_id, field)
        if after != before:
            changes[field] = after
    return changes


async def _run(args: argparse.Namespace) -> int:
    import asyncpg

    url = os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    if not url:
        print("DATABASE_URL not set", file=sys.stderr)
        return 2
    old = Fernet(args.from_key.encode())
    new = Fernet(args.to_key.encode())
    new_kid = _kid(args.to_key.encode())
    report = RotationReport()
    cols = ["id"] + BLOB_FIELDS + PII_KEY_FIELDS
    conn = await asyncpg.connect(url)
    try:
        # trips carries FORCE ROW LEVEL SECURITY keyed on app.current_agency_id
        # (spine_api/core/rls.py); without it the rotation would silently see
        # zero rows. Agency scoping is also the safety rail for this tool.
        await conn.execute("SELECT set_config('app.current_agency_id', $1, false)", args.agency)
        if args.ids:
            ids = [i.strip() for i in args.ids.split(",") if i.strip()]
            rows = await conn.fetch(
                f"SELECT {', '.join(cols)} FROM trips WHERE agency_id = $1 AND id = ANY($2::text[])",
                args.agency, ids,
            )
        else:
            rows = await conn.fetch(
                f"SELECT {', '.join(cols)} FROM trips WHERE agency_id = $1 ORDER BY created_at DESC LIMIT $2",
                args.agency, args.limit,
            )
        for r in rows:
            report.rows_seen += 1
            row = {c: (json.loads(r[c]) if isinstance(r[c], str) and c != "id" else r[c]) for c in cols}
            changes = rotate_row(row, old, new, new_kid, report)
            if not changes:
                continue
            report.rows_changed += 1
            if args.apply:
                sets = ", ".join(f"{f} = ${i + 2}::jsonb" for i, f in enumerate(changes))
                async with conn.transaction():
                    await conn.execute(
                        f"UPDATE trips SET {sets}, updated_at = now() WHERE id = $1",
                        row["id"], *[json.dumps(v, default=str) for v in changes.values()],
                    )
    finally:
        await conn.close()
    print(json.dumps({"applied": bool(args.apply), "from_kid": _kid(args.from_key.encode()),
                      "to_kid": new_kid, **report.as_dict()}, indent=2))
    return 1 if report.unreadable and not args.allow_unreadable else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from-key", default=os.environ.get("REENCRYPT_FROM_KEY"), required=False)
    ap.add_argument("--to-key", default=os.environ.get("REENCRYPT_TO_KEY"), required=False)
    ap.add_argument("--ids", help="comma-separated trip ids (scoped to --agency)")
    ap.add_argument("--agency", required=True, help="agency id — RLS context and safety scope")
    ap.add_argument("--limit", type=int, default=500)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    ap.add_argument("--allow-unreadable", action="store_true",
                    help="exit 0 even if some fields could not be opened with --from-key")
    args = ap.parse_args()
    if not args.from_key or not args.to_key:
        ap.error("--from-key and --to-key (or REENCRYPT_FROM_KEY/REENCRYPT_TO_KEY) are required")
    return asyncio.run(_run(args))


if __name__ == "__main__":
    sys.exit(main())
