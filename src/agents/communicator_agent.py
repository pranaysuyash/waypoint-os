"""
agents.communicator_agent — Autonomous Clarification Drafting Agent.

Generates multi-tonal clarification drafts when inquiries hit ASK_FOLLOWUP or STOP_NEEDS_REVIEW,
empowering operators to respond to travelers instantly with high-empathy, contextual questions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable, List

from src.agents.runtime import (
    AgentDefinition,
    AgentExecutionResult,
    RetryPolicy,
    TripRepository,
    WorkItem,
    WorkStatus,
)

logger = logging.getLogger("communicator_agent")


def get_field(data: Any, *keys: str) -> Any:
    if not isinstance(data, dict):
        return None
    for k in keys:
        if k in data and data[k] is not None:
            return data[k]
    return None


class CommunicatorAgent:
    """
    The Communicator Agent monitors trips requiring additional information
    and drafts 1-3 contextually appropriate, empathetic clarification messages.
    """

    definition = AgentDefinition(
        name="communicator_agent",
        description="Autonomously drafts empathetic clarification messages when trips need traveler follow-up.",
        trigger_contract="Trip is in ASK_FOLLOWUP or STOP_NEEDS_REVIEW state with missing facts or ambiguities.",
        input_contract="Trip record with decision, follow_up_questions, hard_blockers, and traveler facts.",
        output_contract="Trip updated with 3 tonal clarification drafts (concise, consultative, formal).",
        idempotency_contract="One draft generation pass per trip_id + decision/revision timestamp.",
        failure_contract="Retry transient generation errors; fallback to template-based question synthesis.",
        retry_policy=RetryPolicy(max_attempts=3, backoff_seconds=(0, 1, 5)),
    )

    _terminal_statuses = {"closed", "cancelled", "completed", "archived"}

    def scan(self, trip_repo: TripRepository) -> Iterable[WorkItem]:
        for trip in trip_repo.list_active():
            trip_id = str(get_field(trip, "id", "trip_id") or "")
            if not trip_id:
                continue

            status = str(get_field(trip, "status", "stage") or "").lower()
            if status in self._terminal_statuses:
                continue

            decision = get_field(trip, "decision") or {}
            decision_state = str(get_field(decision, "decision_state", "state") or "")
            followup_questions = get_field(decision, "follow_up_questions") or get_field(trip, "follow_up_questions") or []
            hard_blockers = get_field(decision, "hard_blockers") or []

            # Trigger condition: trip is blocked awaiting clarification or needs followup
            needs_clarification = (
                decision_state in ("ASK_FOLLOWUP", "STOP_NEEDS_REVIEW")
                or len(followup_questions) > 0
                or len(hard_blockers) > 0
            )

            if not needs_clarification:
                continue

            # Check if drafts already exist for the current revision
            last_draft_at = get_field(trip, "last_communicator_draft_at")
            updated_at = str(get_field(trip, "updated_at") or get_field(trip, "created_at") or "")
            drafts = get_field(trip, "clarification_drafts") or []

            if drafts and last_draft_at and updated_at and last_draft_at >= updated_at:
                continue

            idempotency_key = f"{self.definition.name}:{trip_id}:{updated_at or 'init'}"

            yield WorkItem(
                agent_name=self.definition.name,
                trip_id=trip_id,
                action="draft_clarification_messages",
                idempotency_key=idempotency_key,
                payload={
                    "decision_state": decision_state,
                    "followup_questions": followup_questions,
                    "hard_blockers": hard_blockers,
                },
            )

    def execute(self, work_item: WorkItem, trip_repo: TripRepository) -> AgentExecutionResult:
        trip = trip_repo.get_trip(work_item.trip_id)
        if not trip:
            return AgentExecutionResult(
                work_item,
                WorkStatus.POISONED,
                False,
                f"Trip {work_item.trip_id} not found",
            )

        decision = get_field(trip, "decision") or {}
        followup_questions = get_field(decision, "follow_up_questions") or get_field(trip, "follow_up_questions") or []
        hard_blockers = get_field(decision, "hard_blockers") or []
        packet = get_field(trip, "packet") or {}
        facts = get_field(packet, "facts") or {}

        destination = get_field(facts, "destination_candidates")
        dest_str = "your upcoming journey"
        if isinstance(destination, dict) and "value" in destination:
            val = destination["value"]
            if isinstance(val, list) and val:
                dest_str = val[0]
            elif isinstance(val, str) and val:
                dest_str = val
        elif isinstance(destination, list) and destination:
            dest_str = destination[0]
        elif isinstance(destination, str) and destination:
            dest_str = destination

        # Extract main questions
        questions_text: List[str] = []
        for q in followup_questions:
            if isinstance(q, dict) and "question" in q:
                questions_text.append(q["question"])
            elif isinstance(q, str):
                questions_text.append(q)

        if not questions_text and hard_blockers:
            for b in hard_blockers:
                clean_b = str(b).replace("_", " ").title()
                questions_text.append(f"Could you clarify your preference for {clean_b}?")

        if not questions_text:
            questions_text = ["Could you confirm your preferred travel dates and budget range?"]

        # Synthesize 3 tonal variants
        drafts = [
            {
                "tone": "concise",
                "channel": "whatsapp_or_sms",
                "label": "Quick & Direct (Messaging)",
                "subject": f"Quick question about {dest_str}",
                "body": (
                    f"Hi! To get your itinerary for {dest_str} just right, could you quickly confirm:\n"
                    + "\n".join(f"• {q}" for q in questions_text[:3])
                    + "\n\nThanks!"
                ),
            },
            {
                "tone": "consultative",
                "channel": "email_or_chat",
                "label": "Consultative & Warm (Recommended)",
                "subject": f"Customizing your {dest_str} travel plans",
                "body": (
                    f"Hello,\n\nWe are currently curating your bespoke travel proposal for {dest_str}. "
                    f"To make sure every detail matches your expectations, we would love your guidance on a couple of quick points:\n\n"
                    + "\n".join(f"{i+1}. {q}" for i, q in enumerate(questions_text[:4]))
                    + "\n\nOnce confirmed, we will finalize your customized options.\n\nWarm regards,\nWaypoint Travel Team"
                ),
            },
            {
                "tone": "formal",
                "channel": "email_proposal",
                "label": "Formal & Detailed (Corporate/Luxury)",
                "subject": f"Travel Specification Clarification — {dest_str}",
                "body": (
                    f"Dear Traveler,\n\nThank you for choosing Waypoint OS. To ensure complete itinerary precision and compliance with your preferences for {dest_str}, please advise on the following specifications:\n\n"
                    + "\n".join(f"[{i+1}] {q}" for i, q in enumerate(questions_text[:4]))
                    + "\n\nWe appreciate your prompt response so we may deliver your complete quotation.\n\nSincerely,\nClient Services Team"
                ),
            },
        ]

        now_iso = datetime.now(timezone.utc).isoformat()
        updated = trip_repo.update_trip(
            work_item.trip_id,
            {
                "clarification_drafts": drafts,
                "last_communicator_draft_at": now_iso,
                "last_agent_action": self.definition.name,
                "last_agent_action_at": now_iso,
            },
        )

        if not updated:
            return AgentExecutionResult(
                work_item,
                WorkStatus.RETRY_PENDING,
                False,
                "Failed to persist clarification drafts to trip record",
            )

        return AgentExecutionResult(
            work_item,
            WorkStatus.COMPLETED,
            True,
            f"Generated {len(drafts)} clarification drafts for {dest_str}",
            {"draft_count": len(drafts), "destination": dest_str},
        )
