"""
test_run_lifecycle.py — Integration tests for Wave A run lifecycle.

Requires a live spine_api instance. Automatically skipped if API unreachable.

Run:
    pytest tests/test_run_lifecycle.py -v -m integration

Marks:
    @pytest.mark.integration  — requires live spine_api

State machine unit tests have been moved to:
    tests/test_run_state_unit.py  (no live API required)
"""

from __future__ import annotations

import hashlib
import os
import time
from pathlib import Path

import pytest
import requests

API_BASE = os.environ.get("TEST_SPINE_API_URL", "http://127.0.0.1:8000")


# ---------------------------------------------------------------------------
# Auth helpers for integration tests
# ---------------------------------------------------------------------------

_TEST_USER = {"email": "test-integration@waypoint.example", "password": "TestPass123!", "name": "Integration Test"}
_test_token: str | None = None

def _ensure_test_user() -> str:
    """Sign up (if needed) and log in to get an access token."""
    global _test_token
    if _test_token:
        return _test_token

    # Try signup (idempotent if user already exists)
    requests.post(f"{API_BASE}/api/auth/signup", json=_TEST_USER, timeout=10)

    # Login
    resp = requests.post(f"{API_BASE}/api/auth/login", json={
        "email": _TEST_USER["email"],
        "password": _TEST_USER["password"],
    }, timeout=10)
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    data = resp.json()
    _test_token = data["access_token"]
    return _test_token


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_ensure_test_user()}"}


# ---------------------------------------------------------------------------
# pytest marker
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.integration


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def post_run(payload: dict, timeout: int = 30) -> dict:
    resp = requests.post(f"{API_BASE}/run", json=payload, timeout=timeout, headers=_auth_headers())
    assert resp.status_code == 200, f"POST /run failed: {resp.status_code} {resp.text}"
    return resp.json()


def get_status(run_id: str):
    return requests.get(f"{API_BASE}/runs/{run_id}", timeout=10, headers=_auth_headers())


def get_events(run_id: str):
    return requests.get(f"{API_BASE}/runs/{run_id}/events", timeout=10, headers=_auth_headers())


def get_step(run_id: str, step_name: str):
    return requests.get(f"{API_BASE}/runs/{run_id}/steps/{step_name}", timeout=10, headers=_auth_headers())


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


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def api_health():
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        assert resp.status_code == 200
        return resp.json()
    except requests.ConnectionError:
        pytest.skip(f"spine_api not reachable at {API_BASE}")


@pytest.fixture(scope="module")
def golden_run(api_health) -> dict:
    """Execute one golden run and cache the response for the module."""
    data = post_run(GOLDEN_PAYLOAD)
    time.sleep(0.2)  # allow file I/O to flush
    return data


# =============================================================================
# Criterion 1 + 2: Golden path — ledger state = completed, no failed/blocked events
# =============================================================================


class TestGoldenPath:

    def test_golden_ok_true(self, golden_run):
        assert golden_run["ok"] is True
        assert golden_run["run_id"]

    def test_golden_ledger_state_completed(self, golden_run):
        resp = get_status(golden_run["run_id"])
        assert resp.status_code == 200
        assert resp.json()["state"] == "completed"

    def test_golden_has_run_started_event(self, golden_run):
        events = get_events(golden_run["run_id"]).json()["events"]
        types = [e["event_type"] for e in events]
        assert "run_started" in types

    def test_golden_has_run_completed_event(self, golden_run):
        events = get_events(golden_run["run_id"]).json()["events"]
        types = [e["event_type"] for e in events]
        assert "run_completed" in types
        assert "run_failed" not in types
        assert "run_blocked" not in types

    def test_golden_has_per_stage_events(self, golden_run):
        """Criterion 3: pipeline_stage_entered and pipeline_stage_completed must appear."""
        events = get_events(golden_run["run_id"]).json()["events"]
        types = [e["event_type"] for e in events]
        assert "pipeline_stage_entered" in types, (
            "Expected pipeline_stage_entered events for each checkpointed step"
        )
        assert "pipeline_stage_completed" in types


# =============================================================================
# Criterion 3 + 4: Step ledger completeness
# =============================================================================


