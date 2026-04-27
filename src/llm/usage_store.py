"""
llm.usage_store — SQLite-backed LLM usage tracking storage.

Abstracts usage persistence so the guard does not depend directly on SQLite.
Supports atomic check-and-reserve, WAL mode, busy timeout, and durable paths.

Usage (via guard):
    store = LLMUsageStore()
    store.record_event(model, feature, cost, status)
    count = store.get_hourly_calls(model, feature, since)
    cost = store.get_daily_cost(model, feature, for_date)

All operations are atomic and transactional.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

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
                        metadata_json TEXT
                    )
                """)
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
        except Exception as exc:
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

            # ── 1. rate limit ────────────────────────────────────────────────────
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

            # ── 2. budget block ───────────────────────────────────────────────────
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

            # ── 3. reserve ───────────────────────────────────────────────────────
            cursor = conn.execute(
                """
                INSERT INTO usage_events
                (request_id, agency_id, model, feature, created_at, usage_date,
                 status, estimated_cost, actual_cost, block_reason, warning_flags)
                VALUES (?, ?, ?, ?, ?, ?, 'reserved', ?, NULL, NULL, ?)
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
        except Exception as exc:
            conn.rollback()
            raise GuardStorageError(f"check_and_reserve failed: {exc}") from exc
        finally:
            try:
                conn.close()
            except Exception:
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
        """Update a previously reserved event with actual cost and final status."""
        conn = self._connect()
        try:
            conn.execute(
                """
                UPDATE usage_events
                   SET status = ?, actual_cost = ?
                 WHERE id = ?
                """,
                (status, actual_cost, event_id),
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
        cursor = conn.execute(
            """
            INSERT INTO usage_events
            (request_id, agency_id, model, feature, created_at, usage_date,
             status, estimated_cost, actual_cost, block_reason, warning_flags)
            VALUES (?, ?, ?, ?, ?, ?, 'blocked', ?, NULL, ?, ?)
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

    def check_and_reserve(
        self,
        *,
        request_id: str,
        agency_id: str,
        model: str,
        feature: str,
        estimated_cost: float,
        hourly_limit: Optional[int],
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
                    {
                        "id": event_id,
                        "request_id": request_id,
                        "agency_id": agency_id,
                        "model": model,
                        "feature": feature,
                        "created_at": now.isoformat(),
                        "usage_date": usage_date,
                        "status": "blocked",
                        "estimated_cost": estimated_cost,
                        "actual_cost": None,
                        "block_reason": "rate_limit_exceeded",
                        "warning_flags": json.dumps(warnings) if warnings else None,
                    }
                )
                return {
                    "event_id": event_id,
                    "hourly_calls": hourly_calls,
                    "daily_cost": daily_cost,
                    "projected_cost": projected_cost,
                    "block_reason": "rate_limit_exceeded",
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
                        {
                            "id": event_id,
                            "request_id": request_id,
                            "agency_id": agency_id,
                            "model": model,
                            "feature": feature,
                            "created_at": now.isoformat(),
                            "usage_date": usage_date,
                            "status": "blocked",
                            "estimated_cost": estimated_cost,
                            "actual_cost": None,
                            "block_reason": "budget_exceeded",
                            "warning_flags": json.dumps(warnings) if warnings else None,
                        }
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
        with self._lock:
            for e in self._events:
                if e["id"] == event_id:
                    e["actual_cost"] = actual_cost
                    e["status"] = status
                    return

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

