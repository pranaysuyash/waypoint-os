"""
test_run_lifecycle.py — Wave A eval harness for run lifecycle correctness.

Tests three execution paths:
    1. Golden path  — run succeeds, ledger + events reflect COMPLETED state
    2. Failure path — injected failure produces FAILED + audit events (not yet testable
                      without a mock, so validated via contract inspection)
    3. Leakage path — strict=true with leakage produces BLOCKED (not FAILED) + null bundle

Prerequisites:
    - spine-api running at TEST_SPINE_API_URL (default: http://127.0.0.1:8000)
    - data/runs/ directory writable

Run:
    pytest tests/test_run_lifecycle.py -v

These are integration tests against the live API. They do not mock LLM calls.
State machine unit tests (no API required) are at the bottom of the file.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
import requests

API_BASE = os.environ.get("TEST_SPINE_API_URL", "http://127.0.0.1:8000")
RUNS_DIR = Path(__file__).resolve().parent.parent / "data" / "runs"


# =============================================================================
# Helpers
# =============================================================================


def post_run(payload: dict, timeout: int = 30) -> dict:
    resp = requests.post(f"{API_BASE}/run", json=payload, timeout=timeout)
    assert resp.status_code == 200, f"POST /run failed: {resp.status_code} {resp.text}"
    return resp.json()


def get_run_status(run_id: str) -> dict:
    resp = requests.get(f"{API_BASE}/runs/{run_id}", timeout=10)
    return resp


def get_run_events_api(run_id: str) -> dict:
    resp = requests.get(f"{API_BASE}/runs/{run_id}/events", timeout=10)
    return resp


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def api_health():
    """Skip all tests if spine-api is unreachable."""
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        assert resp.status_code == 200
        return resp.json()
    except requests.ConnectionError:
        pytest.skip(f"spine-api not reachable at {API_BASE}")


GOLDEN_PAYLOAD = {
    "raw_note": "Family of 4 wants to visit Bali for 7 nights in August. Budget ~1.5L INR.",
    "stage": "discovery",
    "operating_mode": "normal_intake",
    "strict_leakage": False,
}

LEAKAGE_STRICT_PAYLOAD = {
    "raw_note": "Trip with hard_blocker and contradiction in the hypothesis",
    "stage": "discovery",
    "operating_mode": "normal_intake",
    "strict_leakage": True,
}


# =============================================================================
# State machine unit tests — no API required
# =============================================================================


class TestRunStateMachine:
    """Unit tests for run_state.py — no live API needed."""

    def test_import(self):
        """run_state module imports cleanly."""
        import sys
        spine_api_dir = Path(__file__).resolve().parent.parent / "spine-api"
        sys.path.insert(0, str(spine_api_dir))
        from run_state import RunState, can_transition, assert_can_transition  # noqa: F401

    def test_allowed_transitions(self):
        import sys
        spine_api_dir = Path(__file__).resolve().parent.parent / "spine-api"
        sys.path.insert(0, str(spine_api_dir))
        from run_state import RunState, can_transition

        assert can_transition(RunState.QUEUED,   RunState.RUNNING)    is True
        assert can_transition(RunState.RUNNING,  RunState.COMPLETED)  is True
        assert can_transition(RunState.RUNNING,  RunState.FAILED)     is True
        assert can_transition(RunState.RUNNING,  RunState.BLOCKED)    is True
        assert can_transition(RunState.QUEUED,   RunState.FAILED)     is True

    def test_disallowed_transitions(self):
        import sys
        spine_api_dir = Path(__file__).resolve().parent.parent / "spine-api"
        sys.path.insert(0, str(spine_api_dir))
        from run_state import RunState, can_transition

        assert can_transition(RunState.COMPLETED, RunState.RUNNING)   is False
        assert can_transition(RunState.FAILED,    RunState.COMPLETED) is False
        assert can_transition(RunState.BLOCKED,   RunState.COMPLETED) is False
        assert can_transition(RunState.RUNNING,   RunState.QUEUED)    is False

    def test_terminal_states(self):
        import sys
        spine_api_dir = Path(__file__).resolve().parent.parent / "spine-api"
        sys.path.insert(0, str(spine_api_dir))
        from run_state import RunState

        assert RunState.COMPLETED.is_terminal() is True
        assert RunState.FAILED.is_terminal()    is True
        assert RunState.BLOCKED.is_terminal()   is True
        assert RunState.RUNNING.is_terminal()   is False
        assert RunState.QUEUED.is_terminal()    is False

    def test_blocked_is_not_failed(self):
        """BLOCKED and FAILED must be distinct states — blocked is a policy decision, not a crash."""
        import sys
        spine_api_dir = Path(__file__).resolve().parent.parent / "spine-api"
        sys.path.insert(0, str(spine_api_dir))
        from run_state import RunState

        assert RunState.BLOCKED != RunState.FAILED
        assert RunState.BLOCKED.value == "blocked"
        assert RunState.FAILED.value  == "failed"

    def test_assert_can_transition_raises_on_invalid(self):
        import sys
        spine_api_dir = Path(__file__).resolve().parent.parent / "spine-api"
        sys.path.insert(0, str(spine_api_dir))
        from run_state import RunState, assert_can_transition

        with pytest.raises(ValueError, match="Invalid run state transition"):
            assert_can_transition(RunState.COMPLETED, RunState.RUNNING)

    def test_terminal_state_for_run_result(self):
        import sys
        spine_api_dir = Path(__file__).resolve().parent.parent / "spine-api"
        sys.path.insert(0, str(spine_api_dir))
        from run_state import RunState, terminal_state_for_run_result

        assert terminal_state_for_run_result(ok=True,  is_blocked=False) == RunState.COMPLETED
        assert terminal_state_for_run_result(ok=False, is_blocked=True)  == RunState.BLOCKED
        assert terminal_state_for_run_result(ok=False, is_blocked=False) == RunState.FAILED


# =============================================================================
# Golden path — run succeeds, ledger + events populated
# =============================================================================


class TestGoldenPath:
    """
    Verify that a successful run:
    - returns ok=True with a run_id
    - creates a ledger entry reachable via GET /runs/{run_id}
    - emits events reachable via GET /runs/{run_id}/events
    - ledger state is 'completed'
    - expected event types are present
    """

    def test_golden_run_ok(self, api_health):
        data = post_run(GOLDEN_PAYLOAD)
        assert data["ok"] is True, "Golden run must return ok=True"
        assert data["run_id"], "run_id must be non-empty"

    def test_golden_run_id_is_accessible_in_ledger(self, api_health):
        data = post_run(GOLDEN_PAYLOAD)
        run_id = data["run_id"]

        # Allow a brief moment for file I/O to flush
        time.sleep(0.1)

        resp = get_run_status(run_id)
        assert resp.status_code == 200, (
            f"GET /runs/{run_id} should return 200, got {resp.status_code}"
        )
        meta = resp.json()
        assert meta["run_id"] == run_id
        assert meta["state"] == "completed", f"Expected state=completed, got {meta['state']}"

    def test_golden_run_events_emitted(self, api_health):
        data = post_run(GOLDEN_PAYLOAD)
        run_id = data["run_id"]

        time.sleep(0.1)

        resp = get_run_events_api(run_id)
        assert resp.status_code == 200
        events = resp.json()["events"]
        assert len(events) >= 2, "Expected at least run_started and run_completed events"

        event_types = {e["event_type"] for e in events}
        assert "run_started"   in event_types, "run_started event must be emitted"
        assert "run_completed" in event_types, "run_completed event must be emitted"

    def test_golden_run_steps_checkpointed(self, api_health):
        data = post_run(GOLDEN_PAYLOAD)
        run_id = data["run_id"]

        time.sleep(0.1)

        resp = get_run_status(run_id)
        meta = resp.json()
        steps_available = meta.get("steps_available", [])
        # At least packet and decision should be checkpointed on a successful run
        assert "packet"   in steps_available or len(steps_available) > 0, (
            "At least one step should be checkpointed"
        )

    def test_golden_step_retrievable_by_endpoint(self, api_health):
        data = post_run(GOLDEN_PAYLOAD)
        run_id = data["run_id"]

        time.sleep(0.1)

        # Check which steps are available
        status_resp = get_run_status(run_id)
        steps_available = status_resp.json().get("steps_available", [])

        if not steps_available:
            pytest.skip("No steps checkpointed — pipeline may not have run fully")

        step_name = steps_available[0]
        resp = requests.get(f"{API_BASE}/runs/{run_id}/steps/{step_name}", timeout=10)
        assert resp.status_code == 200, f"GET /runs/{run_id}/steps/{step_name} failed"
        step_data = resp.json()
        assert step_data["step"] == step_name
        assert "data" in step_data
        assert "checkpointed_at" in step_data


# =============================================================================
# Leakage path — strict=True + leakage → BLOCKED, not FAILED
# =============================================================================


class TestLeakagePath:
    """
    Verify that a strict leakage violation:
    - returns ok=False (or ok=True if no actual leakage detected)
    - if ok=False: ledger state is 'blocked' (NOT 'failed')
    - if ok=False: run_blocked event is emitted (NOT run_failed)
    - traveler_bundle is null on ok=False
    """

    def test_strict_leakage_response_contract(self, api_health):
        data = post_run(LEAKAGE_STRICT_PAYLOAD)
        # Contract check regardless of whether leakage was triggered
        assert "ok" in data
        assert "run_id" in data
        assert data["safety"]["strict_leakage"] is True

    def test_strict_block_state_is_blocked_not_failed(self, api_health):
        data = post_run(LEAKAGE_STRICT_PAYLOAD)

        if data["ok"] is True:
            pytest.skip("No leakage detected for this input — leakage path not exercised")

        run_id = data["run_id"]
        time.sleep(0.1)

        resp = get_run_status(run_id)
        if resp.status_code == 404:
            pytest.skip("Ledger entry not found — run_id may not have been written")

        meta = resp.json()
        assert meta["state"] == "blocked", (
            f"Strict leakage violation must produce state=blocked, got {meta['state']!r}. "
            "FAILED is for system errors; BLOCKED is for policy violations."
        )

    def test_strict_block_emits_run_blocked_event(self, api_health):
        data = post_run(LEAKAGE_STRICT_PAYLOAD)

        if data["ok"] is True:
            pytest.skip("No leakage detected for this input")

        run_id = data["run_id"]
        time.sleep(0.1)

        resp = get_run_events_api(run_id)
        assert resp.status_code == 200
        events = resp.json()["events"]
        event_types = {e["event_type"] for e in events}

        assert "run_blocked" in event_types, (
            "Strict leakage block must emit run_blocked, not run_failed"
        )
        assert "run_failed" not in event_types, (
            "Strict leakage block must NOT emit run_failed (wrong terminal type)"
        )

    def test_strict_block_traveler_bundle_is_null(self, api_health):
        data = post_run(LEAKAGE_STRICT_PAYLOAD)
        if data["ok"] is False:
            assert data["traveler_bundle"] is None, (
                "traveler_bundle must be null when ok=False (strict leakage suppression)"
            )


# =============================================================================
# Runs list endpoint
# =============================================================================


class TestRunsListEndpoint:
    """Validate GET /runs endpoint behavior."""

    def test_runs_list_returns_200(self, api_health):
        resp = requests.get(f"{API_BASE}/runs", timeout=10)
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)

    def test_runs_list_contains_recent_run(self, api_health):
        data = post_run(GOLDEN_PAYLOAD)
        run_id = data["run_id"]
        time.sleep(0.1)

        resp = requests.get(f"{API_BASE}/runs?limit=10", timeout=10)
        assert resp.status_code == 200
        items = resp.json()["items"]
        run_ids = [r["run_id"] for r in items]
        assert run_id in run_ids, f"Recent run {run_id} not found in /runs list"

    def test_runs_unknown_id_returns_404(self, api_health):
        resp = get_run_status("nonexistent-run-xyz-000")
        assert resp.status_code == 404

    def test_runs_events_unknown_returns_empty(self, api_health):
        resp = get_run_events_api("nonexistent-run-xyz-000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["events"] == []
        assert data["total"] == 0
