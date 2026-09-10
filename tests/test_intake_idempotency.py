"""
Tests for intake-boundary idempotency (register N-1 / FINDINGS_REGISTER F-28 class).

Contract under test:
- `IdempotencyRegistry.try_acquire` is genuinely thread-safe (exactly one winner
  among concurrent acquirers of the same key).
- `POST /api/v1/inbound/parse`: an identical retry (same channel/text/customer
  payload, same agency) replays the original trip instead of minting a duplicate.
- A different payload mints a different trip (dedup is per-payload, not global).
- Registry semantics: FAILED allows retry, PENDING blocks concurrent execution.
- `process_inbound_traveler_message`: a retried webhook delivery replays the
  original reply instead of dispatching a duplicate.
"""

import os
import uuid
from concurrent.futures import ThreadPoolExecutor

os.environ["RUNNING_TESTS"] = "1"
if not os.environ.get("JWT_SECRET"):
    os.environ["JWT_SECRET"] = "test-jwt-secret-for-pytest-only-32byt"

import pytest

from spine_api import persistence
from src.agents.idempotency import IdempotencyRegistry, IdempotencyStatus
from spine_api.services.messaging_webhooks import InboundMessage, process_inbound_traveler_message

TripStore = persistence.TripStore

AGENCY = "test_agency_idem"


@pytest.fixture(autouse=True)
def idem_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def _headers() -> dict:
    return {"X-Agency-ID": AGENCY}


def test_registry_concurrent_acquire_single_winner():
    registry = IdempotencyRegistry()
    key = IdempotencyRegistry.generate_key("t", "action", {"x": 1})

    def attempt():
        acquired, _ = registry.try_acquire(key, trip_id="t", action_name="action", payload={"x": 1})
        return acquired

    with ThreadPoolExecutor(max_workers=16) as pool:
        results = list(pool.map(lambda _: attempt(), range(16)))

    assert results.count(True) == 1
    assert results.count(False) == 15


def test_registry_failed_allows_retry():
    registry = IdempotencyRegistry()
    key = IdempotencyRegistry.generate_key("t", "action", {"x": 2})
    acquired, first_record = registry.try_acquire(
        key, trip_id="t", action_name="action", payload={"x": 2}
    )
    assert acquired
    assert first_record is not None

    assert registry.mark_failed(
        key, "boom", fencing_token=first_record.fencing_token
    ) is True
    acquired_again, record = registry.try_acquire(key, trip_id="t", action_name="action", payload={"x": 2})
    assert acquired_again
    assert record is not None and record.status == IdempotencyStatus.PENDING


def test_registry_stale_owner_cannot_complete_reclaimed_row():
    """In-memory twin of the SQL fencing regression (misc-probes S8 / N-06-R1).

    After a TTL reclaim, the stale owner and the reclaimed owner are BOTH
    pending, so a status-only guard would let the stale owner's late
    completion overwrite the reclaimed owner's row. The generation
    (fencing) token must fence that write: the stale owner's mark no-ops.
    """
    registry = IdempotencyRegistry()
    key = IdempotencyRegistry.generate_key("t", "action", {"x": 9})
    acquired, stale_record = registry.try_acquire(
        key, trip_id="t", action_name="action", payload={"x": 9}
    )
    assert acquired
    assert stale_record is not None

    # Age the pending record past its TTL so the next acquire reclaims it,
    # exactly like the SQL backend's guarded-UPDATE reclaim.
    registry._records[key].created_at -= stale_record.ttl_seconds + 2
    acquired_again, fresh_record = registry.try_acquire(
        key, trip_id="t", action_name="action", payload={"x": 9}
    )
    assert acquired_again
    assert fresh_record is not None
    assert fresh_record.fencing_token != stale_record.fencing_token

    # Stale owner's late completion must NOT close the reclaimed owner's row.
    assert (
        registry.mark_completed(key, {"who": "stale-owner"}, fencing_token=stale_record.fencing_token)
        is False
    )
    record = registry._records[key]
    assert record.status == IdempotencyStatus.PENDING
    assert record.response_payload is None

    # The reclaimed owner completes normally.
    assert (
        registry.mark_completed(key, {"who": "reclaimed-owner"}, fencing_token=fresh_record.fencing_token)
        is True
    )
    assert registry._records[key].response_payload == {"who": "reclaimed-owner"}


