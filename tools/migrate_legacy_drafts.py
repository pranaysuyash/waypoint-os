"""
tools/migrate_legacy_drafts.py — one-time migration: re-encrypt legacy
plaintext draft files through the DraftStore's own encryption seam.

FND-0377 (retracted as invalid-premise): the DraftStore has encrypted drafts
at rest since the FND-0326 residual (2026-10-23, ``__encrypted_draft`` v2
envelope, re-encrypt-on-next-save for legacy files). This tool completes that
migration for the 673 legacy files created before the fix, WITHOUT inventing
a parallel crypto path: each file is loaded (plaintext legacy or already-
enveloped) and re-saved through ``FileDraftStore._save_json``, which applies
the canonical envelope. Files that fail to parse are left untouched and
reported (never deleted).

Usage:
    .venv/bin/python tools/migrate_legacy_drafts.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DRAFTS = REPO / "data" / "drafts"
sys.path.insert(0, str(REPO))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    from spine_api.draft_store import FileDraftStore

    migrated = skipped_enveloped = unparseable = 0
    for f in sorted(DRAFTS.glob("draft_*.json")):
        try:
            raw = json.loads(f.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            unparseable += 1
            continue
        if raw.get("__encrypted_draft"):
            skipped_enveloped += 1
            continue
        if not isinstance(raw, dict):
            unparseable += 1
            continue
        if args.dry_run:
            migrated += 1
            continue
        # Canonical seam: _save_json applies the encrypted envelope.
        FileDraftStore._save_json(f, raw)
        migrated += 1

    print(
        f"migrated={migrated} already_enveloped={skipped_enveloped} "
        f"unparseable={unparseable} dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
