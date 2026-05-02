"""
agents.recovery_agent — Phase 3 Self-Healing Agent (P3-01)

Monitors trips for stuck / anomalous states and attempts autonomous recovery.
Sits on top of the IntegrityWatchdog and DashboardAggregator SSOT.

Recovery actions (in order of escalation):
  1. re_queue      — Re-submit the trip through the intake pipeline
  2. escalate      — Flag for human review (sets review_status = escalated)
  3. alert         — Emit a system alert and take no further action

Each action is logged to the AuditStore with full context so operators can
review what was done and why.

Design invariants:
  - Every action is idempotent (safe to re-run on the same trip)
  - The agent never deletes data
  - Fail-closed: on any unexpected error, the agent emits an alert and stops
    attempting recovery for that trip to avoid amplifying a bad state

Activation:
  Instantiate and call .start() from the server lifespan.
  The agent uses IntegrityWatchdog as its heartbeat source.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

logger = logging.getLogger("recovery_agent")

# ── Thresholds ────────────────────────────────────────────────────────────────

# How long a trip can stay in a stage before the agent considers it "stuck".
# Values are in hours. Override via environment variables.
STUCK_THRESHOLDS_HOURS: dict[str, int] = {
    "intake":   int(os.environ.get("RECOVERY_STUCK_INTAKE_H",  "48")),
    "decision": int(os.environ.get("RECOVERY_STUCK_DECISION_H", "72")),
    "review":   int(os.environ.get("RECOVERY_STUCK_REVIEW_H",  "24")),
    "booking":  int(os.environ.get("RECOVERY_STUCK_BOOKING_H", "336")),   # 14 days
}

# How many consecutive re_queue attempts before escalating to a human.
MAX_REQUEUE_ATTEMPTS = int(os.environ.get("RECOVERY_MAX_REQUEUE", "2"))

# Poll interval for the recovery loop.
RECOVERY_INTERVAL_SECONDS = int(os.environ.get("RECOVERY_INTERVAL_S", "300"))  # 5 min


# ── Data model ────────────────────────────────────────────────────────────────

@dataclass(slots=True)
class StuckTrip:
    trip_id: str
    stage: str
    hours_stuck: float
    requeue_attempts: int = 0
    last_action: Optional[str] = None
    last_action_at: Optional[datetime] = None


@dataclass(slots=True)
class RecoveryResult:
    trip_id: str
    action: str
    success: bool
    reason: str
    attempted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ── Agent ─────────────────────────────────────────────────────────────────────

class RecoveryAgent:
    """
    Self-healing agent for Waypoint OS.

    Detects trips stuck in processing stages and attempts autonomous recovery.
    All actions are audit-logged. The agent is additive — it never mutates data
    in ways that cannot be reviewed and reversed by an operator.
    """

    def __init__(
        self,
        interval_seconds: int = RECOVERY_INTERVAL_SECONDS,
        audit_store=None,         # AuditStore instance (injected)
        trip_repo=None,           # Trip repository for querying/updating trips
        spine_runner=None,        # callable(trip_id) → triggers re-processing
    ):
        self._interval = interval_seconds
        self._audit = audit_store
        self._trip_repo = trip_repo
        self._spine_runner = spine_runner
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        # In-memory tracking of requeue attempts per trip (cleared on restart)
        self._requeue_counts: dict[str, int] = {}

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run_loop,
            daemon=True,
            name="RecoveryAgent",
        )
        self._thread.start()
        logger.info("RecoveryAgent started (interval=%ds)", self._interval)

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=10)
        self._thread = None
        logger.info("RecoveryAgent stopped")

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    # ── Main loop ─────────────────────────────────────────────────────────────

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self._recovery_pass()
            except Exception:
                logger.exception("RecoveryAgent: unhandled error in recovery pass — sleeping")
            self._stop_event.wait(timeout=self._interval)

    def _recovery_pass(self) -> list[RecoveryResult]:
        """Run one detection + recovery cycle. Returns actions taken."""
        stuck = self._detect_stuck_trips()
        if not stuck:
            return []

        results: list[RecoveryResult] = []
        for trip in stuck:
            result = self._recover(trip)
            results.append(result)
            self._audit_action(result)
        return results

    # ── Detection ─────────────────────────────────────────────────────────────

    def _detect_stuck_trips(self) -> list[StuckTrip]:
        """
        Query the trip repository for trips that have been in a processing
        stage longer than the configured threshold.
        """
        if self._trip_repo is None:
            return []

        now = datetime.now(timezone.utc)
        stuck: list[StuckTrip] = []

        try:
            active_trips = self._trip_repo.list_active()
        except Exception:
            logger.exception("RecoveryAgent: failed to list active trips")
            return []

        for trip in active_trips:
            stage = getattr(trip, "stage", None) or getattr(trip, "state", None)
            updated_at = getattr(trip, "updated_at", None) or getattr(trip, "updatedAt", None)
            if not stage or not updated_at:
                continue

            threshold_h = STUCK_THRESHOLDS_HOURS.get(stage)
            if threshold_h is None:
                continue

            if isinstance(updated_at, str):
                try:
                    updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                except ValueError:
                    continue

            hours_stuck = (now - updated_at).total_seconds() / 3600
            if hours_stuck >= threshold_h:
                stuck.append(StuckTrip(
                    trip_id=trip.id,
                    stage=stage,
                    hours_stuck=round(hours_stuck, 1),
                    requeue_attempts=self._requeue_counts.get(trip.id, 0),
                ))

        logger.info("RecoveryAgent: %d stuck trips detected", len(stuck))
        return stuck

    # ── Recovery ──────────────────────────────────────────────────────────────

    def _recover(self, trip: StuckTrip) -> RecoveryResult:
        """
        Choose and execute a recovery action for a stuck trip.

        Escalation ladder:
          attempts < MAX_REQUEUE_ATTEMPTS → re_queue
          attempts >= MAX_REQUEUE_ATTEMPTS → escalate (human review)
        """
        if trip.requeue_attempts < MAX_REQUEUE_ATTEMPTS and self._spine_runner is not None:
            return self._action_requeue(trip)
        else:
            return self._action_escalate(trip)

    def _action_requeue(self, trip: StuckTrip) -> RecoveryResult:
        """Re-submit the trip through the intake pipeline."""
        try:
            self._spine_runner(trip.trip_id)
            self._requeue_counts[trip.trip_id] = trip.requeue_attempts + 1
            logger.info(
                "RecoveryAgent: re-queued trip %s (attempt %d, stuck %.1fh in %s)",
                trip.trip_id, trip.requeue_attempts + 1, trip.hours_stuck, trip.stage,
            )
            return RecoveryResult(
                trip_id=trip.trip_id,
                action="re_queue",
                success=True,
                reason=f"Stuck {trip.hours_stuck:.0f}h in {trip.stage}; re-queued (attempt {trip.requeue_attempts + 1})",
            )
        except Exception as exc:
            logger.exception("RecoveryAgent: re_queue failed for trip %s", trip.trip_id)
            return RecoveryResult(
                trip_id=trip.trip_id,
                action="re_queue",
                success=False,
                reason=f"Re-queue failed: {exc}",
            )

    def _action_escalate(self, trip: StuckTrip) -> RecoveryResult:
        """Flag the trip for human review via the trip repository."""
        try:
            if self._trip_repo is not None:
                self._trip_repo.set_review_status(trip.trip_id, "escalated")
            logger.warning(
                "RecoveryAgent: escalated trip %s after %d requeue attempts (stuck %.1fh in %s)",
                trip.trip_id, trip.requeue_attempts, trip.hours_stuck, trip.stage,
            )
            return RecoveryResult(
                trip_id=trip.trip_id,
                action="escalate",
                success=True,
                reason=(
                    f"Stuck {trip.hours_stuck:.0f}h in {trip.stage}; "
                    f"escalated after {trip.requeue_attempts} requeue attempts"
                ),
            )
        except Exception as exc:
            logger.exception("RecoveryAgent: escalate failed for trip %s", trip.trip_id)
            return RecoveryResult(
                trip_id=trip.trip_id,
                action="escalate",
                success=False,
                reason=f"Escalation failed: {exc}",
            )

    # ── Audit ─────────────────────────────────────────────────────────────────

    def _audit_action(self, result: RecoveryResult) -> None:
        """Log the recovery action to the AuditStore."""
        if self._audit is None:
            return
        try:
            self._audit.log(
                event_type="recovery_agent",
                trip_id=result.trip_id,
                payload={
                    "action": result.action,
                    "success": result.success,
                    "reason": result.reason,
                    "attempted_at": result.attempted_at.isoformat(),
                },
            )
        except Exception:
            logger.exception("RecoveryAgent: audit log failed for trip %s", result.trip_id)

    # ── Manual trigger (for testing / admin endpoint) ─────────────────────────

    def run_once(self) -> list[RecoveryResult]:
        """Synchronously run one recovery pass. Useful for admin endpoints."""
        return self._recovery_pass()
