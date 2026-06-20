"""
agents.closed_loop_learning — ClosedLoopLearningAgent

Consumes AgenticEvalWorkItem instances produced by the eval feedback loop
and generates structured fix candidates with shadow testing.

The agent follows the ProductAgent protocol (scan + execute) and integrates
with the AgentSupervisor for durable work leasing.

Architecture:
  scan()  → queries execution events via TripRepository, produces WorkItems
             for each repeated failure signature with enough occurrences.
  execute()→ for each WorkItem:
             1. Builds a FixCandidate from the work item's layer recommendation
             2. Runs a shadow test: simulates the proposed fix against sample events
             3. Returns structured output with fix candidate, shadow results, and verdict
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Iterable, Optional

from src.agents.runtime import (
    AgentDefinition,
    AgentExecutionResult,
    ProductAgent,
    RetryPolicy,
    TripRepository,
    WorkItem,
    WorkStatus,
    get_field,
    get_nested,
    first_non_empty,
)
from src.evals.agentic_feedback import (
    AgenticEvalWorkItem,
    build_repeated_failure_signal,
    _LAYER_RECOMMENDATIONS,
    _estimate_severity,
)

logger = logging.getLogger("closed_loop_learning")


# ---------------------------------------------------------------------------
# Fix Candidate model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class FixCandidate:
    """A proposed fix for a repeated failure pattern."""

    candidate_id: str
    failure_signature: str
    failure_layer: str
    next_fix_layer: str
    severity: str
    proposed_change: str
    expected_improvement: str
    regression_risk: str
    rerun_subset: str
    owner: str
    occurrences: int
    first_seen: str
    last_seen: str
    sample_events: list[str]
    created_at: str = ""

    def __post_init__(self) -> None:
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Shadow Test Result model
# ---------------------------------------------------------------------------

@dataclass(slots=True)
class ShadowTestResult:
    """Outcome of a shadow test run against sample events."""

    candidate_id: str
    sample_count: int
    simulated_fixes: int
    simulated_regressions: int
    simulated_unchanged: int
    confidence_delta: float  # positive = improvement expected
    verdict: str  # "proceed", "defer", "reject"
    rationale: str
    run_at: str = ""

    def __post_init__(self) -> None:
        if not self.run_at:
            self.run_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Shadow testing engine
# ---------------------------------------------------------------------------

# Minimum confidence delta to recommend "proceed"
PROCEED_CONFIDENCE_THRESHOLD = 0.05

# Maximum regressions before "reject"
MAX_REGRESSIONS_BEFORE_REJECT = 2


def run_shadow_test(
    candidate: FixCandidate,
    sample_events: list[dict[str, Any]],
) -> ShadowTestResult:
    """Simulate the proposed fix against historical sample events.

    This is a deterministic shadow simulation, not a real reprocessing.
    It checks whether the proposed change would have resolved the failure
    signatures in the sample events.

    Args:
        candidate: The fix candidate to test.
        sample_events: List of event metadata dicts with failure info.

    Returns:
        ShadowTestResult with simulation outcomes.
    """
    simulated_fixes = 0
    simulated_regressions = 0
    simulated_unchanged = 0

    for event in sample_events:
        metadata = event.get("event_metadata", {})
        event_failure_layer = metadata.get("failure_layer", "unknown")
        event_review_outcome = metadata.get("review_outcome")
        event_fallback_result = metadata.get("fallback_result")

        # Simulate: does this fix address the event's failure?
        if event_failure_layer == candidate.next_fix_layer:
            # Fix targets this layer — likely resolves the failure
            simulated_fixes += 1
        elif event_failure_layer == candidate.failure_layer:
            # Fix targets a different layer than where this event failed
            # Could be a regression if the fix changes behavior at the wrong layer
            if candidate.regression_risk and "overfit" in candidate.regression_risk.lower():
                simulated_regressions += 1
            else:
                simulated_unchanged += 1
        else:
            # Different layer entirely — no impact
            simulated_unchanged += 1

    total = max(len(sample_events), 1)
    fix_rate = simulated_fixes / total
    regression_rate = simulated_regressions / total
    confidence_delta = fix_rate - regression_rate

    # Determine verdict
    if simulated_regressions >= MAX_REGRESSIONS_BEFORE_REJECT:
        verdict = "reject"
        rationale = (
            f"Shadow test flagged {simulated_regressions} potential regression(s) "
            f"out of {len(sample_events)} samples. Review manually before proceeding."
        )
    elif confidence_delta >= PROCEED_CONFIDENCE_THRESHOLD:
        verdict = "proceed"
        rationale = (
            f"Shadow test shows {simulated_fixes}/{len(sample_events)} simulated fixes "
            f"({fix_rate:.0%}) with {simulated_regressions} potential regressions. "
            f"Confidence delta: +{confidence_delta:.2f}."
        )
    elif confidence_delta > 0:
        verdict = "defer"
        rationale = (
            f"Shadow test shows marginal improvement ({simulated_fixes} fixes, "
            f"{simulated_regressions} regressions). Recommend gathering more samples "
            f"before proceeding."
        )
    else:
        verdict = "reject"
        rationale = (
            f"Shadow test shows no improvement ({simulated_fixes} fixes, "
            f"{simulated_regressions} regressions out of {len(sample_events)} samples)."
        )

    return ShadowTestResult(
        candidate_id=candidate.candidate_id,
        sample_count=len(sample_events),
        simulated_fixes=simulated_fixes,
        simulated_regressions=simulated_regressions,
        simulated_unchanged=simulated_unchanged,
        confidence_delta=round(confidence_delta, 4),
        verdict=verdict,
        rationale=rationale,
    )


# ---------------------------------------------------------------------------
# Fix candidate builder
# ---------------------------------------------------------------------------

def _build_candidate_id(failure_signature: str, layer: str) -> str:
    """Generate a deterministic candidate ID from the failure signature."""
    raw = f"{failure_signature}:{layer}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:16]
    return f"fix_{digest}"


def build_fix_candidate(
    work_item: AgenticEvalWorkItem,
) -> FixCandidate:
    """Convert an AgenticEvalWorkItem into a FixCandidate with layer-specific recommendations."""
    layer_key = work_item.next_fix_layer or work_item.failure_layer or "unknown"
    recommendation = _LAYER_RECOMMENDATIONS.get(layer_key, _LAYER_RECOMMENDATIONS["unknown"])

    return FixCandidate(
        candidate_id=_build_candidate_id(work_item.failure_signature, layer_key),
        failure_signature=work_item.failure_signature,
        failure_layer=work_item.failure_layer,
        next_fix_layer=layer_key,
        severity=work_item.severity or _estimate_severity(work_item.occurrences),
        proposed_change=work_item.proposed_change or recommendation["proposed_change"],
        expected_improvement=work_item.expected_improvement or recommendation["expected_improvement"],
        regression_risk=work_item.regression_risk or recommendation["regression_risk"],
        rerun_subset=work_item.rerun_subset or recommendation["rerun_subset"],
        owner=work_item.owner or recommendation["owner"],
        occurrences=work_item.occurrences,
        first_seen=work_item.first_seen.isoformat(),
        last_seen=work_item.last_seen.isoformat(),
        sample_events=work_item.sample_events,
    )


# ---------------------------------------------------------------------------
# ClosedLoopLearningAgent
# ---------------------------------------------------------------------------

class ClosedLoopLearningAgent:
    """Agent that consumes eval failure signals and produces fix candidates.

    Follows the ProductAgent protocol for integration with AgentSupervisor.

    scan():
        Queries the TripRepository for trips with execution events that have
        repeated failure signatures. Uses build_repeated_failure_signal() to
        find patterns with enough occurrences to warrant a fix candidate.

    execute():
        For each WorkItem:
        1. Builds a FixCandidate from the work item payload
        2. Retrieves sample event metadata for shadow testing
        3. Runs a shadow simulation
        4. Returns structured output with fix candidate, shadow results, and verdict
    """

    definition = AgentDefinition(
        name="closed_loop_learning_agent",
        description="Consumes eval failure signals, produces fix candidates with shadow testing, and surfaces actionable recommendations.",
        trigger_contract="Execution events contain repeated failure_signature with enough occurrences (≥3) to indicate a systemic issue.",
        input_contract="Trip records with execution events and review history. WorkItem payload contains AgenticEvalWorkItem fields.",
        output_contract="Trip is updated with closed_loop_fix_candidate, closed_loop_shadow_test, and closed_loop_verdict.",
        idempotency_contract="One fix candidate per failure_signature until the signature changes or the candidate is resolved.",
        failure_contract="Retry event query failures; poison after retry budget. Shadow test failures produce 'defer' verdict, not poison.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 2, 8)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}

    def __init__(
        self,
        min_occurrences: int = 3,
        window_hours: int = 24 * 7,
        event_query_fn: Optional[Callable[..., Any]] = None,
        now_provider: Optional[Callable[[], datetime]] = None,
    ):
        self.min_occurrences = min_occurrences
        self.window_hours = window_hours
        self._event_query_fn = event_query_fn
        self._now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    # -- ProductAgent protocol ------------------------------------------------

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        """Scan for trips with repeated eval failure signals."""
        now = self._now_provider()
        window_start = now - timedelta(hours=self.window_hours)
        seen_signatures: set[str] = set()

        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            if not trip_id or status in self._terminal_statuses:
                continue

            # Check if this trip already has a fix candidate
            existing = get_field(trip, "closed_loop_fix_candidate")
            if isinstance(existing, dict) and existing.get("candidate_id"):
                sig = existing.get("failure_signature", "")
                if sig:
                    seen_signatures.add(sig)
                continue

            # Look for execution events with eval metadata on the trip
            eval_events = self._extract_eval_events(trip)
            if not eval_events:
                continue

            # Build repeated failure signals from the trip's events
            work_items = build_repeated_failure_signal(
                eval_events,
                min_occurrences=self.min_occurrences,
            )

            for item in work_items:
                if item.failure_signature in seen_signatures:
                    continue
                seen_signatures.add(item.failure_signature)

                marker = f"{item.failure_signature}:{item.occurrences}:{item.last_seen.isoformat()}"
                yield WorkItem(
                    agent_name=self.definition.name,
                    trip_id=trip_id,
                    action="generate_fix_candidate",
                    idempotency_key=f"{self.definition.name}:{trip_id}:{marker}",
                    payload={
                        "failure_signature": item.failure_signature,
                        "failure_layer": item.failure_layer,
                        "next_fix_layer": item.next_fix_layer,
                        "occurrences": item.occurrences,
                        "first_seen": item.first_seen.isoformat(),
                        "last_seen": item.last_seen.isoformat(),
                        "sample_events": item.sample_events,
                        "severity": item.severity,
                        "proposed_change": item.proposed_change,
                        "expected_improvement": item.expected_improvement,
                        "regression_risk": item.regression_risk,
                        "rerun_subset": item.rerun_subset,
                        "keep_if": item.keep_if,
                        "revert_if": item.revert_if,
                        "owner": item.owner,
                    },
                )

    def execute(
        self, work_item: WorkItem, trip_repo: TripRepository
    ) -> AgentExecutionResult:
        """Generate a fix candidate and run shadow testing."""
        payload = work_item.payload or {}
        failure_signature = payload.get("failure_signature", "")

        if not failure_signature:
            return AgentExecutionResult(
                work_item=work_item,
                status=WorkStatus.RETRY_PENDING,
                success=False,
                reason="Work item payload missing failure_signature",
            )

        try:
            # Step 1: Build the AgenticEvalWorkItem from the payload
            work_item_data = AgenticEvalWorkItem(
                failure_signature=failure_signature,
                failure_layer=payload.get("failure_layer", "unknown"),
                next_fix_layer=payload.get("next_fix_layer", "unknown"),
                occurrences=payload.get("occurrences", 0),
                first_seen=datetime.fromisoformat(payload["first_seen"]),
                last_seen=datetime.fromisoformat(payload["last_seen"]),
                sample_events=payload.get("sample_events", []),
                severity=payload.get("severity", "medium"),
                proposed_change=payload.get("proposed_change"),
                expected_improvement=payload.get("expected_improvement"),
                regression_risk=payload.get("regression_risk"),
                rerun_subset=payload.get("rerun_subset"),
                keep_if=payload.get("keep_if"),
                revert_if=payload.get("revert_if"),
                owner=payload.get("owner"),
            )

            # Step 2: Build FixCandidate
            candidate = build_fix_candidate(work_item_data)

            # Step 3: Retrieve sample event metadata for shadow testing.
            # Look up the trip to access its execution events, then extract
            # real metadata instead of returning stubs.
            trip = self._lookup_trip(work_item.trip_id, trip_repo)
            sample_events = self._retrieve_sample_event_metadata(
                trip, payload.get("sample_events", [])
            ) if trip else []

            if not sample_events and payload.get("sample_events"):
                logger.warning(
                    "ClosedLoopLearningAgent: no sample event metadata found for %d IDs on trip %s",
                    len(payload["sample_events"]), work_item.trip_id,
                )

            # Step 4: Run shadow test
            shadow_result = run_shadow_test(candidate, sample_events)

            # Step 5: Build output
            output = {
                "fix_candidate": candidate.to_dict(),
                "shadow_test": shadow_result.to_dict(),
                "verdict": shadow_result.verdict,
                "rationale": shadow_result.rationale,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "source": self.definition.name,
            }

            # Step 6: Update trip with the fix candidate
            updated = trip_repo.update_trip(
                work_item.trip_id,
                {
                    "closed_loop_fix_candidate": candidate.to_dict(),
                    "closed_loop_shadow_test": shadow_result.to_dict(),
                    "closed_loop_verdict": shadow_result.verdict,
                    "last_agent_action": self.definition.name,
                    "last_agent_action_at": datetime.now(timezone.utc).isoformat(),
                },
            )

            if not updated:
                return AgentExecutionResult(
                    work_item=work_item,
                    status=WorkStatus.RETRY_PENDING,
                    success=False,
                    reason="Trip update returned empty result",
                )

            return AgentExecutionResult(
                work_item=work_item,
                status=WorkStatus.COMPLETED,
                success=True,
                reason=f"Generated fix candidate with shadow verdict: {shadow_result.verdict}",
                output=output,
            )

        except Exception as exc:
            logger.exception(
                "ClosedLoopLearningAgent: failed to generate fix candidate for %s",
                failure_signature,
            )
            return AgentExecutionResult(
                work_item=work_item,
                status=WorkStatus.RETRY_PENDING,
                success=False,
                reason=f"Fix candidate generation failed: {exc}",
            )

    # -- Internal helpers -----------------------------------------------------

    def _lookup_trip(self, trip_id: str, trip_repo: TripRepository) -> Optional[Any]:
        """Find a trip by ID from the repository's active list."""
        for trip in trip_repo.list_active():
            if str(get_field(trip, "id") or "") == trip_id:
                return trip
        return None

    def _extract_eval_events(self, trip: Any) -> list[Any]:
        """Extract execution events from a trip record that have eval metadata.

        Returns lightweight event objects compatible with
        ``build_repeated_failure_signal()`` which expects objects with
        attribute access (``.event_metadata``, ``.trip_id``, etc.).
        """
        from types import SimpleNamespace

        raw_events = first_non_empty(
            get_field(trip, "execution_events"),
            get_nested(trip, "events"),
            get_nested(trip, "analytics.execution_events"),
            [],
        )

        if not isinstance(raw_events, list):
            return []

        eval_relevant_keys = {
            "failure_signature",
            "fallback_trigger_reason",
            "review_trigger_reason",
            "review_outcome",
            "escalation_outcome",
        }
        events: list[SimpleNamespace] = []
        for raw in raw_events:
            if not isinstance(raw, dict):
                continue
            metadata = raw.get("event_metadata") or raw.get("metadata") or {}
            if not any(key in metadata for key in eval_relevant_keys):
                continue
            # Convert to an object with attribute access for AgenticEvalRecord.from_event
            created_at = raw.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    created_at = self._now_provider()
            elif not isinstance(created_at, datetime):
                created_at = self._now_provider()
            events.append(SimpleNamespace(
                id=raw.get("id", "unknown"),
                trip_id=raw.get("trip_id", trip.get("id", "unknown") if isinstance(trip, dict) else "unknown"),
                event_category=raw.get("event_category", "unknown"),
                event_type=raw.get("event_type", "unknown"),
                subject_type=raw.get("subject_type", "trip"),
                subject_id=raw.get("subject_id", "unknown"),
                event_metadata=metadata,
                created_at=created_at,
            ))

        return events

    def _retrieve_sample_event_metadata(
        self,
        trip: Any,
        sample_event_ids: list[str],
    ) -> list[dict[str, Any]]:
        """Retrieve real metadata for specific sample events from the trip.

        Uses the trip's execution events (already extracted via
        ``_extract_eval_events``) and returns the raw event dicts
        matching the requested IDs.  Missing events are skipped
        gracefully — the shadow test handles partial data.
        """
        if not sample_event_ids:
            return []

        # Build an index of the trip's raw execution events by ID.
        raw_events = first_non_empty(
            get_field(trip, "execution_events"),
            get_nested(trip, "events"),
            get_nested(trip, "analytics.execution_events"),
            [],
        )
        if not isinstance(raw_events, list):
            return []

        events_by_id: dict[str, dict[str, Any]] = {}
        for raw in raw_events:
            if isinstance(raw, dict):
                eid = raw.get("id")
                if eid:
                    events_by_id[str(eid)] = raw

        # Return metadata for requested events, skipping any not found.
        return [
            events_by_id[event_id]
            for event_id in sample_event_ids
            if event_id in events_by_id
        ]
