"""
Canonical backend product-agent runtime primitives.

The runtime is deliberately static and in-repo: agents are registered by code,
then supervised through deterministic scans and single-owner work execution.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Iterable, Optional, Protocol
from uuid import uuid4

from src.agents.events import AgentEvent, AgentEventType
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
        coordinator: Optional[InMemoryWorkCoordinator] = None,
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
            decision_output = trip.get("decision_output")
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


def build_default_registry() -> AgentRegistry:
    return AgentRegistry([
        FrontDoorAgent(),
        SalesActivationAgent(),
        DocumentReadinessAgent(),
        FollowUpAgent(),
        QualityEscalationAgent(),
    ])
