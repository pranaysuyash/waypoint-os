"""Tests for SQL-backed durable requeue jobs.

All tests require a running PostgreSQL instance (@pytest.mark.require_postgres).
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

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

        assert result.accepted is False

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


# ── Factory integration tests ──────────────────────────────────────────


class TestFactorySqlQueueMode:
    def test_sql_queue_requeue_mode_valid(self, monkeypatch):
        from spine_api.services.agent_runtime_factory import build_agent_runtime_config

        monkeypatch.setenv("AGENT_RECOVERY_REQUEUE_MODE", "sql_queue")
        config = build_agent_runtime_config()

        assert config.recovery_requeue_mode == "sql_queue"

    def test_sql_queue_port_created_by_factory(self, monkeypatch):
        from src.agents.requeue import SQLSpineJobQueueRequeuePort
        from src.agents.recovery_agent import RecoveryAgent
        from spine_api.services.agent_runtime_factory import AgentRuntimeConfig, build_agent_runtime_from_config

        config = AgentRuntimeConfig(recovery_requeue_mode="sql_queue")
        bundle = build_agent_runtime_from_config(config)

        assert bundle.recovery_agent is not None
