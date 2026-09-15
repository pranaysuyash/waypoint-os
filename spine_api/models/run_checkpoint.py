"""
spine_api/models/run_checkpoint.py — SQL run-checkpoint models (FND-0226).

Backs ``spine_api.run_ledger_sql.SQLRunCheckpointStore`` when the trip/state
store is SQL-backed (``TRIPSTORE_BACKEND=sql|postgres``). Run checkpoint
durability must live in the SAME store as the trip state: disk
(``data/runs/``) is demoted to a local cache, so a rolling deploy that loses
a pod's local checkpoint can no longer orphan a run as RUNNING forever.

Two tables:

``run_checkpoints``
    One row per run — the authoritative lifecycle record (state, stage,
    heartbeat, timing, failure/block info). Mirrored on every run-ledger
    meta write.

``run_checkpoint_steps``
    One row per checkpointed pipeline step output (packet, validation,
    decision, strategy, safety, output, blocked_result). Mirrored
    best-effort: losing a step artifact degrades replay, never lifecycle
    truth (the run state stays honest).
"""

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, DateTime, Float, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from spine_api.core.database import Base

_JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RunCheckpointModel(Base):
    """Authoritative SQL lifecycle record for one pipeline run."""

    __tablename__ = "run_checkpoints"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    trip_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    draft_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    agency_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    stage: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    operating_mode: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    total_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Failure / block forensics (mirror of the disk meta fields).
    error_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    failure_class: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    stage_at_failure: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    block_reason: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    recovered_after_timeout: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Reconciliation bookkeeping (startup orphan sweep).
    reconciled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    reconciled_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Extensible escape hatch for late-binding meta fields not columned above.
    extra_meta: Mapped[Optional[dict[str, Any]]] = mapped_column(_JSON_TYPE, nullable=True)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )


class RunCheckpointStepModel(Base):
    """One checkpointed pipeline step output (best-effort SQL mirror)."""

    __tablename__ = "run_checkpoint_steps"

    run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    step_name: Mapped[str] = mapped_column(String(64), primary_key=True)
    checkpointed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    data: Mapped[Optional[Any]] = mapped_column(_JSON_TYPE, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_utcnow, onupdate=_utcnow
    )
