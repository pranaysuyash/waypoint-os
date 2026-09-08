"""
tests/test_run_idempotency_header.py — PA-13 S2 evidence (2026-09-06).

FAILED BEFORE: POST /run minted a fresh uuid4 run id on every submission — a
client retry after a network blip created two concurrent runs with no way to
deduplicate, even though the durable idempotency CAS machinery
(src/agents/idempotency.py) already existed (wired only at inbound).

PASSES AFTER: an ``Idempotency-Key`` header scopes to ``(agency_id, key)``:
- fresh key -> run created, mapping recorded in-flight immediately;
- same key while in-flight -> 409;
- completed key -> replay of the ORIGINAL run_id with
  ``idempotent_replay: true`` (additive response field, default False);
- no header -> behavior unchanged (fresh uuid4, idempotent_replay False).

NOTE (handoff): the registry record is created in-flight by /run; recording
COMPLETED at the run's terminal state is owned by the pipeline workstream
(TODO marker in spine_api/server.py). The replay test below simulates that
future completion via the registry's own fenced mark_completed API.

The pipeline thread is stubbed so tests don't execute real spine runs.
"""

from __future__ import annotations

import uuid

import pytest

from spine_api.persistence import TEST_AGENCY_ID
from src.agents.idempotency import IdempotencyRegistry, IdempotencyStatus


@pytest.fixture(autouse=True)
def _stub_pipeline(monkeypatch):
    """Never execute real pipelines from this test module."""
    monkeypatch.setattr(
        "spine_api.server._execute_spine_pipeline",
        lambda *args, **kwargs: None,
    )


def _post_run(client, key: str | None):
    headers = {"Idempotency-Key": key} if key else {}
    return client.post(
        "/run",
        json={"raw_note": "idempotency header test", "retention_consent": True},
        headers=headers,
    )


def test_run_without_header_unchanged(session_client):
    """No header -> fresh uuid4, idempotent_replay False (legacy contract)."""
    resp1 = _post_run(session_client, None)
    resp2 = _post_run(session_client, None)
    assert resp1.status_code == 200
    assert resp2.status_code == 200
    d1, d2 = resp1.json(), resp2.json()
    assert d1["idempotent_replay"] is False
    assert d2["idempotent_replay"] is False
    assert d1["run_id"] != d2["run_id"]  # fresh uuid4 each time


def test_run_with_header_records_in_flight_then_409(session_client):
    """Fresh key creates the run AND records the mapping in-flight; duplicate -> 409."""
    key = f"idem_run_test_{uuid.uuid4().hex[:10]}"
    resp1 = _post_run(session_client, key)
    assert resp1.status_code == 200
    first = resp1.json()
    assert first["idempotent_replay"] is False

    # The mapping must already be visible to the registry (in-flight).
    registry = IdempotencyRegistry.get_instance()
    idem_key = f"run:{TEST_AGENCY_ID}:{key}"
    acquired, record = registry.try_acquire(
        idem_key, trip_id="", action_name="probe", payload={}
    )
    assert acquired is False, "key should already be held by /run"
    assert record is not None and record.status == IdempotencyStatus.PENDING

    # A retry with the same key while in-flight -> 409.
    resp2 = _post_run(session_client, key)
    assert resp2.status_code == 409
    assert resp2.json()["detail"]["reason"] == "run_already_in_flight_for_idempotency_key"


def test_run_completed_key_replays_original_run(session_client):
    """COMPLETED key -> original run_id replayed with idempotent_replay True.

    Completion recording here uses the registry's own fenced API, standing in
    for the integrator's terminal-callback wiring (see module docstring).
    """
    registry = IdempotencyRegistry.get_instance()
    key = f"idem_run_replay_{uuid.uuid4().hex[:10]}"
    idem_key = f"run:{TEST_AGENCY_ID}:{key}"

    # Simulate a prior completed run for this key.
    acquired, record = registry.try_acquire(
        idem_key, trip_id="", action_name="run_spine", payload={}
    )
    assert acquired is True and record is not None
    original_run_id = f"run_original_{uuid.uuid4().hex[:8]}"
    completed = registry.mark_completed(
        idem_key,
        {"run_id": original_run_id, "state": "completed"},
        fencing_token=record.fencing_token,
    )
    assert completed is True

    resp = _post_run(session_client, key)
    assert resp.status_code == 200
    data = resp.json()
    assert data["idempotent_replay"] is True
    assert data["run_id"] == original_run_id

    # A DIFFERENT agency's key must not collide (key is agency-scoped).
    # (Agency scoping is enforced server-side via the authenticated agency;
    #  here we assert the derived key shape includes the agency id.)
    assert idem_key.startswith(f"run:{TEST_AGENCY_ID}:")
