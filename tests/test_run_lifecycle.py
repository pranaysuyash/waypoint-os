"""
test_run_lifecycle.py — Integration tests for async run lifecycle.

Requires a live spine_api instance. Skips automatically if API is unreachable.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import pytest
import requests

from tests.helpers.run_polling import (
    TERMINAL_RUN_STATES,
    get_run_events,
    get_run_status,
    get_run_step,
    wait_for_terminal,
)

API_BASE = os.environ.get("TEST_SPINE_API_URL", "http://127.0.0.1:8000")

_TEST_USER = {
    "email": "test-integration@waypoint.example",
    "password": "TestPass123!",
    "name": "Integration Test",
}
_test_token: str | None = None


pytestmark = pytest.mark.integration


def _ensure_test_user() -> str:
    global _test_token
    if _test_token:
        return _test_token

    requests.post(f"{API_BASE}/api/auth/signup", json=_TEST_USER, timeout=10)
    resp = requests.post(
        f"{API_BASE}/api/auth/login",
        json={"email": _TEST_USER["email"], "password": _TEST_USER["password"]},
        timeout=10,
    )
    assert resp.status_code == 200, f"Login failed: {resp.status_code} {resp.text}"
    token = resp.cookies.get("access_token")
    assert token, "Login did not set access_token cookie"
    _test_token = token
    return _test_token


def _auth_headers() -> dict:
    return {"Authorization": f"Bearer {_ensure_test_user()}"}


def post_run(payload: dict, timeout: int = 30) -> dict:
    resp = requests.post(f"{API_BASE}/run", json=payload, timeout=timeout, headers=_auth_headers())
    assert resp.status_code == 200, f"POST /run failed: {resp.status_code} {resp.text}"
    return resp.json()


def get_status(run_id: str):
    return get_run_status(API_BASE, run_id, _auth_headers())


def get_events(run_id: str):
    return get_run_events(API_BASE, run_id, _auth_headers())


def get_step(run_id: str, step_name: str):
    return get_run_step(API_BASE, run_id, step_name, _auth_headers())


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
    accepted = post_run(GOLDEN_PAYLOAD)
    assert accepted["state"] == "queued"
    status = wait_for_terminal(API_BASE, accepted["run_id"], _auth_headers())
    return {"accepted": accepted, "status": status}


class TestGoldenPath:
    def test_golden_accepted_has_run_id(self, golden_run):
        assert golden_run["accepted"]["run_id"]

    def test_golden_reaches_terminal_state(self, golden_run):
        assert golden_run["status"]["state"] in TERMINAL_RUN_STATES

    def test_golden_has_run_started_event(self, golden_run):
        events = get_events(golden_run["accepted"]["run_id"]).json()["events"]
        types = [e["event_type"] for e in events]
        assert "run_started" in types

    def test_golden_terminal_event_present(self, golden_run):
        events = get_events(golden_run["accepted"]["run_id"]).json()["events"]
        terminal_types = {"run_completed", "run_failed", "run_blocked"}
        assert any(t in terminal_types for t in [e["event_type"] for e in events])

    def test_golden_has_per_stage_events(self, golden_run):
        events = get_events(golden_run["accepted"]["run_id"]).json()["events"]
        types = [e["event_type"] for e in events]
        assert "pipeline_stage_entered" in types
        assert "pipeline_stage_completed" in types


class TestStepLedger:
    def test_steps_available_in_status(self, golden_run):
        steps = golden_run["status"].get("steps_completed", [])
        assert len(steps) > 0

    def test_packet_step_retrievable(self, golden_run):
        steps = golden_run["status"].get("steps_completed", [])
        if "packet" not in steps:
            pytest.skip("packet not checkpointed in this run")
        r = get_step(golden_run["accepted"]["run_id"], "packet")
        assert r.status_code == 200
        data = r.json()
        assert data["step"] == "packet"
        assert "data" in data
        assert "checkpointed_at" in data

    def test_step_read_is_deterministic(self, golden_run):
        steps = golden_run["status"].get("steps_completed", [])
        if not steps:
            pytest.skip("No steps available")
        step_name = steps[0]

        r1 = get_step(golden_run["accepted"]["run_id"], step_name).json()
        r2 = get_step(golden_run["accepted"]["run_id"], step_name).json()
        h1 = hashlib.sha256(str(sorted(r1.items())).encode()).hexdigest()
        h2 = hashlib.sha256(str(sorted(r2.items())).encode()).hexdigest()
        assert h1 == h2


class TestConsistencyInvariant:
    def test_run_id_consistent_across_status_and_events(self, golden_run):
        run_id = golden_run["accepted"]["run_id"]
        assert golden_run["status"]["run_id"] == run_id
        events = get_events(run_id).json()["events"]
        for event in events:
            assert event["run_id"] == run_id

    def test_event_sequence_starts_with_run_started(self, golden_run):
        events = get_events(golden_run["accepted"]["run_id"]).json()["events"]
        assert events[0]["event_type"] == "run_started"

    def test_event_sequence_ends_with_terminal_event(self, golden_run):
        events = get_events(golden_run["accepted"]["run_id"]).json()["events"]
        terminal_types = {"run_completed", "run_failed", "run_blocked"}
        assert events[-1]["event_type"] in terminal_types


class TestIdempotencyAndRetry:
    def test_same_payload_creates_different_run_ids(self, api_health):
        r1 = post_run(GOLDEN_PAYLOAD)
        r2 = post_run(GOLDEN_PAYLOAD)
        assert r1["run_id"] != r2["run_id"]

    def test_both_retry_runs_appear_in_ledger(self, api_health):
        r1 = post_run(GOLDEN_PAYLOAD)
        r2 = post_run(GOLDEN_PAYLOAD)
        s1 = wait_for_terminal(API_BASE, r1["run_id"], _auth_headers())
        s2 = wait_for_terminal(API_BASE, r2["run_id"], _auth_headers())
        assert s1["state"] in TERMINAL_RUN_STATES
        assert s2["state"] in TERMINAL_RUN_STATES


class TestEndpointEdgeCases:
    def test_unknown_run_id_returns_404(self, api_health):
        resp = get_status("totally-nonexistent-000")
        assert resp.status_code == 404

    def test_unknown_run_events_returns_404(self, api_health):
        resp = get_events("totally-nonexistent-000")
        assert resp.status_code == 404

    def test_unknown_step_returns_404(self, api_health):
        resp = get_step("totally-nonexistent-000", "packet")
        assert resp.status_code == 404

    def test_unknown_step_name_for_known_run_returns_404(self, api_health):
        data = post_run(GOLDEN_PAYLOAD)
        wait_for_terminal(API_BASE, data["run_id"], _auth_headers())
        resp = get_step(data["run_id"], "notreal_stage")
        assert resp.status_code == 404

    def test_runs_list_returns_200(self, api_health):
        resp = requests.get(f"{API_BASE}/runs", timeout=10, headers=_auth_headers())
        assert resp.status_code == 200
        body = resp.json()
        assert "items" in body and isinstance(body["items"], list)
        assert "total" in body


class TestLeakagePath:
    @pytest.fixture(scope="class")
    def leakage_run(self, api_health):
        accepted = post_run(LEAKAGE_STRICT_PAYLOAD)
        status = wait_for_terminal(API_BASE, accepted["run_id"], _auth_headers())
        return {"accepted": accepted, "status": status}

    def test_blocked_event_consistency_when_blocked(self, leakage_run):
        if leakage_run["status"]["state"] != "blocked":
            pytest.skip("No strict leakage block triggered in this run")
        run_id = leakage_run["accepted"]["run_id"]
        events = get_events(run_id).json()["events"]
        types = {e["event_type"] for e in events}
        assert "run_blocked" in types
        assert "run_failed" not in types


class TestWriteFailureIsolation:
    def test_golden_run_accepts_without_500(self, api_health):
        resp = requests.post(f"{API_BASE}/run", json=GOLDEN_PAYLOAD, timeout=30, headers=_auth_headers())
        assert resp.status_code == 200
        body = resp.json()
        assert "run_id" in body and "state" in body

    def test_server_source_wraps_ledger_writes(self):
        server_path = Path(__file__).resolve().parent.parent / "spine_api" / "server.py"
        source = server_path.read_text(encoding="utf-8")
        assert "Wave A: result step checkpointing failed" in source
        assert "Wave A: ledger complete failed" in source
        assert "Wave A: block ledger failed" in source
        assert "Wave A: fail ledger failed" in source
