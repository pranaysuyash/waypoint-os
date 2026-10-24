"""Ephemeral per-run test databases — FND-0366 root-cause architecture.

Why this exists (two confirmed incidents, 2026-10-23 and 2026-10-24): test
processes shared the canonical ``waypoint_os`` database with the developer's
working environment, and twice an unidentified scoped ``DELETE`` wiped the
corpus. The invariant enforced here: **no test process can issue a destructive
statement against state whose loss anyone would notice.**

Layers (design record: Docs/architecture/TEST_DB_ISOLATION_FND0366_2026-10-24.md):

1. **Template** — ``waypoint_test_template`` holds schema (alembic) + the
   canonical-agency bootstrap seed, plus a stamp of the migration files so the
   next session detects schema drift and rebuilds. It is NEVER derived from a
   data copy of the canonical DB: zero canonical reads, ever.
2. **Run DB** — each pytest session gets
   ``waypoint_test_run_<epoch>_<rand>`` created ``TEMPLATE``-fast, and it is
   dropped at session end (atexit; epoch-aged orphans are swept next session).
3. **Canonical-URL refusal** — ``create_engine`` / ``create_async_engine`` are
   wrapped (test process only) so any engine targeting the canonical database
   *by name* raises ``CanonicalTestDatabaseViolationError`` at construction.

The canonical database is never opened by this module: reachability probes and
all DDL target the ``postgres`` maintenance database or template/run names.

Escape hatch: ``WAYPOINT_EPHEMERAL_DB=0`` restores legacy shared-DB behavior.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]

TEMPLATE_DB_NAME = "waypoint_test_template"
RUN_DB_PREFIX = "waypoint_test_run_"
META_TABLE = "waypoint_test_template_meta"
OPT_OUT_ENV = "WAYPOINT_EPHEMERAL_DB"
STALE_RUN_DB_HOURS = 6

# Advisory-lock keys (fixed so concurrent pytest sessions serialize).
_TEMPLATE_LOCK_KEY = 8123471
_RUN_CREATE_LOCK_KEY = 8123472


class CanonicalTestDatabaseViolationError(RuntimeError):
    """Raised when a test-process engine would target the canonical database."""


@dataclass
class ProvisionResult:
    """Outcome of :func:`provision` — conftest consumes this."""

    canonical_url: Optional[str] = None
    canonical_db_name: Optional[str] = None
    run_database_url: Optional[str] = None
    run_database_name: Optional[str] = None
    template_rebuilt: bool = False
    skipped_reason: Optional[str] = None


# ---------------------------------------------------------------------------
# URL helpers (sqlalchemy make_url only — no engine construction)
# ---------------------------------------------------------------------------


def _make_url(url: str) -> Any:
    from sqlalchemy.engine import make_url

    return make_url(url)


def resolve_canonical_url() -> Optional[str]:
    """The canonical URL the suite would have used, BEFORE any override.

    Honors the process env first (runner script / CI export it), then falls
    back to ``.env`` values WITHOUT loading them into ``os.environ`` — that
    loading is the app's job, and the app must see the run-DB URL instead.
    """
    configured = (os.environ.get("DATABASE_URL") or "").strip()
    if configured:
        return configured
    try:
        from dotenv import dotenv_values

        value = (dotenv_values(PROJECT_ROOT / ".env").get("DATABASE_URL") or "").strip()
        return value or None
    except Exception:
        return None


def _connect_kwargs(url: str, database: Optional[str] = None) -> dict:
    u = _make_url(url)
    return {
        "host": u.host or "localhost",
        "port": u.port or 5432,
        "user": u.username,
        "password": u.password,
        "database": database or u.database,
    }


async def _connect(url: str, database: Optional[str] = None):
    import asyncpg

    return await asyncpg.connect(**_connect_kwargs(url, database=database))


def _database_exists(conn: Any, dbname: str) -> bool:
    return conn.fetchval("SELECT 1 FROM pg_database WHERE datname = $1", dbname) == 1


def _quote_ident(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


# ---------------------------------------------------------------------------
# Migration stamp (schema-drift detection for the template)
# ---------------------------------------------------------------------------


def migration_stamp() -> str:
    """Deterministic hash of the alembic migration surface.

    Any change to ``alembic/versions/*.py`` (added/edited/touched migration)
    or ``alembic/env.py`` produces a new stamp; a matching stamp means the
    template schema is current and no rebuild is needed.
    """
    digest = hashlib.sha256()
    versions_dir = PROJECT_ROOT / "alembic" / "versions"
    for path in sorted(versions_dir.glob("*.py")):
        stat = path.stat()
        digest.update(f"{path.name}:{stat.st_size}:{stat.st_mtime_ns};".encode())
    env_py = PROJECT_ROOT / "alembic" / "env.py"
    if env_py.exists():
        stat = env_py.stat()
        digest.update(f"env.py:{stat.st_size}:{stat.st_mtime_ns}".encode())
    return digest.hexdigest()[:16]


# ---------------------------------------------------------------------------
# Template lifecycle
# ---------------------------------------------------------------------------


def _subprocess_env_for(template_db_name: str) -> dict:
    env = os.environ.copy()
    url = resolve_canonical_url() or ""
    template_url = _make_url(url).set(database=template_db_name).render_as_string(
        hide_password=False
    )
    env["DATABASE_URL"] = template_url
    env["TRIPSTORE_BACKEND"] = "sql"
    env.setdefault("JWT_SECRET", "test-jwt-secret-for-pytest-only-32byt")
    env.setdefault(
        "PROPOSAL_SIGNING_KEY", "test-proposal-signing-key-for-pytest-32bytes"
    )
    env.setdefault(
        "PUBLIC_CHECKER_AGENCY_ID", "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
    )
    return env


def _build_template_via_subprocesses(template_db_name: str) -> None:
    """Schema + auth bootstrap — identical to the CI path, never canonical reads."""
    env = _subprocess_env_for(template_db_name)
    migrate = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if migrate.returncode != 0:
        raise RuntimeError(
            "test-template build failed at 'alembic upgrade head':\n"
            f"{migrate.stdout[-2000:]}\n{migrate.stderr[-2000:]}"
        )
    bootstrap = subprocess.run(
        [sys.executable, "scripts/bootstrap_public_checker_agency.py"],
        cwd=str(PROJECT_ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
    )
    if bootstrap.returncode != 0:
        raise RuntimeError(
            "test-template build failed at bootstrap_public_checker_agency:\n"
            f"{bootstrap.stdout[-2000:]}\n{bootstrap.stderr[-2000:]}"
        )


def ensure_template(
    conn: Any, app_user: str
) -> bool:
    """Create or refresh ``waypoint_test_template``. Returns True if rebuilt.

    Caller must hold ``_TEMPLATE_LOCK_KEY``. ``conn`` is an admin connection to
    the maintenance database (NOT the canonical database).
    """
    stamp = migration_stamp()
    if _database_exists(conn, TEMPLATE_DB_NAME):
        try:
            existing = conn.fetchval(
                f"SELECT stamp FROM {_quote_ident(META_TABLE)} WHERE id = 1"
            )
        except Exception:
            existing = None
        if existing == stamp:
            return False

    conn.execute(f"DROP DATABASE IF EXISTS {_quote_ident(TEMPLATE_DB_NAME)} WITH (FORCE)")
    conn.execute(
        f"CREATE DATABASE {_quote_ident(TEMPLATE_DB_NAME)} OWNER {_quote_ident(app_user)}"
    )
    _build_template_via_subprocesses(TEMPLATE_DB_NAME)

    template_conn = asyncio.run(_connect(resolve_canonical_url() or "", TEMPLATE_DB_NAME))
    try:
        template_conn.execute(
            f"CREATE TABLE IF NOT EXISTS {_quote_ident(META_TABLE)} "
            "(id int PRIMARY KEY, stamp text NOT NULL, built_at timestamptz DEFAULT now())"
        )
        template_conn.execute(
            f"INSERT INTO {_quote_ident(META_TABLE)} (id, stamp) VALUES (1, $1) "
            "ON CONFLICT (id) DO UPDATE SET stamp = EXCLUDED.stamp, built_at = now()",
            stamp,
        )
    finally:
        asyncio.run(template_conn.close())
    return True


# ---------------------------------------------------------------------------
# Run-DB lifecycle
# ---------------------------------------------------------------------------


def run_db_url_for(canonical_url: str, run_db_name: str) -> str:
    return (
        _make_url(canonical_url)
        .set(database=run_db_name)
        .render_as_string(hide_password=False)
    )


def create_run_database(conn: Any, app_user: str) -> str:
    """Create a fresh run DB from the template. Returns its name.

    Caller must hold ``_RUN_CREATE_LOCK_KEY``: Postgres refuses concurrent
    ``CREATE DATABASE ... TEMPLATE`` from one template.
    """
    name = f"{RUN_DB_PREFIX}{int(time.time())}_{uuid.uuid4().hex[:8]}"
    conn.execute(
        f"CREATE DATABASE {_quote_ident(name)} "
        f"TEMPLATE {_quote_ident(TEMPLATE_DB_NAME)} OWNER {_quote_ident(app_user)}"
    )
    return name


def drop_run_database(conn: Any, name: str) -> None:
    if not name.startswith(RUN_DB_PREFIX):
        raise CanonicalTestDatabaseViolationError(
            f"refusing to drop {name!r}: not a {RUN_DB_PREFIX}* database"
        )
    conn.execute(f"DROP DATABASE IF EXISTS {_quote_ident(name)} WITH (FORCE)")


def sweep_stale_run_databases(conn: Any, max_age_hours: float = STALE_RUN_DB_HOURS) -> list:
    """Drop orphaned run DBs (epoch in the name older than the threshold).

    Only names under ``waypoint_test_run_*`` are ever considered; canonical and
    template names are structurally outside this namespace.
    """
    cutoff = time.time() - max_age_hours * 3600
    rows = conn.fetch(
        "SELECT datname FROM pg_database WHERE datname LIKE $1", RUN_DB_PREFIX + "%"
    )
    dropped = []
    for row in rows:
        name = row["datname"]
        try:
            epoch = int(name[len(RUN_DB_PREFIX):].split("_", 1)[0])
        except ValueError:
            continue
        if epoch < cutoff:
            drop_run_database(conn, name)
            dropped.append(name)
    return dropped


# ---------------------------------------------------------------------------
# Canonical-URL refusal (engine construction guard)
# ---------------------------------------------------------------------------

_ENGINE_GUARD_ORIGINALS: dict = {}


def install_engine_creation_guard(canonical_db_name: str) -> None:
    """Refuse engines targeting the canonical database, by name, forever.

    Covers code paths that bypass the ``DATABASE_URL`` constant and hardcode a
    canonical URL: the failure is loud at construction, never a silent read or
    write against the working environment.
    """
    import sqlalchemy
    import sqlalchemy.ext.asyncio as sa_asyncio
    from sqlalchemy import engine as sa_engine_module

    if _ENGINE_GUARD_ORIGINALS:
        return

    from sqlalchemy.engine import make_url

    originals = {
        "sync": sqlalchemy.create_engine,
        "async": sa_asyncio.create_async_engine,
    }

    def _refuse_if_canonical(url: Any) -> None:
        if url is None:
            return
        try:
            parsed = make_url(url) if isinstance(url, str) else url
            db = parsed.database or ""
        except Exception:
            return
        if db == canonical_db_name:
            raise CanonicalTestDatabaseViolationError(
                f"REFUSED: engine targets the canonical database {canonical_db_name!r}. "
                "Tests run against an ephemeral per-session database (FND-0366 "
                "isolation); the developer working environment is not reachable "
                "from test code. See tests/_test_db_provision.py."
            )

    def guarded_create_engine(url=None, *args, **kwargs):
        _refuse_if_canonical(url if url is not None else kwargs.get("url"))
        return originals["sync"](url, *args, **kwargs)

    def guarded_create_async_engine(url=None, *args, **kwargs):
        _refuse_if_canonical(url if url is not None else kwargs.get("url"))
        return originals["async"](url, *args, **kwargs)

    # sqlalchemy.create_engine and sqlalchemy.engine.create_engine are the same
    # function object; patch both module attributes so either import path is
    # guarded.
    sqlalchemy.create_engine = guarded_create_engine
    sa_engine_module.create_engine = guarded_create_engine
    sa_asyncio.create_async_engine = guarded_create_async_engine

    _ENGINE_GUARD_ORIGINALS.update(originals)


def uninstall_engine_creation_guard() -> None:
    """Restore original creators (used by the guard's own unit tests)."""
    if not _ENGINE_GUARD_ORIGINALS:
        return
    import sqlalchemy
    import sqlalchemy.ext.asyncio as sa_asyncio
    from sqlalchemy import engine as sa_engine_module

    sqlalchemy.create_engine = _ENGINE_GUARD_ORIGINALS["sync"]
    sa_engine_module.create_engine = _ENGINE_GUARD_ORIGINALS["sync"]
    sa_asyncio.create_async_engine = _ENGINE_GUARD_ORIGINALS["async"]
    _ENGINE_GUARD_ORIGINALS.clear()


# ---------------------------------------------------------------------------
# CREATEDB bootstrap (local trust superuser only — never password guessing)
# ---------------------------------------------------------------------------


def _grant_createdb_if_needed(url: str) -> None:
    """Ensure the URL's role may create databases (one-time, idempotent).

    Local developer clusters run with trust auth (brew initdb), so a
    passwordless local superuser connection is attempted WITHOUT host/network
    credential guessing: host ``localhost``, the URL's user's needed privilege
    is granted by ``postgres``. On CI the service role is already superuser and
    this is a no-op check.
    """
    u = _make_url(url)
    probe_kwargs = _connect_kwargs(url, database="postgres")

    async def _check_and_grant() -> bool:
        import asyncpg

        conn = await asyncpg.connect(**probe_kwargs)
        try:
            role = u.username
            has = await conn.fetchval(
                "SELECT rolcreatedb FROM pg_roles WHERE rolname = $1", role
            )
            if has:
                return False
            await conn.execute("ALTER ROLE " + _quote_ident(role) + " CREATEDB")
            return True
        finally:
            await conn.close()

    asyncio.run(_check_and_grant())


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

_ACTIVE_RUN_DB: Optional[str] = None


def teardown() -> None:
    """Drop the active run DB (atexit-registered; best-effort)."""
    global _ACTIVE_RUN_DB
    if not _ACTIVE_RUN_DB:
        return
    url = resolve_canonical_url() or ""
    if not url:
        return
    try:
        conn = asyncio.run(_connect(url, database="postgres"))
        try:
            drop_run_database(conn, _ACTIVE_RUN_DB)
        finally:
            asyncio.run(conn.close())
    except Exception:
        # Orphans are swept by age on the next session; never mask the
        # suite's own exit status with teardown noise.
        pass
    finally:
        _ACTIVE_RUN_DB = None


def provision() -> ProvisionResult:
    """Provision an ephemeral run DB and override ``DATABASE_URL``.

    Call from conftest BEFORE any ``spine_api`` import. Never raises for
    "cannot reach Postgres" (legacy skip machinery must keep working); raises
    for anything that would otherwise silently degrade to shared-DB mode.
    """
    result = ProvisionResult()
    if (os.environ.get(OPT_OUT_ENV, "").strip().lower() in ("0", "false", "no")):
        result.skipped_reason = f"{OPT_OUT_ENV}=0 (legacy shared-DB mode)"
        return result

    canonical_url = resolve_canonical_url()
    if not canonical_url:
        result.skipped_reason = "DATABASE_URL not configured"
        return result

    result.canonical_url = canonical_url
    result.canonical_db_name = _make_url(canonical_url).database or ""

    # Reachability: TCP probe only. Same semantics as the pre-existing
    # require_postgres skip machinery; no canonical connection is opened.
    import socket

    probe = _make_url(canonical_url)
    host = probe.host or "localhost"
    port = probe.port or 5432
    family = socket.AF_INET6 if ":" in host else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        reachable = sock.connect_ex((host, port)) == 0
    finally:
        sock.close()
    if not reachable:
        result.skipped_reason = (
            "PostgreSQL not reachable — require_postgres skips apply as before"
        )
        return result

    _grant_createdb_if_needed(canonical_url)

    app_user = _make_url(canonical_url).username or ""
    admin_conn = asyncio.run(_connect(canonical_url, database="postgres"))
    try:
        # Serialize template work across concurrent pytest sessions.
        admin_conn.execute("SELECT pg_advisory_lock($1)", _TEMPLATE_LOCK_KEY)
        try:
            result.template_rebuilt = ensure_template(admin_conn, app_user)
        finally:
            admin_conn.execute("SELECT pg_advisory_unlock($1)", _TEMPLATE_LOCK_KEY)

        # Serialize template→run copies (Postgres refuses concurrent copies).
        admin_conn.execute("SELECT pg_advisory_lock($1)", _RUN_CREATE_LOCK_KEY)
        try:
            run_name = create_run_database(admin_conn, app_user)
        finally:
            admin_conn.execute("SELECT pg_advisory_unlock($1)", _RUN_CREATE_LOCK_KEY)

        sweep_stale_run_databases(admin_conn)
    finally:
        asyncio.run(admin_conn.close())

    global _ACTIVE_RUN_DB
    _ACTIVE_RUN_DB = run_name
    result.run_database_name = run_name
    result.run_database_url = run_db_url_for(canonical_url, run_name)

    os.environ["DATABASE_URL"] = result.run_database_url
    result.skipped_reason = None
    return result
