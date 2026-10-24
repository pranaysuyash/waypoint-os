"""Tests for the FND-0366 ephemeral test-database provisioner.

These exercise the isolation contract itself: template freshness, run-DB
lifecycle, namespace safety (nothing outside ``waypoint_test_run_*`` is ever
dropped), and the engine-construction refusal of the canonical database name.

Every test here is additive by construction — the module under test never
opens a connection to the canonical database. asyncpg connections are
event-loop-affine, so each test drives its whole body through ONE
``asyncio.run`` that opens and closes its own admin connection.
"""

from __future__ import annotations

import asyncio

import pytest

from tests import _test_db_provision as prov

pytestmark = pytest.mark.require_postgres


def test_migration_stamp_is_deterministic():
    assert prov.migration_stamp() == prov.migration_stamp()


def test_template_ensure_is_idempotent_when_fresh():
    async def body():
        url = prov.resolve_canonical_url() or ""
        app_user = prov._make_url(url).username or ""
        conn = await prov._connect(url, database="postgres")
        try:
            await prov.ensure_template(conn, url, app_user)
            rebuilt_second = await prov.ensure_template(conn, url, app_user)
            assert rebuilt_second is False
        finally:
            await conn.close()

    asyncio.run(body())


def test_template_rebuilds_when_stamp_stale():
    async def body():
        url = prov.resolve_canonical_url() or ""
        app_user = prov._make_url(url).username or ""
        conn = await prov._connect(url, database="postgres")
        try:
            await prov.ensure_template(conn, url, app_user)

            template_conn = await prov._connect(url, prov.TEMPLATE_DB_NAME)
            try:
                await template_conn.execute(
                    " ".join(
                        ["UPDATE", prov.META_TABLE, "SET", "stamp", "=", "'stale'",
                         "WHERE", "id", "=", "1"]
                    )
                )
            finally:
                await template_conn.close()

            rebuilt = await prov.ensure_template(conn, url, app_user)
            assert rebuilt is True

            template_conn = await prov._connect(url, prov.TEMPLATE_DB_NAME)
            try:
                stamp = await template_conn.fetchval(
                    " ".join(
                        ["SELECT", "stamp", "FROM", prov.META_TABLE,
                         "WHERE", "id", "=", "1"]
                    )
                )
            finally:
                await template_conn.close()
            assert stamp == prov.migration_stamp()
        finally:
            await conn.close()

    asyncio.run(body())


def test_run_db_create_and_drop_roundtrip():
    async def body():
        url = prov.resolve_canonical_url() or ""
        app_user = prov._make_url(url).username or ""
        conn = await prov._connect(url, database="postgres")
        try:
            name = await prov.create_run_database(conn, app_user)
            assert name.startswith(prov.RUN_DB_PREFIX)
            assert await prov._database_exists(conn, name) is True
            await prov.drop_run_database(conn, name)
            assert await prov._database_exists(conn, name) is False
        finally:
            await conn.close()

    asyncio.run(body())


def test_drop_refuses_names_outside_run_namespace():
    async def body():
        url = prov.resolve_canonical_url() or ""
        conn = await prov._connect(url, database="postgres")
        try:
            with pytest.raises(prov.CanonicalTestDatabaseViolationError):
                await prov.drop_run_database(conn, "waypoint_os")
            with pytest.raises(prov.CanonicalTestDatabaseViolationError):
                await prov.drop_run_database(conn, prov.TEMPLATE_DB_NAME)
        finally:
            await conn.close()

    asyncio.run(body())


