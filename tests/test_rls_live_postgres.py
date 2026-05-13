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
from spine_api.core.rls import (
    RLS_TENANT_TABLES,
    RLS_EXCLUDED_AGENCY_TABLES,
    inspect_rls_runtime_posture,
)


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

                # Set RLS context for agency A BEFORE inserting trips
                # (FORCE RLS blocks INSERT without app.current_agency_id)
                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_a},
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

                # Switch RLS context to agency B for trip_b insert
                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_b},
                )
                await conn.execute(
                    trip_insert,
                    {"id": trip_b, "agency_id": agency_b, "created_at": now},
                )

                # Now set context to agency A for the visibility test
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


@pytest.mark.asyncio
async def test_all_tenant_tables_have_rls_enabled():
    """Every table in RLS_TENANT_TABLES must have RLS enabled."""
    test_engine = _make_test_engine()
    try:
        async with test_engine.connect() as conn:
            posture = await inspect_rls_runtime_posture(conn)

        for table in posture.tables:
            assert table.rls_enabled, f"{table.table_name} does not have RLS enabled"
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_all_tenant_tables_have_force_rls():
    """Every table in RLS_TENANT_TABLES must have FORCE ROW LEVEL SECURITY."""
    test_engine = _make_test_engine()
    try:
        async with test_engine.connect() as conn:
            posture = await inspect_rls_runtime_posture(conn)

        for table in posture.tables:
            assert table.force_rls, f"{table.table_name} does not have FORCE RLS"
    finally:
        await test_engine.dispose()


@pytest.mark.asyncio
async def test_rls_policies_exist_on_all_tenant_tables():
    """Both waypoint_rls_select and waypoint_rls_all must exist on every tenant table."""
    test_engine = _make_test_engine()
    try:
        async with test_engine.connect() as conn:
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
        assert (table, "waypoint_rls_select") in policies, (
            f"waypoint_rls_select policy missing on {table}"
        )
        assert (table, "waypoint_rls_all") in policies, (
            f"waypoint_rls_all policy missing on {table}"
        )


@pytest.mark.asyncio
async def test_no_tenant_tables_missing_from_rls_tenant_tables():
    """Every SQLAlchemy model with agency_id must be protected or explicitly exempted."""
    from spine_api.models.tenant import Base

    all_tables = set()
    for mapper in Base.registry.mappers:
        table = mapper.local_table
        if table is not None and "agency_id" in table.c:
            all_tables.add(table.name)

    protected = set(RLS_TENANT_TABLES)
    exempted = set(RLS_EXCLUDED_AGENCY_TABLES.keys())
    unprotected = all_tables - protected - exempted
    assert not unprotected, (
        f"Tables with agency_id but no RLS: {unprotected}. "
        "Add to RLS_TENANT_TABLES or RLS_EXCLUDED_AGENCY_TABLES."
    )


# ---------------------------------------------------------------------------
# Cross-tenant isolation for Phase 4/5 sensitive tables
# ---------------------------------------------------------------------------

_SENSITIVE_TABLES = (
    "booking_documents",
    "document_extractions",
    "document_extraction_attempts",
    "booking_tasks",
    "booking_confirmations",
    "execution_events",
)


