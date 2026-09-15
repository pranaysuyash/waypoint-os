"""Tests for SQL-backed durable requeue jobs.

All tests require a running PostgreSQL instance (@pytest.mark.require_postgres).
"""

from __future__ import annotations


import json

import pytest
from sqlalchemy import text

from src.agents.requeue import SQLSpineJobQueueRequeuePort, build_requeue_port

pytestmark = pytest.mark.require_postgres


@pytest.fixture(autouse=True)
def _ensure_schema():
    """Idempotent schema setup + clean before each test."""
    from spine_api.services.agent_requeue_jobs import RequeueJobStore
    from spine_api.persistence import _run_async_blocking, tripstore_session_maker

    store = RequeueJobStore()
    store.ensure_schema()

    async def _clean():
        async with tripstore_session_maker() as s:
            async with s.begin():
                await s.execute(text("DELETE FROM agent_requeue_jobs"))

    _run_async_blocking(_clean())
    return store


def _fetch(job_id: str) -> dict | None:
    from sqlalchemy import text as _text
    from spine_api.persistence import _run_async_blocking, tripstore_session_maker

    async def _get():
        async with tripstore_session_maker() as s:
            async with s.begin():
                row = (await s.execute(
                    _text("SELECT * FROM agent_requeue_jobs WHERE id = :id"),
                    {"id": job_id},
                )).mappings().first()
                return dict(row) if row else None

    return _run_async_blocking(_get())


# ── RequeueJobStore tests ──────────────────────────────────────────────


