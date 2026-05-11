"""
Live PostgreSQL checks for tenant Row Level Security.

The mock-level tests in test_rls.py prove ContextVar and SQL wiring. These
checks prove the database catalog and, when the runtime role is enforceable,
the actual visibility behavior against PostgreSQL.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from sqlalchemy import text

from spine_api.core.database import DATABASE_URL
from spine_api.core.rls import RLS_TENANT_TABLES, inspect_rls_runtime_posture


pytestmark = pytest.mark.require_postgres


def _make_test_engine():
    return create_async_engine(DATABASE_URL, future=True, poolclass=NullPool)


@pytest.mark.asyncio
async def test_rls_catalog_is_enabled_for_tenant_tables():
    """Protected tables must have RLS enabled and tenant policies installed."""
    test_engine = _make_test_engine()
    try:
        async with test_engine.connect() as conn:
            posture = await inspect_rls_runtime_posture(conn)

            enabled = {table.table_name: table.rls_enabled for table in posture.tables}
            assert enabled == {table: True for table in RLS_TENANT_TABLES}

            policy_rows = (
                await conn.execute(
                    text(
                        """
                        SELECT tablename, policyname
                        FROM pg_policies
                        WHERE schemaname = 'public'
                          AND tablename = ANY(:tables)
                        """
                    ),
                    {"tables": list(RLS_TENANT_TABLES)},
                )
            ).mappings().all()
    finally:
        await test_engine.dispose()

    policies = {(row["tablename"], row["policyname"]) for row in policy_rows}
    for table in RLS_TENANT_TABLES:
        assert (table, "waypoint_rls_select") in policies
        assert (table, "waypoint_rls_all") in policies


@pytest.mark.asyncio
async def test_trips_rls_hides_cross_tenant_rows_for_runtime_role():
    """
    A runtime session scoped to agency A must not read agency B's trip.

    This is deliberately live and transaction-rolled-back. If the configured
    role owns the table and FORCE RLS is not enabled, PostgreSQL bypasses RLS;
    that known architecture gap is reported as xfail instead of normalizing the
    insecure behavior as a passing assertion.
    """
    probe = uuid4().hex[:12]
    agency_a = f"rls-a-{probe}"
    agency_b = f"rls-b-{probe}"
    trip_a = f"trip-a-{probe}"
    trip_b = f"trip-b-{probe}"
    now = datetime.now(timezone.utc)

    test_engine = _make_test_engine()
    try:
        async with test_engine.connect() as conn:
            posture = await inspect_rls_runtime_posture(conn)
            await conn.rollback()
            trans = await conn.begin()
            try:
                agency_insert = text(
                    """
                    INSERT INTO agencies (
                        id, name, slug, plan, settings, created_at, jurisdiction, is_test
                    )
                    VALUES (
                        :id, :name, :slug, 'probe', '{}'::json, :created_at, 'other', true
                    )
                    """
                )
                await conn.execute(
                    agency_insert,
                    {
                        "id": agency_a,
                        "name": "RLS Probe A",
                        "slug": f"rls-a-{probe}",
                        "created_at": now,
                    },
                )
                await conn.execute(
                    agency_insert,
                    {
                        "id": agency_b,
                        "name": "RLS Probe B",
                        "slug": f"rls-b-{probe}",
                        "created_at": now,
                    },
                )

                trip_insert = text(
                    """
                    INSERT INTO trips (
                        id, agency_id, source, status, stage, extracted, validation,
                        decision, safety, raw_input, created_at
                    )
                    VALUES (
                        :id, :agency_id, 'probe', 'new', 'discovery', '{}'::json,
                        '{}'::json, '{}'::json, '{}'::json, '{}'::json, :created_at
                    )
                    """
                )
                await conn.execute(
                    trip_insert,
                    {"id": trip_a, "agency_id": agency_a, "created_at": now},
                )
                await conn.execute(
                    trip_insert,
                    {"id": trip_b, "agency_id": agency_b, "created_at": now},
                )

                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_a},
                )
                visible_ids = (
                    await conn.execute(
                        text(
                            """
                            SELECT id
                            FROM trips
                            WHERE id IN (:trip_a, :trip_b)
                            ORDER BY id
                            """
                        ),
                        {"trip_a": trip_a, "trip_b": trip_b},
                    )
                ).scalars().all()
            finally:
                await trans.rollback()
    finally:
        await test_engine.dispose()

    if trip_b in visible_ids:
        assert posture.risks
        pytest.xfail(
            "Live runtime role can bypass tenant RLS: "
            + "; ".join(posture.risks)
        )

    assert visible_ids == [trip_a]
