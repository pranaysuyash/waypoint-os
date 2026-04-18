"""
run_state.py — Run lifecycle state machine for Waypoint OS spine-api.

States
------
    queued     → run is registered but not yet started (reserved for async future)
    running    → run_spine_once is actively executing
    completed  → all pipeline stages finished, ok=True
    failed     → unexpected error (exception, infra failure, non-leakage)
    blocked    → strict leakage violation detected; requires operator review

'blocked' is a first-class terminal state distinct from 'failed':
    - failed  : system error (crash, timeout, bad input)
    - blocked : pipeline worked correctly, but output violated leakage policy

Transition guards
-----------------
Use can_transition(from_state, to_state) to validate state changes before
writing to the ledger. Invalid transitions raise ValueError.

Allowed transitions:
    queued  → running
    running → completed
    running → failed
    running → blocked
    queued  → failed   (before run even starts, e.g. validation error)
"""

from __future__ import annotations

from enum import Enum
from typing import Set


class RunState(str, Enum):
    """Canonical lifecycle states for a spine run."""

    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"  # strict leakage — first-class terminal

    def is_terminal(self) -> bool:
        """Return True if no further transitions are allowed."""
        return self in _TERMINAL_STATES

    def __str__(self) -> str:
        return self.value


# States from which no further transitions are valid.
_TERMINAL_STATES: Set[RunState] = {
    RunState.COMPLETED,
    RunState.FAILED,
    RunState.BLOCKED,
}

# Explicit allowed transitions. Only these are valid.
_ALLOWED_TRANSITIONS: dict[RunState, Set[RunState]] = {
    RunState.QUEUED:   {RunState.RUNNING, RunState.FAILED},
    RunState.RUNNING:  {RunState.COMPLETED, RunState.FAILED, RunState.BLOCKED},
    RunState.COMPLETED: set(),
    RunState.FAILED:   set(),
    RunState.BLOCKED:  set(),
}


def can_transition(from_state: RunState, to_state: RunState) -> bool:
    """
    Return True if the transition from_state → to_state is allowed.

    Does not raise — callers that need guaranteed enforcement should use
    assert_can_transition() instead.
    """
    return to_state in _ALLOWED_TRANSITIONS.get(from_state, set())


def assert_can_transition(from_state: RunState, to_state: RunState) -> None:
    """
    Raise ValueError if the transition is not allowed.

    Use this before recording any state change in the ledger.

    >>> assert_can_transition(RunState.RUNNING, RunState.COMPLETED)  # OK
    >>> assert_can_transition(RunState.COMPLETED, RunState.RUNNING)  # raises
    """
    if not can_transition(from_state, to_state):
        allowed = {s.value for s in _ALLOWED_TRANSITIONS.get(from_state, set())}
        raise ValueError(
            f"Invalid run state transition: {from_state!r} → {to_state!r}. "
            f"Allowed from {from_state!r}: {allowed or 'none (terminal state)'}"
        )


def terminal_state_for_run_result(ok: bool, is_blocked: bool) -> RunState:
    """
    Derive the correct terminal RunState from a /run response.

    Args:
        ok:         SpineRunResponse.ok field
        is_blocked: True when ok=False AND strict_leakage=True (leakage block)

    Returns:
        RunState.BLOCKED    if is_blocked
        RunState.COMPLETED  if ok=True
        RunState.FAILED     if ok=False and not blocked
    """
    if is_blocked:
        return RunState.BLOCKED
    return RunState.COMPLETED if ok else RunState.FAILED
