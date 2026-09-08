"""
llm.usage_store — LLM usage tracking storage backends.

Three backends are provided, sharing the same interface:
  LLMUsageStore        — SQLite, single-container, WAL mode, cross-thread safe
  InMemoryUsageStore   — In-memory, unit tests and single-process dev
  RedisUsageStore      — Redis, multi-instance production deployments (P4-03)

Usage (via guard):
    store = RedisUsageStore.from_env()   # production
    store = LLMUsageStore()              # single-container
    store = InMemoryUsageStore()         # tests

All backends expose the same three methods:
    check_and_reserve(...)   → dict   (atomic)
    finalize_reservation(*)  → None
    get_summary(*)           → dict
"""

from __future__ import annotations

import contextvars
import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# PA-20 cost-correlation context
# ---------------------------------------------------------------------------
# Wave 1 (zero-migration): run/trip correlation rode inside the existing
# metadata_json column. Wave 2: usage_events also carries real nullable
# ``run_id``/``trip_id`` String columns (the alembic revision adding them in
# PG is owned by the migrations workstream; this store's SQLite schema adds
# them directly and self-heals older DB files via ALTER TABLE). Rows written
# before the columns existed keep their correlation in metadata_json only and
# read back as NULL columns — every insert path populates BOTH so either
# surface can be used for reconciliation. Callers on the serving path bind
# the context once per run (spine_api.services.pipeline_execution_service →
# set_usage_context) and every reservation/finalization written while the
# context is set gains the correlation. Trip id is unknown at run start —
# trip correlation for earlier events lands via run_id → run-meta lookup.

_usage_context: contextvars.ContextVar = contextvars.ContextVar(
    "waypoint_usage_correlation", default=None
)


def set_usage_context(run_id: Optional[str] = None, trip_id: Optional[str] = None) -> None:
    """Bind the current run/trip for usage-event correlation (PA-20)."""
    _usage_context.set({"run_id": run_id, "trip_id": trip_id})


def get_usage_context() -> Optional[dict]:
    """Return the active correlation context, or None when unset."""
    return _usage_context.get()


def clear_usage_context() -> None:
    """Reset the correlation context (e.g. between pipeline runs in tests)."""
    _usage_context.set(None)


def _correlation_ids() -> tuple[Optional[str], Optional[str]]:
    """Return (run_id, trip_id) from the active context (PA-20 Wave 2)."""
    ctx = _usage_context.get()
    if not ctx:
        return None, None
    return ctx.get("run_id"), ctx.get("trip_id")


def _event_with_metadata(event: dict) -> dict:
    """Return a copy of an event dict with ``metadata_json`` parsed (PA-20)."""
    event = dict(event)
    raw_metadata = event.get("metadata_json")
    if raw_metadata:
        try:
            event["metadata"] = json.loads(raw_metadata)
        except (TypeError, ValueError):
            event["metadata"] = None
    return event


def _merge_correlation_metadata(existing_json: Optional[str]) -> Optional[str]:
    """Merge the active correlation into a metadata_json value.

    Returns the merged JSON string, the untouched existing value when there is
    nothing to merge, or None when there is no context and no existing value.
    """
    ctx = _usage_context.get()
    correlation = None
    if ctx and (ctx.get("run_id") or ctx.get("trip_id")):
        correlation = {"run_id": ctx.get("run_id"), "trip_id": ctx.get("trip_id")}

    if existing_json:
        try:
            existing = json.loads(existing_json)
            if not isinstance(existing, dict):
                existing = {"legacy": existing}
        except (TypeError, ValueError):
            existing = {}
        if correlation is not None:
            existing["correlation"] = correlation
        return json.dumps(existing)

    if correlation is not None:
        return json.dumps({"correlation": correlation})
    return None

# Persistent data directory relative to project root.
# If the data directory itself is not persisted (e.g., ephemeral container),
# usage history will be lost on redeploy.
_DEFAULT_DATA_PATH = Path(__file__).parent.parent.parent / "data" / "guard"

# Schema version; bump only if table shape changes and a migration is added.
_SCHEMA_VERSION = 1

# SQLite performance/security settings.
_WAL_MODE = "on"   # Write-Ahead Logging
_BUSY_TIMEOUT_MS = 5000  # 5 seconds


class GuardStorageError(Exception):
    """Raised when guard storage cannot satisfy a request."""
    pass  # noqa: WPS420


