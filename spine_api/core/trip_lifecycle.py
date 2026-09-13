"""Canonical trip-execution lifecycle — council-ratified ontology (2026-09-14).

Ratified by the persona council (PER-0450 lead, PER-0444, PER-0453, PER-0369,
PER-0274 skeptic; decision record: blueprint Addendum 8). This replaces the
"14 vs 17" ambiguity with explicit rulings:

CANONICAL TRIP MACHINE — 12 enforced-eligible states (lowercase tokens):
    intake → planning → awaiting_customer_approval → approved →
    booking_in_progress → booked → (change_requested loop) → in_trip →
    completed; terminals: completed, cancelled, lost; exception: escalated.

Demoted from the taught 14 (NOT states):
    - needs_information  → typed condition (freezes only dependent work)
    - feasibility_check  → planning-stage marker (derived assessment)
    - needs_revision     → re-entry condition on planning (request-failure)

Ratified in model only, dormant (no producers; post-trip arc, PER-0444):
    - returned, archived (COMPLETED split; activates with post-trip work)

ADDITIONS: cancelled (terminal) — a booked trip's cancellation is not
lead-death: refunds/penalties differ from LOST obligations (financial seat).

RELATIONSHIP AXIS (separate machine, 6 stages — PER-0369; NOT modeled here):
    prospect, booked_active, post_trip, repeat_client, dormant, lost(churned).
    GHOST_RISK/ENGAGED_AFTER_QUOTE/QUOTE_SENT/WON/RETENTION_WINDOW demoted to
    derived signals/events per the events-vs-conditions-vs-risks doctrine.

ENFORCEMENT (staged ratchet — PER-0274 skeptic's evidence accepted):
    Every write is CLASSIFIED against this machine now (dormant-but-tested,
    never forgotten); violation RESPONSE graduates by evidence:
      RAISE : the legacy invariant (intake-blocked ↛ quote-capable) — P1.
      LOG   : machine-illegal pairs among non-proven classes (counted, so the
              distribution harness can graduate classes to RAISE later).
    Unknown strings never brick a writer (preserved verbatim from
    trip_status.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, FrozenSet, Optional, Set

# --- Canonical states -------------------------------------------------------

SPINE_STATES: FrozenSet[str] = frozenset({
    "intake", "planning", "awaiting_customer_approval", "approved",
    "booking_in_progress", "booked", "change_requested", "in_trip",
    "completed", "cancelled", "lost", "escalated",
})

# Ratified in the model, dormant until post-trip workflows exist.
DORMANT_MODEL_STATES: FrozenSet[str] = frozenset({"returned", "archived"})

TERMINAL_STATES: FrozenSet[str] = frozenset({
    "completed", "cancelled", "lost", "returned", "archived",
})

# Typed conditions (not states) — freezes only dependent work.
CONDITIONS: FrozenSet[str] = frozenset({
    "needs_information", "attention_needed", "quote_ready",
    "freshness_recheck_pending", "revision_pending",
})

# --- Legal transitions (taught table, demotions applied, CANCELLED added) ---

LEGAL_TRANSITIONS: Dict[str, FrozenSet[str]] = {
    "intake": frozenset({"planning", "lost", "escalated"}),
    "planning": frozenset({"awaiting_customer_approval", "lost", "escalated"}),
    "awaiting_customer_approval": frozenset({
        "approved", "planning", "lost", "escalated",
    }),
    "approved": frozenset({
        "booking_in_progress", "awaiting_customer_approval", "planning",
        "escalated",
    }),
    "booking_in_progress": frozenset({"booked", "cancelled", "escalated"}),
    "booked": frozenset({
        "change_requested", "in_trip", "cancelled", "escalated",
    }),
    "change_requested": frozenset({
        "planning", "booked", "cancelled", "escalated",
    }),
    "in_trip": frozenset({"completed", "cancelled", "escalated"}),
    "completed": frozenset(set()),   # terminal (dormant: → returned)
    "cancelled": frozenset(set()),   # terminal (dormant: → returned)
    "lost": frozenset(set()),        # terminal
    "escalated": frozenset(set()),   # operator-dynamic exits (see below)
}


def legal_targets(state: str) -> Set[str]:
    """Legal target states. ESCALATED exits are operator-dynamic: any
    non-terminal state is permitted (operator-attributed audited writes
    only); the mapping layer flags them for audit rather than declaring
    static edges."""
    if state == "escalated":
        return SPINE_STATES - TERMINAL_STATES - {"escalated"}
    return set(LEGAL_TRANSITIONS.get(state, frozenset()))


def is_terminal(state: str) -> bool:
    return state in TERMINAL_STATES


# --- V3 runtime-string mapping (council table, Addendum 8) ------------------
# Financial seat rulings encoded: ready_to_book NEVER maps to approved
# (readiness is not authorization); in_progress/active are audit-gated
# (ambiguous semantics pending the persisted-distribution audit).

@dataclass(frozen=True)
class Classification:
    state: str
    condition: Optional[str] = None
    audit_gated: bool = False   # mapping is provisional pending distribution audit


_RUNTIME_ALIASES: Dict[str, Classification] = {
    "new": Classification("intake"),
    "in_progress": Classification("planning", None, audit_gated=True),
    "active": Classification("in_trip", None, audit_gated=True),
    "incomplete": Classification("planning", "needs_information"),
    "needs_followup": Classification("planning", "attention_needed"),
    "needs_clarification": Classification("planning", "needs_information"),
    "awaiting_customer_details": Classification("planning", "needs_information"),
    "escalated": Classification("escalated"),
    "ready_to_quote": Classification("planning", "quote_ready"),
    "quote_ready": Classification("planning", "quote_ready"),
    # Readiness masquerading as authorization is the priority financial
    # hazard (PER-0453): quote_ready condition, NEVER approved.
    "ready_to_book": Classification("planning", "quote_ready"),
    # Canonical names map to themselves.
    **{s: Classification(s) for s in SPINE_STATES},
    **{s: Classification(s) for s in DORMANT_MODEL_STATES},
}


def classify(raw_status: Optional[str]) -> Optional[Classification]:
    """Map a runtime status string onto (canonical state, condition).
    Returns None for unknown strings — the caller keeps its pass-through
   -with-warning behavior; classification never invents a position."""
    if raw_status is None:
        return None
    key = str(raw_status).strip().lower()
    return _RUNTIME_ALIASES.get(key)


# --- Staged gate ------------------------------------------------------------

class TransitionAssessment:
    """Outcome of consulting the machine for one status write."""

    __slots__ = ("verdict", "reason", "old_state", "new_state", "audit_gated")

    def __init__(self, verdict: str, reason: str,
                 old: Optional[Classification], new: Optional[Classification]):
        self.verdict = verdict          # "allow" | "log" | "raise"
        self.reason = reason
        self.old_state = old.state if old else None
        self.new_state = new.state if new else None
        self.audit_gated = bool(old and old.audit_gated) or bool(new and new.audit_gated)

    def __repr__(self) -> str:  # pragma: no cover - debug aid
        return (f"TransitionAssessment({self.verdict!r}, {self.old_state!r} -> "
                f"{self.new_state!r}, {self.reason!r})")


def assess_transition(old_status: Optional[str],
                      new_status: Optional[str]) -> TransitionAssessment:
    """Consult the machine for one status write (staged enforcement).

    verdict="raise": the legacy proven-safe invariant (intake-blocked
    condition attempting to land on a quote-capable/consent state) — the
    one class with a proven writer-harm history.
    verdict="log": machine-illegal pair among classes not yet proven safe —
    counted for the distribution harness; writers are never blocked.
    verdict="allow": legal, same-state, or unclassifiable (unknown strings
    preserve their pass-through contract).
    """
    if old_status is None or new_status is None:
        return TransitionAssessment("allow", "no transition", None, None)
    old_s = str(old_status).strip().lower()
    new_s = str(new_status).strip().lower()
    if old_s == new_s:
        return TransitionAssessment("allow", "same state", None, None)

    old_c = classify(old_s)
    new_c = classify(new_s)
    if old_c is None or new_c is None:
        return TransitionAssessment("allow", "unclassified string (pass-through)", old_c, new_c)

    # P1 — proven invariant, restated canonically: an input-deficit condition
    # may never land directly on a consent/commitment state.
    p1_old = old_s in {
        "incomplete", "needs_followup", "needs_clarification",
        "awaiting_customer_details",
    }
    p1_new = new_s in {"ready_to_quote", "quote_ready", "ready_to_book"}
    if p1_old and p1_new:
        return TransitionAssessment(
            "raise",
            "intake-blocked condition cannot become quote-capable in one hop",
            old_c, new_c,
        )

    # Machine consultation (staged): illegal pairs LOG, they do not raise.
    if new_c.state not in legal_targets(old_c.state):
        return TransitionAssessment(
            "log",
            "machine-illegal transition (logged for distribution harness; "
            "enforcement graduates by evidence)",
            old_c, new_c,
        )

    return TransitionAssessment("allow", "legal transition", old_c, new_c)