def _insert_sql_for_table(
    table_name: str, agency_id: str, trip_id: str, row_id: str, now: datetime,
) -> tuple[str, dict]:
    """Return (SQL, params) for a minimal valid row in the given table."""
    if table_name == "booking_documents":
        return (
            text(
                """
                INSERT INTO booking_documents (
                    id, trip_id, agency_id, uploaded_by_type, filename_hash,
                    filename_ext, storage_key, mime_type, size_bytes, sha256,
                    document_type, status, created_at
                ) VALUES (
                    :id, :trip_id, :agency_id, 'agent', :hash, '.pdf',
                    :storage, 'application/pdf', 100, :sha256, 'passport',
                    'accepted', :now
                )
                """
            ),
            {
                "id": row_id, "trip_id": trip_id, "agency_id": agency_id,
                "hash": f"hash-{row_id[:8]}", "storage": f"key-{row_id[:8]}",
                "sha256": f"sha256-{row_id[:8]}", "now": now,
            },
        )
    if table_name == "document_extractions":
        return (
            text(
                """
                INSERT INTO document_extractions (
                    id, document_id, trip_id, agency_id, status, attempt_count,
                    run_count, extracted_fields_encrypted, fields_present, field_count,
                    extracted_by, provider_name, created_at
                ) VALUES (
                    :id, :doc_id, :trip_id, :agency_id, 'running', 0, 1,
                    NULL, '{}'::json, 0, 'pending', 'pending', :now
                )
                """
            ),
            {
                "id": row_id, "doc_id": f"doc-{row_id[:8]}",
                "trip_id": trip_id, "agency_id": agency_id, "now": now,
            },
        )
    if table_name == "document_extraction_attempts":
        return (
            text(
                """
                INSERT INTO document_extraction_attempts (
                    id, extraction_id, agency_id, trip_id, run_number,
                    attempt_number, provider_name, status, created_at
                ) VALUES (
                    :id, :ext_id, :agency_id, :trip_id, 1, 1, 'probe', 'failed', :now
                )
                """
            ),
            {
                "id": row_id, "ext_id": f"ext-{row_id[:8]}",
                "agency_id": agency_id, "trip_id": trip_id, "now": now,
            },
        )
    if table_name == "booking_tasks":
        return (
            text(
                """
                INSERT INTO booking_tasks (
                    id, trip_id, agency_id, task_type, title, status, priority,
                    source, created_by, created_at
                ) VALUES (
                    :id, :trip_id, :agency_id, 'confirm_flights', 'Test task',
                    'not_started', 'medium', 'agent', :created_by, :now
                )
                """
            ),
            {
                "id": row_id, "trip_id": trip_id, "agency_id": agency_id,
                "created_by": agency_id, "now": now,
            },
        )
    if table_name == "booking_confirmations":
        return (
            text(
                """
                INSERT INTO booking_confirmations (
                    id, agency_id, trip_id, confirmation_type, confirmation_status,
                    created_by, created_at
                ) VALUES (
                    :id, :agency_id, :trip_id, 'flight', 'draft', :created_by, :now
                )
                """
            ),
            {
                "id": row_id, "agency_id": agency_id, "trip_id": trip_id,
                "created_by": agency_id, "now": now,
            },
        )
    if table_name == "execution_events":
        return (
            text(
                """
                INSERT INTO execution_events (
                    id, agency_id, trip_id, subject_type, subject_id, event_type,
                    event_category, status_to, actor_type, source, created_at
                ) VALUES (
                    :id, :agency_id, :trip_id, 'booking_task', :subject_id,
                    'task_created', 'task', 'not_started', 'system',
                    'system_generation', :now
                )
                """
            ),
            {
                "id": row_id, "agency_id": agency_id, "trip_id": trip_id,
                "subject_id": row_id, "now": now,
            },
        )
    raise ValueError(f"Unknown table: {table_name}")