class LLMUsageStore:
    """
    SQLite-backed usage store for LLM guard.

    Stores every call attempt with status, timestamps, and cost.
    Supports atomic check-and-reserve:
    - open transaction
    - read hourly/daily usage
    - if allowed, INSERT a 'reserved' event
    - commit
    - caller calls LLM
    - update to 'completed' or 'failed'

    Thread-safe (each thread gets its own SQLite connection).
    Cross-process safe on the same filesystem (SQLite file locking).
    Not safe across different hosts/containers.
    """

    _init_lock = threading.Lock()
    _initialized: set[int] = set()

    def __init__(self, db_path: Optional[Path] = None, create: bool = True):
        """
        Initialize the usage store.

        Args:
            db_path: Path to the SQLite file. Defaults to data/guard/usage.db.
            create: Create directories and schema if they don't exist.
        """
        self._db_path = db_path or _DEFAULT_DATA_PATH / "usage.db"
        self._db_path = self._db_path.resolve()

        if create:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            self._init_schema()

    # ─────────────────────────────────────────────────────────────────────────────────
    # Schema
    # ─────────────────────────────────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        """Ensure WAL mode and schema exist in a single lock-protected pass."""
        with self._init_lock:
            key = hash(str(self._db_path))
            if key in self._initialized:
                return
            conn = self._connect()
            try:
                conn.execute(f"PRAGMA journal_mode={_WAL_MODE}")
                conn.execute(f"PRAGMA busy_timeout={_BUSY_TIMEOUT_MS}")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usage_events (
                        id           INTEGER PRIMARY KEY AUTOINCREMENT,
                        request_id   TEXT NOT NULL,
                        agency_id    TEXT DEFAULT 'default',
                        model        TEXT NOT NULL,
                        feature      TEXT NOT NULL,
                        created_at   TEXT NOT NULL,
                        usage_date   TEXT NOT NULL,
                        status       TEXT NOT NULL CHECK(status IN (
                            'reserved','completed','blocked','failed','guard_unavailable'
                        )),
                        estimated_cost REAL NOT NULL DEFAULT 0.0,
                        actual_cost    REAL,
                        block_reason TEXT,
                        warning_flags TEXT,
                        metadata_json TEXT,
                        run_id       TEXT,
                        trip_id      TEXT
                    )
                """)
                # PA-20 Wave 2: self-heal SQLite files created before the
                # correlation columns existed (old rows read back as NULL,
                # matching the PG migration's backfill-free contract). Column
                # names are hardcoded literals — identifiers cannot be bound
                # as SQL parameters and no user input reaches here.
                existing_columns = {
                    row["name"]
                    for row in conn.execute("PRAGMA table_info(usage_events)").fetchall()
                }
                if "run_id" not in existing_columns:
                    conn.execute("ALTER TABLE usage_events ADD COLUMN run_id TEXT")
                if "trip_id" not in existing_columns:
                    conn.execute("ALTER TABLE usage_events ADD COLUMN trip_id TEXT")
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_usage_lookup
                    ON usage_events(usage_date, agency_id, model, feature, status)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_usage_hourly
                    ON usage_events(created_at, agency_id, model, feature, status)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_request_id
                    ON usage_events( request_id )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_usage_run_id
                    ON usage_events( run_id )
                """)
                conn.commit()
                self._initialized.add(key)
            finally:
                conn.close()

    # ─────────────────────────────────────────────────────────────────────────────────
    # Connections
    # ─────────────────────────────────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    # ─────────────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────────────

    # ─────────────────────────────────────────────────────────────────────────────────
    # Atomic check-and-reserve
    # ─────────────────────────────────────────────────────────────────────────────────

    def check_and_reserve(
        self,
        *,
        request_id: str,
        agency_id: str,
        model: str,
        feature: str,
        estimated_cost: float,
        hourly_limit: Optional[int],
        model_hourly_limit: Optional[int] = None,
        daily_budget: Optional[float],
        budget_mode: str,
        warning_thresholds: list[float],
        now_func,
    ) -> tuple[bool, 
         Optional[dict]]:
        """
        Atomic check and optional reservation.

        Returns (allowed, reservation_dict).

        If allowed is True, a reservation event is INSERTed within the same
        transaction and committed before returning.

        If allowed is False, a blocked event is INSERTed and committed.

        Raises GuardStorageError on underlying DB failure so that callers
        can decide between fail-open / fail-closed.

        Returns reservation dict like:
            {
                'event_id': int,
                'status': 'reserved',
                'request_id': str,
                'estimated_cost': float,
                'hourly_calls': int,
                'daily_cost': float,
            }
        """
        now: datetime = now_func()
        usage_date = now.strftime("%Y-%m-%d")
        cutoff = (now - timedelta(hours=1)).isoformat()

        try:
            conn = self._connect()
        except (OSError, sqlite3.Error) as exc:
            raise GuardStorageError(f"Cannot open usage DB: {exc}") from exc

        try:
            # single write transaction for the whole check-and-reserve
            conn.isolation_level = "EXCLUSIVE"

            # read current state under transaction lock
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN created_at > ? AND status IN ('reserved','completed') THEN 1 ELSE 0 END), 0) AS hourly_calls,
                    COALESCE(SUM(CASE WHEN status IN ('reserved','completed') THEN actual_cost ELSE estimated_cost END), 0) AS daily_cost
                FROM usage_events
                WHERE usage_date = ? AND agency_id = ? AND model = ? AND feature = ?
                """,
                (cutoff, usage_date, agency_id, model, feature),
            ).fetchone()
            hourly_calls = int(row["hourly_calls"] or 0)
            daily_cost = float(row["daily_cost"] or 0.0)

            projected_cost = daily_cost + estimated_cost
            warnings: list[str] = []
            block_reason: Optional[str] = None

            # ── 1. rate limit (per-agency, per-model scoped) ────────────────────
            if hourly_limit is not None and hourly_calls >= hourly_limit:
                block_reason = "rate_limit_exceeded"
                self._insert_blocked(
                    conn,
                    request_id=request_id,
                    agency_id=agency_id,
                    model=model,
                    feature=feature,
                    usage_date=usage_date,
                    created_at=now.isoformat(),
                    estimated_cost=estimated_cost,
                    block_reason=block_reason,
                    warning_flags=json.dumps(warnings) if warnings else None,
                )
                conn.commit()
                return False, {
                    "hourly_calls": hourly_calls,
                    "daily_cost": daily_cost,
                    "projected_cost": projected_cost,
                    "block_reason": block_reason,
                    "warnings": warnings,
                }

            # ── 2. per-model hourly limit ──────────────────────────────────────────
            if model_hourly_limit is not None and hourly_calls >= model_hourly_limit:
                block_reason = "model_rate_limit_exceeded"
                self._insert_blocked(
                    conn,
                    request_id=request_id,
                    agency_id=agency_id,
                    model=model,
                    feature=feature,
                    usage_date=usage_date,
                    created_at=now.isoformat(),
                    estimated_cost=estimated_cost,
                    block_reason=block_reason,
                    warning_flags=json.dumps(warnings) if warnings else None,
                )
                conn.commit()
                return False, {
                    "hourly_calls": hourly_calls,
                    "daily_cost": daily_cost,
                    "projected_cost": projected_cost,
                    "block_reason": block_reason,
                    "warnings": warnings,
                }

            # ── 3. budget block ───────────────────────────────────────────────────
            if daily_budget is not None:
                # warnings
                for t in warning_thresholds:
                    threshold_cost = daily_budget * t
                    if daily_cost < threshold_cost <= projected_cost:
                        pct = int(t * 100)
                        warnings.append(
                            f"Daily budget {pct}% threshold reached (₹{threshold_cost:.2f}/₹{daily_budget:.2f})"
                        )

                # block
                if projected_cost > daily_budget and budget_mode == "block":
                    block_reason = "budget_exceeded"
                    self._insert_blocked(
                        conn,
                        request_id=request_id,
                        agency_id=agency_id,
                        model=model,
                        feature=feature,
                        usage_date=usage_date,
                        created_at=now.isoformat(),
                        estimated_cost=estimated_cost,
                        block_reason=block_reason,
                        warning_flags=json.dumps(warnings) if warnings else None,
                    )
                    conn.commit()
                    return False, {
                        "hourly_calls": hourly_calls,
                        "daily_cost": daily_cost,
                        "projected_cost": projected_cost,
                        "block_reason": block_reason,
                        "warnings": warnings,
                    }
                elif projected_cost > daily_budget and budget_mode == "warn":
                    warnings.append(
                        f"Daily budget exceeded: ₹{projected_cost:.2f} > ₹{daily_budget:.2f} (mode=warn)"
                    )

            # ── 4. reserve ───────────────────────────────────────────────────────
            # PA-20: bind run/trip correlation at insert time so the
            # reservation row is attributable even if finalization never runs —
            # into the real run_id/trip_id columns (Wave 2) AND metadata_json
            # (back-compat with rows written before the migration).
            correlation_json = _merge_correlation_metadata(None)
            run_id_ctx, trip_id_ctx = _correlation_ids()
            cursor = conn.execute(
                """
                INSERT INTO usage_events
                (request_id, agency_id, model, feature, created_at, usage_date,
                 status, estimated_cost, actual_cost, block_reason, warning_flags,
                 metadata_json, run_id, trip_id)
                VALUES (?, ?, ?, ?, ?, ?, 'reserved', ?, NULL, NULL, ?, ?, ?, ?)
                """,
                (
                    request_id,
                    agency_id,
                    model,
                    feature,
                    now.isoformat(),
                    usage_date,
                    estimated_cost,
                    json.dumps(warnings) if warnings else None,
                    correlation_json,
                    run_id_ctx,
                    trip_id_ctx,
                ),
            )
            conn.commit()
            event_id = cursor.lastrowid
            return True, {
                "event_id": event_id,
                "status": "reserved",
                "request_id": request_id,
                "estimated_cost": estimated_cost,
                "hourly_calls": hourly_calls,
                "daily_cost": daily_cost,
                "projected_cost": projected_cost,
                "warnings": warnings,
            }

        except GuardStorageError:
            raise
        except (OSError, sqlite3.Error) as exc:
            conn.rollback()
            raise GuardStorageError(f"check_and_reserve failed: {exc}") from exc
        finally:
            try:
                conn.close()
            except (OSError, sqlite3.Error):
                pass

    # ─────────────────────────────────────────────────────────────────────────────────
    # Finish reservation
    # ─────────────────────────────────────────────────────────────────────────────────

    def finalize_reservation(
        self,
        *,
        event_id: int,
        actual_cost: float,
        status: str,  # 'completed' | 'failed' | 'guard_unavailable'
    ) -> None:
        """Update a previously reserved event with actual cost and final status.

        PA-20: this is the sink of UsageGuard.record_call — when a run/trip
        correlation context is set, it is merged into the row's
        metadata_json here (idempotent; an existing correlation is preserved)
        AND backfilled into the real run_id/trip_id columns via COALESCE,
        without clobbering values already written at reserve time.
        """
        run_id_ctx, trip_id_ctx = _correlation_ids()
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT metadata_json FROM usage_events WHERE id = ?",
                (event_id,),
            ).fetchone()
            merged_metadata = _merge_correlation_metadata(
                row["metadata_json"] if row else None
            )
            if merged_metadata is not None:
                conn.execute(
                    """
                    UPDATE usage_events
                       SET status = ?, actual_cost = ?, metadata_json = ?,
                           run_id = COALESCE(run_id, ?), trip_id = COALESCE(trip_id, ?)
                     WHERE id = ?
                    """,
                    (status, actual_cost, merged_metadata, run_id_ctx, trip_id_ctx, event_id),
                )
            else:
                conn.execute(
                    """
                    UPDATE usage_events
                       SET status = ?, actual_cost = ?,
                           run_id = COALESCE(run_id, ?), trip_id = COALESCE(trip_id, ?)
                     WHERE id = ?
                    """,
                    (status, actual_cost, run_id_ctx, trip_id_ctx, event_id),
                )
            conn.commit()
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────────────────────
    # Read-only helpers (outside transaction)
    # ─────────────────────────────────────────────────────────────────────────────────

    def get_summary(
        self,
        *,
        agency_id: str,
        model: str,
        feature: str,
        usage_date: str,
        now: Optional[datetime] = None,
    ) -> dict:
        """Return daily summary for debugging/monitoring."""
        if now is None:
            now = datetime.now()
        cutoff = (now - timedelta(hours=1)).isoformat()
        conn = self._connect()
        try:
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN created_at > ? THEN 1 ELSE 0 END), 0) AS hourly_calls,
                    COALESCE(SUM(CASE WHEN status IN ('reserved','completed') THEN actual_cost ELSE estimated_cost END), 0) AS daily_cost
                FROM usage_events
                WHERE usage_date = ? AND agency_id = ? AND model = ? AND feature = ?
                """,
                (cutoff, usage_date, agency_id, model, feature),
            ).fetchone()
            return {
                "hourly_calls": int(row["hourly_calls"] or 0),
                "daily_cost": float(row["daily_cost"] or 0.0),
            }
        finally:
            conn.close()

    def get_event(self, event_id: int) -> Optional[dict]:
        """Return one usage event (metadata_json parsed) — PA-20 test/ops aid."""
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM usage_events WHERE id = ?",
                (event_id,),
            ).fetchone()
            if row is None:
                return None
            return _event_with_metadata(dict(row))
        finally:
            conn.close()

    def get_events_for_run(self, run_id: str) -> list[dict]:
        """Return all usage events correlated to a run (PA-20 Wave 2).

        Reads the real ``run_id`` column via a parameterized query. Rows
        written before the columns existed carry their correlation in
        metadata_json only and are intentionally not matched here — reconcile
        those via their run's meta lookup.
        """
        conn = self._connect()
        try:
            rows = conn.execute(
                "SELECT * FROM usage_events WHERE run_id = ? ORDER BY id",
                (run_id,),
            ).fetchall()
            return [_event_with_metadata(dict(row)) for row in rows]
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────────────────────
    # Private helpers
    # ─────────────────────────────────────────────────────────────────────────────────

    def _insert_blocked(
        self,
        conn: sqlite3.Connection,
        *,
        request_id: str,
        agency_id: str,
        model: str,
        feature: str,
        usage_date: str,
        created_at: str,
        estimated_cost: float,
        block_reason: str,
        warning_flags: Optional[str],
    ) -> int:
        # PA-20: blocked events are also attributable when the run context is
        # set — real columns (Wave 2) plus metadata_json (back-compat).
        correlation_json = _merge_correlation_metadata(None)
        run_id_ctx, trip_id_ctx = _correlation_ids()
        cursor = conn.execute(
            """
            INSERT INTO usage_events
            (request_id, agency_id, model, feature, created_at, usage_date,
             status, estimated_cost, actual_cost, block_reason, warning_flags,
             metadata_json, run_id, trip_id)
            VALUES (?, ?, ?, ?, ?, ?, 'blocked', ?, NULL, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                agency_id,
                model,
                feature,
                created_at,
                usage_date,
                estimated_cost,
                block_reason,
                warning_flags,
                correlation_json,
                run_id_ctx,
                trip_id_ctx,
            ),
        )
        return cursor.lastrowid

    def reset(self) -> None:
        """Delete all events. Used in tests only."""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM usage_events")
            conn.commit()
        finally:
            conn.close()

    # ─────────────────────────────────────────────────────────────────────────────────
    # Configuration helpers
    # ─────────────────────────────────────────────────────────────────────────────────

    @classmethod
    def get_default_path(cls) -> Path:
        return _DEFAULT_DATA_PATH / "usage.db"

    @property
    def db_path(self) -> Path:
        return self._db_path


# ─── In-memory store for testing / single-process ---

class InMemoryUsageStore(LLMUsageStore):
    """
    In-memory usage store for unit tests and single-process scenarios.
    Not suitable for multi-worker deployments.
    """

    def __init__(self):
        import threading
        self._id_counter = 0
        self._events: list[dict] = []
        self._lock = threading.Lock()

    def _next_id(self) -> int:
        self._id_counter += 1
        return self._id_counter

    def _blocked_event(
        self,
        *,
        event_id: int,
        request_id: str,
        agency_id: str,
        model: str,
        feature: str,
        created_at: str,
        usage_date: str,
        estimated_cost: float,
        block_reason: str,
        warning_flags: Optional[str],
    ) -> dict:
        """Build a blocked event row, mirroring the SQLite INSERT (PA-20).

        Carries the run/trip correlation in the real run_id/trip_id fields AND
        metadata_json so both backends expose the same contract.
        """
        run_id_ctx, trip_id_ctx = _correlation_ids()
        return {
            "id": event_id,
            "request_id": request_id,
            "agency_id": agency_id,
            "model": model,
            "feature": feature,
            "created_at": created_at,
            "usage_date": usage_date,
            "status": "blocked",
            "estimated_cost": estimated_cost,
            "actual_cost": None,
            "block_reason": block_reason,
            "warning_flags": warning_flags,
            "metadata_json": _merge_correlation_metadata(None),
            "run_id": run_id_ctx,
            "trip_id": trip_id_ctx,
        }

    def check_and_reserve(
        self,
        *,
        request_id: str,
        agency_id: str,
        model: str,
        feature: str,
        estimated_cost: float,
        hourly_limit: Optional[int],
        model_hourly_limit: Optional[int] = None,
        daily_budget: Optional[float],
        budget_mode: str,
        warning_thresholds: list[float],
        now_func: Callable,
    ) -> dict:
        now = now_func()
        usage_date = now.strftime("%Y-%m-%d")
        cutoff = (now - timedelta(hours=1)).isoformat()

        with self._lock:
            hourly_calls = sum(
                1
                for e in self._events
                if e["usage_date"] == usage_date
                and e["agency_id"] == agency_id
                and e["model"] == model
                and e["feature"] == feature
                and e["created_at"] > cutoff
                and e["status"] in ("reserved", "completed")
            )

            daily_cost = sum(
                (e.get("actual_cost") or e.get("estimated_cost", 0.0))
                for e in self._events
                if e["usage_date"] == usage_date
                and e["agency_id"] == agency_id
                and e["model"] == model
                and e["feature"] == feature
                and e["status"] in ("reserved", "completed")
            )

            projected_cost = daily_cost + estimated_cost
            warnings: list[str] = []

            if hourly_limit is not None and hourly_calls >= hourly_limit:
                event_id = self._next_id()
                self._events.append(
                    self._blocked_event(
                        event_id=event_id,
                        request_id=request_id,
                        agency_id=agency_id,
                        model=model,
                        feature=feature,
                        created_at=now.isoformat(),
                        usage_date=usage_date,
                        estimated_cost=estimated_cost,
                        block_reason="rate_limit_exceeded",
                        warning_flags=json.dumps(warnings) if warnings else None,
                    )
                )
                return {
                    "event_id": event_id,
                    "hourly_calls": hourly_calls,
                    "daily_cost": daily_cost,
                    "projected_cost": projected_cost,
                    "block_reason": "rate_limit_exceeded",
                    "warnings": warnings,
                }

            if model_hourly_limit is not None and hourly_calls >= model_hourly_limit:
                event_id = self._next_id()
                self._events.append(
                    self._blocked_event(
                        event_id=event_id,
                        request_id=request_id,
                        agency_id=agency_id,
                        model=model,
                        feature=feature,
                        created_at=now.isoformat(),
                        usage_date=usage_date,
                        estimated_cost=estimated_cost,
                        block_reason="model_rate_limit_exceeded",
                        warning_flags=json.dumps(warnings) if warnings else None,
                    )
                )
                return {
                    "event_id": event_id,
                    "hourly_calls": hourly_calls,
                    "daily_cost": daily_cost,
                    "projected_cost": projected_cost,
                    "block_reason": "model_rate_limit_exceeded",
                    "warnings": warnings,
                }

            if daily_budget is not None:
                for t in warning_thresholds:
                    threshold_cost = daily_budget * t
                    if daily_cost < threshold_cost <= projected_cost:
                        pct = int(t * 100)
                        warnings.append(
                            f"Daily budget {pct}% threshold reached (₹{threshold_cost:.2f}/₹{daily_budget:.2f})"
                        )

                if projected_cost > daily_budget and budget_mode == "block":
                    event_id = self._next_id()
                    self._events.append(
                        self._blocked_event(
                            event_id=event_id,
                            request_id=request_id,
                            agency_id=agency_id,
                            model=model,
                            feature=feature,
                            created_at=now.isoformat(),
                            usage_date=usage_date,
                            estimated_cost=estimated_cost,
                            block_reason="budget_exceeded",
                            warning_flags=json.dumps(warnings) if warnings else None,
                        )
                    )
                    return {
                        "event_id": event_id,
                        "hourly_calls": hourly_calls,
                        "daily_cost": daily_cost,
                        "projected_cost": projected_cost,
                        "block_reason": "budget_exceeded",
                        "warnings": warnings,
                    }
                elif projected_cost > daily_budget and budget_mode == "warn":
                    warnings.append(
                        f"Daily budget exceeded: ₹{projected_cost:.2f} > ₹{daily_budget:.2f} (mode=warn)"
                    )

            event_id = self._next_id()
            # PA-20: carry the run/trip correlation in the real run_id/trip_id
            # fields AND metadata_json so the in-memory backend matches the
            # SQLite contract in tests.
            run_id_ctx, trip_id_ctx = _correlation_ids()
            correlation_json = _merge_correlation_metadata(None)
            self._events.append(
                {
                    "id": event_id,
                    "request_id": request_id,
                    "agency_id": agency_id,
                    "model": model,
                    "feature": feature,
                    "created_at": now.isoformat(),
                    "usage_date": usage_date,
                    "status": "reserved",
                    "estimated_cost": estimated_cost,
                    "actual_cost": None,
                    "block_reason": None,
                    "warning_flags": json.dumps(warnings) if warnings else None,
                    "metadata_json": correlation_json,
                    "run_id": run_id_ctx,
                    "trip_id": trip_id_ctx,
                }
            )
            return {
                "event_id": event_id,
                "status": "reserved",
                "request_id": request_id,
                "estimated_cost": estimated_cost,
                "hourly_calls": hourly_calls,
                "daily_cost": daily_cost,
                "projected_cost": projected_cost,
                "warnings": warnings,
            }

    def finalize_reservation(self, *, event_id: int, actual_cost: float, status: str) -> None:
        run_id_ctx, trip_id_ctx = _correlation_ids()
        with self._lock:
            for e in self._events:
                if e["id"] == event_id:
                    e["actual_cost"] = actual_cost
                    e["status"] = status
                    # PA-20: merge correlation on finalization (record_call
                    # sink), matching the SQLite backend — metadata_json merge
                    # plus COALESCE-style backfill of the real columns.
                    merged = _merge_correlation_metadata(e.get("metadata_json"))
                    if merged is not None:
                        e["metadata_json"] = merged
                    if e.get("run_id") is None:
                        e["run_id"] = run_id_ctx
                    if e.get("trip_id") is None:
                        e["trip_id"] = trip_id_ctx
                    return

    def get_event(self, event_id: int) -> Optional[dict]:
        """Return one in-memory usage event — PA-20 test/ops aid."""
        with self._lock:
            for e in self._events:
                if e["id"] == event_id:
                    return _event_with_metadata(e)
            return None

    def get_events_for_run(self, run_id: str) -> list[dict]:
        """Return all in-memory usage events correlated to a run (PA-20 Wave 2)."""
        with self._lock:
            return [
                _event_with_metadata(e) for e in self._events if e.get("run_id") == run_id
            ]

    def get_summary(self, *, agency_id: str, model: str, feature: str, usage_date: str, now: Optional[datetime] = None) -> dict:
        if now is None:
            now = datetime.now()
        cutoff = (now - timedelta(hours=1)).isoformat()
        with self._lock:
            def _match(e: dict) -> bool:
                ok = e["usage_date"] == usage_date and e["agency_id"] == agency_id
                if ok and model != "*":
                    ok = ok and e["model"] == model
                if ok and feature != "*":
                    ok = ok and e["feature"] == feature
                return ok

            hourly_calls = sum(
                1
                for e in self._events
                if e["created_at"] > cutoff and _match(e)
                and e["status"] in ("reserved", "completed", "failed")
            )
            daily_cost = sum(
                (e.get("actual_cost") or e.get("estimated_cost", 0.0))
                for e in self._events
                if _match(e) and e["status"] == "completed"
            )
            return {"hourly_calls": hourly_calls, "daily_cost": daily_cost}

    def reset(self) -> None:
        with self._lock:
            self._events.clear()


# ─── Redis-backed store for multi-instance production (P4-03) ─────────────────

_LUA_CHECK_AND_RESERVE = """
-- KEYS: {calls_key} {cost_key}
-- ARGV: request_id ts_now ts_cutoff hourly_limit model_hourly_limit daily_budget budget_mode estimated_cost
local calls_key  = KEYS[1]
local cost_key   = KEYS[2]

local request_id          = ARGV[1]
local ts_now              = tonumber(ARGV[2])
local ts_cutoff           = tonumber(ARGV[3])
local hourly_limit        = tonumber(ARGV[4])   -- 0 means "no limit"
local model_hourly_limit  = tonumber(ARGV[5])   -- 0 means "no limit"
local daily_budget        = tonumber(ARGV[6])   -- 0 means "no limit"
local budget_mode         = ARGV[7]
local estimated_cost      = tonumber(ARGV[8])

-- count calls in last hour
redis.call('ZREMRANGEBYSCORE', calls_key, '-inf', ts_cutoff)
local hourly_calls = redis.call('ZCARD', calls_key)

-- read daily cost
local daily_cost = tonumber(redis.call('GET', cost_key) or '0')
local projected  = daily_cost + estimated_cost

-- check limits
if hourly_limit > 0 and hourly_calls >= hourly_limit then
    return {0, hourly_calls, daily_cost, 'hourly_limit_reached'}
end

if model_hourly_limit > 0 and hourly_calls >= model_hourly_limit then
    return {0, hourly_calls, daily_cost, 'model_rate_limit_exceeded'}
end

if daily_budget > 0 and projected > daily_budget and budget_mode == 'block' then
    return {0, hourly_calls, daily_cost, 'budget_exceeded'}
end

-- reserve: add timestamp to ZSET, increment cost
local member = request_id .. ':' .. tostring(ts_now)
redis.call('ZADD', calls_key, ts_now, member)
redis.call('EXPIRE', calls_key, 7200)  -- 2h TTL

redis.call('INCRBYFLOAT', cost_key, estimated_cost)
redis.call('EXPIRE', cost_key, 172800)  -- 48h TTL

-- return: allowed=1, hourly_calls, daily_cost, warnings
local warning = ''
if daily_budget > 0 and projected > daily_budget then
    warning = 'budget_warn'
end
return {1, hourly_calls, daily_cost, warning}
"""


class RedisUsageStore(LLMUsageStore):
    """
    Redis-backed LLM usage store for multi-instance / multi-container deployments.

    Key layout (per agency_id / model / feature / date):
      guard:{agency}:{model}:{feature}:{date}:calls  — ZSET of (timestamp, member)
      guard:{agency}:{model}:{feature}:{date}:cost   — float (INCRBYFLOAT)
      guard:event:{request_id}                       — HASH  (status, actual_cost)

    Atomic check-and-reserve uses a Lua script to avoid TOCTOU races.
    Fail-closed: raises GuardStorageError on any Redis connectivity issue.

    Environment variables:
      REDIS_URL     — Redis connection URL (default: redis://localhost:6379/0)
    """

    def __init__(self, url: str = "redis://localhost:6379/0"):
        try:
            import redis as _redis
            self._redis = _redis.Redis.from_url(url, decode_responses=True)
            self._script = self._redis.register_script(_LUA_CHECK_AND_RESERVE)
        except ImportError as exc:  # pragma: no cover
            raise GuardStorageError(
                "redis package is not installed. Run: uv add redis"
            ) from exc
        except (OSError, ValueError, TypeError) as exc:
            raise GuardStorageError(
                f"Failed to connect to Redis: {exc}"
            ) from exc
        self._id_counter = 0
        self._id_lock = threading.Lock()

    @classmethod
    def from_env(cls) -> "RedisUsageStore":
        url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        return cls(url=url)

    # ── key helpers ──────────────────────────────────────────────────────────

    def _day_prefix(self, agency_id: str, model: str, feature: str, usage_date: str) -> str:
        return f"guard:{agency_id}:{model}:{feature}:{usage_date}"

    def _calls_key(self, agency_id: str, model: str, feature: str, usage_date: str) -> str:
        return self._day_prefix(agency_id, model, feature, usage_date) + ":calls"

    def _cost_key(self, agency_id: str, model: str, feature: str, usage_date: str) -> str:
        return self._day_prefix(agency_id, model, feature, usage_date) + ":cost"

    def _event_key(self, request_id: str) -> str:
        return f"guard:event:{request_id}"

    def _next_id(self) -> int:
        with self._id_lock:
            self._id_counter += 1
            return self._id_counter

    # ── public API ───────────────────────────────────────────────────────────

    def check_and_reserve(
        self,
        *,
        request_id: str,
        agency_id: str,
        model: str,
        feature: str,
        estimated_cost: float,
        hourly_limit: Optional[int],
        model_hourly_limit: Optional[int] = None,
        daily_budget: Optional[float],
        budget_mode: str,
        warning_thresholds: list[float],
        now_func,
    ) -> dict:
        now = now_func()
        usage_date = now.strftime("%Y-%m-%d")
        ts_now = now.timestamp()
        ts_cutoff = (now - timedelta(hours=1)).timestamp()

        calls_key = self._calls_key(agency_id, model, feature, usage_date)
        cost_key = self._cost_key(agency_id, model, feature, usage_date)

        try:
            result = self._script(
                keys=[calls_key, cost_key],
                args=[
                    request_id,
                    str(ts_now),
                    str(ts_cutoff),
                    str(hourly_limit or 0),
                    str(model_hourly_limit or 0),
                    str(daily_budget or 0),
                    budget_mode,
                    str(estimated_cost),
                ],
            )
        except (OSError, ValueError) as exc:
            raise GuardStorageError(f"Redis check_and_reserve failed: {exc}") from exc

        allowed = int(result[0]) == 1
        hourly_calls = int(result[1])
        daily_cost = float(result[2])
        flag = result[3] if isinstance(result[3], str) else result[3].decode()

        event_id = self._next_id()
        status = "reserved" if allowed else "blocked"
        block_reason = flag if not allowed else None
        warnings = [flag] if allowed and flag == "budget_warn" else []

        event_data = {
            "status": status,
            "actual_cost": "0",
            "estimated_cost": str(estimated_cost),
            "block_reason": block_reason or "",
        }
        try:
            self._redis.hset(self._event_key(request_id), mapping=event_data)
            self._redis.expire(self._event_key(request_id), 172800)
        except (OSError,):  # redis.RedisError already re-raised by redis-py; OSError covers connection issues
            pass  # event metadata loss is non-critical

        return {
            "event_id": event_id,
            "status": status,
            "request_id": request_id,
            "estimated_cost": estimated_cost,
            "hourly_calls": hourly_calls,
            "daily_cost": daily_cost,
            "projected_cost": daily_cost + estimated_cost,
            "block_reason": block_reason,
            "warnings": warnings,
        }

    def finalize_reservation(self, *, event_id: int, actual_cost: float, status: str) -> None:
        # event_id is opaque in Redis (request_id based); guard passes reservation dict
        # This is a no-op for Redis: cost was already incremented in the Lua script.
        # Actual cost delta correction is done via a separate key if needed.
        pass

    def get_summary(
        self,
        *,
        agency_id: str,
        model: str,
        feature: str,
        usage_date: str,
        now: Optional[datetime] = None,
    ) -> dict:
        if now is None:
            now = datetime.now()
        ts_cutoff = (now - timedelta(hours=1)).timestamp()
        calls_key = self._calls_key(agency_id, model, feature, usage_date)
        cost_key = self._cost_key(agency_id, model, feature, usage_date)
        try:
            self._redis.zremrangebyscore(calls_key, "-inf", ts_cutoff)
            hourly_calls = self._redis.zcard(calls_key)
            daily_cost = float(self._redis.get(cost_key) or 0.0)
        except (OSError, ValueError) as exc:
            raise GuardStorageError(f"Redis get_summary failed: {exc}") from exc
        return {"hourly_calls": int(hourly_calls), "daily_cost": daily_cost}

    def reset(self) -> None:
        try:
            for key in self._redis.scan_iter("guard:*"):
                self._redis.delete(key)
        except Exception as exc:
            raise GuardStorageError(f"Redis reset failed: {exc}") from exc