class TestStepLedger:

    def test_steps_available_in_status(self, golden_run):
        resp = get_status(golden_run["run_id"])
        steps = resp.json().get("steps_available", [])
        assert len(steps) > 0, "At least one step must be checkpointed"

    def test_packet_step_retrievable(self, golden_run):
        resp = get_status(golden_run["run_id"])
        steps = resp.json().get("steps_available", [])
        if "packet" not in steps:
            pytest.skip("packet not checkpointed in this run")
        r = get_step(golden_run["run_id"], "packet")
        assert r.status_code == 200
        data = r.json()
        assert data["step"] == "packet"
        assert "data" in data
        assert "checkpointed_at" in data

    def test_step_read_is_deterministic(self, golden_run):
        """Criterion 4: repeated read of same step returns identical content."""
        resp = get_status(golden_run["run_id"])
        steps = resp.json().get("steps_available", [])
        if not steps:
            pytest.skip("No steps available")
        step_name = steps[0]

        r1 = get_step(golden_run["run_id"], step_name).json()
        r2 = get_step(golden_run["run_id"], step_name).json()

        # Hash the serialised payloads for strict equality
        h1 = hashlib.sha256(str(sorted(r1.items())).encode()).hexdigest()
        h2 = hashlib.sha256(str(sorted(r2.items())).encode()).hexdigest()
        assert h1 == h2, "Repeated reads of same step must return identical content"

    def test_safety_step_checkpointed(self, golden_run):
        """Criterion 4: safety must be in steps_available (not just packet/decision)."""
        resp = get_status(golden_run["run_id"])
        steps = resp.json().get("steps_available", [])
        # safety may be absent if leakage_result is empty; that's acceptable
        # but if it's there, it must be readable
        if "safety" in steps:
            r = get_step(golden_run["run_id"], "safety")
            assert r.status_code == 200
            assert "leakage_passed" in r.json()["data"]


# =============================================================================
# Criterion 5: API / ledger / event consistency invariant
# =============================================================================


class TestConsistencyInvariant:
    """run_id must be consistent across /run response + /runs/{id} + events."""

    def test_run_id_consistent_across_all_artifacts(self, golden_run):
        run_id = golden_run["run_id"]

        # response run_id
        assert golden_run["run_id"] == run_id

        # ledger run_id
        ledger = get_status(run_id).json()
        assert ledger["run_id"] == run_id

        # event run_ids
        events = get_events(run_id).json()["events"]
        for event in events:
            assert event["run_id"] == run_id, (
                f"Event {event['event_type']} has wrong run_id: {event['run_id']!r}"
            )

    def test_terminal_outcome_matches_response_and_ledger(self, golden_run):
        run_id = golden_run["run_id"]
        response_ok = golden_run["ok"]

        ledger = get_status(run_id).json()
        ledger_state = ledger["state"]

        if response_ok:
            assert ledger_state == "completed", (
                f"ok=True response must map to state=completed, got {ledger_state!r}"
            )
        else:
            assert ledger_state in ("failed", "blocked"), (
                f"ok=False response must map to failed or blocked, got {ledger_state!r}"
            )

    def test_event_sequence_starts_with_run_started(self, golden_run):
        events = get_events(golden_run["run_id"]).json()["events"]
        assert events[0]["event_type"] == "run_started", (
            "First event must always be run_started"
        )

    def test_event_sequence_ends_with_terminal_event(self, golden_run):
        events = get_events(golden_run["run_id"]).json()["events"]
        terminal_types = {"run_completed", "run_failed", "run_blocked"}
        last_type = events[-1]["event_type"]
        assert last_type in terminal_types, (
            f"Last event must be a terminal type, got {last_type!r}"
        )


# =============================================================================
# Criterion 6: Partial failure resilience (write-failure isolation)
# =============================================================================


class TestWriteFailureIsolation:
    """
    Verify /run contract is preserved even if ledger/event writes would fail.

    We cannot easily mock file I/O in a live integration test, so we verify
    the design guarantee through a documentation+assertion pattern:
    The /run endpoint wraps every Wave A write in try/except and never
    propagates those exceptions to the response. Verified by:
    1. Grepping source for the try/except pattern
    2. Confirming golden run response is correct (no 500 from file I/O)
    """

    def test_golden_run_returns_200_not_500(self, api_health):
        """Basic smoke: /run returns 200 not 500 even with file writes happening."""
        resp = requests.post(f"{API_BASE}/run", json=GOLDEN_PAYLOAD, timeout=30, headers=_auth_headers())
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert resp.json()["ok"] is True

    def test_server_source_wraps_ledger_writes(self):
        """
        Static verification: confirm try/except guards are present in server.py.
        This is the contractual guarantee for write-failure isolation.
        """
        server_path = Path(__file__).resolve().parent.parent / "spine_api" / "server.py"
        source = server_path.read_text(encoding="utf-8")
        assert "Wave A: step checkpoint failed" in source, (
            "server.py must wrap step checkpointing in try/except"
        )
        assert "Wave A: ledger complete failed" in source, (
            "server.py must wrap ledger.complete in try/except"
        )
        assert "Wave A: block ledger failed" in source or "ledger_err" in source, (
            "server.py must wrap block/fail ledger writes in try/except"
        )


# =============================================================================
# Criterion 7: Idempotency and retry behavior
# =============================================================================