@pytest.mark.asyncio
async def test_cross_tenant_isolation_for_sensitive_tables():
    """
    Cross-tenant rows must be invisible on all Phase 4/5 sensitive tables.

    Inserts rows for two agencies, sets app.current_agency_id to one,
    and verifies only that agency's rows are visible. xfails when the
    runtime role can bypass RLS (unsafe dev posture).
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

            if posture.risks:
                pytest.xfail(
                    "Runtime role can bypass RLS: " + "; ".join(posture.risks)
                )

            trans = await conn.begin()
            try:
                # Insert agencies
                agency_insert = text(
                    """
                    INSERT INTO agencies (
                        id, name, slug, plan, settings, created_at, jurisdiction, is_test
                    ) VALUES (
                        :id, :name, :slug, 'probe', '{}'::json, :created_at, 'other', true
                    )
                    """
                )
                await conn.execute(
                    agency_insert,
                    {"id": agency_a, "name": "RLS Probe A", "slug": f"rls-a-{probe}", "created_at": now},
                )
                await conn.execute(
                    agency_insert,
                    {"id": agency_b, "name": "RLS Probe B", "slug": f"rls-b-{probe}", "created_at": now},
                )

                # Set RLS context to agency A for all agency A inserts
                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_a},
                )

                # Insert trips
                trip_insert = text(
                    """
                    INSERT INTO trips (
                        id, agency_id, source, status, stage, extracted, validation,
                        decision, safety, raw_input, created_at
                    ) VALUES (
                        :id, :agency_id, 'probe', 'new', 'discovery', '{}'::json,
                        '{}'::json, '{}'::json, '{}'::json, '{}'::json, :created_at
                    )
                    """
                )
                await conn.execute(
                    trip_insert,
                    {"id": trip_a, "agency_id": agency_a, "created_at": now},
                )

                # Switch to agency B for trip_b
                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_b},
                )
                await conn.execute(
                    trip_insert,
                    {"id": trip_b, "agency_id": agency_b, "created_at": now},
                )

                # Switch back to agency A for doc_a
                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_a},
                )

                # For booking_documents: insert docs for both agencies
                # (document_extractions and attempts need these as parents)
                doc_a = f"doc-a-{probe}"
                doc_b = f"doc-b-{probe}"
                await conn.execute(
                    text(
                        """
                        INSERT INTO booking_documents (
                            id, trip_id, agency_id, uploaded_by_type, filename_hash,
                            filename_ext, storage_key, mime_type, size_bytes, sha256,
                            document_type, status, created_at
                        ) VALUES (
                            :id, :trip_id, :agency_id, 'agent', :hash, '.pdf',
                            :storage, 'application/pdf', 100, :sha256, 'passport',
                            'accepted', :now
                        )
                        """
                    ),
                    {
                        "id": doc_a, "trip_id": trip_a, "agency_id": agency_a,
                        "hash": f"hash-doc-a-{probe}", "storage": f"key-doc-a-{probe}",
                        "sha256": f"sha-doc-a-{probe}", "now": now,
                    },
                )

                # Switch to agency B for doc_b
                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_b},
                )
                await conn.execute(
                    text(
                        """
                        INSERT INTO booking_documents (
                            id, trip_id, agency_id, uploaded_by_type, filename_hash,
                            filename_ext, storage_key, mime_type, size_bytes, sha256,
                            document_type, status, created_at
                        ) VALUES (
                            :id, :trip_id, :agency_id, 'agent', :hash, '.pdf',
                            :storage, 'application/pdf', 100, :sha256, 'passport',
                            'accepted', :now
                        )
                        """
                    ),
                    {
                        "id": doc_b, "trip_id": trip_b, "agency_id": agency_b,
                        "hash": f"hash-doc-b-{probe}", "storage": f"key-doc-b-{probe}",
                        "sha256": f"sha-doc-b-{probe}", "now": now,
                    },
                )

                # For document_extractions: insert extractions for both agencies
                ext_a = f"ext-a-{probe}"
                ext_b = f"ext-b-{probe}"
                for ext_id, doc_id, t_id, a_id in [
                    (ext_a, doc_a, trip_a, agency_a),
                    (ext_b, doc_b, trip_b, agency_b),
                ]:
                    # Switch RLS context before each insert
                    await conn.execute(
                        text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                        {"agency_id": a_id},
                    )
                    await conn.execute(
                        text(
                            """
                            INSERT INTO document_extractions (
                                id, document_id, trip_id, agency_id, status,
                                attempt_count, run_count, extracted_fields_encrypted,
                                fields_present, field_count, extracted_by, provider_name,
                                created_at
                            ) VALUES (
                                :id, :doc_id, :trip_id, :agency_id, 'running', 0, 1,
                                NULL, '{}'::json, 0, 'pending', 'pending', :now
                            )
                            """
                        ),
                        {
                            "id": ext_id, "doc_id": doc_id, "trip_id": t_id,
                            "agency_id": a_id, "now": now,
                        },
                    )

                # Insert rows for remaining tables (booking_tasks, confirmations, events, attempts)
                for table_name in ("document_extraction_attempts", "booking_tasks", "booking_confirmations", "execution_events"):
                    row_a = f"{table_name[:4]}-a-{probe}"
                    row_b = f"{table_name[:4]}-b-{probe}"
                    for row_id, t_id, a_id in [
                        (row_a, trip_a, agency_a),
                        (row_b, trip_b, agency_b),
                    ]:
                        # Switch RLS context before each insert
                        await conn.execute(
                            text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                            {"agency_id": a_id},
                        )
                        sql, params = _insert_sql_for_table(table_name, a_id, t_id, row_id, now)
                        # Fix FK references for attempts
                        if table_name == "document_extraction_attempts":
                            ext_ref = ext_a if a_id == agency_a else ext_b
                            params["ext_id"] = ext_ref
                        await conn.execute(sql, params)

                # Set RLS context to agency A
                await conn.execute(
                    text("SELECT set_config('app.current_agency_id', :agency_id, true)"),
                    {"agency_id": agency_a},
                )

                # Verify cross-tenant isolation for each sensitive table
                for table_name in _SENSITIVE_TABLES:
                    visible = (
                        await conn.execute(
                            text(
                                f"SELECT agency_id FROM {table_name} "
                                f"WHERE trip_id IN (:trip_a, :trip_b)"
                            ),
                            {"trip_a": trip_a, "trip_b": trip_b},
                        )
                    ).scalars().all()
                    assert all(v == agency_a for v in visible), (
                        f"{table_name}: cross-tenant row leak: visible={visible}"
                    )

            finally:
                await trans.rollback()
    finally:
        await test_engine.dispose()