def test_stale_sweep_drops_only_aged_run_dbs():
    async def body():
        url = prov.resolve_canonical_url() or ""
        app_user = prov._make_url(url).username or ""
        conn = await prov._connect(url, database="postgres")
        aged_name = f"{prov.RUN_DB_PREFIX}1000000_sweepme"
        fresh_name = None
        try:
            fresh_name = await prov.create_run_database(conn, app_user)
            await conn.execute(
                " ".join(
                    ["CREATE", "DATABASE", aged_name,
                     "TEMPLATE", prov.TEMPLATE_DB_NAME,
                     "OWNER", app_user]
                )
            )
            dropped = await prov.sweep_stale_run_databases(conn)
            assert aged_name in dropped
            assert fresh_name not in dropped
            assert await prov._database_exists(conn, fresh_name) is True
        finally:
            for name in (aged_name, fresh_name):
                if name and await prov._database_exists(conn, name):
                    await prov.drop_run_database(conn, name)
            await conn.close()

    asyncio.run(body())


def test_run_db_url_rewrites_database_only():
    url = prov.resolve_canonical_url() or ""
    run_url = prov.run_db_url_for(url, f"{prov.RUN_DB_PREFIX}123_ab")
    run_parsed = prov._make_url(run_url)
    base_parsed = prov._make_url(url)
    assert run_parsed.database.startswith(prov.RUN_DB_PREFIX)
    assert run_parsed.host == base_parsed.host
    assert run_parsed.port == base_parsed.port
    assert run_parsed.username == base_parsed.username


def _real_canonical_db_name() -> str:
    """The TRUE canonical name — never derived from DATABASE_URL, which
    conftest provisioning has already pointed at the run database."""
    if prov.LAST_CANONICAL_DB_NAME:
        return prov.LAST_CANONICAL_DB_NAME
    url = prov.resolve_canonical_url() or ""
    return prov._make_url(url).database or "waypoint_os"


def test_engine_guard_refuses_canonical_name():
    canonical_db = _real_canonical_db_name()
    # conftest already installed the guard for this session; if an opt-out
    # left it uninstalled, install it here for the duration of the check.
    guard_pre_installed = bool(prov._ENGINE_GUARD_ORIGINALS)
    if not guard_pre_installed:
        prov.install_engine_creation_guard(canonical_db)
    try:
        from sqlalchemy import create_engine

        with pytest.raises(prov.CanonicalTestDatabaseViolationError):
            create_engine(f"postgresql+asyncpg://u:p@localhost:5432/{canonical_db}")
        with pytest.raises(prov.CanonicalTestDatabaseViolationError):
            create_engine(
                prov._make_url("postgresql://u:p@localhost:5432/x")
                .set(database=canonical_db)
                .render_as_string()
            )
    finally:
        if not guard_pre_installed:
            prov.uninstall_engine_creation_guard()


def test_engine_guard_allows_run_namespace():
    canonical_db = _real_canonical_db_name()
    guard_pre_installed = bool(prov._ENGINE_GUARD_ORIGINALS)
    if not guard_pre_installed:
        prov.install_engine_creation_guard(canonical_db)
    try:
        from sqlalchemy import create_engine

        # Must NOT raise — constructing (not connecting to) a run-namespace
        # engine is exactly what the app does under isolation.
        engine = create_engine(
            f"postgresql+asyncpg://u:p@localhost:5432/{prov.RUN_DB_PREFIX}x"
        )
        assert engine is not None
        engine.dispose()
    finally:
        if not guard_pre_installed:
            prov.uninstall_engine_creation_guard()


def test_engine_guard_restores_originals():
    canonical_db = _real_canonical_db_name()
    # Uninstall to exercise the real patch/unpatch cycle, then RE-INSTALL with
    # the real canonical name so the session keeps its protection afterwards.
    prov.uninstall_engine_creation_guard()
    import sqlalchemy
    import sqlalchemy.ext.asyncio as sa_asyncio

    sync_original = sqlalchemy.create_engine
    prov.install_engine_creation_guard("synthetic_guard_probe_db")
    assert sqlalchemy.create_engine is not sync_original
    prov.uninstall_engine_creation_guard()
    assert sqlalchemy.create_engine is sync_original
    assert sa_asyncio.create_async_engine is not None
    prov.install_engine_creation_guard(canonical_db)
