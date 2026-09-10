"""
Seed or verify the canonical non-prod PUBLIC_CHECKER_AGENCY_ID in SQL environments.

Usage:
  TMPDIR=/private/tmp PYTHONDONTWRITEBYTECODE=1 uv run python scripts/bootstrap_public_checker_agency.py

Behavior:
- If TRIPSTORE_BACKEND != sql, exits cleanly (no-op).
- If agencies table is missing, exits non-zero with actionable error.
- Inserts canonical agency row when missing.
- Idempotent: safe to run on every deploy/startup bootstrap.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sqlalchemy import text

from spine_api.core.database import engine

CANONICAL_NONPROD_PUBLIC_CHECKER_AGENCY_ID = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
CANONICAL_NONPROD_PUBLIC_CHECKER_AGENCY_SLUG = "waypoint-nonprod-public-checker"
CANONICAL_NONPROD_PUBLIC_CHECKER_AGENCY_NAME = "Waypoint Non-Prod Public Checker"


def _resolve_target_agency_id() -> str:
    configured = (os.environ.get("PUBLIC_CHECKER_AGENCY_ID") or "").strip()
    if configured:
        return configured
    return CANONICAL_NONPROD_PUBLIC_CHECKER_AGENCY_ID


async def _seed_agency_if_missing() -> int:
    backend = (os.environ.get("TRIPSTORE_BACKEND") or "file").strip().lower()
    if backend != "sql":
        print(
            json.dumps(
                {
                    "ok": True,
                    "skipped": True,
                    "reason": "TRIPSTORE_BACKEND is not sql",
                    "tripstore_backend": backend,
                }
            )
        )
        return 0

    agency_id = _resolve_target_agency_id()

    async with engine.begin() as conn:
        table_exists_result = await conn.execute(
            text(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'agencies'
                )
                """
            )
        )
        table_exists = bool(table_exists_result.scalar())
        if not table_exists:
            raise RuntimeError(
                "agencies table is missing. Run migrations first (alembic upgrade head)."
            )

        exists_result = await conn.execute(
            text("SELECT EXISTS (SELECT 1 FROM agencies WHERE id = :agency_id)"),
            {"agency_id": agency_id},
        )
        exists = bool(exists_result.scalar())
        if exists:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "seeded": False,
                        "agency_id": agency_id,
                        "reason": "agency already exists",
                    }
                )
            )
            return 0

        now = datetime.now(timezone.utc)
        await conn.execute(
            text(
                """
                INSERT INTO agencies (
                    id,
                    slug,
                    name,
                    plan,
                    settings,
                    created_at,
                    jurisdiction,
                    is_test
                )
                VALUES (
                    :id,
                    :slug,
                    :name,
                    :plan,
                    CAST(:settings AS JSONB),
                    :created_at,
                    :jurisdiction,
                    :is_test
                )
                """
            ),
            {
                "id": agency_id,
                "slug": CANONICAL_NONPROD_PUBLIC_CHECKER_AGENCY_SLUG,
                "name": CANONICAL_NONPROD_PUBLIC_CHECKER_AGENCY_NAME,
                "plan": "internal",
                "settings": json.dumps({"source": "bootstrap_public_checker_agency"}),
                "created_at": now,
                "jurisdiction": "other",
                "is_test": True,
            },
        )

    print(
        json.dumps(
            {
                "ok": True,
                "seeded": True,
                "agency_id": agency_id,
                "slug": CANONICAL_NONPROD_PUBLIC_CHECKER_AGENCY_SLUG,
            }
        )
    )
    _seed_marketplace_profile(agency_id)
    return 0


def _seed_marketplace_profile(agency_id: str) -> None:
    """GO punch-list item 5 (WOBS Part 3.7): seed the agency's marketplace
    profile so an onboarded receiver can appear in matched-choice results.
    Idempotent; failure is non-fatal (matched-choice degrades to waitlist)."""
    try:
        from spine_api.services.agency_marketplace import (
            AgencyMarketplaceProfile,
            AgencyMarketplaceStore,
        )

        existing = [
            p
            for p in AgencyMarketplaceStore.list_profiles()
            if p.agency_id == agency_id
        ]
        if existing:
            print(json.dumps({"ok": True, "marketplace_profile": "exists", "agency_id": agency_id}))
            return
        AgencyMarketplaceStore.upsert_profile(
            AgencyMarketplaceProfile(
                agency_id=agency_id,
                display_name="Waypoint Trips Desk",
                places_covered=[],
                customer_types=[],
                services=[],
                languages=["English"],
                response_sla_hours=48,
                blurb="Placeholder profile — edit places/customer-types/services when the receiver agreement is signed.",
            )
        )
        print(json.dumps({"ok": True, "marketplace_profile": "seeded", "agency_id": agency_id}))
    except Exception as exc:  # non-fatal: matched-choice degrades to waitlist
        print(json.dumps({"ok": False, "marketplace_profile": "failed", "error": str(exc)}))


def main() -> int:
    try:
        return asyncio.run(_seed_agency_if_missing())
    except Exception as exc:  # pragma: no cover - CLI error path
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