def test_registry_completed_returns_cached():
    registry = IdempotencyRegistry()
    key = IdempotencyRegistry.generate_key("t", "action", {"x": 3})
    acquired, first_record = registry.try_acquire(
        key, trip_id="t", action_name="action", payload={"x": 3}
    )
    assert acquired
    assert first_record is not None
    assert registry.mark_completed(
        key,
        {"trip_id": "trip_cached"},
        fencing_token=first_record.fencing_token,
    ) is True

    acquired, record = registry.try_acquire(key, trip_id="t", action_name="action", payload={"x": 3})
    assert not acquired
    assert record is not None
    assert record.status == IdempotencyStatus.COMPLETED
    assert record.response_payload == {"trip_id": "trip_cached"}


def test_parse_retry_same_payload_replays_same_trip(session_client):
    payload = {
        "channel": "chrome_extension",
        "raw_text": f"Family of 4 to Tokyo for a week in November, budget 9000 USD. ID-{uuid.uuid4().hex[:8]}",
        "customer_name": "Retry Rider",
        "customer_contact": "+1-555-0177",
        "strict_leakage": False,
    }

    first = session_client.post("/api/v1/inbound/parse", json=payload, headers=_headers())
    assert first.status_code == 200
    first_trip_id = first.json()["trip_id"]

    retry = session_client.post("/api/v1/inbound/parse", json=payload, headers=_headers())
    assert retry.status_code == 200
    assert retry.json()["trip_id"] == first_trip_id  # replayed, not a new trip
    assert TripStore.get_trip(first_trip_id) is not None


def test_parse_different_payload_mints_new_trip(session_client):
    base = {
        "channel": "chrome_extension",
        "customer_name": "Distinct Dawn",
        "customer_contact": "+1-555-0178",
        "strict_leakage": False,
    }
    a = session_client.post(
        "/api/v1/inbound/parse",
        json={**base, "raw_text": f"Trip to Lisbon in May, 2 adults. ID-{uuid.uuid4().hex[:8]}"},
        headers=_headers(),
    )
    b = session_client.post(
        "/api/v1/inbound/parse",
        json={**base, "raw_text": f"Trip to Lisbon in May, 2 adults. ID-{uuid.uuid4().hex[:8]}"},
        headers=_headers(),
    )
    assert a.status_code == 200 and b.status_code == 200
    assert a.json()["trip_id"] != b.json()["trip_id"]


def test_parse_same_text_different_agency_mints_new_trip(session_client):
    raw = f"Honeymoon in Bali for 10 days in June. ID-{uuid.uuid4().hex[:8]}"
    a = session_client.post("/api/v1/inbound/parse", json={"channel": "email", "raw_text": raw}, headers={"X-Agency-ID": "agency_x"})
    b = session_client.post("/api/v1/inbound/parse", json={"channel": "email", "raw_text": raw}, headers={"X-Agency-ID": "agency_y"})
    assert a.status_code == 200 and b.status_code == 200
    assert a.json()["trip_id"] != b.json()["trip_id"]


def test_webhook_retry_replays_same_reply():
    msg = InboundMessage(
        message_id=f"SM-{uuid.uuid4().hex[:10]}",
        channel="whatsapp",
        from_phone="whatsapp:+15550001111",
        to_phone="+15550002222",
        body="what gate is my flight from",
    )

    first = process_inbound_traveler_message(msg)
    retry = process_inbound_traveler_message(msg)

    assert first.action_taken == retry.action_taken
    assert first.reply_text == retry.reply_text
    assert retry.reply_to_message_id == msg.message_id


def test_webhook_different_message_not_suppressed():
    shared = {"channel": "sms", "from_phone": "+15550003333", "to_phone": "+15550004444", "body": "hello there"}
    a = process_inbound_traveler_message(InboundMessage(message_id=f"SM-{uuid.uuid4().hex[:10]}", **shared))
    b = process_inbound_traveler_message(InboundMessage(message_id=f"SM-{uuid.uuid4().hex[:10]}", **shared))

    assert a.action_taken == b.action_taken
    assert a.reply_to_message_id != b.reply_to_message_id
    assert a.action_taken != "duplicate_suppressed"
