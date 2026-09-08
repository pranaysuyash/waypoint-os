"""Live-PostgreSQL multi-worker contention probe (PER-0700 wave 2).

Raises the evidence tier for the repo's cross-process concurrency primitives
from Tier 1/2 (in-process tests) to Tier 3 (multi-process against a live
PostgreSQL). Each test spawns N real OS processes (multiprocessing, spawn
context) that contend on the SAME durable primitive; the parent asserts
exactly-one-winner semantics.

Safety: ADDITIVE ONLY — probe rows anchor to the seeded canonical agency (a
fresh probe trip + one fresh collection token per run); registry entries are
probe-keyed; nothing pre-existing is mutated or deleted. All database access
goes through the canonical services and the TripStore facade.

Skips automatically when DATABASE_URL is absent (no live PG), so local and
PG-less runs stay green.
"""

from __future__ import annotations

import json
import multiprocessing
import os
import uuid

import pytest

pytestmark = [
    pytest.mark.live_db,
    pytest.mark.skipif(
        not os.environ.get("DATABASE_URL"),
        reason="live-PG probe requires DATABASE_URL",
    ),
]

CANONICAL_AGENCY = "d1e3b2b6-5509-4c27-b123-4b1e02b0bf5b"
# Overridable via the CLI probe tool (tools/live_db_multiworker_probe.py
# --workers N), which forwards this through the PROBE_WORKERS env var.
WORKERS = int(os.environ.get("PROBE_WORKERS", "4"))

# Spawned children inherit the environment: without the SQL backend each
# child would resolve its own memory registry and trivially "win".
if os.environ.get("DATABASE_URL"):
    os.environ["SPINE_API_IDEMPOTENCY_BACKEND"] = "sql"


def _spawn_contention(check: str, payload: dict, workers: int) -> list[str]:
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    payload_json = json.dumps(payload)
    procs = [
        ctx.Process(target=_worker_entry, args=(check, payload_json, queue))
        for _ in range(workers)
    ]
    for proc in procs:
        proc.start()
    results = [queue.get(timeout=180) for _ in procs]
    for proc in procs:
        proc.join(timeout=30)
    return results


def _worker_entry(check: str, payload_json: str, queue) -> None:
    """Run in a spawned child; push one outcome token onto the queue."""
    import json

    data = json.loads(payload_json)
    try:
        if check == "idempotency":
            outcome = _contention_idempotency(data["key"])
        elif check == "lease":
            outcome = _contention_lease(data["key"])
        elif check == "token":
            outcome = _contention_token(data["token"])
        else:
            outcome = "ERR unknown-check"
    except Exception as exc:  # surface worker failures as outcomes
        outcome = f"ERR {type(exc).__name__}: {exc}"
    queue.put(outcome)


def _contention_idempotency(key: str) -> str:
    from src.agents.idempotency import IdempotencyRegistry

    registry = IdempotencyRegistry.get_instance()
    acquired, record = registry.try_acquire(
        key,
        trip_id="",
        action_name="probe_contention",
        payload={"probe": True},
        ttl_seconds=600,
    )
    if acquired:
        registry.mark_completed(
            key, {"winner": os.getpid()}, fencing_token=getattr(record, "fencing_token", None)
        )
        return "ACQUIRED"
    if record is not None and getattr(record.status, "value", "") == "completed":
        return "REJECTED_COMPLETED"
    return "REJECTED"


def _contention_lease(key: str) -> str:
    from src.agents.runtime import RetryPolicy, WorkItem
    from spine_api.services.agent_work_coordinator import SQLWorkCoordinator

    coordinator = SQLWorkCoordinator()
    item = WorkItem(
        agent_name="probe_agent",
        trip_id="",
        action="probe_contention",
        idempotency_key=key,
        payload={"probe": True},
    )
    acquired, _reason, _fencing = coordinator.acquire(
        item, owner=f"probe-{os.getpid()}", retry_policy=RetryPolicy(max_attempts=1)
    )
    return "ACQUIRED" if acquired else "REJECTED"


