"""
test_spine_api_contract.py — Smoke tests for async /run contract.

POST /run now returns RunAcceptedResponse and run artifacts are verified by polling
GET /runs/{run_id} and reading checkpointed steps.

Run with: pytest -m integration tests/test_spine_api_contract.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
import requests

from tests.helpers.run_polling import (
    TERMINAL_RUN_STATES,
    get_run_step,
    wait_for_terminal,
)

pytestmark = pytest.mark.integration

API_BASE = os.environ.get("TEST_SPINE_API_URL", "http://127.0.0.1:8000")

_TEST_USER = {
    "email": "test-contract@waypoint.example",
    "password": "TestPass123!",
    "name": "Contract Test",
}
_test_token: str | None = None

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


@pytest.fixture(scope="module")
def api_health():
    try:
        resp = requests.get(f"{API_BASE}/health", timeout=5)
        assert resp.status_code == 200, f"Health check failed: {resp.status_code}"
        return resp.json()
    except requests.ConnectionError:
        pytest.skip(f"spine_api not reachable at {API_BASE}")


@pytest.fixture(scope="module")
def sc_001_payload() -> dict:
    fixture_path = Path(__file__).resolve().parent.parent / "data/fixtures/scenarios/SC-001_clean_family_booking.json"
    if not fixture_path.exists():
        pytest.skip(f"Fixture not found: {fixture_path}")

    with fixture_path.open(encoding="utf-8") as f:
        raw = json.load(f)

    return {
        "raw_note": raw.get("input_note", ""),
        "owner_note": raw.get("owner_note", ""),
        "structured_json": raw.get("structured_input"),
        "itinerary_text": raw.get("itinerary_text", ""),
        "stage": raw.get("stage", "discovery"),
        "operating_mode": raw.get("operating_mode", "normal_intake"),
        "strict_leakage": False,
        "scenario_id": "SC-001",
    }


@pytest.fixture(scope="module")
def golden_terminal_status(api_health, sc_001_payload) -> dict:
    accepted = post_run(sc_001_payload)
    run_id = accepted["run_id"]
    assert accepted["state"] == "queued"
    return wait_for_terminal(API_BASE, run_id, _auth_headers())


class TestSpineApiHealth:
    def test_health_returns_ok(self, api_health):
        assert api_health["status"] == "ok"
        assert "version" in api_health


class TestAcceptedContract:
    def test_post_run_returns_accepted_shape(self, api_health, sc_001_payload):
        accepted = post_run(sc_001_payload)
        assert set(accepted.keys()) == {"run_id", "state"}
        assert isinstance(accepted["run_id"], str) and accepted["run_id"]
        assert accepted["state"] == "queued"


class TestRunStatusContract:
    def test_terminal_status_has_core_fields(self, golden_terminal_status):
        required = {"run_id", "state", "steps_completed", "events"}
        missing = required - set(golden_terminal_status.keys())
        assert not missing, f"Missing status fields: {missing}"

    def test_terminal_status_state_is_valid(self, golden_terminal_status):
        assert golden_terminal_status["state"] in TERMINAL_RUN_STATES

    def test_steps_and_events_are_lists(self, golden_terminal_status):
        assert isinstance(golden_terminal_status["steps_completed"], list)
        assert isinstance(golden_terminal_status["events"], list)


class TestSpineSectionsFromCheckpoints:
    def test_packet_checkpoint_is_readable_if_present(self, golden_terminal_status):
        run_id = golden_terminal_status["run_id"]
        if "packet" not in golden_terminal_status["steps_completed"]:
            pytest.skip("packet not checkpointed in this run")
        resp = get_run_step(API_BASE, run_id, "packet", _auth_headers())
        assert resp.status_code == 200
        payload = resp.json()
        assert payload["step"] == "packet"
        assert isinstance(payload.get("data"), dict)

    def test_decision_checkpoint_has_decision_state_if_present(self, golden_terminal_status):
        run_id = golden_terminal_status["run_id"]
        if "decision" not in golden_terminal_status["steps_completed"]:
            pytest.skip("decision not checkpointed in this run")
        resp = get_run_step(API_BASE, run_id, "decision", _auth_headers())
        assert resp.status_code == 200
        decision_data = resp.json().get("data") or {}
        assert "decision_state" in decision_data


class TestStrictLeakageMode:
    def test_strict_true_records_strict_mode_in_safety_step(self, api_health):
        payload = {
            "raw_note": "Family of 4 wants to visit Tokyo in July for 5 nights",
            "stage": "discovery",
            "operating_mode": "normal_intake",
            "strict_leakage": True,
        }
        accepted = post_run(payload)
        status = wait_for_terminal(API_BASE, accepted["run_id"], _auth_headers())
        if "safety" not in status["steps_completed"]:
            pytest.skip("safety not checkpointed in this run")

        safety_resp = get_run_step(API_BASE, status["run_id"], "safety", _auth_headers())
        assert safety_resp.status_code == 200
        safety_data = safety_resp.json().get("data") or {}
        assert safety_data.get("strict_leakage") is True
        assert isinstance(safety_data.get("leakage_errors", []), list)


class TestExecutionTiming:
    def test_total_ms_non_negative_when_terminal(self, golden_terminal_status):
        total_ms = golden_terminal_status.get("total_ms")
        if total_ms is None:
            pytest.skip("total_ms not set for this run")
        assert isinstance(total_ms, (int, float))
        assert total_ms >= 0