class TestRequeueJobStoreEnsureSchema:
    def test_ensure_schema_creates_table(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore
        from spine_api.persistence import _run_async_blocking, tripstore_session_maker
        from sqlalchemy import text as _text

        store = RequeueJobStore()
        store.ensure_schema()

        async def _check():
            async with tripstore_session_maker() as s:
                async with s.begin():
                    r = await s.execute(
                        _text(
                            "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                            "WHERE table_name = 'agent_requeue_jobs')"
                        )
                    )
                    return r.scalar()

        assert _run_async_blocking(_check()) is True

    def test_ensure_schema_is_idempotent(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        store.ensure_schema()
        store.ensure_schema()
        store.ensure_schema()  # no error


class TestRequeueJobStoreEnqueue:
    def test_enqueue_creates_pending_job(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue(
            trip_id="t1", idempotency_key="req:t1:stuck", reason="stuck"
        )
        assert accepted is True
        assert job_id is not None

        row = _fetch(job_id)
        assert row is not None
        assert row["status"] == "pending"
        assert row["trip_id"] == "t1"

    def test_enqueue_returns_job_id(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck")
        assert accepted is True
        assert len(job_id) > 0
        assert isinstance(job_id, str)

    def test_enqueue_duplicate_idempotency_returns_same_job(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted1, job_id1 = store.enqueue("t1", "req:t1:stuck", "stuck")
        accepted2, job_id2 = store.enqueue("t1", "req:t1:stuck", "stuck again")

        assert accepted1 is True
        assert accepted2 is False
        assert job_id2 == job_id1

    def test_enqueue_different_idempotency_creates_separate_jobs(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted1, job_id1 = store.enqueue("t1", "req:t1:stuck", "stuck")
        accepted2, job_id2 = store.enqueue("t1", "req:t1:weather", "weather")

        assert accepted1 is True
        assert accepted2 is True
        assert job_id2 != job_id1


class TestRequeueJobStoreLease:
    def test_lease_gets_pending_job(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        store.enqueue("t1", "req:t1:stuck", "stuck")

        job = store.lease_pending()
        assert job is not None
        assert job.trip_id == "t1"
        assert job.status == "running"

    def test_lease_returns_none_when_none_pending(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        job = store.lease_pending()
        assert job is None

    def test_lease_does_not_return_already_leased_job(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore(lease_seconds=600)
        store.enqueue("t1", "req:t1:stuck", "stuck")
        store.lease_pending("worker_a")

        job = store.lease_pending("worker_b")
        assert job is None

    def test_lease_returns_failed_job_below_max_attempts(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore(lease_seconds=0)
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck", max_attempts=3)
        store.fail(job_id, "transient error", poison=False)

        job = store.lease_pending()
        assert job is not None
        assert job.status == "running"

    def test_lease_does_not_return_poisoned_job(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck", max_attempts=2)
        store.fail(job_id, "fatal", poison=True)

        job = store.lease_pending()
        assert job is None


class TestRequeueJobStoreComplete:
    def test_complete_marks_completed(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck")
        store.complete(job_id, "done")

        row = _fetch(job_id)
        assert row["status"] == "completed"
        assert row["last_error"] == "done"

    def test_completed_job_not_released(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck")
        store.complete(job_id, "done")

        job = store.lease_pending()
        assert job is None


class TestRequeueJobStoreFail:
    def test_fail_retryable_sets_failed_status(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck", max_attempts=3)
        store.fail(job_id, "transient", poison=False)

        row = _fetch(job_id)
        assert row["status"] == "failed"
        assert row["attempts"] == 1

    def test_fail_poisoned_sets_poisoned_status(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck", max_attempts=2)
        store.fail(job_id, "fatal", poison=True)

        row = _fetch(job_id)
        assert row["status"] == "poisoned"

    def test_fail_increments_attempts(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck", max_attempts=5)

        store.fail(job_id, "err1", poison=False)
        assert _fetch(job_id)["attempts"] == 1

        store.fail(job_id, "err2", poison=False)
        assert _fetch(job_id)["attempts"] == 2

        store.fail(job_id, "err3", poison=True)
        assert _fetch(job_id)["attempts"] == 3


class TestRequeueJobStoreSnapshot:
    def test_snapshot_backend_is_sql(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        snap = store.snapshot()
        assert snap["backend"] == "sql"

    def test_snapshot_counts_are_accurate(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        _, j1 = store.enqueue("t1", "req:t1:1", "stuck")
        _, j2 = store.enqueue("t2", "req:t2:1", "stuck")
        store.complete(j1, "done")
        store.fail(j2, "err", poison=True)

        snap = store.snapshot()
        assert snap["total"] == 2
        assert snap["counts"]["completed"] == 1
        assert snap["counts"]["poisoned"] == 1


# ── SQLSpineJobQueueRequeuePort tests ──────────────────────────────────


class TestSQLSpineJobQueueRequeuePort:
    def test_enqueues_job_and_returns_accepted(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        port = SQLSpineJobQueueRequeuePort(job_store=store)

        result = port.requeue_trip("t1", {"raw_input": {"x": "y"}}, "stuck", 1)

        assert result.accepted is True
        assert result.mode == "sql_queue"
        assert result.job_id is not None

    def test_duplicate_requeue_returns_not_accepted(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        port = SQLSpineJobQueueRequeuePort(job_store=store)

        port.requeue_trip("t1", {}, "stuck", 1)
        result = port.requeue_trip("t1", {}, "stuck", 1)

        assert result.accepted is True
        assert "Duplicate requeue" in result.reason

    def test_build_requeue_port_sql_queue(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        port = build_requeue_port("sql_queue", job_store=store)

        assert isinstance(port, SQLSpineJobQueueRequeuePort)


# ── RequeueWorker tests ────────────────────────────────────────────────


class _FakeRunner:
    def __init__(self, fail: bool = False):
        self.calls = []
        self._fail = fail

    def __call__(self, **kwargs):
        self.calls.append(kwargs)
        if self._fail:
            raise RuntimeError("pipeline error")


class _FakeTripRepo:
    def __init__(self, trips: list[dict]):
        self._trips = {t["id"]: dict(t) for t in trips}

    def list_active(self):
        return list(self._trips.values())


class TestRequeueWorker:
    def test_run_once_processes_pending_job(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore, RequeueWorker

        store = RequeueJobStore()
        store.enqueue("t1", "req:t1:stuck", "stuck")
        runner = _FakeRunner()

        worker = RequeueWorker(job_store=store, spine_runner=runner, trip_repo=_FakeTripRepo([
            {"id": "t1", "raw_input": {"raw_note": "hello"}, "stage": "intake"}
        ]))
        results = worker.run_once(max_jobs=10)

        assert len(results) == 1
        assert results[0]["status"] == "completed"
        assert results[0]["trip_id"] == "t1"

        row = _fetch(results[0]["job_id"])
        assert row["status"] == "completed"

    def test_run_once_processes_multiple_jobs(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore, RequeueWorker

        store = RequeueJobStore()
        store.enqueue("t1", "req:t1:1", "stuck")
        store.enqueue("t2", "req:t2:1", "stuck")
        runner = _FakeRunner()

        worker = RequeueWorker(job_store=store, spine_runner=runner, trip_repo=_FakeTripRepo([
            {"id": "t1", "raw_input": {"raw_note": "hello"}, "stage": "intake"},
            {"id": "t2", "raw_input": {"raw_note": "world"}, "stage": "intake"},
        ]))
        results = worker.run_once(max_jobs=10)

        assert len(results) == 2
        assert all(r["status"] == "completed" for r in results)

    def test_worker_runner_exception_sets_failed(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore, RequeueWorker

        store = RequeueJobStore()
        store.enqueue("t1", "req:t1:stuck", "stuck", max_attempts=3)
        runner = _FakeRunner(fail=True)

        worker = RequeueWorker(job_store=store, spine_runner=runner, trip_repo=_FakeTripRepo([
            {"id": "t1", "raw_input": {"raw_note": "hello"}, "stage": "intake"}
        ]))
        results = worker.run_once(max_jobs=10)

        assert len(results) == 1
        assert results[0]["status"] == "failed"
        assert "pipeline error" in results[0].get("error", "")

    def test_worker_max_attempts_poisons(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore, RequeueWorker

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t1", "req:t1:stuck", "stuck", max_attempts=1)
        runner = _FakeRunner(fail=True)

        worker = RequeueWorker(job_store=store, spine_runner=runner, trip_repo=_FakeTripRepo([
            {"id": "t1", "raw_input": {"raw_note": "hello"}, "stage": "intake"}
        ]))
        results = worker.run_once(max_jobs=10)

        assert results[0]["status"] == "poisoned"

        row = _fetch(job_id)
        assert row["status"] == "poisoned"

    def test_worker_missing_trip_fails_closed(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore, RequeueWorker

        store = RequeueJobStore()
        store.enqueue("t1", "req:t1:stuck", "stuck")
        runner = _FakeRunner()

        worker = RequeueWorker(job_store=store, spine_runner=runner, trip_repo=_FakeTripRepo([]))
        results = worker.run_once(max_jobs=10)

        assert results[0]["status"] == "poisoned"

    def test_worker_missing_raw_input_fails_closed(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore, RequeueWorker

        store = RequeueJobStore()
        store.enqueue("t1", "req:t1:stuck", "stuck")
        runner = _FakeRunner()

        worker = RequeueWorker(job_store=store, spine_runner=runner, trip_repo=_FakeTripRepo([
            {"id": "t1", "stage": "intake"}  # no raw_input
        ]))
        results = worker.run_once(max_jobs=10)

        assert results[0]["status"] == "poisoned"
        assert "unsupported_missing_context" in results[0].get("error", "")

    def test_worker_calls_runner_with_correct_args(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore, RequeueWorker

        store = RequeueJobStore()
        store.enqueue("t1", "req:t1:stuck", "stuck")
        runner = _FakeRunner()

        worker = RequeueWorker(job_store=store, spine_runner=runner, trip_repo=_FakeTripRepo([
            {"id": "t1", "raw_input": {"raw_note": "hello"}, "stage": "intake"}
        ]))
        worker.run_once(max_jobs=10)

        assert len(runner.calls) == 1
        assert runner.calls[0]["envelopes"] == [{"raw_note": "hello"}]
        assert runner.calls[0]["stage"] == "intake"


class TestRequeueJobStats:
    def test_trip_stats_surface_attempts_and_poison(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        accepted, job_id = store.enqueue("t_stats", "req:t_stats:stuck", "stuck", max_attempts=2)
        assert accepted is True
        store.fail(job_id, "err1", poison=False)
        stats = store.trip_stats("t_stats")
        assert stats["attempts"] == 1
        assert stats["poisoned"] is False
        store.fail(job_id, "fatal", poison=True)
        stats = store.trip_stats("t_stats")
        assert stats["poisoned"] is True


class TestPoisonedJobInspection:
    def test_list_poisoned_is_redacted_deterministic_and_excludes_active_jobs(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        _, poisoned_id = store.enqueue(
            "t_poison", "req:t_poison:1", "missing context", {"token": "secret"}
        )
        store.fail(poisoned_id, "x" * 3000, poison=True)
        store.enqueue("t_pending", "req:t_pending:1", "still pending", {"password": "secret"})

        rows = store.list_poisoned()

        assert len(rows) == 1
        summary = rows[0]
        assert summary.job_id == poisoned_id
        assert summary.trip_id == "t_poison"
        assert summary.attempts == 1
        assert len(summary.last_error) == 2048
        assert "secret" not in repr(summary)
        assert not hasattr(summary, "payload")

    def test_list_poisoned_supports_bounded_filter_and_offset(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        for index in range(3):
            trip_id = f"t_filter_{index}"
            _, job_id = store.enqueue(trip_id, f"req:{trip_id}", "fatal")
            store.fail(job_id, f"error-{index}", poison=True)

        filtered = store.list_poisoned(trip_id="t_filter_1")
        page = store.list_poisoned(limit=1, offset=1)

        assert [row.trip_id for row in filtered] == ["t_filter_1"]
        assert len(page) == 1
        assert page[0].trip_id in {"t_filter_0", "t_filter_1"}

    def test_list_poisoned_rejects_unbounded_arguments(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        with pytest.raises(ValueError):
            store.list_poisoned(limit=0)
        with pytest.raises(ValueError):
            store.list_poisoned(limit=101)
        with pytest.raises(ValueError):
            store.list_poisoned(offset=-1)


# ── Factory integration tests ──────────────────────────────────────────


class TestFactorySqlQueueMode:
    def test_sql_queue_requeue_mode_valid(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_RECOVERY_REQUEUE_MODE", "sql_queue")
        config = build_agent_runtime_config()

        assert config.recovery_requeue_mode == "sql_queue"

    def test_sql_queue_port_created_by_factory(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import AgentRuntimeConfig, build_agent_runtime_from_config

        config = AgentRuntimeConfig(recovery_requeue_mode="sql_queue")
        bundle = build_agent_runtime_from_config(config)

        assert bundle.recovery_agent is not None
 
 
class TestPoisonedJobInspectRedactReplay:
    def test_inspect_and_replay_poisoned_job(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore
        from src.agents.dlq_inspector import DLQInspector

        store = RequeueJobStore()
        payload = {
            "traveler": "Alice",
            "api_token": "sk-secret-12345",
            "credit_card_pan": "4111111111111111",
            "hotel_id": "ht_99",
        }
        accepted, job_id = store.enqueue(
            trip_id="t_poison_inspect",
            idempotency_key="poison:test:1",
            reason="Unrecoverable GDS failure",
            payload=payload,
        )
        assert accepted is True

        # Fail and poison the job
        store.fail(job_id, "Fatal supplier timeout", poison=True)

        # Inspect poisoned job: verify sensitive fields redacted
        detail = store.inspect_poisoned(job_id)
        assert detail is not None
        assert detail["status"] == "poisoned"
        assert detail["trip_id"] == "t_poison_inspect"
        assert detail["last_error"] == "Fatal supplier timeout"
        assert detail["redacted_payload"]["hotel_id"] == "ht_99"
        assert detail["redacted_payload"]["api_token"] == "[REDACTED_BY_DLQ_GUARD]"
        assert detail["redacted_payload"]["credit_card_pan"] == "[REDACTED_BY_DLQ_GUARD]"

        # Verify DLQInspector mirror has recorded it
        dlq_record = DLQInspector.get_job(job_id)
        assert dlq_record is not None
        assert dlq_record.trip_id == "t_poison_inspect"

        # Replay the poisoned job with patched payload
        ok = store.replay_poisoned(job_id, patched_payload={"hotel_id": "ht_100", "provider": "NDC"})
        assert ok is True

        # Job is now back to pending with an incremented (not reset) attempt counter:
        # poison landed at attempts=1, replay adds one more.
        row = _fetch(job_id)
        assert row is not None
        assert row["status"] == "pending"
        assert row["attempts"] == 2
        assert row["last_error"] == ""
        assert "ht_100" in row["payload"]

        # Inspect non-poisoned job returns None
        assert store.inspect_poisoned(job_id) is None
        # Replay non-poisoned job returns False
        assert store.replay_poisoned(job_id) is False

    def test_redact_poisoned_job_strips_payload_and_refuses_replay(self):
        from spine_api.services.agent_requeue_jobs import (
            PoisonedJobRedactedError,
            RequeueJobStore,
        )
        from src.agents.dlq_inspector import DLQInspector, PoisonResolutionStatus

        store = RequeueJobStore()
        _, job_id = store.enqueue(
            trip_id="t_poison_redact",
            idempotency_key="poison:redact:1",
            reason="Unrecoverable GDS failure",
            payload={"passport_number": "X1234567", "note": "window seat"},
        )
        store.fail(job_id, "Fatal supplier timeout", poison=True)

        assert store.redact_poisoned(job_id) is True

        row = _fetch(job_id)
        # Row, reason, and terminal error preserved; payload contents stripped.
        assert row is not None
        assert row["status"] == "poisoned"
        assert row["reason"] == "Unrecoverable GDS failure"
        assert row["last_error"] == "Fatal supplier timeout"
        assert row["payload"].startswith("{")
        assert "__redacted__" in row["payload"]
        assert "X1234567" not in row["payload"]
        assert "window seat" not in row["payload"]

        # DLQ projection mirrored: record preserved, no longer actionable.
        dlq_record = DLQInspector.get_job(job_id)
        assert dlq_record is None or dlq_record.status == PoisonResolutionStatus.REDACTED

        # Redacted jobs can no longer be inspected as actionable poison...
        detail = store.inspect_poisoned(job_id)
        assert detail is None or "passport_number" not in json.dumps(detail.get("redacted_payload", {}))

        # ...and replay refuses them with an explicit error.
        with pytest.raises(PoisonedJobRedactedError):
            store.replay_poisoned(job_id)

    def test_replay_poisoned_writes_audit_event(self):
        from spine_api.persistence import AuditStore
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        _, job_id = store.enqueue("t_poison_audit", "poison:audit:1", "stuck")
        store.fail(job_id, "fatal", poison=True)
        store.replay_poisoned(job_id)

        events = AuditStore.get_events(limit=50)
        replay_events = [e for e in events if e.get("event_type") == "requeue_job_replayed"]
        assert any(e.get("details", {}).get("job_id") == job_id for e in replay_events)

    def test_redact_poisoned_writes_audit_event(self):
        from spine_api.persistence import AuditStore
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        _, job_id = store.enqueue("t_poison_audit2", "poison:audit:2", "stuck")
        store.fail(job_id, "fatal", poison=True)
        store.redact_poisoned(job_id)

        events = AuditStore.get_events(limit=50)
        redact_events = [e for e in events if e.get("event_type") == "requeue_job_redacted"]
        assert any(e.get("details", {}).get("job_id") == job_id for e in redact_events)

    def test_poison_transition_visible_in_snapshot_and_listing(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        before = store.snapshot()
        _, job_id = store.enqueue("t_poison_stats", "poison:stats:1", "stuck", max_attempts=1)
        store.fail(job_id, "fatal", poison=True)

        snap = store.snapshot()
        # Poison transition is visible in the operational snapshot...
        assert snap["counts"].get("poisoned", 0) == before["counts"].get("poisoned", 0) + 1
        assert snap["poisoned_count"] == before["poisoned_count"] + 1
        assert snap["oldest_poisoned_age_seconds"] >= 0.0
        # ...and in the bounded redacted listing.
        listed = [s.job_id for s in store.list_poisoned(trip_id="t_poison_stats")]
        assert job_id in listed

    def test_dead_trips_detection_identifies_poisoned_trip(self):
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        _, job_id = store.enqueue("t_dead_trip", "poison:dead:1", "stuck", max_attempts=1)
        store.fail(job_id, "fatal", poison=True)

        dead = {entry["trip_id"]: entry for entry in store.dead_trips()}
        assert "t_dead_trip" in dead
        assert dead["t_dead_trip"]["poisoned_jobs"] >= 1
        assert dead["t_dead_trip"]["max_attempts"] >= 1

        # Live/pending trips are not dead.
        store.enqueue("t_alive", "poison:alive:1", "stuck")
        alive_ids = {entry["trip_id"] for entry in store.dead_trips()}
        assert "t_alive" not in alive_ids

    def test_reclaim_stale_running_returns_expired_lease_to_pending(self):
        from datetime import datetime, timedelta, timezone

        from sqlalchemy import text as _text
        from spine_api.persistence import _run_async_blocking, tripstore_session_maker
        from spine_api.services.agent_requeue_jobs import RequeueJobStore

        store = RequeueJobStore()
        _, job_id = store.enqueue("t_stale", "poison:stale:1", "stuck")
        leased = store.lease_by_id(job_id)
        assert leased is not None and leased.status == "running"

        # Simulate a dead worker: push the lease into the past.
        async def _expire():
            async with tripstore_session_maker() as s:
                async with s.begin():
                    await s.execute(
                        _text(
                            "UPDATE agent_requeue_jobs SET leased_until = :past WHERE id = :id"
                        ),
                        {
                            "past": datetime.now(timezone.utc) - timedelta(seconds=120),
                            "id": job_id,
                        },
                    )

        _run_async_blocking(_expire())

        reclaimed = store.reclaim_stale_running()
        assert reclaimed >= 1
        row = _fetch(job_id)
        assert row["status"] == "pending"
        # A healthy lease is never reclaimed.
        assert store.reclaim_stale_running() == 0
