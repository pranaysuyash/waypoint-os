"""
run_ledger_sql.py — SQL-backed run checkpoint durability (FND-0226).

The run ledger's lifecycle state must live in the SAME store as the trip
state. When ``TRIPSTORE_BACKEND`` is sql/postgres, every run-ledger meta
transition is mirrored into ``run_checkpoints`` (and step checkpoints
best-effort into ``run_checkpoint_steps``); the on-disk ``data/runs/`` tree
is demoted to a local cache. A rolling deploy that loses a pod's disk can
no longer orphan a run as RUNNING forever.

Startup reconciliation
----------------------
``reconcile_interrupted_runs()`` runs at boot (server lifespan): runs still
marked queued/running whose heartbeat is stale AND whose agent lease (if
any) is not live are marked ``interrupted`` — an honest terminal state —
instead of lying about being RUNNING. The heartbeat is the primary
liveness signal (pipelines touch() at every stage checkpoint); the lease
check (read-only ``DurableAgentLeaseManager.get_lease``) is a courtesy
second witness and is never allowed to break reconciliation.

Failure semantics: the lifecycle mirror (``mirror_meta``) is STRICT — a
failed mirror raises so the divergence surfaces loudly instead of silently
re-creating the disk/SQL split-brain this finding describes. Heartbeat and
step-artifact mirrors are best-effort (logged, never fatal) because they
are not lifecycle truth.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

logger = logging.getLogger("spine_api.run_ledger_sql")

_SQL_BACKEND_VALUES = frozenset({"sql", "postgres", "postgresql"})

# Lifecycle-truth meta keys that map 1:1 onto RunCheckpointModel columns.
_META_COLUMNS = (
    "run_id",
    "trip_id",
    "draft_id",
    "agency_id",
    "state",
    "stage",
    "operating_mode",
    "created_at",
    "started_at",
    "completed_at",
    "heartbeat_at",
    "total_ms",
    "error_type",
    "error_message",
    "failure_class",
    "stage_at_failure",
    "block_reason",
    "recovered_after_timeout",
)


def checkpoint_backend_is_sql() -> bool:
    """True when the configured state store (TRIPSTORE_BACKEND) is SQL.

    Mirrors the TripStore backend vocabulary. Only production-grade backends
    (sql/postgres/postgresql) count — an unset value means the file store,
    where disk checkpoints ARE the state store and no mirror applies.
    """
    return os.getenv("TRIPSTORE_BACKEND", "").strip().lower() in _SQL_BACKEND_VALUES


def _parse_iso(value: Any) -> Optional[datetime]:
    """Best-effort ISO-8601 string → aware datetime (None on garbage)."""
    if value is None or isinstance(value, datetime):
        return value if isinstance(value, datetime) else None
    try:
        parsed = datetime.fromisoformat(str(value))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError):
        return None


class SQLRunCheckpointStore:
    """Mirror and reconcile run ledger state in PostgreSQL (FND-0226)."""

    _ensure_table_done = False

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    @staticmethod
    def _run(coro: Any) -> Any:
        from spine_api.persistence import _run_async_blocking

        return _run_async_blocking(coro)

    @classmethod
    def _ensure_table(cls) -> None:
        """Idempotently create the run checkpoint tables (lazily, once)."""
        if cls._ensure_table_done:
            return

        async def _create_all() -> None:
            from spine_api.core.database import Base, engine
            from spine_api.models.run_checkpoint import (
                RunCheckpointModel,
                RunCheckpointStepModel,
            )

            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn: Base.metadata.create_all(
                        sync_conn,
                        tables=[RunCheckpointModel.__table__, RunCheckpointStepModel.__table__],
                        checkfirst=True,
                    )
                )

        cls._run(_create_all())
        cls._ensure_table_done = True

    # ------------------------------------------------------------------
    # Mirrors (write path)
    # ------------------------------------------------------------------

    @classmethod
    def mirror_meta(cls, meta: dict[str, Any]) -> None:
        """Upsert the authoritative lifecycle record for one run. STRICT."""
        cls._ensure_table()

        if not meta.get("run_id"):
            raise ValueError("mirror_meta requires meta['run_id']")

        from sqlalchemy.dialects.postgresql import insert

        from spine_api.core.database import engine
        from spine_api.models.run_checkpoint import RunCheckpointModel

        values: dict[str, Any] = {}
        extra: dict[str, Any] = {}
        for key, value in meta.items():
            if key in _META_COLUMNS:
                if key in ("created_at", "started_at", "completed_at", "heartbeat_at"):
                    values[key] = _parse_iso(value)
                else:
                    values[key] = value
            elif key not in ("reconciled_at", "reconciled_reason"):
                extra[key] = value
        values.setdefault("state", "queued")
        values["extra_meta"] = extra or None

        target = RunCheckpointModel.__table__
        stmt = insert(target).values(**values)
        update_cols = {
            c.name: stmt.excluded[c.name]
            for c in target.columns
            if c.name != "run_id"
        }
        stmt = stmt.on_conflict_do_update(index_elements=["run_id"], set_=update_cols)

        async def _upsert() -> None:
            async with engine.begin() as conn:
                await conn.execute(stmt)

        cls._run(_upsert())

    @classmethod
    def mirror_step(cls, run_id: str, step_name: str, checkpoint: dict[str, Any]) -> None:
        """Best-effort mirror of one pipeline step artifact (cache, not truth)."""
        cls._ensure_table()

        from sqlalchemy.dialects.postgresql import insert

        from spine_api.core.database import engine
        from spine_api.models.run_checkpoint import RunCheckpointStepModel

        values = {
            "run_id": run_id,
            "step_name": step_name,
            "checkpointed_at": _parse_iso(checkpoint.get("checkpointed_at")),
            "data": checkpoint.get("data"),
        }
        target = RunCheckpointStepModel.__table__
        stmt = insert(target).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["run_id", "step_name"],
            set_={
                "checkpointed_at": stmt.excluded.checkpointed_at,
                "data": stmt.excluded.data,
                "updated_at": datetime.now(timezone.utc),
            },
        )

        async def _upsert() -> None:
            async with engine.begin() as conn:
                await conn.execute(stmt)

        cls._run(_upsert())

    # ------------------------------------------------------------------
    # Read-through (disk cache misses)
    # ------------------------------------------------------------------

    @classmethod
    def load_meta(cls, run_id: str) -> Optional[dict[str, Any]]:
        """Return the SQL lifecycle record for a run as ledger-shaped meta."""
        cls._ensure_table()

        from sqlalchemy import select

        from spine_api.core.database import async_session_maker
        from spine_api.models.run_checkpoint import RunCheckpointModel

        async def _load() -> Optional[dict[str, Any]]:

            async with async_session_maker() as session:
                row = (
                    await session.execute(
                        select(RunCheckpointModel).where(RunCheckpointModel.run_id == run_id)
                    )
                ).scalar_one_or_none()
                if row is None:
                    return None
                meta: dict[str, Any] = {}
                for column in _META_COLUMNS:
                    value = getattr(row, column, None)
                    meta[column] = value.isoformat() if isinstance(value, datetime) else value
                if row.reconciled_at is not None:
                    meta["reconciled_at"] = row.reconciled_at.isoformat()
                if row.reconciled_reason:
                    meta["reconciled_reason"] = row.reconciled_reason
                if row.extra_meta:
                    meta.update(row.extra_meta)
                return meta

        return cls._run(_load())

    @classmethod
    def load_step(cls, run_id: str, step_name: str) -> Optional[dict[str, Any]]:
        """Return one mirrored step checkpoint (ledger-shaped), or None."""
        cls._ensure_table()

        from sqlalchemy import select

        from spine_api.core.database import async_session_maker
        from spine_api.models.run_checkpoint import RunCheckpointStepModel

        async def _load() -> Optional[dict[str, Any]]:
            async with async_session_maker() as session:
                row = (
                    await session.execute(
                        select(RunCheckpointStepModel).where(
                            RunCheckpointStepModel.run_id == run_id,
                            RunCheckpointStepModel.step_name == step_name,
                        )
                    )
                ).scalar_one_or_none()
                if row is None:
                    return None
                checkpointed_at = (
                    row.checkpointed_at.isoformat() if row.checkpointed_at else None
                )
                return {
                    "step": row.step_name,
                    "run_id": row.run_id,
                    "checkpointed_at": checkpointed_at,
                    "data": row.data,
                }

        return cls._run(_load())

    @classmethod
    def list_metas(
        cls,
        trip_id: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """List SQL run records newest-first, ledger-shaped."""
        cls._ensure_table()

        from sqlalchemy import select

        from spine_api.core.database import async_session_maker
        from spine_api.models.run_checkpoint import RunCheckpointModel

        async def _list() -> list[dict[str, Any]]:
            async with async_session_maker() as session:
                query = select(RunCheckpointModel).order_by(
                    RunCheckpointModel.created_at.desc().nullslast(),
                    RunCheckpointModel.run_id.desc(),
                )
                if trip_id is not None:
                    query = query.where(RunCheckpointModel.trip_id == trip_id)
                if state is not None:
                    query = query.where(RunCheckpointModel.state == state)
                rows = session.scalars(query.limit(limit)).all()
                metas: list[dict[str, Any]] = []
                for row in rows:
                    meta: dict[str, Any] = {}
                    for column in _META_COLUMNS:
                        value = getattr(row, column, None)
                        meta[column] = (
                            value.isoformat() if isinstance(value, datetime) else value
                        )
                    if row.extra_meta:
                        meta.update(row.extra_meta)
                    metas.append(meta)
                return metas

        return cls._run(_list())

    # ------------------------------------------------------------------
    # Startup reconciliation (FND-0226)
    # ------------------------------------------------------------------

    @classmethod
    def _list_orphan_candidates(cls) -> list[Any]:
        """Return SQL run rows still queued/running (reconciliation input).

        Extracted as its own seam so tests can drive the reconciliation
        decision loop without a live database.
        """
        cls._ensure_table()

        from sqlalchemy import select

        from spine_api.core.database import async_session_maker
        from spine_api.models.run_checkpoint import RunCheckpointModel

        async def _candidates() -> list[Any]:
            async with async_session_maker() as session:
                rows = (
                    await session.execute(
                        select(RunCheckpointModel).where(
                            RunCheckpointModel.state.in_(["queued", "running"])
                        )
                    )
                ).scalars().all()
                return list(rows)

        return cls._run(_candidates())

    @classmethod
    def reconcile_interrupted_runs(
        cls,
        max_heartbeat_age_seconds: int = 300,
    ) -> list[str]:
        """Mark orphaned queued/running runs INTERRUPTED at boot. Returns ids.

        An orphan is a SQL run record still queued/running whose heartbeat
        (``heartbeat_at``) is missing or older than the threshold AND whose
        agent lease — when the run is bound to a trip with a live lease — is
        not currently held. Live leases (unexpired, active) vouch for a run
        even across a heartbeat gap; the heartbeat remains the primary
        signal because pipelines touch() at every stage checkpoint.
        """
        cls._ensure_table()

        now = datetime.now(timezone.utc)
        heartbeat_cutoff = now - timedelta(seconds=max_heartbeat_age_seconds)

        rows = cls._list_orphan_candidates()

        reconciled: list[str] = []
        for row in rows:
            heartbeat = row.heartbeat_at
            if heartbeat is not None and heartbeat.tzinfo is None:
                heartbeat = heartbeat.replace(tzinfo=timezone.utc)
            if heartbeat is not None and heartbeat >= heartbeat_cutoff:
                continue  # fresh heartbeat ⇒ alive

            if cls._lease_is_live(row.trip_id):
                logger.debug(
                    "reconcile: run %s has stale heartbeat but a live lease on "
                    "trip %s — skipping (lease liveness wins).",
                    row.run_id,
                    row.trip_id,
                )
                continue

            try:
                from spine_api.run_ledger import RunLedger

                RunLedger.mark_interrupted(
                    row.run_id,
                    reason=(
                        "startup_reconciliation: no heartbeat since "
                        f"{heartbeat.isoformat() if heartbeat else 'never'} "
                        f"(threshold {max_heartbeat_age_seconds}s)"
                    ),
                )
                reconciled.append(row.run_id)
                logger.warning(
                    "Run-ledger reconciliation: run %s (state=%s, trip=%s) had "
                    "no live lease/heartbeat — marked interrupted.",
                    row.run_id,
                    row.state,
                    row.trip_id,
                )
            except ValueError as exc:
                # Benign race: the row changed state (e.g. → failed/blocked)
                # between candidate selection and interruption. The state
                # machine correctly refused to clobber a terminal record.
                logger.info("Run-ledger reconciliation skipped run %s: %s", row.run_id, exc)
            except Exception as exc:  # noqa: BLE001 — one bad row never stops the sweep
                logger.error(
                    "Run-ledger reconciliation failed for run %s: %s", row.run_id, exc
                )

        return reconciled

    @staticmethod
    def _lease_is_live(trip_id: Optional[str]) -> bool:
        """Courtesy second liveness witness via the durable lease manager.

        Read-only: never acquires, renews, or releases. Any failure to
        consult the lease manager counts as no-live-lease evidence (the
        heartbeat check remains authoritative), and a memory-backend lease
        manager can only vouch for leases held in THIS process — which is
        exactly the honest scope of what it can prove.
        """
        if not trip_id:
            return False
        try:
            from src.orchestration.agent_lease import DurableAgentLeaseManager

            record = DurableAgentLeaseManager.get_lease(trip_id)
            if record is None:
                return False
            return bool(record.is_active and not record.is_expired())
        except Exception as exc:  # noqa: BLE001 — never break reconciliation
            logger.debug(
                "reconcile: lease liveness check for trip %s unavailable: %s",
                trip_id,
                exc,
            )
            return False
