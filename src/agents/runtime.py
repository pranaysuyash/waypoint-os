"""
Canonical backend product-agent runtime primitives.

The runtime is deliberately static and in-repo: agents are registered by code,
then supervised through deterministic scans and single-owner work execution.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Iterable, Optional, Protocol
from uuid import uuid4

from src.agents.events import AgentEvent, AgentEventType
from src.agents.risk_contracts import feasibility_constraint_to_structured
from src.intake.risk_action_policy import build_risk_action_plan
from src.intake.route_analysis import analyze_route_complexity, parse_itinerary_text
from src.intake.regional_risk import assess_regional_disruption
from src.intake.scenario_policy import ScenarioPolicy, load_scenario_policy
from src.agents.live_tools import (
    FlightStatusTool,
    PriceWatchTool,
    SafetyAlertTool,
    WeatherTool,
    build_flight_status_tool_from_env,
    build_price_watch_tool_from_env,
    build_safety_alert_tool_from_env,
    build_weather_tool_from_env,
)
from src.agents.tool_contracts import ToolFreshnessPolicy, ToolResult

logger = logging.getLogger("agent_runtime")


class WorkStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    RETRY_PENDING = "retry_pending"
    POISONED = "poisoned"
    ESCALATED = "escalated"


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 3
    backoff_seconds: tuple[int, ...] = (0, 1, 5)


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    name: str
    description: str
    trigger_contract: str
    input_contract: str
    output_contract: str
    idempotency_contract: str
    failure_contract: str
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["retry_policy"] = asdict(self.retry_policy)
        return data


@dataclass(frozen=True, slots=True)
class WorkItem:
    agent_name: str
    trip_id: str
    action: str
    idempotency_key: str
    payload: dict[str, Any] = field(default_factory=dict)
    correlation_id: str = field(default_factory=lambda: f"corr_{uuid4().hex[:12]}")


@dataclass(slots=True)
class AgentExecutionResult:
    work_item: WorkItem
    status: WorkStatus
    success: bool
    reason: str
    output: dict[str, Any] = field(default_factory=dict)
    attempt: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_name": self.work_item.agent_name,
            "trip_id": self.work_item.trip_id,
            "action": self.work_item.action,
            "idempotency_key": self.work_item.idempotency_key,
            "correlation_id": self.work_item.correlation_id,
            "status": self.status.value,
            "success": self.success,
            "reason": self.reason,
            "output": self.output,
            "attempt": self.attempt,
        }


class AgentAuditSink(Protocol):
    def log(self, event_type: str, trip_id: str, payload: dict[str, Any], user_id: Optional[str] = None) -> None:
        ...


class TripRepository(Protocol):
    def list_active(self) -> list[Any]:
        ...

    def update_trip(self, trip_id: str, updates: dict[str, Any]) -> Optional[dict[str, Any]]:
        ...


class ProductAgent(Protocol):
    definition: AgentDefinition

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        ...

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        ...


class WorkCoordinator(Protocol):
    def acquire(self, work_item: WorkItem, owner: str, retry_policy: RetryPolicy) -> tuple[bool, str, int]:
        ...

    def complete(self, work_item: WorkItem, reason: str = "") -> None:
        ...

    def fail(self, work_item: WorkItem, status: WorkStatus, reason: str) -> None:
        ...

    def snapshot(self) -> dict[str, Any]:
        ...


@dataclass(slots=True)
class LeaseRecord:
    owner: str
    leased_until: float
    status: WorkStatus
    attempts: int = 0
    last_reason: str = ""


class InMemoryWorkCoordinator:
    """Thread-safe single-owner lease and idempotency boundary."""

    def __init__(self, lease_seconds: int = 60):
        self._lease_seconds = lease_seconds
        self._lock = threading.RLock()
        self._leases: dict[str, LeaseRecord] = {}
        self._completed: set[str] = set()
        self._poisoned: set[str] = set()

    def acquire(self, work_item: WorkItem, owner: str, retry_policy: RetryPolicy) -> tuple[bool, str, int]:
        now = time.monotonic()
        key = work_item.idempotency_key
        with self._lock:
            if key in self._completed:
                return False, "idempotent_reentry_completed", 0
            if key in self._poisoned:
                return False, "poisoned_fail_closed", 0
            current = self._leases.get(key)
            if current and current.status == WorkStatus.RUNNING and current.leased_until > now:
                return False, f"owned_by:{current.owner}", current.attempts

            attempts = (current.attempts + 1) if current else 1
            if attempts > retry_policy.max_attempts:
                self._poisoned.add(key)
                self._leases[key] = LeaseRecord(
                    owner=owner,
                    leased_until=now,
                    status=WorkStatus.POISONED,
                    attempts=attempts - 1,
                    last_reason="retry_policy_exhausted",
                )
                return False, "retry_policy_exhausted", attempts - 1

            self._leases[key] = LeaseRecord(
                owner=owner,
                leased_until=now + self._lease_seconds,
                status=WorkStatus.RUNNING,
                attempts=attempts,
            )
            return True, "acquired", attempts

    def complete(self, work_item: WorkItem, reason: str = "") -> None:
        with self._lock:
            self._completed.add(work_item.idempotency_key)
            record = self._leases.get(work_item.idempotency_key)
            attempts = record.attempts if record else 1
            self._leases[work_item.idempotency_key] = LeaseRecord(
                owner=work_item.agent_name,
                leased_until=time.monotonic(),
                status=WorkStatus.COMPLETED,
                attempts=attempts,
                last_reason=reason,
            )

    def fail(self, work_item: WorkItem, status: WorkStatus, reason: str) -> None:
        with self._lock:
            record = self._leases.get(work_item.idempotency_key)
            attempts = record.attempts if record else 1
            if status == WorkStatus.POISONED:
                self._poisoned.add(work_item.idempotency_key)
            self._leases[work_item.idempotency_key] = LeaseRecord(
                owner=work_item.agent_name,
                leased_until=time.monotonic(),
                status=status,
                attempts=attempts,
                last_reason=reason,
            )

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "completed": len(self._completed),
                "poisoned": len(self._poisoned),
                "leases": {
                    key: {
                        "owner": value.owner,
                        "status": value.status.value,
                        "attempts": value.attempts,
                        "last_reason": value.last_reason,
                    }
                    for key, value in sorted(self._leases.items())
                },
            }


class AgentRegistry:
    """Explicit static registry; no dynamic plugin loading."""

    def __init__(self, agents: Iterable[ProductAgent]):
        self._agents = {agent.definition.name: agent for agent in agents}

    def get(self, name: str) -> ProductAgent:
        return self._agents[name]

    def agents(self) -> list[ProductAgent]:
        return [self._agents[name] for name in sorted(self._agents)]

    def definitions(self) -> list[dict[str, Any]]:
        return [agent.definition.to_dict() for agent in self.agents()]


class AgentSupervisor:
    def __init__(
        self,
        registry: AgentRegistry,
        trip_repo: TripRepository,
        audit: Optional[AgentAuditSink],
        interval_seconds: int = 300,
        coordinator: Optional[WorkCoordinator] = None,
    ):
        self.registry = registry
        self.trip_repo = trip_repo
        self.audit = audit
        self.interval_seconds = interval_seconds
        self.coordinator = coordinator or InMemoryWorkCoordinator()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._started_at: Optional[str] = None
        self._last_pass_at: Optional[str] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self._thread is not None:
            return
        self._stop_event.clear()
        self._started_at = datetime.now(timezone.utc).isoformat()
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="AgentSupervisor")
        self._thread.start()
        self._emit_system_event(AgentEventType.AGENT_STARTED, {"agents": [a.definition.name for a in self.registry.agents()]})

    def stop(self) -> None:
        if self._thread is None:
            return
        self._stop_event.set()
        self._thread.join(timeout=10)
        self._thread = None
        self._emit_system_event(AgentEventType.AGENT_STOPPED, {"agents": [a.definition.name for a in self.registry.agents()]})

    def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                logger.exception("AgentSupervisor: unhandled runtime pass failure")
            self._stop_event.wait(timeout=self.interval_seconds)

    def run_once(self, agent_name: Optional[str] = None) -> list[AgentExecutionResult]:
        selected = [self.registry.get(agent_name)] if agent_name else self.registry.agents()
        results: list[AgentExecutionResult] = []
        for agent in selected:
            definition = agent.definition
            try:
                work_items = list(agent.scan(self.trip_repo))
            except Exception as exc:
                self._emit_agent_event(
                    definition.name,
                    AgentEventType.AGENT_FAILED,
                    trip_id=None,
                    correlation_id=f"corr_{uuid4().hex[:12]}",
                    payload={"phase": "scan", "reason": str(exc), "failure_mode": definition.failure_contract},
                )
                continue

            for item in work_items:
                acquired, acquire_reason, attempt = self.coordinator.acquire(
                    item,
                    owner=definition.name,
                    retry_policy=definition.retry_policy,
                )
                if not acquired:
                    event_type = AgentEventType.AGENT_RETRY if acquire_reason.startswith("owned_by:") else AgentEventType.AGENT_DECISION
                    self._emit_agent_event(
                        definition.name,
                        event_type,
                        trip_id=item.trip_id,
                        correlation_id=item.correlation_id,
                        payload={
                            "decision": "skip",
                            "reason": acquire_reason,
                            "idempotency_key": item.idempotency_key,
                        },
                    )
                    continue

                self._emit_agent_event(
                    definition.name,
                    AgentEventType.AGENT_DECISION,
                    trip_id=item.trip_id,
                    correlation_id=item.correlation_id,
                    payload={
                        "decision": "execute",
                        "action": item.action,
                        "attempt": attempt,
                        "idempotency_key": item.idempotency_key,
                    },
                )
                try:
                    result = agent.execute(item, self.trip_repo)
                    result.attempt = attempt
                except Exception as exc:
                    result = AgentExecutionResult(
                        work_item=item,
                        status=WorkStatus.RETRY_PENDING,
                        success=False,
                        reason=str(exc),
                        output={"failure_mode": definition.failure_contract},
                        attempt=attempt,
                    )

                if result.success:
                    self.coordinator.complete(item, result.reason)
                    event_type = AgentEventType.AGENT_ACTION
                else:
                    terminal = attempt >= definition.retry_policy.max_attempts
                    status = WorkStatus.POISONED if terminal else WorkStatus.RETRY_PENDING
                    self.coordinator.fail(item, status=status, reason=result.reason)
                    result.status = status
                    event_type = AgentEventType.AGENT_ESCALATED if terminal else AgentEventType.AGENT_RETRY

                self._emit_agent_event(
                    definition.name,
                    event_type,
                    trip_id=item.trip_id,
                    correlation_id=item.correlation_id,
                    payload=result.to_dict(),
                )
                results.append(result)
        self._last_pass_at = datetime.now(timezone.utc).isoformat()
        return results

    def health(self) -> dict[str, Any]:
        return {
            "running": self.is_running,
            "started_at": self._started_at,
            "last_pass_at": self._last_pass_at,
            "registered_agents": [agent.definition.name for agent in self.registry.agents()],
            "coordinator": self.coordinator.snapshot(),
        }

    def _emit_system_event(self, event_type: AgentEventType, payload: dict[str, Any]) -> None:
        self._emit_agent_event(
            "agent_supervisor",
            event_type,
            trip_id=None,
            correlation_id=f"corr_{uuid4().hex[:12]}",
            payload=payload,
        )

    def _emit_agent_event(
        self,
        agent_name: str,
        event_type: AgentEventType,
        trip_id: Optional[str],
        correlation_id: str,
        payload: dict[str, Any],
    ) -> None:
        if self.audit is None:
            return
        event = AgentEvent(
            agent_name=agent_name,
            event_type=event_type,
            trip_id=trip_id,
            correlation_id=correlation_id,
            payload=payload,
        )
        try:
            self.audit.log(
                event_type="agent_event",
                trip_id=trip_id or "",
                payload=event.to_dict(),
                user_id=agent_name,
            )
        except TypeError:
            self.audit.log(event_type="agent_event", trip_id=trip_id or "", payload=event.to_dict())
        except Exception:
            logger.exception("AgentSupervisor: audit log failed for %s", agent_name)


def parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None


def get_field(source: Any, *names: str) -> Any:
    for name in names:
        if isinstance(source, dict) and name in source:
            return source[name]
        if not isinstance(source, dict) and hasattr(source, name):
            return getattr(source, name)
    return None


def get_nested(source: Any, path: str, default: Any = None) -> Any:
    current = source
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        else:
            current = getattr(current, part, None)
        if current is None:
            return default
    return current


def first_non_empty(*values: Any) -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return None


def _word_count(value: Any) -> int:
    if not isinstance(value, str):
        return 0
    return len([part for part in value.replace("\n", " ").split(" ") if part.strip()])


def _slot_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    if hasattr(value, "value"):
        return getattr(value, "value")
    return value


def _flatten_values(value: Any) -> list[Any]:
    if value in (None, "", [], {}):
        return []
    if isinstance(value, list):
        return value
    return [value]


def _stringify(value: Any) -> str:
    if isinstance(value, dict):
        return str(first_non_empty(value.get("value"), value.get("name"), value.get("label"), value))
    return str(value)


class FrontDoorAgent:
    definition = AgentDefinition(
        name="front_door_agent",
        description="Classifies fresh or incomplete inquiries so every lead gets a next operational step.",
        trigger_contract="Trip is new/incomplete/unassigned and has no current front_door_assessment.",
        input_contract="Trip record with id, status/stage, raw_input, extracted facts, decision state, assignment metadata.",
        output_contract="Trip is updated with front_door_assessment, priority, recommended_next_action, and acknowledgment draft.",
        idempotency_contract="One assessment per trip_id plus raw/updated timestamp marker until the inquiry changes.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _eligible_statuses = {"", "new", "incomplete", "needs_clarification", "awaiting_customer_details"}

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            stage = str(get_field(trip, "stage") or "").lower()
            if not trip_id or (status not in self._eligible_statuses and stage not in {"discovery", "intake"}):
                continue
            assessment = get_field(trip, "front_door_assessment")
            if isinstance(assessment, dict) and assessment.get("assessed_at"):
                continue
            marker = first_non_empty(get_field(trip, "updated_at", "updatedAt"), get_field(trip, "created_at", "createdAt"), "initial")
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="classify_inquiry",
                idempotency_key=f"{self.definition.name}:{trip_id}:{marker}",
                payload={"status": status, "stage": stage},
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        trip = self._lookup_trip(work_item.trip_id, trip_repo)
        if not trip:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip not found during front-door assessment")

        facts = get_nested(trip, "extracted.facts", {}) or {}
        raw_text = first_non_empty(
            get_nested(trip, "raw_input.raw_note"),
            get_field(trip, "raw_note", "rawNote"),
            get_field(trip, "customer_notes", "customerNotes"),
            "",
        )
        destination = first_non_empty(
            _slot_value(facts.get("destination_candidates")),
            _slot_value(facts.get("destination")),
            get_field(trip, "destination"),
        )
        date_window = first_non_empty(_slot_value(facts.get("date_window")), get_field(trip, "date_window", "dateWindow"))
        party = first_non_empty(_slot_value(facts.get("party_composition")), get_field(trip, "party_composition", "partyComposition"))
        budget = first_non_empty(_slot_value(facts.get("budget")), get_field(trip, "budget"))
        decision_state = str(first_non_empty(get_field(trip, "decision_state", "decisionState"), get_nested(trip, "decision.decision_state"), "")).upper()
        hard_blockers = first_non_empty(get_field(trip, "hard_blockers", "hardBlockers"), get_nested(trip, "decision.hard_blockers"), [])

        missing = [
            name
            for name, value in {
                "destination": destination,
                "travel dates": date_window,
                "traveler count": party,
                "budget": budget,
            }.items()
            if value in (None, "", [], {})
        ]
        word_count = _word_count(raw_text)
        is_real_lead = bool(destination or date_window or party or budget or word_count >= 12)
        priority = "urgent" if self._is_urgent(date_window, raw_text) else "normal"
        if missing or decision_state in {"ASK_FOLLOWUP", "STOP_NEEDS_REVIEW"} or hard_blockers:
            priority = "high" if priority != "urgent" else priority
            next_action = "clarify_missing_trip_details"
        elif is_real_lead:
            next_action = "qualify_and_route"
        else:
            priority = "low"
            next_action = "request_basic_trip_context"

        assessment = {
            "is_real_lead": is_real_lead,
            "priority": priority,
            "missing_fields": missing,
            "decision_state": decision_state or None,
            "hard_blocker_count": len(hard_blockers) if isinstance(hard_blockers, list) else 0,
            "recommended_next_action": next_action,
            "acknowledgment_draft": self._acknowledgment(destination, missing),
            "assessed_at": datetime.now(timezone.utc).isoformat(),
            "source": self.definition.name,
        }
        updates = {
            "front_door_assessment": assessment,
            "lead_priority": priority,
            "recommended_next_action": next_action,
            "last_agent_action": self.definition.name,
            "last_agent_action_at": datetime.now(timezone.utc).isoformat(),
        }
        updated = trip_repo.update_trip(work_item.trip_id, updates)
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Classified inquiry and drafted acknowledgment", assessment)

    def _lookup_trip(self, trip_id: str, trip_repo: TripRepository) -> Optional[Any]:
        for trip in trip_repo.list_active():
            if str(get_field(trip, "id") or "") == trip_id:
                return trip
        return None

    def _is_urgent(self, date_window: Any, raw_text: Any) -> bool:
        text = f"{date_window or ''} {raw_text or ''}".lower()
        urgent_terms = {"urgent", "asap", "today", "tomorrow", "this week", "last minute", "immediate"}
        if any(term in text for term in urgent_terms):
            return True
        parsed = parse_dt(str(date_window)) if date_window else None
        return bool(parsed and parsed <= datetime.now(timezone.utc) + timedelta(days=14))

    def _acknowledgment(self, destination: Any, missing: list[str]) -> str:
        dest_text = f" for {destination}" if destination else ""
        if missing:
            return f"Thanks for the inquiry{dest_text}. We are reviewing it and need a few details: {', '.join(missing)}."
        return f"Thanks for the inquiry{dest_text}. We are reviewing the trip details and will come back with the next step."


class SalesActivationAgent:
    definition = AgentDefinition(
        name="sales_activation_agent",
        description="Keeps qualified leads moving by scheduling stage-aware follow-up tasks before they go cold.",
        trigger_contract="Open lead has no pending follow-up and has been idle beyond its stage SLA.",
        input_contract="Trip record with id, status/stage, timestamps, lead priority, and follow-up fields.",
        output_contract="Trip is updated with follow_up_due_date, follow_up_status=pending, and a follow-up reason/draft.",
        idempotency_contract="One scheduled follow-up per trip_id plus current status/stage and timestamp marker.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost", "booked"}
    _stage_sla_hours = {
        "new": 24,
        "incomplete": 24,
        "needs_clarification": 24,
        "contacted": 48,
        "quoted": 48,
        "proposal": 48,
        "shortlist": 72,
    }

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        now = datetime.now(timezone.utc)
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(first_non_empty(get_field(trip, "status"), get_field(trip, "stage"), "")).lower()
            if not trip_id or status in self._terminal_statuses:
                continue
            due = parse_dt(get_field(trip, "follow_up_due_date", "followUpDueDate"))
            follow_status = str(get_field(trip, "follow_up_status", "followUpStatus") or "").lower()
            if due and follow_status in {"", "pending", "due", "snoozed"}:
                continue
            updated_at = parse_dt(first_non_empty(get_field(trip, "updated_at", "updatedAt"), get_field(trip, "created_at", "createdAt")))
            if not updated_at:
                continue
            sla_h = self._stage_sla_hours.get(status, 72)
            idle_h = (now - updated_at).total_seconds() / 3600
            if idle_h < sla_h:
                continue
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="schedule_sales_follow_up",
                idempotency_key=f"{self.definition.name}:{trip_id}:{status}:{updated_at.isoformat()}",
                payload={"status": status, "idle_hours": round(idle_h, 1), "sla_hours": sla_h},
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        status = str(work_item.payload.get("status") or "open")
        due_at = datetime.now(timezone.utc) + timedelta(hours=4 if status in {"new", "incomplete", "needs_clarification"} else 24)
        reason = f"Lead idle {work_item.payload.get('idle_hours')}h in {status}; stage SLA is {work_item.payload.get('sla_hours')}h"
        draft = self._draft_for_status(status)
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "follow_up_due_date": due_at.isoformat(),
                "follow_up_status": "pending",
                "follow_up_reason": reason,
                "follow_up_draft": draft,
                "last_agent_action": self.definition.name,
                "last_agent_action_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(
            work_item,
            WorkStatus.COMPLETED,
            True,
            "Scheduled stage-aware sales follow-up",
            {"follow_up_due_date": updated.get("follow_up_due_date"), "follow_up_reason": reason, "follow_up_draft": draft},
        )

    def _draft_for_status(self, status: str) -> str:
        if status in {"new", "incomplete", "needs_clarification"}:
            return "Hi, thanks again for the inquiry. Could you confirm the missing trip details so we can shape the right options?"
        if status in {"quoted", "proposal"}:
            return "Hi, checking whether you had a chance to review the proposal. I can adjust options or answer any questions."
        return "Hi, following up on your trip plan so we can keep the next step moving."


class FollowUpAgent:
    definition = AgentDefinition(
        name="follow_up_agent",
        description="Marks overdue open trips for follow-up so operators do not miss promised callbacks.",
        trigger_contract="Trip has follow_up_due_date/followUpDueDate at or before now and is not terminal.",
        input_contract="Trip record with id, status/stage, follow_up_due_date, and optional follow_up_status.",
        output_contract="Trip is updated with follow_up_status=due, status=needs_followup, and agent marker metadata.",
        idempotency_contract="One completed action per trip_id + due timestamp.",
        failure_contract="Retry transient update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived"}

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        now = datetime.now(timezone.utc)
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            due_at_raw = get_field(trip, "follow_up_due_date", "followUpDueDate")
            due_at = parse_dt(due_at_raw)
            status = str(get_field(trip, "status", "stage") or "").lower()
            follow_status = str(get_field(trip, "follow_up_status", "followUpStatus") or "").lower()
            if not trip_id or not due_at or due_at > now:
                continue
            if status in self._terminal_statuses or follow_status == "due":
                continue
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="mark_follow_up_due",
                idempotency_key=f"{self.definition.name}:{trip_id}:{due_at.isoformat()}",
                payload={"follow_up_due_date": due_at.isoformat(), "previous_status": status},
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "status": "needs_followup",
                "follow_up_status": "due",
                "last_agent_action": self.definition.name,
                "last_agent_action_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(
            work_item,
            WorkStatus.COMPLETED,
            True,
            "Marked overdue follow-up as due",
            {"status": updated.get("status"), "follow_up_status": updated.get("follow_up_status")},
        )


class QualityEscalationAgent:
    definition = AgentDefinition(
        name="quality_escalation_agent",
        description="Escalates high-risk or blocked trips to human review.",
        trigger_contract="Trip exposes decision_state=ESCALATED/BLOCKED, hard_blockers, or high/critical suitability flags.",
        input_contract="Trip record with id plus decision_state, hard_blockers, decision_output.suitability_flags, or suitability_flags.",
        output_contract="Trip is updated with review_status=escalated and an escalation reason.",
        idempotency_contract="One completed action per trip_id + stable escalation reason.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=2, backoff_seconds=(0, 2)),
    )

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            if not trip_id:
                continue
            if str(get_field(trip, "review_status") or "").lower() == "escalated":
                continue
            reason = self._escalation_reason(trip)
            if reason:
                yield WorkItem(
                    agent_name=self.definition.name,
                    trip_id=trip_id,
                    action="escalate_quality_review",
                    idempotency_key=f"{self.definition.name}:{trip_id}:{reason}",
                    payload={"reason": reason},
                )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "review_status": "escalated",
                "escalation_reason": work_item.payload.get("reason", "quality_risk"),
                "last_agent_action": self.definition.name,
                "last_agent_action_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(
            work_item,
            WorkStatus.COMPLETED,
            True,
            "Escalated trip for human quality review",
            {"review_status": updated.get("review_status"), "escalation_reason": updated.get("escalation_reason")},
        )

    def _escalation_reason(self, trip: Any) -> Optional[str]:
        decision_state = str(get_field(trip, "decision_state", "decisionState") or "").upper()
        if decision_state in {"ESCALATED", "BLOCKED", "REJECTED"}:
            return f"decision_state:{decision_state.lower()}"

        hard_blockers = get_field(trip, "hard_blockers", "hardBlockers")
        if isinstance(hard_blockers, list) and hard_blockers:
            return "hard_blockers_present"

        flags = get_field(trip, "suitability_flags", "suitabilityFlags")
        if not flags and isinstance(trip, dict):
            decision_output = trip.get("decision")
            if isinstance(decision_output, dict):
                flags = decision_output.get("suitability_flags")
        if isinstance(flags, list):
            for flag in flags:
                if not isinstance(flag, dict):
                    continue
                severity = str(flag.get("severity") or flag.get("tier") or "").lower()
                confidence = flag.get("confidence")
                if severity in {"high", "critical"}:
                    return f"suitability_flag:{severity}"
                if isinstance(confidence, (int, float)) and confidence >= 0.85:
                    return "suitability_flag:high_confidence"
        return None


class DocumentReadinessAgent:
    definition = AgentDefinition(
        name="document_readiness_agent",
        description="Creates passport, visa, insurance, and transit readiness checklists before proposal or booking handoff.",
        trigger_contract="Trip has destination/route or is at proposal/booking stage and no current document_readiness_checklist.",
        input_contract="Trip record with id, stage/status, extracted facts, destination, route/transit, traveler nationalities, passport/document metadata.",
        output_contract="Trip is updated with document_readiness_checklist, document_risk_level, must_confirm, and tool evidence metadata.",
        idempotency_contract="One checklist per trip_id plus destination/route/stage marker until trip facts change.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}
    _india_passport_terms = {"india", "indian", "in", "ind"}
    _visa_required_for_indian = {
        "united states",
        "usa",
        "us",
        "canada",
        "schengen",
        "united kingdom",
        "uk",
        "australia",
        "new zealand",
    }
    _eta_like_for_indian = {"singapore", "thailand", "uae", "dubai", "qatar", "doha"}

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            if not trip_id or status in self._terminal_statuses:
                continue
            current = get_field(trip, "document_readiness_checklist")
            if isinstance(current, dict) and current.get("checked_at"):
                continue
            context = self._extract_context(trip)
            if not context["destinations"] and context["stage"] not in {"proposal", "booking"}:
                continue
            marker = "|".join(
                [
                    context["stage"] or "unknown",
                    ",".join(context["destinations"]) or "no_destination",
                    ",".join(context["transits"]) or "no_transit",
                    ",".join(context["nationalities"]) or "no_nationality",
                ]
            )
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="build_document_readiness_checklist",
                idempotency_key=f"{self.definition.name}:{trip_id}:{marker}",
                payload=context,
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        context = dict(work_item.payload)
        checklist = self._build_checklist(context)
        evidence = ToolResult.from_static(
            tool_name="document_rules_static_seed",
            query={
                "destinations": context.get("destinations", []),
                "transits": context.get("transits", []),
                "nationalities": context.get("nationalities", []),
            },
            data={
                "rule_set": "static_document_readiness_v1",
                "legal_finality": False,
                "requires_authoritative_verification": True,
            },
            source="in_repo_static_rules",
            raw_reference="Docs/context/TRIP_VISA_DOCUMENT_RISK_SCENARIO_2026-04-15.md",
            freshness=ToolFreshnessPolicy(max_age_seconds=86_400),
            confidence=0.65,
        )
        output = {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "source": self.definition.name,
            "risk_level": checklist["risk_level"],
            "items": checklist["items"],
            "must_confirm": checklist["must_confirm"],
            "critical_changes": checklist["critical_changes"],
            "tool_evidence": [evidence.to_dict()],
            "disclaimer": "Internal readiness support only. Verify visa, passport, health, and transit rules with authoritative sources before quote or booking.",
        }
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "document_readiness_checklist": output,
                "document_risk_level": output["risk_level"],
                "must_confirm_documents": output["must_confirm"],
                "last_agent_action": self.definition.name,
                "last_agent_action_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Built document readiness checklist", output)

    def _extract_context(self, trip: Any) -> dict[str, Any]:
        facts = get_nested(trip, "extracted.facts", {}) or {}
        destination_values = first_non_empty(
            _slot_value(facts.get("destination_candidates")),
            _slot_value(facts.get("destination")),
            get_field(trip, "destination", "destinations"),
        )
        destinations = self._normalize_list(destination_values)
        transits = self._normalize_list(first_non_empty(get_field(trip, "transit_points", "transits"), _slot_value(facts.get("transit_points"))))
        nationalities = self._normalize_list(
            first_non_empty(
                get_field(trip, "traveler_nationalities", "nationalities", "passport_country"),
                _slot_value(facts.get("nationality")),
                _slot_value(facts.get("passport_country")),
            )
        )
        if not nationalities:
            raw_text = first_non_empty(get_nested(trip, "raw_input.raw_note"), get_field(trip, "raw_note"), "")
            if "indian passport" in str(raw_text).lower() or "indian passports" in str(raw_text).lower():
                nationalities = ["indian"]
        return {
            "stage": str(first_non_empty(get_field(trip, "stage"), get_field(trip, "status"), "")).lower(),
            "destinations": destinations,
            "transits": transits,
            "nationalities": nationalities,
            "travelers": get_field(trip, "travelers") or get_nested(trip, "booking_data.travelers", []) or [],
            "date_window": first_non_empty(_slot_value(facts.get("date_window")), get_field(trip, "date_window", "dateWindow")),
            "raw_note": first_non_empty(get_nested(trip, "raw_input.raw_note"), get_field(trip, "raw_note"), ""),
        }

    def _normalize_list(self, value: Any) -> list[str]:
        values: list[str] = []
        for item in _flatten_values(value):
            if isinstance(item, dict) and "value" in item:
                nested = item.get("value")
                values.extend(self._normalize_list(nested))
                continue
            text = _stringify(item).strip()
            if text:
                for part in text.replace(" + ", ",").replace(" and ", ",").split(","):
                    normalized = part.strip().lower()
                    if normalized and normalized not in values:
                        values.append(normalized)
        return values

    def _build_checklist(self, context: dict[str, Any]) -> dict[str, Any]:
        destinations = context.get("destinations", [])
        transits = context.get("transits", [])
        nationalities = context.get("nationalities", [])
        travelers = context.get("travelers", [])
        indian_passport = any(n in self._india_passport_terms or "indian" in n for n in nationalities)

        items: list[dict[str, Any]] = []
        must_confirm: list[str] = []
        critical_changes: list[str] = []

        if not nationalities:
            items.append(self._item("nationality", "missing", "Traveler nationality/passport country is required for document checks."))
            must_confirm.append("passport country for every traveler")
        if not destinations:
            items.append(self._item("destination", "missing", "Destination is required for visa and entry checks."))
            must_confirm.append("final destination country/countries")

        for destination in destinations:
            if indian_passport and self._matches(destination, self._visa_required_for_indian):
                items.append(self._item("visa", "critical", f"Indian passport holders likely need pre-travel authorization/visa confirmation for {destination}."))
                must_confirm.append(f"current visa/entry requirement for Indian passport holders entering {destination}")
                critical_changes.append(f"Verify visa category and processing timeline for {destination} before quote is firm")
            elif indian_passport and self._matches(destination, self._eta_like_for_indian):
                items.append(self._item("visa", "review", f"Confirm current e-visa/ETA/visa-on-arrival rules for {destination}."))
                must_confirm.append(f"current e-visa/ETA/arrival rules for {destination}")
            else:
                items.append(self._item("visa", "review", f"Verify entry authorization rules for {destination} based on each passport."))
                must_confirm.append(f"entry authorization for {destination}")

        for transit in transits:
            items.append(self._item("transit", "review", f"Confirm airside/landside transit visa and baggage recheck requirements for {transit}."))
            must_confirm.append(f"transit permission and baggage recheck rules for {transit}")

        if not travelers:
            items.append(self._item("passport_validity", "missing", "Passport expiry dates are not captured for all travelers."))
            must_confirm.append("passport expiry date for every traveler")
        else:
            for index, traveler in enumerate(travelers, start=1):
                expiry = parse_dt(first_non_empty(get_field(traveler, "passport_expiry", "passportExpiry"), get_field(traveler, "passport_expiry_date")))
                if not expiry:
                    items.append(self._item("passport_validity", "missing", f"Passport expiry missing for traveler {index}."))
                    must_confirm.append(f"passport expiry for traveler {index}")
                elif context.get("date_window") and expiry <= datetime.now(timezone.utc) + timedelta(days=180):
                    items.append(self._item("passport_validity", "critical", f"Passport for traveler {index} may be inside a 6-month validity risk window."))
                    critical_changes.append(f"Renew or verify passport validity for traveler {index}")

        raw_note = str(context.get("raw_note") or "").lower()
        senior_or_medical = "senior" in raw_note or any(
            str(get_field(t, "traveler_type", "type", "age_group") or "").lower() in {"senior", "elderly"}
            for t in _flatten_values(travelers)
        )
        if senior_or_medical:
            items.append(self._item("insurance", "review", "Senior traveler detected; confirm medical coverage, pre-existing condition terms, and emergency limits."))
            must_confirm.append("travel insurance with senior/pre-existing condition coverage")
        else:
            items.append(self._item("insurance", "review", "Confirm travel insurance requirements and recommended coverage before booking."))
            must_confirm.append("travel insurance requirement and coverage level")

        risk_order = {"missing": 3, "critical": 3, "review": 2, "ok": 1}
        max_score = max((risk_order.get(item["status"], 1) for item in items), default=1)
        risk_level = "high" if max_score >= 3 else "medium" if max_score == 2 else "low"
        return {
            "risk_level": risk_level,
            "items": items,
            "must_confirm": sorted(set(must_confirm)),
            "critical_changes": sorted(set(critical_changes)),
        }

    def _item(self, category: str, status: str, message: str) -> dict[str, Any]:
        return {"category": category, "status": status, "message": message}

    def _matches(self, value: str, candidates: set[str]) -> bool:
        normalized = value.lower()
        return any(candidate in normalized or normalized in candidate for candidate in candidates)


class DestinationIntelligenceAgent:
    definition = AgentDefinition(
        name="destination_intelligence_agent",
        description="Attaches destination weather/risk intelligence with freshness-aware evidence before proposal or travel.",
        trigger_contract="Trip has destination context, is not terminal, and has no current destination_intelligence_snapshot.",
        input_contract="Trip record with id, stage/status, destination/extracted facts, date window, and optional route metadata.",
        output_contract="Trip is updated with destination_intelligence_snapshot, destination_risk_level, recommendations, and tool evidence.",
        idempotency_contract="One snapshot per trip_id plus destination/stage/date marker until trip facts change.",
        failure_contract="Tool failures are fail-closed into unknown-risk snapshots; update failures retry and poison after retry budget.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}

    def __init__(
        self,
        weather_tool: Optional[WeatherTool] = None,
        now_provider: Callable[[], datetime] | None = None,
    ):
        self.weather_tool = weather_tool or build_weather_tool_from_env()
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            if not trip_id or status in self._terminal_statuses:
                continue
            current = get_field(trip, "destination_intelligence_snapshot")
            if isinstance(current, dict) and current.get("checked_at"):
                continue
            context = self._extract_context(trip)
            if not context["destinations"]:
                continue
            marker = "|".join(
                [
                    context["stage"] or "unknown",
                    ",".join(context["destinations"]),
                    str(context.get("date_window") or "no_date_window"),
                ]
            )
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="attach_destination_intelligence",
                idempotency_key=f"{self.definition.name}:{trip_id}:{marker}",
                payload=context,
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        context = dict(work_item.payload)
        checked_at = self.now_provider()
        destination_outputs: list[dict[str, Any]] = []
        recommendations: list[str] = []
        risk_scores: list[int] = []

        for destination in context.get("destinations", []):
            tool_result = self._call_weather(destination)
            if not tool_result.is_fresh(now=checked_at):
                destination_outputs.append(
                    {
                        "destination": destination,
                        "status": "stale",
                        "risk_level": "unknown",
                        "summary": "Destination intelligence is stale and must be refreshed before use.",
                        "tool_evidence": [tool_result.to_dict(now=checked_at)],
                    }
                )
                recommendations.append(f"Refresh destination intelligence for {destination} before proposal, booking, or customer messaging.")
                continue

            assessment = self._assess_weather(destination, tool_result)
            destination_outputs.append(
                {
                    "destination": destination,
                    "status": "fresh",
                    "risk_level": assessment["risk_level"],
                    "summary": assessment["summary"],
                    "signals": assessment["signals"],
                    "tool_evidence": [tool_result.to_dict(now=checked_at)],
                }
            )
            recommendations.extend(assessment["recommendations"])
            risk_scores.append(assessment["risk_score"])

        risk_level = self._overall_risk(risk_scores, destination_outputs)
        output = {
            "checked_at": checked_at.isoformat(),
            "source": self.definition.name,
            "risk_level": risk_level,
            "destinations": destination_outputs,
            "recommendations": sorted(set(recommendations)),
            "authority": "Internal intelligence only. Recommend pivots/escalations; do not auto-send, book, ticket, or change suppliers.",
        }
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "destination_intelligence_snapshot": output,
                "destination_risk_level": risk_level,
                "destination_intelligence_recommendations": output["recommendations"],
                "last_agent_action": self.definition.name,
                "last_agent_action_at": checked_at.isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Attached destination intelligence snapshot", output)

    def _extract_context(self, trip: Any) -> dict[str, Any]:
        facts = get_nested(trip, "extracted.facts", {}) or {}
        destination_values = first_non_empty(
            _slot_value(facts.get("destination_candidates")),
            _slot_value(facts.get("destination")),
            get_field(trip, "destination", "destinations"),
        )
        destinations = self._normalize_list(destination_values)
        return {
            "stage": str(first_non_empty(get_field(trip, "stage"), get_field(trip, "status"), "")).lower(),
            "destinations": destinations,
            "date_window": first_non_empty(_slot_value(facts.get("date_window")), get_field(trip, "date_window", "dateWindow")),
        }

    def _normalize_list(self, value: Any) -> list[str]:
        values: list[str] = []
        for item in _flatten_values(value):
            if isinstance(item, dict) and "value" in item:
                values.extend(self._normalize_list(item.get("value")))
                continue
            text = _stringify(item).strip()
            if text:
                for part in text.replace(" + ", ",").replace(" and ", ",").split(","):
                    normalized = part.strip().lower()
                    if normalized and normalized not in values:
                        values.append(normalized)
        return values

    def _call_weather(self, destination: str) -> ToolResult:
        try:
            return self.weather_tool.current_conditions(destination)
        except Exception as exc:
            logger.exception("DestinationIntelligenceAgent: weather tool failed for %s", destination)
            return ToolResult.from_static(
                tool_name="weather_tool_error",
                query={"destination": destination},
                data={"status": "error", "message": str(exc)[:240]},
                source="destination_intelligence_agent",
                freshness=ToolFreshnessPolicy(max_age_seconds=300),
                confidence=0.1,
            )

    def _assess_weather(self, destination: str, tool_result: ToolResult) -> dict[str, Any]:
        current = tool_result.data.get("current", {})
        daily = tool_result.data.get("daily", {})
        temperature = _as_float(current.get("temperature_c")) if isinstance(current, dict) else None
        wind = _as_float(current.get("wind_speed_kmh")) if isinstance(current, dict) else None
        precipitation_probability = _as_float(daily.get("precipitation_probability_max")) if isinstance(daily, dict) else None
        uv_index = _as_float(daily.get("uv_index_max")) if isinstance(daily, dict) else None
        status = str(tool_result.data.get("status") or "")

        signals: list[dict[str, Any]] = []
        recommendations: list[str] = []
        risk_score = 1

        if status == "not_found" or status == "error":
            signals.append({"category": "coverage", "severity": "unknown", "message": "Weather tool did not return usable destination data."})
            recommendations.append(f"Manually verify current destination conditions for {destination}.")
            return {
                "risk_level": "unknown",
                "risk_score": 0,
                "signals": signals,
                "recommendations": recommendations,
                "summary": "No usable live destination data was available.",
            }

        if precipitation_probability is not None and precipitation_probability >= 70:
            signals.append({"category": "weather", "severity": "medium", "message": f"Rain probability is {precipitation_probability:g}%."})
            recommendations.append(f"Prepare rain/indoor alternatives for {destination}.")
            risk_score = max(risk_score, 2)
        if wind is not None and wind >= 50:
            signals.append({"category": "weather", "severity": "high", "message": f"Wind speed is {wind:g} km/h."})
            recommendations.append(f"Review outdoor transfers, ferries, and exposed activities for {destination}.")
            risk_score = max(risk_score, 3)
        if temperature is not None and (temperature >= 38 or temperature <= -10):
            signals.append({"category": "weather", "severity": "high", "message": f"Temperature is {temperature:g} C."})
            recommendations.append(f"Review heat/cold exposure, pacing, hydration, and vulnerable-traveler needs for {destination}.")
            risk_score = max(risk_score, 3)
        if uv_index is not None and uv_index >= 8:
            signals.append({"category": "weather", "severity": "medium", "message": f"UV index max is {uv_index:g}."})
            recommendations.append(f"Add sun-protection guidance and shaded pacing for {destination}.")
            risk_score = max(risk_score, 2)
        if not signals:
            signals.append({"category": "weather", "severity": "low", "message": "No material weather pivot signal detected."})
            recommendations.append(f"Keep standard destination monitoring cadence for {destination}.")

        risk_level = "high" if risk_score >= 3 else "medium" if risk_score == 2 else "low"
        return {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "signals": signals,
            "recommendations": recommendations,
            "summary": f"Fresh destination weather intelligence assessed as {risk_level} risk.",
        }

    def _overall_risk(self, risk_scores: list[int], destination_outputs: list[dict[str, Any]]) -> str:
        if any(output.get("risk_level") == "unknown" for output in destination_outputs) and not risk_scores:
            return "unknown"
        max_score = max(risk_scores, default=0)
        if max_score >= 3:
            return "high"
        if max_score == 2:
            return "medium"
        if max_score == 1:
            return "low"
        return "unknown"


class WeatherPivotAgent:
    definition = AgentDefinition(
        name="weather_pivot_agent",
        description="Converts fresh destination weather intelligence into internal activity, transfer, and operator pivot packets.",
        trigger_contract="Trip has destination_intelligence_snapshot and no current weather_pivot_packet for that snapshot.",
        input_contract="Trip record with id, stage/status, destination_intelligence_snapshot, itinerary/activity/transfer metadata.",
        output_contract="Trip is updated with weather_pivot_packet, weather_pivot_risk_level, and operator next action.",
        idempotency_contract="One pivot packet per trip_id plus destination_intelligence_snapshot checked_at marker until intelligence changes.",
        failure_contract="Stale evidence produces unknown-risk refresh packet; update failures retry and poison after retry budget.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}
    _outdoor_terms = {"outdoor", "walk", "walking", "garden", "beach", "hike", "park", "tour", "cruise", "ferry", "boat"}
    _transfer_terms = {"transfer", "airport", "drive", "driver", "car", "ferry", "boat", "rail", "train"}

    def __init__(self, now_provider: Callable[[], datetime] | None = None):
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            if not trip_id or status in self._terminal_statuses:
                continue
            snapshot = get_field(trip, "destination_intelligence_snapshot")
            if not isinstance(snapshot, dict) or not snapshot.get("checked_at"):
                continue
            existing = get_field(trip, "weather_pivot_packet")
            if isinstance(existing, dict) and existing.get("source_snapshot_checked_at") == snapshot.get("checked_at"):
                continue
            context = {
                "snapshot": snapshot,
                "activities": self._extract_activities(trip),
                "stage": str(first_non_empty(get_field(trip, "stage"), get_field(trip, "status"), "")).lower(),
            }
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="build_weather_pivot_packet",
                idempotency_key=f"{self.definition.name}:{trip_id}:{snapshot.get('checked_at')}",
                payload=context,
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        checked_at = self.now_provider()
        snapshot = work_item.payload.get("snapshot") if isinstance(work_item.payload, dict) else {}
        if not isinstance(snapshot, dict):
            snapshot = {}
        activities = work_item.payload.get("activities", []) if isinstance(work_item.payload, dict) else []
        if not self._has_fresh_evidence(snapshot):
            packet = {
                "created_at": checked_at.isoformat(),
                "source": self.definition.name,
                "source_snapshot_checked_at": snapshot.get("checked_at"),
                "risk_level": "unknown",
                "summary": "Destination weather evidence is stale or missing; refresh destination intelligence before pivot decisions.",
                "affected_activities": [],
                "transport_risks": [],
                "pivot_options": [],
                "operator_next_action": "refresh_destination_intelligence",
                "authority": "Internal pivot support only. Do not auto-send, book, ticket, or change suppliers.",
            }
        else:
            packet = self._build_packet(snapshot, activities, checked_at)

        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "weather_pivot_packet": packet,
                "weather_pivot_risk_level": packet["risk_level"],
                "operator_next_action": packet["operator_next_action"],
                "last_agent_action": self.definition.name,
                "last_agent_action_at": checked_at.isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Built weather pivot packet", packet)

    def _extract_activities(self, trip: Any) -> list[dict[str, Any]]:
        raw_items = first_non_empty(
            get_field(trip, "itinerary_items", "activities", "planned_activities"),
            get_nested(trip, "itinerary.items"),
            get_nested(trip, "structured_json.itinerary_items"),
            [],
        )
        activities: list[dict[str, Any]] = []
        for index, item in enumerate(_flatten_values(raw_items), start=1):
            if isinstance(item, dict):
                title = _stringify(first_non_empty(item.get("title"), item.get("name"), item.get("label"), f"Activity {index}"))
                activity_type = _stringify(first_non_empty(item.get("type"), item.get("category"), item.get("mode"), "")).lower()
                raw_location = first_non_empty(item.get("location"), item.get("destination"))
                location = _stringify(raw_location) if raw_location else ""
            else:
                title = _stringify(item)
                activity_type = ""
                location = ""
            if title:
                activities.append({"title": title, "type": activity_type, "location": location})
        return activities

    def _has_fresh_evidence(self, snapshot: dict[str, Any]) -> bool:
        destinations = snapshot.get("destinations")
        if not isinstance(destinations, list) or not destinations:
            return False
        for destination in destinations:
            if not isinstance(destination, dict):
                continue
            evidence_items = destination.get("tool_evidence")
            if not isinstance(evidence_items, list) or not evidence_items:
                return False
            if any(isinstance(evidence, dict) and evidence.get("fresh") is False for evidence in evidence_items):
                return False
            if destination.get("status") == "stale":
                return False
        return True

    def _build_packet(self, snapshot: dict[str, Any], activities: list[dict[str, Any]], checked_at: datetime) -> dict[str, Any]:
        destinations = [d for d in snapshot.get("destinations", []) if isinstance(d, dict)]
        signals = [signal for destination in destinations for signal in destination.get("signals", []) if isinstance(signal, dict)]
        rain_signal = any("rain" in str(signal.get("message", "")).lower() for signal in signals)
        uv_signal = any("uv" in str(signal.get("message", "")).lower() for signal in signals)
        wind_signal = any("wind" in str(signal.get("message", "")).lower() for signal in signals)

        affected_activities: list[dict[str, Any]] = []
        transport_risks: list[dict[str, Any]] = []
        for activity in activities:
            text = f"{activity.get('title', '')} {activity.get('type', '')}".lower()
            if rain_signal and any(term in text for term in self._outdoor_terms):
                affected_activities.append(
                    {
                        **activity,
                        "reason": "rain exposure",
                        "suggested_adjustment": "Prepare indoor/covered alternative or flexible timing.",
                    }
                )
            if uv_signal and any(term in text for term in self._outdoor_terms):
                affected_activities.append(
                    {
                        **activity,
                        "reason": "high UV exposure",
                        "suggested_adjustment": "Shift to shaded/early timing and add sun-protection guidance.",
                    }
                )
            if wind_signal and any(term in text for term in self._transfer_terms):
                transport_risks.append(
                    {
                        **activity,
                        "reason": "wind-sensitive transfer",
                        "suggested_adjustment": "Review ferry/boat/exposed transfer reliability and buffer time.",
                    }
                )
            elif rain_signal and any(term in text for term in self._transfer_terms):
                transport_risks.append(
                    {
                        **activity,
                        "reason": "rain-sensitive transfer",
                        "suggested_adjustment": "Add pickup buffers and covered meeting points.",
                    }
                )

        pivot_options = self._pivot_options(rain_signal=rain_signal, uv_signal=uv_signal, wind_signal=wind_signal)
        risk_level = self._risk_level(snapshot, affected_activities, transport_risks)
        operator_next_action = "review_weather_pivots" if risk_level in {"medium", "high"} else "monitor_weather"
        return {
            "created_at": checked_at.isoformat(),
            "source": self.definition.name,
            "source_snapshot_checked_at": snapshot.get("checked_at"),
            "risk_level": risk_level,
            "summary": f"Weather pivot packet built from fresh destination intelligence with {len(affected_activities)} activity and {len(transport_risks)} transfer considerations.",
            "affected_activities": affected_activities,
            "transport_risks": transport_risks,
            "pivot_options": pivot_options,
            "source_destinations": destinations,
            "operator_next_action": operator_next_action,
            "authority": "Internal pivot support only. Do not auto-send, book, ticket, or change suppliers.",
        }

    def _pivot_options(self, rain_signal: bool, uv_signal: bool, wind_signal: bool) -> list[str]:
        options: list[str] = []
        if rain_signal:
            options.append("Prepare indoor or covered alternatives for exposed activities.")
            options.append("Add rain gear, covered pickup points, and flexible activity timing.")
        if uv_signal:
            options.append("Shift outdoor touring earlier/later and add shaded pacing plus sun-protection guidance.")
        if wind_signal:
            options.append("Review exposed transfers, ferries, viewpoints, and buffer timing.")
        if not options:
            options.append("Continue monitoring; no material pivot recommended from current weather evidence.")
        return options

    def _risk_level(self, snapshot: dict[str, Any], affected_activities: list[dict[str, Any]], transport_risks: list[dict[str, Any]]) -> str:
        source_risk = str(snapshot.get("risk_level") or "").lower()
        if source_risk == "high" or len(transport_risks) >= 2:
            return "high"
        if source_risk == "medium" or affected_activities or transport_risks:
            return "medium"
        if source_risk == "low":
            return "low"
        return "unknown"


class ConstraintFeasibilityAgent:
    definition = AgentDefinition(
        name="constraint_feasibility_agent",
        description="Detects impossible or risky budget/date/document/weather/pace/accessibility combinations before proposal.",
        trigger_contract="Trip has enough destination, stage, or proposal context and no current constraint_feasibility_assessment for the same fact marker.",
        input_contract="Trip record with extracted facts, budget/date/traveler context, document readiness, destination intelligence, and weather pivot metadata.",
        output_contract="Trip is updated with constraint_feasibility_assessment, feasibility_status, hard/soft blockers, missing facts, and operator next action.",
        idempotency_contract="One feasibility assessment per trip_id plus stage/destination/date/budget/traveler marker until facts change.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}
    _eligible_stages = {"", "discovery", "intake", "qualification", "feasibility", "shortlist", "proposal", "quoted", "booking", "ticketed", "pre_departure", "in_progress", "traveling"}
    _active_refresh_stages = {"ticketed", "pre_departure", "in_progress", "traveling"}
    def __init__(self, now_provider: Callable[[], datetime] | None = None, policy: ScenarioPolicy | None = None):
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))
        self.policy = policy or load_scenario_policy()

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            if not trip_id or status in self._terminal_statuses:
                continue
            context = self._extract_context(trip)
            if context["stage"] not in self._eligible_stages:
                continue
            if not context["destinations"] and context["stage"] not in {"feasibility", "shortlist", "proposal", "quoted", "booking"}:
                continue
            existing = get_field(trip, "constraint_feasibility_assessment")
            if (
                isinstance(existing, dict)
                and existing.get("facts_marker") == context["facts_marker"]
                and not self._needs_periodic_refresh(context["stage"], existing)
            ):
                continue
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="assess_constraints",
                idempotency_key=f"{self.definition.name}:{trip_id}:{context['facts_marker']}",
                payload=context,
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        assessed_at = self.now_provider()
        context = dict(work_item.payload)
        assessment = self._assess(context, assessed_at)
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "constraint_feasibility_assessment": assessment,
                "feasibility_status": assessment["status"],
                "feasibility_hard_blockers": assessment["hard_blockers"],
                "feasibility_soft_constraints": assessment["soft_constraints"],
                "feasibility_missing_facts": assessment["missing_facts"],
                "operator_next_action": assessment["operator_next_action"],
                "last_agent_action": self.definition.name,
                "last_agent_action_at": assessed_at.isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Assessed trip feasibility constraints", assessment)

    def _extract_context(self, trip: Any) -> dict[str, Any]:
        facts = get_nested(trip, "extracted.facts", {}) or {}
        destination_values = first_non_empty(
            _slot_value(facts.get("destination_candidates")),
            _slot_value(facts.get("destination")),
            get_field(trip, "destination", "destinations"),
        )
        destinations = self._normalize_list(destination_values)
        date_window = first_non_empty(_slot_value(facts.get("date_window")), get_field(trip, "date_window", "dateWindow"))
        budget_value = first_non_empty(_slot_value(facts.get("budget")), get_field(trip, "budget", "budget_amount", "budgetAmount"))
        travelers_value = first_non_empty(
            _slot_value(facts.get("travelers")),
            _slot_value(facts.get("traveler_count")),
            get_field(trip, "traveler_count", "travelerCount"),
            get_field(trip, "travelers"),
        )
        traveler_count = self._traveler_count(travelers_value)
        stage = str(first_non_empty(get_field(trip, "stage"), get_field(trip, "status"), "")).lower()
        raw_note = str(first_non_empty(get_nested(trip, "raw_input.raw_note"), get_field(trip, "raw_note"), "") or "")
        party_composition = self._extract_party_composition(facts)
        route_summary = self._extract_route_summary(trip)
        activity_titles = self._extract_activity_titles(trip)
        facts_marker = "|".join(
            [
                stage or "unknown",
                ",".join(destinations) or "no_destination",
                str(date_window or "no_date_window").lower(),
                str(budget_value or "no_budget").lower(),
                str(traveler_count or "no_travelers"),
                str(route_summary.get("flight_legs") or 0),
                str(route_summary.get("transfer_like_items") or 0),
                str(route_summary.get("tight_connections") or 0),
                str(route_summary.get("activity_count") or 0),
                str(party_composition.get("elderly") or 0),
                str(party_composition.get("toddlers") or 0),
            ]
        )
        return {
            "stage": stage,
            "destinations": destinations,
            "date_window": date_window,
            "budget_amount": _extract_money_amount(budget_value),
            "traveler_count": traveler_count,
            "raw_note": raw_note,
            "travelers": get_field(trip, "travelers") or [],
            "party_composition": party_composition,
            "route_summary": route_summary,
            "activity_titles": activity_titles,
            "document_readiness": get_field(trip, "document_readiness_checklist") or {},
            "destination_intelligence": get_field(trip, "destination_intelligence_snapshot") or {},
            "weather_pivot": get_field(trip, "weather_pivot_packet") or {},
            "safety_alert": get_field(trip, "safety_alert_packet") or {},
            "flight_status": get_field(trip, "flight_status_snapshot") or {},
            "facts_marker": facts_marker,
        }

    def _needs_periodic_refresh(self, stage: str, existing_assessment: dict[str, Any]) -> bool:
        if stage not in self._active_refresh_stages:
            return False
        assessed_at = parse_dt(existing_assessment.get("assessed_at"))
        if assessed_at is None:
            return True
        age = self.now_provider() - assessed_at
        stage_hours = self.policy.feasibility_refresh_hours_active
        if stage == "pre_departure":
            stage_hours = self.policy.feasibility_refresh_hours_pre_departure
        elif stage in {"in_progress", "traveling"}:
            stage_hours = self.policy.feasibility_refresh_hours_in_progress
        return age >= timedelta(hours=max(1, stage_hours))

    def _extract_party_composition(self, facts: dict[str, Any]) -> dict[str, int]:
        slot = facts.get("party_composition")
        raw = _slot_value(slot) if slot is not None else None
        if not isinstance(raw, dict):
            return {}
        output: dict[str, int] = {}
        for key in ("adults", "children", "toddlers", "elderly"):
            value = raw.get(key)
            if isinstance(value, (int, float)) and value > 0:
                output[key] = int(value)
        return output

    def _extract_route_summary(self, trip: Any) -> dict[str, int]:
        raw_flights = first_non_empty(
            get_field(trip, "flights", "flight_segments"),
            get_nested(trip, "booking_data.flights"),
            get_nested(trip, "itinerary.flights"),
            [],
        )
        flight_legs = sum(1 for item in _flatten_values(raw_flights) if isinstance(item, dict) or _stringify(item))

        raw_items = first_non_empty(
            get_field(trip, "itinerary_items", "activities", "planned_activities"),
            get_nested(trip, "itinerary.items"),
            get_nested(trip, "structured_json.itinerary_items"),
            [],
        )
        transfer_like_items = 0
        activity_count = 0
        for item in _flatten_values(raw_items):
            text = ""
            if isinstance(item, dict):
                activity_count += 1
                text = " ".join(
                    [
                        _stringify(item.get("title")),
                        _stringify(item.get("name")),
                        _stringify(item.get("label")),
                        _stringify(item.get("type")),
                        _stringify(item.get("category")),
                    ]
                ).lower()
            else:
                text = _stringify(item).lower()
                if text:
                    activity_count += 1
            if text and any(term in text for term in self.policy.transfer_terms):
                transfer_like_items += 1

        tight_connections = self._tight_connection_count(raw_flights)
        if flight_legs == 0 and transfer_like_items == 0 and activity_count == 0:
            note_text = _stringify(first_non_empty(get_nested(trip, "raw_input.raw_note"), get_field(trip, "raw_note"), ""))
            inferred = parse_itinerary_text(note_text)
            flight_legs = int(inferred.get("inferred_flight_legs") or 0)
            transfer_like_items = int(inferred.get("inferred_transfer_like_items") or 0)
            activity_count = int(inferred.get("inferred_activity_count") or 0)

        route_hubs = self._extract_route_hubs(raw_flights)
        return {
            "flight_legs": flight_legs,
            "transfer_like_items": transfer_like_items,
            "activity_count": activity_count,
            "tight_connections": tight_connections,
            "route_hubs": route_hubs,
        }

    def _extract_route_hubs(self, raw_flights: Any) -> list[str]:
        hubs: list[str] = []
        for item in _flatten_values(raw_flights):
            if not isinstance(item, dict):
                continue
            for key in ("arrival_airport", "departure_airport", "origin", "destination", "from", "to"):
                value = str(item.get(key) or "").upper().strip()
                if len(value) == 3 and value.isalpha() and value not in hubs:
                    hubs.append(value)
        return hubs

    def _tight_connection_count(self, raw_flights: Any) -> int:
        flights: list[dict[str, Any]] = [item for item in _flatten_values(raw_flights) if isinstance(item, dict)]
        if len(flights) < 2:
            return 0
        count = 0
        for idx in range(len(flights) - 1):
            current = flights[idx]
            nxt = flights[idx + 1]
            explicit_minutes = first_non_empty(
                nxt.get("connection_minutes"),
                nxt.get("layover_minutes"),
                current.get("connection_minutes"),
                current.get("layover_minutes"),
            )
            explicit = _as_float(explicit_minutes)
            if explicit is not None:
                threshold = float(self.policy.tight_connection_minutes_threshold)
                if self._connection_uses_stress_hub(current, nxt):
                    threshold += 20.0
                if explicit < threshold:
                    count += 1
                continue
            arr = parse_dt(first_non_empty(current.get("arrival_time"), current.get("arrival_at"), current.get("arrive_at")))
            dep = parse_dt(first_non_empty(nxt.get("departure_time"), nxt.get("departure_at"), nxt.get("depart_at")))
            if arr and dep:
                delta_minutes = (dep - arr).total_seconds() / 60.0
                threshold = float(self.policy.tight_connection_minutes_threshold)
                if self._connection_uses_stress_hub(current, nxt):
                    threshold += 20.0
                if 0 <= delta_minutes < threshold:
                    count += 1
        return count

    def _connection_uses_stress_hub(self, current: dict[str, Any], nxt: dict[str, Any]) -> bool:
        current_arrival = str(
            first_non_empty(
                current.get("arrival_airport"),
                current.get("destination"),
                current.get("to"),
            )
            or ""
        ).upper()
        next_departure = str(
            first_non_empty(
                nxt.get("departure_airport"),
                nxt.get("origin"),
                nxt.get("from"),
            )
            or ""
        ).upper()
        hubs = self.policy.stress_hub_airports
        return (current_arrival in hubs) or (next_departure in hubs)

    def _extract_activity_titles(self, trip: Any) -> list[str]:
        raw_items = first_non_empty(
            get_field(trip, "itinerary_items", "activities", "planned_activities"),
            get_nested(trip, "itinerary.items"),
            get_nested(trip, "structured_json.itinerary_items"),
            [],
        )
        titles: list[str] = []
        for item in _flatten_values(raw_items):
            if isinstance(item, dict):
                text = _stringify(first_non_empty(item.get("title"), item.get("name"), item.get("label"), item.get("type"), item.get("category")))
            else:
                text = _stringify(item)
            if text:
                titles.append(text)
        return titles

    def _normalize_list(self, value: Any) -> list[str]:
        values: list[str] = []
        for item in _flatten_values(value):
            if isinstance(item, dict) and "value" in item:
                values.extend(self._normalize_list(item.get("value")))
                continue
            text = _stringify(item).strip()
            if text:
                for part in text.replace(" + ", ",").replace(" and ", ",").split(","):
                    normalized = part.strip().lower()
                    if normalized and normalized not in values:
                        values.append(normalized)
        return values

    def _traveler_count(self, value: Any) -> Optional[int]:
        if isinstance(value, int):
            return value
        if isinstance(value, list):
            return len(value)
        if isinstance(value, dict):
            nested = first_non_empty(value.get("value"), value.get("count"), value.get("total"))
            return self._traveler_count(nested)
        if isinstance(value, str):
            match = re.search(r"\d+", value)
            if match:
                return int(match.group(0))
        return None

    def _assess(self, context: dict[str, Any], assessed_at: datetime) -> dict[str, Any]:
        hard_blockers: list[dict[str, Any]] = []
        soft_constraints: list[dict[str, Any]] = []
        missing_facts: list[str] = []

        destinations = context.get("destinations", [])
        budget = context.get("budget_amount")
        traveler_count = context.get("traveler_count") or 1
        raw_note = str(context.get("raw_note") or "").lower()
        date_window = context.get("date_window")
        travel_dates = _extract_date_range(date_window)
        month = travel_dates[0].month if travel_dates else None

        if not destinations:
            missing_facts.append("destination")
        if not date_window:
            missing_facts.append("date_window")
        if not budget:
            missing_facts.append("budget")
        if not context.get("traveler_count"):
            missing_facts.append("traveler_count")

        if budget is not None and traveler_count:
            per_person_budget = budget / max(traveler_count, 1)
            if per_person_budget < 350:
                hard_blockers.append(
                    self._constraint(
                        "budget",
                        "hard",
                        f"Budget appears below basic feasibility at approximately {per_person_budget:.0f} per traveler.",
                        "Clarify budget scope, currency, inclusions, and whether flights are included.",
                    )
                )
            elif per_person_budget < 750:
                soft_constraints.append(
                    self._constraint(
                        "budget",
                        "soft",
                        f"Budget is tight at approximately {per_person_budget:.0f} per traveler.",
                        "Limit destinations, simplify hotel/transfer assumptions, and present tradeoffs.",
                    )
                )

        if travel_dates:
            days_until_departure = (travel_dates[0].date() - assessed_at.date()).days
            trip_days = max((travel_dates[1].date() - travel_dates[0].date()).days + 1, 1)
            if days_until_departure < 7:
                hard_blockers.append(
                    self._constraint(
                        "date_window",
                        "hard",
                        "Departure is inside a 7-day rush window.",
                        "Require human feasibility review for document, inventory, payment, and operational lead times.",
                    )
                )
            elif days_until_departure < 21:
                soft_constraints.append(
                    self._constraint(
                        "date_window",
                        "soft",
                        "Departure is inside a 21-day compressed planning window.",
                        "Use fast-confirming suppliers and avoid visa-sensitive proposals unless verified.",
                    )
                )
            if len(destinations) > 1 and trip_days < len(destinations) * 3:
                soft_constraints.append(
                    self._constraint(
                        "pace",
                        "soft",
                        "Trip duration is short for the number of destinations.",
                        "Reduce destination count or add nights before proposal.",
                    )
                )
            if len(destinations) >= 3 and trip_days <= len(destinations):
                hard_blockers.append(
                    self._constraint(
                        "routing",
                        "hard",
                        "Multi-country hop density is too high for available trip days.",
                        "Reduce destination count or add nights to avoid same-day cross-country fatigue.",
                        {"destinations": destinations, "trip_days": trip_days},
                    )
                )

        document_readiness = context.get("document_readiness") if isinstance(context.get("document_readiness"), dict) else {}
        doc_risk = str(document_readiness.get("risk_level") or "").lower()
        must_confirm = document_readiness.get("must_confirm")
        if doc_risk == "high":
            hard_blockers.append(
                self._constraint(
                    "document_readiness",
                    "hard",
                    "High document readiness risk exists.",
                    "Confirm passport, visa, transit, and insurance requirements before firm proposal or booking.",
                    {"must_confirm": must_confirm if isinstance(must_confirm, list) else []},
                )
            )
        elif doc_risk == "medium":
            soft_constraints.append(
                self._constraint(
                    "document_readiness",
                    "soft",
                    "Document readiness needs review.",
                    "Resolve document checklist before booking handoff.",
                )
            )

        weather_pivot = context.get("weather_pivot") if isinstance(context.get("weather_pivot"), dict) else {}
        weather_risk = str(weather_pivot.get("risk_level") or "").lower()
        if weather_risk == "high":
            hard_blockers.append(
                self._constraint("weather", "hard", "Weather pivot risk is high.", "Review pivot packet before proposal or travel plan confirmation.")
            )
        elif weather_risk == "medium":
            soft_constraints.append(
                self._constraint("weather", "soft", "Weather pivot risk needs operator review.", "Include weather alternatives and buffers in proposal.")
            )

        safety_alert = context.get("safety_alert") if isinstance(context.get("safety_alert"), dict) else {}
        safety_risk = str(safety_alert.get("risk_level") or "").lower()
        if safety_risk in {"high", "unknown"}:
            hard_blockers.append(
                self._constraint(
                    "safety",
                    "hard",
                    f"Regional safety advisory risk is {safety_risk}.",
                    "Require human safety review, alternate routing, and traveler briefing before confirmation.",
                )
            )
        elif safety_risk == "medium":
            soft_constraints.append(
                self._constraint(
                    "safety",
                    "soft",
                    "Regional safety advisory needs review.",
                    "Include safety assumptions, contingency support, and route alternatives.",
                )
            )

        flight_status = context.get("flight_status") if isinstance(context.get("flight_status"), dict) else {}
        flight_risk = str(flight_status.get("risk_level") or "").lower()
        if flight_risk in {"high", "unknown"}:
            hard_blockers.append(
                self._constraint(
                    "flight_disruption",
                    "hard",
                    f"Flight disruption risk is {flight_risk}.",
                    "Revalidate operational timing and alternatives before traveler commitment.",
                )
            )
        elif flight_risk == "medium":
            soft_constraints.append(
                self._constraint(
                    "flight_disruption",
                    "soft",
                    "Flight disruption risk needs operator review.",
                    "Add buffer plans and disruption contingencies.",
                )
            )

        if any(term in raw_note for term in {"wheelchair", "accessible", "mobility", "step-free"}):
            soft_constraints.append(
                self._constraint(
                    "accessibility",
                    "soft",
                    "Accessibility need detected.",
                    "Confirm step-free hotels, transport, attraction access, and realistic pacing.",
                )
            )
        if "senior" in raw_note or any(str(get_field(t, "traveler_type", "type", "age_group") or "").lower() == "senior" for t in _flatten_values(context.get("travelers"))):
            soft_constraints.append(
                self._constraint(
                    "traveler_pace",
                    "soft",
                    "Senior traveler context detected.",
                    "Review daily pacing, medical coverage, transfer comfort, and rest windows.",
                )
            )
        if "fast-paced" in raw_note or "packed" in raw_note:
            soft_constraints.append(
                self._constraint("pace", "soft", "Fast-paced trip requested.", "Validate pace against traveler profile before proposal.")
            )

        composition = context.get("party_composition") if isinstance(context.get("party_composition"), dict) else {}
        profile = self._infer_party_profile(composition, context.get("travelers"), raw_note)
        elderly_count = int(profile.get("elderly_count") or 0)
        toddler_count = int(composition.get("toddlers") or 0)
        parent_ambiguous = bool(profile.get("parent_ambiguous"))
        older_adult_present = bool(profile.get("older_adult_present"))
        infant_present = bool(profile.get("infant_present"))
        mobility_constrained_present = bool(profile.get("mobility_constrained_present"))
        route_summary = context.get("route_summary") if isinstance(context.get("route_summary"), dict) else {}
        flight_legs = int(route_summary.get("flight_legs") or 0)
        transfer_like_items = int(route_summary.get("transfer_like_items") or 0)
        activity_count = int(route_summary.get("activity_count") or 0)
        tight_connections = int(route_summary.get("tight_connections") or 0)
        route_hubs = route_summary.get("route_hubs") if isinstance(route_summary.get("route_hubs"), list) else []
        activity_titles = context.get("activity_titles") if isinstance(context.get("activity_titles"), list) else []
        activity_text = " ".join(_stringify(value).lower() for value in activity_titles)
        route_analysis = analyze_route_complexity(
            flight_legs=flight_legs,
            transfer_like_items=transfer_like_items,
            activity_count=activity_count,
            elderly_count=elderly_count,
            toddler_count=toddler_count,
        )

        if elderly_count > 0 and flight_legs >= self.policy.elderly_hard_flight_leg_threshold:
            hard_blockers.append(
                self._constraint(
                    "routing",
                    "hard",
                    f"Elderly traveler context with {flight_legs} flight legs indicates high transfer-fatigue risk.",
                    "Reduce flight legs, insert recovery windows, and confirm assisted transfer support before proposal.",
                    {"elderly_count": elderly_count, "flight_legs": flight_legs, "route_analysis": route_analysis.to_dict()},
                )
            )
        elif elderly_count > 0 and (
            flight_legs >= self.policy.elderly_soft_flight_leg_threshold
            or transfer_like_items >= self.policy.elderly_soft_transfer_threshold
        ):
            soft_constraints.append(
                self._constraint(
                    "routing",
                    "soft",
                    "Elderly traveler context suggests route complexity/transfer fatigue risk.",
                    "Prefer simpler routing and confirm mobility-assist transfer planning.",
                    {
                        "elderly_count": elderly_count,
                        "flight_legs": flight_legs,
                        "transfer_like_items": transfer_like_items,
                        "route_analysis": route_analysis.to_dict(),
                    },
                )
            )

        if toddler_count > 0 and any(term in activity_text for term in self.policy.extreme_activity_terms):
            hard_blockers.append(
                self._constraint(
                    "activity",
                    "hard",
                    "Toddler traveler context conflicts with extreme-intensity activity plan.",
                    "Replace trek/extreme segments with toddler-safe alternatives or split itinerary by traveler cohort.",
                    {"toddlers": toddler_count, "route_analysis": route_analysis.to_dict()},
                )
            )

        if parent_ambiguous and (flight_legs >= self.policy.elderly_soft_flight_leg_threshold or transfer_like_items >= self.policy.elderly_soft_transfer_threshold):
            soft_constraints.append(
                self._constraint(
                    "routing",
                    "soft",
                    "Parent cohort is present but age/mobility tolerance is not explicit for route complexity.",
                    "Confirm parent transfer tolerance before locking dense multi-hop routing.",
                    {"flight_legs": flight_legs, "transfer_like_items": transfer_like_items},
                )
            )

        if older_adult_present and flight_legs >= self.policy.elderly_hard_flight_leg_threshold:
            soft_constraints.append(
                self._constraint(
                    "routing",
                    "soft",
                    "Older-adult traveler context detected on a high-leg itinerary.",
                    "Confirm comfort, recovery windows, and transfer support before confirmation.",
                    {"flight_legs": flight_legs},
                )
            )

        if infant_present and (flight_legs >= 2 or activity_count >= 4):
            soft_constraints.append(
                self._constraint(
                    "pace",
                    "soft",
                    "Infant traveler context suggests elevated transfer and pacing sensitivity.",
                    "Prefer longer layovers, reduce activity density, and confirm infant-ready logistics.",
                    {"flight_legs": flight_legs, "activity_count": activity_count},
                )
            )

        if tight_connections > 0 and (elderly_count > 0 or toddler_count > 0):
            hard_blockers.append(
                self._constraint(
                    "routing",
                    "hard",
                    f"{tight_connections} tight flight connection(s) detected for vulnerable traveler composition.",
                    "Increase layover buffers or simplify routing before proposal confirmation.",
                    {
                        "tight_connections": tight_connections,
                        "threshold_minutes": self.policy.tight_connection_minutes_threshold,
                        "route_analysis": route_analysis.to_dict(),
                    },
                )
            )
        elif tight_connections > 0 and mobility_constrained_present:
            hard_blockers.append(
                self._constraint(
                    "routing",
                    "hard",
                    "Tight connections detected with mobility-constrained traveler context.",
                    "Increase connection buffers and verify assisted transfer support.",
                    {"tight_connections": tight_connections, "threshold_minutes": self.policy.tight_connection_minutes_threshold},
                )
            )

        if elderly_count > 0 and any(term in activity_text for term in self.policy.elderly_water_risk_terms):
            soft_constraints.append(
                self._constraint(
                    "activity",
                    "soft",
                    "Elderly traveler context includes water-intensity activity risk.",
                    "Confirm medical fitness, supervision, and lower-intensity alternatives for elderly travelers.",
                    {"elderly_count": elderly_count, "route_analysis": route_analysis.to_dict()},
                )
            )

        regional = assess_regional_disruption(
            destinations=[str(d) for d in destinations],
            month=month,
            route_hubs=[str(h) for h in route_hubs],
            flight_legs=flight_legs,
        )
        if regional.risk_level == "high":
            hard_blockers.append(
                self._constraint(
                    "safety",
                    "hard",
                    "Regional disruption/security risk assessed as high.",
                    "Require regional safety and disruption review before confirmation.",
                    {"signals": regional.signals, "details": regional.details, "recommendations": regional.recommendations},
                )
            )
        elif regional.risk_level == "medium":
            soft_constraints.append(
                self._constraint(
                    "routing",
                    "soft",
                    "Regional disruption pressure detected for this route window.",
                    "Add contingency buffers and route alternatives before locking itinerary.",
                    {"signals": regional.signals, "details": regional.details, "recommendations": regional.recommendations},
                )
            )

        status = "blocked" if hard_blockers else "review" if soft_constraints or missing_facts else "feasible"
        operator_next_action = "human_feasibility_review" if hard_blockers else "clarify_feasibility_facts" if missing_facts else "include_constraints_in_proposal" if soft_constraints else "continue_proposal"
        structured_risks = [
            feasibility_constraint_to_structured(item, self.definition.name)
            for item in [*hard_blockers, *soft_constraints]
            if isinstance(item, dict)
        ]
        risk_action_plan = build_risk_action_plan(
            stage=str(context.get("stage") or ""),
            structured_risks=structured_risks,
        )
        return {
            "assessed_at": assessed_at.isoformat(),
            "source": self.definition.name,
            "facts_marker": context.get("facts_marker"),
            "status": status,
            "hard_blockers": hard_blockers,
            "soft_constraints": soft_constraints,
            "structured_risks": structured_risks,
            "risk_action_plan": risk_action_plan,
            "missing_facts": sorted(set(missing_facts)),
            "operator_next_action": operator_next_action,
            "authority": "Internal feasibility support only. Do not auto-reject, auto-send, book, or mutate canonical trip stage.",
        }

    def _constraint(self, category: str, severity: str, message: str, recommendation: str, metadata: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        item = {
            "category": category,
            "severity": severity,
            "message": message,
            "recommendation": recommendation,
        }
        if metadata:
            item["metadata"] = metadata
        return item

    def _infer_party_profile(self, composition: dict[str, Any], travelers: Any, raw_note: str) -> dict[str, Any]:
        elderly_count = int(composition.get("elderly") or 0)
        older_adult_present = False
        parent_ambiguous = False
        infant_present = bool(composition.get("infants") or 0)
        mobility_constrained_present = False
        note = (raw_note or "").lower()

        explicit_elderly_terms = {"elderly", "senior", "ageing parent", "aging parent", "grandparent", "grandparents"}
        if elderly_count == 0 and any(term in note for term in explicit_elderly_terms):
            elderly_count = 1

        if any(term in note for term in {"parent", "parents", "mom", "mother", "dad", "father", "in-law", "in laws", "inlaws"}):
            parent_ambiguous = True
        if any(term in note for term in {"grandma", "grandmother", "grandpa", "grandfather", "grandparents"}):
            elderly_count = max(1, elderly_count)
            parent_ambiguous = False
        if any(term in note for term in {"infant", "baby", "newborn"}):
            infant_present = True
        if any(term in note for term in {"wheelchair", "knee issue", "mobility issue", "step-free", "cannot walk long"}):
            mobility_constrained_present = True

        for traveler in _flatten_values(travelers):
            if not isinstance(traveler, dict):
                continue
            age = first_non_empty(traveler.get("age"), traveler.get("traveler_age"), traveler.get("age_years"))
            age_val = _as_float(age)
            if age_val is None:
                traveler_type = str(first_non_empty(traveler.get("traveler_type"), traveler.get("type"), traveler.get("age_group"), "")).lower()
                if traveler_type in {"infant", "baby"}:
                    infant_present = True
                if traveler_type in {"senior", "elderly"}:
                    elderly_count += 1
                    parent_ambiguous = False
                if traveler.get("mobility_constraint") or traveler.get("wheelchair_required"):
                    mobility_constrained_present = True
                continue
            if age_val < 2:
                infant_present = True
            elif age_val >= 60:
                elderly_count += 1
                parent_ambiguous = False
            elif age_val >= 45:
                older_adult_present = True

        return {
            "elderly_count": max(0, elderly_count),
            "older_adult_present": older_adult_present,
            "parent_ambiguous": parent_ambiguous and elderly_count == 0,
            "infant_present": infant_present,
            "mobility_constrained_present": mobility_constrained_present,
        }


class ProposalReadinessAgent:
    definition = AgentDefinition(
        name="proposal_readiness_agent",
        description="Checks whether a proposal is complete enough for operator review without unresolved operational risks.",
        trigger_contract="Trip is at proposal/quoted stage with proposal/quote content and no current proposal_readiness_assessment for the same marker.",
        input_contract="Trip record with proposal/quote content plus document, feasibility, destination, and weather metadata.",
        output_contract="Trip is updated with proposal_readiness_assessment, proposal_readiness_status, missing elements, unresolved risks, and operator next action.",
        idempotency_contract="One proposal readiness assessment per trip_id plus proposal/fact marker until proposal content or risk metadata changes.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}
    _eligible_stages = {"proposal", "quoted", "booking"}

    def __init__(self, now_provider: Callable[[], datetime] | None = None):
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            stage = str(first_non_empty(get_field(trip, "stage"), status, "")).lower()
            if not trip_id or status in self._terminal_statuses or stage not in self._eligible_stages:
                continue
            context = self._extract_context(trip)
            if not context["has_proposal"]:
                continue
            existing = get_field(trip, "proposal_readiness_assessment")
            if isinstance(existing, dict) and existing.get("proposal_marker") == context["proposal_marker"]:
                continue
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="assess_proposal_readiness",
                idempotency_key=f"{self.definition.name}:{trip_id}:{context['proposal_marker']}",
                payload=context,
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        assessed_at = self.now_provider()
        context = dict(work_item.payload)
        assessment = self._assess(context, assessed_at)
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "proposal_readiness_assessment": assessment,
                "proposal_readiness_status": assessment["status"],
                "proposal_missing_elements": assessment["missing_elements"],
                "proposal_unresolved_risks": assessment["unresolved_risks"],
                "operator_next_action": assessment["operator_next_action"],
                "last_agent_action": self.definition.name,
                "last_agent_action_at": assessed_at.isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Assessed proposal readiness", assessment)

    def _extract_context(self, trip: Any) -> dict[str, Any]:
        proposal = first_non_empty(get_field(trip, "proposal", "quote", "proposal_packet"), get_nested(trip, "structured_json.proposal"), {})
        if not isinstance(proposal, dict):
            proposal = {"raw": proposal}
        options = self._proposal_options(proposal)
        budget_summary = first_non_empty(proposal.get("budget_summary"), proposal.get("pricing_summary"), proposal.get("price_summary"), proposal.get("budgetNotes"))
        risk_notes = first_non_empty(proposal.get("risk_notes"), proposal.get("risk_summary"), proposal.get("assumptions"), proposal.get("operator_notes"))
        next_action = first_non_empty(proposal.get("next_action"), proposal.get("nextStep"), proposal.get("cta"), get_field(trip, "recommended_next_action"))
        marker = "|".join(
            [
                str(len(options)),
                str(bool(budget_summary)),
                str(bool(risk_notes)),
                str(bool(next_action)),
                str(get_nested(trip, "constraint_feasibility_assessment.status") or "no_feasibility"),
                str(get_nested(trip, "document_readiness_checklist.risk_level") or "no_documents"),
                str(get_nested(trip, "weather_pivot_packet.risk_level") or "no_weather"),
            ]
        )
        return {
            "has_proposal": bool(proposal),
            "options": options,
            "budget_summary": budget_summary,
            "risk_notes": risk_notes,
            "next_action": next_action,
            "document_readiness": get_field(trip, "document_readiness_checklist") or {},
            "feasibility": get_field(trip, "constraint_feasibility_assessment") or {},
            "weather_pivot": get_field(trip, "weather_pivot_packet") or {},
            "destination_intelligence": get_field(trip, "destination_intelligence_snapshot") or {},
            "proposal_marker": marker,
        }

    def _proposal_options(self, proposal: dict[str, Any]) -> list[Any]:
        options = first_non_empty(proposal.get("options"), proposal.get("itineraries"), proposal.get("packages"), proposal.get("variants"), [])
        flattened = _flatten_values(options)
        if not flattened and proposal.get("raw"):
            flattened = [proposal["raw"]]
        return flattened

    def _assess(self, context: dict[str, Any], assessed_at: datetime) -> dict[str, Any]:
        missing_elements: list[str] = []
        unresolved_risks: list[dict[str, Any]] = []

        if len(context.get("options", [])) < 2:
            missing_elements.append("at least two proposal options")
        if not context.get("budget_summary"):
            missing_elements.append("budget assumptions and inclusions/exclusions")
        if not context.get("risk_notes"):
            missing_elements.append("risk notes or operator assumptions")
        if not context.get("next_action"):
            missing_elements.append("clear next action")

        feasibility = context.get("feasibility") if isinstance(context.get("feasibility"), dict) else {}
        feasibility_status = str(feasibility.get("status") or "").lower()
        if feasibility_status == "blocked":
            unresolved_risks.append(self._risk("feasibility", "hard", "Feasibility assessment is blocked.", "Resolve hard blockers before proposal review."))
        elif feasibility_status == "review":
            unresolved_risks.append(self._risk("feasibility", "soft", "Feasibility assessment needs review.", "Address soft constraints in proposal assumptions."))

        document_readiness = context.get("document_readiness") if isinstance(context.get("document_readiness"), dict) else {}
        doc_risk = str(document_readiness.get("risk_level") or "").lower()
        if doc_risk == "high":
            unresolved_risks.append(self._risk("document_readiness", "hard", "Document readiness risk is high.", "Verify document requirements before proposal is firm."))
        elif doc_risk == "medium":
            unresolved_risks.append(self._risk("document_readiness", "soft", "Document readiness requires review.", "Mention document assumptions and deadlines."))

        weather_pivot = context.get("weather_pivot") if isinstance(context.get("weather_pivot"), dict) else {}
        weather_risk = str(weather_pivot.get("risk_level") or "").lower()
        if weather_risk == "high":
            unresolved_risks.append(self._risk("weather", "hard", "Weather pivot risk is high.", "Resolve weather pivot packet before proposal review."))
        elif weather_risk == "medium":
            unresolved_risks.append(self._risk("weather", "soft", "Weather pivot risk needs review.", "Include weather alternatives in proposal."))

        has_hard_risk = any(risk["severity"] == "hard" for risk in unresolved_risks)
        if missing_elements or has_hard_risk:
            status = "blocked"
            operator_next_action = "revise_proposal_before_review"
        elif unresolved_risks:
            status = "needs_operator_review"
            operator_next_action = "operator_review_proposal_risks"
        else:
            status = "ready_for_operator_review"
            operator_next_action = "operator_review_proposal"

        return {
            "assessed_at": assessed_at.isoformat(),
            "source": self.definition.name,
            "proposal_marker": context.get("proposal_marker"),
            "status": status,
            "missing_elements": sorted(set(missing_elements)),
            "unresolved_risks": unresolved_risks,
            "operator_next_action": operator_next_action,
            "authority": "Internal proposal readiness support only. Do not auto-send, book, ticket, or change suppliers.",
        }

    def _risk(self, category: str, severity: str, message: str, recommendation: str) -> dict[str, Any]:
        return {"category": category, "severity": severity, "message": message, "recommendation": recommendation}


class BookingReadinessAgent:
    definition = AgentDefinition(
        name="booking_readiness_agent",
        description="Verifies traveler, payer, contact, special requirement, and unresolved-risk readiness before human booking.",
        trigger_contract="Trip is at booking/quoted stage with booking_data or pending_booking_data and no current booking_readiness_assessment for the same marker.",
        input_contract="Trip record with booking_data/pending_booking_data plus proposal, document, feasibility, and quote/risk metadata.",
        output_contract="Trip is updated with booking_readiness_assessment, booking_readiness_status, missing elements, blocking risks, and operator next action.",
        idempotency_contract="One booking readiness assessment per trip_id plus booking/fact marker until booking data or risk metadata changes.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}
    _eligible_stages = {"booking", "quoted", "payment", "ticketing"}

    def __init__(self, now_provider: Callable[[], datetime] | None = None):
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            stage = str(first_non_empty(get_field(trip, "stage"), status, "")).lower()
            if not trip_id or status in self._terminal_statuses or stage not in self._eligible_stages:
                continue
            context = self._extract_context(trip)
            if not context["has_booking_data"]:
                continue
            existing = get_field(trip, "booking_readiness_assessment")
            if isinstance(existing, dict) and existing.get("booking_marker") == context["booking_marker"]:
                continue
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="assess_booking_readiness",
                idempotency_key=f"{self.definition.name}:{trip_id}:{context['booking_marker']}",
                payload=context,
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        assessed_at = self.now_provider()
        context = dict(work_item.payload)
        assessment = self._assess(context, assessed_at)
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "booking_readiness_assessment": assessment,
                "booking_readiness_status": assessment["status"],
                "booking_missing_elements": assessment["missing_elements"],
                "booking_blocking_risks": assessment["blocking_risks"],
                "operator_next_action": assessment["operator_next_action"],
                "last_agent_action": self.definition.name,
                "last_agent_action_at": assessed_at.isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Assessed booking readiness", assessment)

    def _extract_context(self, trip: Any) -> dict[str, Any]:
        booking_data = first_non_empty(get_field(trip, "booking_data"), get_field(trip, "pending_booking_data"), get_nested(trip, "structured_json.booking_data"), {})
        if not isinstance(booking_data, dict):
            booking_data = {}
        travelers = _flatten_values(first_non_empty(booking_data.get("travelers"), booking_data.get("passengers"), []))
        payer = first_non_empty(booking_data.get("payer"), booking_data.get("payment_contact"), booking_data.get("billing_contact"), {})
        contact = first_non_empty(booking_data.get("contact"), booking_data.get("primary_contact"), {})
        special_requirements = first_non_empty(booking_data.get("special_requirements"), booking_data.get("specialRequests"), booking_data.get("requirements"))
        marker = "|".join(
            [
                str(len(travelers)),
                str(bool(payer)),
                str(bool(contact)),
                str(bool(special_requirements)),
                str(get_nested(trip, "proposal_readiness_assessment.status") or "no_proposal"),
                str(get_nested(trip, "document_readiness_checklist.risk_level") or "no_documents"),
                str(get_nested(trip, "constraint_feasibility_assessment.status") or "no_feasibility"),
            ]
        )
        return {
            "has_booking_data": bool(booking_data),
            "travelers": travelers,
            "payer": payer,
            "contact": contact,
            "special_requirements": special_requirements,
            "proposal_readiness": get_field(trip, "proposal_readiness_assessment") or {},
            "document_readiness": get_field(trip, "document_readiness_checklist") or {},
            "feasibility": get_field(trip, "constraint_feasibility_assessment") or {},
            "quote": first_non_empty(get_field(trip, "quote"), get_field(trip, "proposal"), {}),
            "booking_marker": marker,
        }

    def _assess(self, context: dict[str, Any], assessed_at: datetime) -> dict[str, Any]:
        missing_elements: list[str] = []
        blocking_risks: list[dict[str, Any]] = []
        travelers = context.get("travelers", [])

        if not travelers:
            missing_elements.append("traveler records")
        for index, traveler in enumerate(travelers, start=1):
            if not isinstance(traveler, dict):
                missing_elements.append(f"traveler {index} structured details")
                continue
            if not first_non_empty(get_field(traveler, "name", "full_name", "fullName"), get_field(traveler, "first_name", "firstName")):
                missing_elements.append(f"traveler {index} full legal name")
            if not first_non_empty(get_field(traveler, "date_of_birth", "dateOfBirth", "dob")):
                missing_elements.append(f"traveler {index} date of birth")
            if not first_non_empty(get_field(traveler, "passport_number", "passportNumber"), get_field(traveler, "document_number", "documentNumber")):
                missing_elements.append(f"traveler {index} passport/document number")
            if not first_non_empty(get_field(traveler, "passport_expiry", "passportExpiry"), get_field(traveler, "passport_expiry_date")):
                missing_elements.append(f"traveler {index} passport expiry")

        payer = context.get("payer") if isinstance(context.get("payer"), dict) else {}
        if not payer or not first_non_empty(payer.get("name"), payer.get("email"), payer.get("phone")):
            missing_elements.append("payer contact/payment owner")
        contact = context.get("contact") if isinstance(context.get("contact"), dict) else {}
        if not contact or not first_non_empty(contact.get("email"), contact.get("phone")):
            missing_elements.append("primary booking contact email or phone")
        if not context.get("special_requirements"):
            missing_elements.append("special requirements confirmation, even if none")

        proposal = context.get("proposal_readiness") if isinstance(context.get("proposal_readiness"), dict) else {}
        proposal_status = str(proposal.get("status") or "").lower()
        if proposal_status == "blocked":
            blocking_risks.append(self._risk("proposal_readiness", "hard", "Proposal readiness is blocked.", "Resolve proposal blockers before booking handoff."))
        elif proposal_status in {"needs_operator_review", "review"}:
            blocking_risks.append(self._risk("proposal_readiness", "soft", "Proposal still needs operator review.", "Confirm proposal assumptions before booking."))

        document_readiness = context.get("document_readiness") if isinstance(context.get("document_readiness"), dict) else {}
        doc_risk = str(document_readiness.get("risk_level") or "").lower()
        if doc_risk == "high":
            blocking_risks.append(self._risk("document_readiness", "hard", "Document readiness risk is high.", "Resolve document/visa/passport checks before booking."))
        elif doc_risk == "medium":
            blocking_risks.append(self._risk("document_readiness", "soft", "Document readiness needs review.", "Confirm document assumptions before booking."))

        feasibility = context.get("feasibility") if isinstance(context.get("feasibility"), dict) else {}
        feasibility_status = str(feasibility.get("status") or "").lower()
        if feasibility_status == "blocked":
            blocking_risks.append(self._risk("feasibility", "hard", "Feasibility is blocked.", "Resolve feasibility blockers before booking."))

        has_hard_risk = any(risk["severity"] == "hard" for risk in blocking_risks)
        if missing_elements:
            status = "blocked"
            operator_next_action = "collect_booking_details"
        elif has_hard_risk:
            status = "blocked"
            operator_next_action = "resolve_booking_blockers"
        elif blocking_risks:
            status = "needs_operator_review"
            operator_next_action = "human_booking_review"
        else:
            status = "ready_for_human_booking"
            operator_next_action = "human_booking_review"

        return {
            "assessed_at": assessed_at.isoformat(),
            "source": self.definition.name,
            "booking_marker": context.get("booking_marker"),
            "status": status,
            "missing_elements": sorted(set(missing_elements)),
            "blocking_risks": blocking_risks,
            "operator_next_action": operator_next_action,
            "authority": "Internal booking readiness support only. Do not book, ticket, charge, contact suppliers, or send customer messages.",
        }

    def _risk(self, category: str, severity: str, message: str, recommendation: str) -> dict[str, Any]:
        return {"category": category, "severity": severity, "message": message, "recommendation": recommendation}


class FlightStatusAgent:
    definition = AgentDefinition(
        name="flight_status_agent",
        description="Checks flight status evidence and creates internal disruption snapshots without rebooking.",
        trigger_contract="Trip has flight segments and no current flight_status_snapshot for the same flight marker.",
        input_contract="Trip record with flights/segments and optional booking stage metadata.",
        output_contract="Trip is updated with flight_status_snapshot, flight_disruption_risk_level, and operator next action.",
        idempotency_contract="One flight status snapshot per trip_id plus flight marker until flight data changes.",
        failure_contract="Tool failures fail closed into unknown-risk snapshots; update failures retry and poison after retry budget.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}

    def __init__(self, flight_tool: Optional[FlightStatusTool] = None, now_provider: Callable[[], datetime] | None = None):
        self.flight_tool = flight_tool or build_flight_status_tool_from_env()
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            if not trip_id or status in self._terminal_statuses:
                continue
            flights = self._extract_flights(trip)
            if not flights:
                continue
            marker = self._marker(flights)
            existing = get_field(trip, "flight_status_snapshot")
            if isinstance(existing, dict) and existing.get("flight_marker") == marker:
                continue
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="check_flight_status",
                idempotency_key=f"{self.definition.name}:{trip_id}:{marker}",
                payload={"flights": flights, "flight_marker": marker},
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        checked_at = self.now_provider()
        flight_outputs: list[dict[str, Any]] = []
        risk_scores: list[int] = []
        for flight in work_item.payload.get("flights", []):
            tool_result = self._call_tool(flight)
            fresh = tool_result.is_fresh(now=checked_at)
            risk_score = self._risk_score(tool_result) if fresh else 0
            risk_scores.append(risk_score)
            flight_outputs.append(
                {
                    "flight": flight,
                    "status": "fresh" if fresh else "stale",
                    "risk_level": self._risk_level(risk_score) if fresh else "unknown",
                    "tool_evidence": [tool_result.to_dict(now=checked_at)],
                }
            )
        overall = self._risk_level(max(risk_scores, default=0))
        if any(output["status"] == "stale" for output in flight_outputs):
            overall = "unknown"
        operator_next_action = "review_flight_disruption" if overall in {"medium", "high", "unknown"} else "monitor_flights"
        output = {
            "checked_at": checked_at.isoformat(),
            "source": self.definition.name,
            "flight_marker": work_item.payload.get("flight_marker"),
            "risk_level": overall,
            "flights": flight_outputs,
            "operator_next_action": operator_next_action,
            "authority": "Internal flight status support only. Do not rebook, ticket, contact suppliers, or send customer messages.",
        }
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "flight_status_snapshot": output,
                "flight_disruption_risk_level": overall,
                "operator_next_action": operator_next_action,
                "last_agent_action": self.definition.name,
                "last_agent_action_at": checked_at.isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Attached flight status snapshot", output)

    def _extract_flights(self, trip: Any) -> list[dict[str, Any]]:
        raw_flights = first_non_empty(get_field(trip, "flights", "flight_segments"), get_nested(trip, "booking_data.flights"), get_nested(trip, "itinerary.flights"), [])
        flights: list[dict[str, Any]] = []
        for item in _flatten_values(raw_flights):
            if isinstance(item, dict):
                flights.append(item)
        return flights

    def _marker(self, flights: list[dict[str, Any]]) -> str:
        parts = []
        for flight in flights:
            parts.append(f"{flight.get('carrier') or flight.get('airline') or ''}{flight.get('flight_number') or flight.get('number') or ''}")
        return ",".join(parts) or "unknown_flights"

    def _call_tool(self, flight: dict[str, Any]) -> ToolResult:
        try:
            return self.flight_tool.flight_status(flight)
        except Exception as exc:
            logger.exception("FlightStatusAgent: flight tool failed")
            return ToolResult.from_static(
                tool_name="flight_status_tool_error",
                query=flight,
                data={"status": "error", "message": str(exc)[:240]},
                source=self.definition.name,
                freshness=ToolFreshnessPolicy(max_age_seconds=300),
                confidence=0.1,
            )

    def _risk_score(self, tool_result: ToolResult) -> int:
        data = tool_result.data
        delay = _as_float(data.get("delay_minutes")) or 0
        status = str(data.get("status") or "").lower()
        if status in {"cancelled", "diverted"} or delay >= 90:
            return 3
        if status in {"delayed", "boarding_changed"} or delay >= 30:
            return 2
        return 1

    def _risk_level(self, score: int) -> str:
        if score >= 3:
            return "high"
        if score == 2:
            return "medium"
        if score == 1:
            return "low"
        return "unknown"


class TicketPriceWatchAgent:
    definition = AgentDefinition(
        name="ticket_price_watch_agent",
        description="Checks quote/fare drift and creates internal revalidation alerts without purchasing.",
        trigger_contract="Trip has quote/proposal price data and no current ticket_price_watch_alert for the same quote marker.",
        input_contract="Trip record with quote/proposal price, currency, quote id, and stage metadata.",
        output_contract="Trip is updated with ticket_price_watch_alert, quote_revalidation_required, and operator next action.",
        idempotency_contract="One price watch alert per trip_id plus quote marker until quote data changes.",
        failure_contract="Stale/tool failures produce unknown-risk revalidation alert; update failures retry and poison after retry budget.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}
    _eligible_stages = {"quoted", "proposal", "booking", "payment"}

    def __init__(self, price_tool: Optional[PriceWatchTool] = None, now_provider: Callable[[], datetime] | None = None):
        self.price_tool = price_tool or build_price_watch_tool_from_env()
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            stage = str(first_non_empty(get_field(trip, "stage"), status, "")).lower()
            if not trip_id or status in self._terminal_statuses or stage not in self._eligible_stages:
                continue
            quote = self._extract_quote(trip)
            if not quote:
                continue
            marker = self._marker(quote)
            existing = get_field(trip, "ticket_price_watch_alert")
            if isinstance(existing, dict) and existing.get("quote_marker") == marker:
                continue
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="watch_ticket_price",
                idempotency_key=f"{self.definition.name}:{trip_id}:{marker}",
                payload={"quote": quote, "quote_marker": marker},
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        checked_at = self.now_provider()
        quote = work_item.payload.get("quote", {})
        tool_result = self._call_tool(quote)
        fresh = tool_result.is_fresh(now=checked_at)
        drift = _as_float(tool_result.data.get("drift_percent")) if fresh else None
        risk_level = self._risk_level(drift) if fresh else "unknown"
        requires_revalidation = risk_level in {"medium", "high", "unknown"}
        operator_next_action = "revalidate_quote_before_payment" if requires_revalidation else "monitor_quote_price"
        output = {
            "checked_at": checked_at.isoformat(),
            "source": self.definition.name,
            "quote_marker": work_item.payload.get("quote_marker"),
            "risk_level": risk_level,
            "quote_revalidation_required": requires_revalidation,
            "tool_evidence": [tool_result.to_dict(now=checked_at)],
            "operator_next_action": operator_next_action,
            "authority": "Internal quote watch support only. Do not purchase, ticket, charge, contact suppliers, or send customer messages.",
        }
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "ticket_price_watch_alert": output,
                "quote_revalidation_required": requires_revalidation,
                "price_watch_risk_level": risk_level,
                "operator_next_action": operator_next_action,
                "last_agent_action": self.definition.name,
                "last_agent_action_at": checked_at.isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Attached ticket price watch alert", output)

    def _extract_quote(self, trip: Any) -> dict[str, Any]:
        quote = first_non_empty(get_field(trip, "quote"), get_field(trip, "proposal"), get_nested(trip, "structured_json.quote"), {})
        return quote if isinstance(quote, dict) else {}

    def _marker(self, quote: dict[str, Any]) -> str:
        return "|".join([str(quote.get("id") or quote.get("quote_id") or "quote"), str(quote.get("price") or quote.get("quoted_price") or quote.get("total") or "no_price"), str(quote.get("currency") or "no_currency")])

    def _call_tool(self, quote: dict[str, Any]) -> ToolResult:
        try:
            return self.price_tool.quote_price(quote)
        except Exception as exc:
            logger.exception("TicketPriceWatchAgent: price tool failed")
            return ToolResult.from_static(
                tool_name="price_watch_tool_error",
                query=quote,
                data={"status": "error", "message": str(exc)[:240]},
                source=self.definition.name,
                freshness=ToolFreshnessPolicy(max_age_seconds=300),
                confidence=0.1,
            )

    def _risk_level(self, drift: Optional[float]) -> str:
        if drift is None:
            return "unknown"
        if abs(drift) >= 15:
            return "high"
        if abs(drift) >= 5:
            return "medium"
        return "low"


class SafetyAlertAgent:
    definition = AgentDefinition(
        name="safety_alert_agent",
        description="Checks destination safety alert evidence and creates internal duty-of-care packets without customer sends.",
        trigger_contract="Trip has destination context and no current safety_alert_packet for the same destination marker.",
        input_contract="Trip record with destination and traveler metadata.",
        output_contract="Trip is updated with safety_alert_packet, safety_risk_level, affected travelers, and operator next action.",
        idempotency_contract="One safety alert packet per trip_id plus destination marker until destination changes.",
        failure_contract="Tool failures fail closed into unknown-risk packets; update failures retry and poison after retry budget.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}

    def __init__(self, safety_tool: Optional[SafetyAlertTool] = None, now_provider: Callable[[], datetime] | None = None):
        self.safety_tool = safety_tool or build_safety_alert_tool_from_env()
        self.now_provider = now_provider or (lambda: datetime.now(timezone.utc))

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            if not trip_id or status in self._terminal_statuses:
                continue
            destinations = self._destinations(trip)
            if not destinations:
                continue
            marker = ",".join(destinations)
            existing = get_field(trip, "safety_alert_packet")
            if isinstance(existing, dict) and existing.get("destination_marker") == marker:
                continue
            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="check_safety_alerts",
                idempotency_key=f"{self.definition.name}:{trip_id}:{marker}",
                payload={"destinations": destinations, "destination_marker": marker, "travelers": get_field(trip, "travelers") or []},
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        checked_at = self.now_provider()
        destination_outputs: list[dict[str, Any]] = []
        risk_scores: list[int] = []
        for destination in work_item.payload.get("destinations", []):
            tool_result = self._call_tool(destination)
            fresh = tool_result.is_fresh(now=checked_at)
            score = self._risk_score(tool_result) if fresh else 0
            risk_scores.append(score)
            destination_outputs.append(
                {
                    "destination": destination,
                    "status": "fresh" if fresh else "stale",
                    "risk_level": self._risk_level(score) if fresh else "unknown",
                    "tool_evidence": [tool_result.to_dict(now=checked_at)],
                }
            )
        risk_level = self._risk_level(max(risk_scores, default=0))
        if any(output["status"] == "stale" for output in destination_outputs):
            risk_level = "unknown"
        travelers = _flatten_values(work_item.payload.get("travelers", []))
        affected = [traveler for traveler in travelers if isinstance(traveler, dict)] or [{"scope": "all_travelers"}]
        operator_next_action = "human_safety_review" if risk_level in {"medium", "high", "unknown"} else "monitor_safety_alerts"
        output = {
            "checked_at": checked_at.isoformat(),
            "source": self.definition.name,
            "destination_marker": work_item.payload.get("destination_marker"),
            "risk_level": risk_level,
            "destinations": destination_outputs,
            "affected_travelers": affected,
            "operator_next_action": operator_next_action,
            "authority": "Internal safety support only. Do not auto-send customer messages, rebook, ticket, or cancel.",
        }
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "safety_alert_packet": output,
                "safety_risk_level": risk_level,
                "operator_next_action": operator_next_action,
                "last_agent_action": self.definition.name,
                "last_agent_action_at": checked_at.isoformat(),
            },
        )
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Attached safety alert packet", output)

    def _destinations(self, trip: Any) -> list[str]:
        facts = get_nested(trip, "extracted.facts", {}) or {}
        value = first_non_empty(_slot_value(facts.get("destination_candidates")), _slot_value(facts.get("destination")), get_field(trip, "destination", "destinations"))
        destinations: list[str] = []
        for item in _flatten_values(value):
            text = _stringify(item).strip().lower()
            if text and text not in destinations:
                destinations.append(text)
        return destinations

    def _call_tool(self, destination: str) -> ToolResult:
        try:
            return self.safety_tool.destination_alerts(destination)
        except Exception as exc:
            logger.exception("SafetyAlertAgent: safety tool failed")
            return ToolResult.from_static(
                tool_name="safety_alert_tool_error",
                query={"destination": destination},
                data={"status": "error", "message": str(exc)[:240]},
                source=self.definition.name,
                freshness=ToolFreshnessPolicy(max_age_seconds=300),
                confidence=0.1,
            )

    def _risk_score(self, tool_result: ToolResult) -> int:
        alerts = tool_result.data.get("alerts")
        severities = []
        if isinstance(alerts, list):
            severities = [str(alert.get("severity") or "").lower() for alert in alerts if isinstance(alert, dict)]
        if "high" in severities or "critical" in severities:
            return 3
        if "medium" in severities or "review" in severities:
            return 2
        return 1

    def _risk_level(self, score: int) -> str:
        if score >= 3:
            return "high"
        if score == 2:
            return "medium"
        if score == 1:
            return "low"
        return "unknown"


class GDSSchemaBridgeAgent:
    definition = AgentDefinition(
        name="gds_schema_bridge_agent",
        description="Normalizes provider/GDS/NDC-like records into canonical travel objects for internal review.",
        trigger_contract="Trip has provider_records/raw_provider_records and no current gds_schema_bridge for the same provider marker.",
        input_contract="Trip record with provider records.",
        output_contract="Trip is updated with gds_schema_bridge and canonical travel objects.",
        idempotency_contract="One normalization per trip_id plus provider record marker until provider records change.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived", "lost"}

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            status = str(get_field(trip, "status") or "").lower()
            if not trip_id or status in self._terminal_statuses:
                continue
            records = self._records(trip)
            if not records:
                continue
            marker = str(len(records)) + "|" + ",".join(str(record.get("kind") or record.get("type") or "unknown") for record in records)
            existing = get_field(trip, "gds_schema_bridge")
            if isinstance(existing, dict) and existing.get("provider_marker") == marker:
                continue
            yield WorkItem(self.definition.name, trip_id, "normalize_provider_records", f"{self.definition.name}:{trip_id}:{marker}", {"records": records, "provider_marker": marker})

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        now = datetime.now(timezone.utc).isoformat()
        canonical = [self._normalize(record) for record in work_item.payload.get("records", [])]
        output = {
            "normalized_at": now,
            "source": self.definition.name,
            "provider_marker": work_item.payload.get("provider_marker"),
            "canonical_objects": canonical,
            "operator_next_action": "review_canonical_travel_objects",
            "authority": "Internal normalization only. Do not ticket, book, or commit supplier inventory.",
        }
        updated = trip_repo.update_trip(work_item.trip_id, {"gds_schema_bridge": output, "canonical_travel_objects": canonical, "last_agent_action": self.definition.name, "last_agent_action_at": now})
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Normalized provider records", output)

    def _records(self, trip: Any) -> list[dict[str, Any]]:
        raw = first_non_empty(get_field(trip, "provider_records", "raw_provider_records", "gds_records"), get_nested(trip, "structured_json.provider_records"), [])
        return [record for record in _flatten_values(raw) if isinstance(record, dict)]

    def _normalize(self, record: dict[str, Any]) -> dict[str, Any]:
        kind = str(record.get("kind") or record.get("type") or "").lower()
        if kind == "flight" or record.get("flight_number"):
            return {
                "type": "flight",
                "carrier": record.get("carrier") or record.get("airline"),
                "flight_number": record.get("flight_number") or record.get("number"),
                "origin": record.get("origin"),
                "destination": record.get("destination"),
                "raw_reference": record.get("id") or record.get("record_locator"),
            }
        if kind == "hotel" or record.get("check_in"):
            return {
                "type": "hotel",
                "name": record.get("name") or record.get("hotel_name"),
                "check_in": record.get("check_in"),
                "check_out": record.get("check_out"),
                "raw_reference": record.get("id") or record.get("confirmation_number"),
            }
        return {"type": kind or "unknown", "raw_reference": record.get("id"), "data": record}


class PNRShadowAgent:
    definition = AgentDefinition(
        name="pnr_shadow_agent",
        description="Compares booking data against PNR/provider records to detect ghost-booking and mismatch risk.",
        trigger_contract="Trip has pnr_record and booking_data with no current pnr_shadow_check for the same marker.",
        input_contract="Trip record with booking_data and pnr_record.",
        output_contract="Trip is updated with pnr_shadow_check, pnr_shadow_risk_level, and issues.",
        idempotency_contract="One PNR shadow check per trip_id plus traveler/segment marker until records change.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            booking = get_field(trip, "booking_data") or {}
            pnr = get_field(trip, "pnr_record") or {}
            if not trip_id or not isinstance(booking, dict) or not isinstance(pnr, dict) or not pnr:
                continue
            marker = f"{len(_flatten_values(booking.get('travelers')))}|{len(_flatten_values(pnr.get('travelers')))}|{len(_flatten_values(pnr.get('segments')))}"
            existing = get_field(trip, "pnr_shadow_check")
            if isinstance(existing, dict) and existing.get("pnr_marker") == marker:
                continue
            yield WorkItem(self.definition.name, trip_id, "compare_pnr_shadow", f"{self.definition.name}:{trip_id}:{marker}", {"booking": booking, "pnr": pnr, "pnr_marker": marker})

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        now = datetime.now(timezone.utc).isoformat()
        issues = self._issues(work_item.payload.get("booking", {}), work_item.payload.get("pnr", {}))
        risk_level = "high" if issues else "low"
        output = {
            "checked_at": now,
            "source": self.definition.name,
            "pnr_marker": work_item.payload.get("pnr_marker"),
            "risk_level": risk_level,
            "issues": issues,
            "operator_next_action": "review_pnr_mismatch" if issues else "monitor_pnr",
            "authority": "Internal PNR comparison only. Do not alter PNR, ticket, or contact suppliers.",
        }
        updated = trip_repo.update_trip(work_item.trip_id, {"pnr_shadow_check": output, "pnr_shadow_risk_level": risk_level, "last_agent_action": self.definition.name, "last_agent_action_at": now})
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Compared PNR shadow record", output)

    def _issues(self, booking: dict[str, Any], pnr: dict[str, Any]) -> list[dict[str, Any]]:
        booking_names = sorted(_normalize_name(get_field(t, "name", "full_name", "fullName")) for t in _flatten_values(booking.get("travelers")) if isinstance(t, dict))
        pnr_names = sorted(_normalize_name(get_field(t, "name", "full_name", "fullName")) for t in _flatten_values(pnr.get("travelers")) if isinstance(t, dict))
        issues = []
        if booking_names and pnr_names and booking_names != pnr_names:
            issues.append({"category": "traveler_names", "severity": "high", "message": "Booking traveler names do not match PNR traveler names."})
        if not _flatten_values(pnr.get("segments")):
            issues.append({"category": "segments", "severity": "high", "message": "PNR has no segments."})
        return issues


class SupplierIntelligenceAgent:
    definition = AgentDefinition(
        name="supplier_intelligence_agent",
        description="Assesses supplier response/reliability metadata and flags operational supplier risk.",
        trigger_contract="Trip has supplier_records and no current supplier_intelligence_snapshot for the same supplier marker.",
        input_contract="Trip record with supplier response/failure metadata.",
        output_contract="Trip is updated with supplier_intelligence_snapshot and supplier risk level.",
        idempotency_contract="One supplier intelligence snapshot per trip_id plus supplier marker until supplier records change.",
        failure_contract="Retry update failures; poison after retry budget and emit agent_escalated.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id") or "")
            records = [r for r in _flatten_values(get_field(trip, "supplier_records")) if isinstance(r, dict)]
            if not trip_id or not records:
                continue
            marker = ",".join(str(record.get("name") or record.get("supplier") or "unknown") for record in records)
            existing = get_field(trip, "supplier_intelligence_snapshot")
            if isinstance(existing, dict) and existing.get("supplier_marker") == marker:
                continue
            yield WorkItem(self.definition.name, trip_id, "assess_supplier_intelligence", f"{self.definition.name}:{trip_id}:{marker}", {"records": records, "supplier_marker": marker})

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        now = datetime.now(timezone.utc).isoformat()
        risks = []
        for record in work_item.payload.get("records", []):
            response_hours = _as_float(record.get("response_hours")) or 0
            failures = _as_float(record.get("failure_count")) or 0
            if response_hours >= 48 or failures >= 2:
                risks.append(
                    {
                        "supplier": record.get("name") or record.get("supplier") or "unknown",
                        "severity": "high" if failures >= 2 else "medium",
                        "message": "Supplier reliability or response-time risk detected.",
                    }
                )
        risk_level = "high" if any(r["severity"] == "high" for r in risks) else "medium" if risks else "low"
        output = {
            "assessed_at": now,
            "source": self.definition.name,
            "supplier_marker": work_item.payload.get("supplier_marker"),
            "risk_level": risk_level,
            "supplier_risks": risks,
            "operator_next_action": "review_supplier_risk" if risks else "monitor_suppliers",
            "authority": "Internal supplier intelligence only. Do not commit inventory or contact suppliers.",
        }
        updated = trip_repo.update_trip(work_item.trip_id, {"supplier_intelligence_snapshot": output, "supplier_risk_level": risk_level, "last_agent_action": self.definition.name, "last_agent_action_at": now})
        if not updated:
            return AgentExecutionResult(work_item, WorkStatus.RETRY_PENDING, False, "Trip update returned empty result")
        return AgentExecutionResult(work_item, WorkStatus.COMPLETED, True, "Assessed supplier intelligence", output)


def _as_float(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _extract_money_amount(value: Any) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, dict):
        return _extract_money_amount(first_non_empty(value.get("value"), value.get("amount"), value.get("total")))
    if isinstance(value, str):
        normalized = value.replace(",", "")
        match = re.search(r"\d+(?:\.\d+)?", normalized)
        if match:
            return float(match.group(0))
    return None


def _extract_date_range(value: Any) -> Optional[tuple[datetime, datetime]]:
    if isinstance(value, dict):
        start = parse_dt(first_non_empty(value.get("start"), value.get("from"), value.get("start_date")))
        end = parse_dt(first_non_empty(value.get("end"), value.get("to"), value.get("end_date")))
        if start and end:
            return start, end
    if isinstance(value, str):
        matches = re.findall(r"\d{4}-\d{2}-\d{2}", value)
        if len(matches) >= 2:
            start = parse_dt(matches[0])
            end = parse_dt(matches[1])
            if start and end:
                return start, end
        if len(matches) == 1:
            start = parse_dt(matches[0])
            if start:
                return start, start
    return None


def _normalize_name(value: Any) -> str:
    return " ".join(str(value or "").lower().replace(".", "").split())


def build_default_registry() -> AgentRegistry:
    return AgentRegistry([
        FrontDoorAgent(),
        SalesActivationAgent(),
        DocumentReadinessAgent(),
        DestinationIntelligenceAgent(),
        WeatherPivotAgent(),
        ConstraintFeasibilityAgent(),
        ProposalReadinessAgent(),
        BookingReadinessAgent(),
        FlightStatusAgent(),
        TicketPriceWatchAgent(),
        SafetyAlertAgent(),
        GDSSchemaBridgeAgent(),
        PNRShadowAgent(),
        SupplierIntelligenceAgent(),
        FollowUpAgent(),
        QualityEscalationAgent(),
    ])