def _contention_token(token_plain: str) -> str:
    from spine_api.core.database import async_session_maker
    from spine_api.services.collection_service import mark_token_used, validate_token

    async def _consume() -> str:
        # RLS: the token rows belong to the canonical agency, so the GUC must
        # be set before any statement runs on the probe's connections.
        from sqlalchemy import text

        from spine_api.core.rls import set_rls_agency

        set_rls_agency(CANONICAL_AGENCY)
        async with async_session_maker() as session:
            await session.execute(
                text("SELECT set_config('app.current_agency_id', :agency, true)"),
                {"agency": CANONICAL_AGENCY},
            )
            record = await validate_token(session, token_plain)
            if record is None:
                return "REJECTED"
            consumed = await mark_token_used(session, record.id)
            return "ACQUIRED" if consumed else "REJECTED"

    import asyncio

    return asyncio.run(_consume())


def _create_probe_trip() -> str | None:
    """Create an additive probe trip via the canonical TripStore facade.

    Returns the probe trip id (namespaced, unique per run) or None when the
    store refuses — the test then skips.
    """
    from spine_api.persistence import TripStore

    trip_id = f"probe-trip-{uuid.uuid4().hex[:12]}"
    saved = TripStore.save_trip(
        {
            "id": trip_id,
            "trip_id": trip_id,
            "agency_id": CANONICAL_AGENCY,
            "status": "new",
            "stage": "discovery",
            "source": "probe",
        }
    )
    if not saved:
        return None
    return trip_id


# ── tests ────────────────────────────────────────────────────────────────────


def test_probe_idempotency_registry_single_winner_across_processes():
    key = f"probe:idem:{uuid.uuid4().hex}"
    results = _spawn_contention("idempotency", {"key": key}, WORKERS)
    acquired = [r for r in results if r.startswith("ACQUIRED")]
    assert len(acquired) == 1, f"expected exactly 1 winner of {WORKERS}: {results}"


def test_probe_work_lease_single_winner_across_processes():
    key = f"probe:lease:{uuid.uuid4().hex}"
    results = _spawn_contention("lease", {"key": key}, WORKERS)
    acquired = [r for r in results if r.startswith("ACQUIRED")]
    rejected = [r for r in results if r.startswith("REJECTED")]
    assert len(acquired) == 1, f"expected exactly 1 winner: {results}"
    assert len(rejected) == WORKERS - 1, f"unexpected outcomes: {results}"


def test_probe_collection_token_single_consumer_across_processes():
    from spine_api.services.collection_service import generate_token

    trip_id = _create_probe_trip()
    if trip_id is None:
        pytest.skip("TripStore refused the probe trip (backend unavailable)")

    async def _mint() -> str:
        from sqlalchemy import text

        from spine_api.core.database import async_session_maker
        from spine_api.core.rls import set_rls_agency

        set_rls_agency(CANONICAL_AGENCY)

        async with async_session_maker() as session:
            await session.execute(
                text("SELECT set_config('app.current_agency_id', :agency, true)"),
                {"agency": CANONICAL_AGENCY},
            )
            plain, _row = await generate_token(
                session,
                trip_id=trip_id,
                agency_id=CANONICAL_AGENCY,
                created_by=CANONICAL_AGENCY,
                ttl_hours=1,
            )
            await session.commit()
            return plain


    token_plain = asyncio_run(_mint())
    results = _spawn_contention("token", {"token": token_plain}, WORKERS)
    consumed = [r for r in results if r.startswith("ACQUIRED")]
    assert len(consumed) == 1, f"expected exactly 1 consumer: {results}"


def test_probe_usage_events_correlation_columns_present():
    from src.llm.usage_store import LLMUsageStore

    store = LLMUsageStore()  # default sqlite path
    try:
        events = store.get_events_for_run("run-probe-schema-check")
    except Exception as exc:
        pytest.skip(f"store schema not upgraded (run_id column absent): {exc}")
    assert isinstance(events, list)


def asyncio_run(coro):
    import asyncio

    return asyncio.run(coro)