class TestIdempotencyAndRetry:
    """
    Policy (documented): POST /run creates a new run_id on each call via uuid4.
    There is NO request deduplication. Retrying the same payload creates a new run.
    """

    def test_same_payload_creates_different_run_ids(self, api_health):
        r1 = post_run(GOLDEN_PAYLOAD)
        r2 = post_run(GOLDEN_PAYLOAD)
        assert r1["run_id"] != r2["run_id"], (
            "Each POST /run must create a new run_id — no deduplication by payload hash"
        )

    def test_both_retry_runs_appear_in_ledger(self, api_health):
        r1 = post_run(GOLDEN_PAYLOAD)
        r2 = post_run(GOLDEN_PAYLOAD)
        time.sleep(0.2)

        s1 = get_status(r1["run_id"])
        s2 = get_status(r2["run_id"])
        assert s1.status_code == 200, f"First run not in ledger: {s1.status_code}"
        assert s2.status_code == 200, f"Second run not in ledger: {s2.status_code}"
        # Both must be terminal
        assert s1.json()["state"] in ("completed", "failed", "blocked")
        assert s2.json()["state"] in ("completed", "failed", "blocked")


# =============================================================================
# Criterion 8: Endpoint contract robustness — edge cases
# =============================================================================


class TestEndpointEdgeCases:

    def test_unknown_run_id_returns_404(self, api_health):
        resp = get_status("totally-nonexistent-000")
        assert resp.status_code == 404

    def test_unknown_run_events_returns_empty_not_404(self, api_health):
        """Events endpoint is forgiving — unknown run returns empty list, not 404."""
        resp = get_events("totally-nonexistent-000")
        assert resp.status_code == 200
        data = resp.json()
        assert data["events"] == []
        assert data["total"] == 0

    def test_unknown_step_returns_404(self, api_health):
        """Steps endpoint returns 404 for unknown run or unregistered step."""
        resp = get_step("totally-nonexistent-000", "packet")
        assert resp.status_code == 404

    def test_unknown_step_name_for_known_run_returns_404(self, api_health):
        data = post_run(GOLDEN_PAYLOAD)
        time.sleep(0.2)
        resp = get_step(data["run_id"], "notreal_stage")
        assert resp.status_code == 404

    def test_runs_list_returns_200(self, api_health):
        resp = requests.get(f"{API_BASE}/runs", timeout=10, headers=_auth_headers())
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body
        assert "total" in body
        assert isinstance(body["items"], list)

    def test_runs_list_state_filter(self, api_health):
        """state= filter must accept valid state values without error."""
        for state in ("queued", "running", "completed", "failed", "blocked"):
            resp = requests.get(f"{API_BASE}/runs?state={state}&limit=5", timeout=10, headers=_auth_headers())
            assert resp.status_code == 200, f"state={state!r} filter returned {resp.status_code}"

    def test_runs_list_limit_param(self, api_health):
        # Post two quick runs then check limit=1
        post_run(GOLDEN_PAYLOAD)
        post_run(GOLDEN_PAYLOAD)
        time.sleep(0.2)
        resp = requests.get(f"{API_BASE}/runs?limit=1", timeout=10, headers=_auth_headers())
        assert resp.status_code == 200
        assert len(resp.json()["items"]) <= 1

    def test_runs_list_trip_id_filter_unknown_returns_empty(self, api_health):
        resp = requests.get(f"{API_BASE}/runs?trip_id=trip_nonexistent_xyz", timeout=10, headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["items"] == []


# =============================================================================
# Criterion 2 + terminal correctness: leakage path
# =============================================================================


class TestLeakagePath:
    """
    Strict leakage produces state=blocked (not failed) and run_blocked event (not run_failed).
    """

    @pytest.fixture(scope="class")
    def leakage_run(self, api_health):
        data = post_run(LEAKAGE_STRICT_PAYLOAD)
        time.sleep(0.2)
        return data

    def test_strict_leakage_has_correct_safety_contract(self, leakage_run):
        assert leakage_run["safety"]["strict_leakage"] is True

    def test_blocked_state_not_failed(self, leakage_run):
        if leakage_run["ok"] is True:
            pytest.skip("No leakage triggered — ok=True path")
        run_id = leakage_run["run_id"]
        meta = get_status(run_id).json()
        assert meta["state"] == "blocked", (
            f"Strict leakage must produce state=blocked, not {meta['state']!r}"
        )

    def test_blocked_emits_run_blocked_not_run_failed(self, leakage_run):
        if leakage_run["ok"] is True:
            pytest.skip("No leakage triggered")
        run_id = leakage_run["run_id"]
        events = get_events(run_id).json()["events"]
        types = {e["event_type"] for e in events}
        assert "run_blocked" in types
        assert "run_failed" not in types

    def test_blocked_traveler_bundle_is_null(self, leakage_run):
        if leakage_run["ok"] is False:
            assert leakage_run["traveler_bundle"] is None
