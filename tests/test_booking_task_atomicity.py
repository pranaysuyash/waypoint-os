"""Task state and its required timeline event are one durable operation.

SQLite exercises real flush/commit/rollback behavior without touching a shared
database. PostgreSQL integration separately checks tenant/RLS behavior.
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from spine_api.models.tenant import BookingTask, ExecutionEvent
from spine_api.services import booking_task_service as service


@pytest_asyncio.fixture
async def task_db():
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as connection:
        for table in (BookingTask.__table__, ExecutionEvent.__table__):
            await connection.run_sync(table.create)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        yield session
    await engine.dispose()


async def _task(db, status="in_progress", **kwargs):
    task = BookingTask(
        trip_id="trip_atomic", agency_id="agency_atomic", task_type="custom",
        title="Confirm the reservation", status=status, priority="medium",
        source="agent_created", created_by="operator", **kwargs,
    )
    db.add(task)
    await db.commit()
    return task


async def _rows(db, model):
    return list((await db.execute(select(model))).scalars().all())


@pytest.mark.asyncio
@pytest.mark.parametrize("action,event_type,target", [
    ("complete_task", "task_completed", "completed"),
    ("cancel_task", "task_cancelled", "cancelled"),
])
async def test_terminal_action_commits_real_event_once(task_db, action, event_type, target):
    task = await _task(task_db)
    operation = getattr(service, action)
    kwargs = {"completed_by": "operator"} if action == "complete_task" else {}
    result = await operation(task_db, task.id, "agency_atomic", **kwargs)
    first_timestamp = result.completed_at if target == "completed" else result.cancelled_at
    await operation(task_db, task.id, "agency_atomic", **kwargs)
    events = await _rows(task_db, ExecutionEvent)
    assert result.status == target
    assert len(events) == 1
    assert events[0].event_type == event_type
    assert events[0].status_from == "in_progress"
    assert events[0].event_metadata == {"task_type": "custom"}
    assert (result.completed_at if target == "completed" else result.cancelled_at) == first_timestamp


@pytest.mark.asyncio
@pytest.mark.parametrize("action", ["complete_task", "cancel_task", "update_task"])
async def test_event_failure_rolls_back_state_without_caller_cleanup(task_db, monkeypatch, action):
    task = await _task(task_db)
    task_id = task.id

    async def unavailable(*args, **kwargs):
        raise RuntimeError("required timeline unavailable")

    monkeypatch.setattr(service.execution_event_service, "emit_event", unavailable)
    kwargs = {
        "complete_task": {"completed_by": "operator"},
        "cancel_task": {},
        "update_task": {"data": {"status": "waiting_on_customer"}},
    }[action]
    with pytest.raises(RuntimeError, match="required timeline unavailable"):
        await getattr(service, action)(task_db, task_id, "agency_atomic", **kwargs)
    task_db.expire_all()
    persisted = (await task_db.execute(select(BookingTask))).scalar_one()
    assert persisted.status == "in_progress"
    assert persisted.completed_at is None
    assert persisted.cancelled_at is None
    assert await _rows(task_db, ExecutionEvent) == []


@pytest.mark.asyncio
async def test_create_event_failure_leaves_no_task(task_db, monkeypatch):
    async def unavailable(*args, **kwargs):
        raise RuntimeError("required timeline unavailable")

    monkeypatch.setattr(service.execution_event_service, "emit_event", unavailable)
    with pytest.raises(RuntimeError):
        await service.create_task(task_db, "trip_atomic", "agency_atomic", "operator", {
            "task_type": "custom", "title": "Keep task and event together",
        })
    assert await _rows(task_db, BookingTask) == []
    assert await _rows(task_db, ExecutionEvent) == []


@pytest.mark.asyncio
async def test_invalid_update_cannot_leave_pending_state_or_event(task_db):
    task = await _task(task_db)
    with pytest.raises(ValueError, match="Invalid priority"):
        await service.update_task(task_db, task.id, "agency_atomic", {
            "status": "waiting_on_customer", "priority": "invalid",
        })
    # A later unrelated commit must not accidentally persist the rejected update.
    await task_db.commit()
    task_db.expire_all()
    persisted = (await task_db.execute(select(BookingTask))).scalar_one()
    assert persisted.status == "in_progress"
    assert await _rows(task_db, ExecutionEvent) == []


@pytest.mark.asyncio
async def test_patch_terminal_status_has_same_completion_contract(task_db):
    task = await _task(task_db)
    result = await service.update_task(task_db, task.id, "agency_atomic", {"status": "completed"})
    events = await _rows(task_db, ExecutionEvent)
    assert result.completed_at is not None
    assert [event.event_type for event in events] == ["task_completed"]


@pytest.mark.asyncio
async def test_generation_rolls_back_creation_when_reconciliation_fails(task_db, monkeypatch):
    async def state(*args):
        return {}

    async def fail_reconciliation(*args):
        raise RuntimeError("reconciliation unavailable")

    monkeypatch.setattr(service, "_fetch_trip_state", state)
    monkeypatch.setattr(service, "_compute_task_candidates", lambda *args: [{
        "trip_id": "trip_atomic", "agency_id": "agency_atomic", "task_type": "confirm_hotels",
    }])
    monkeypatch.setattr(service, "_reconcile_active_tasks", fail_reconciliation)
    with pytest.raises(RuntimeError):
        await service.generate_tasks(task_db, "trip_atomic", "agency_atomic", "operator")
    assert await _rows(task_db, BookingTask) == []
    assert await _rows(task_db, ExecutionEvent) == []


@pytest.mark.asyncio
async def test_reconciliation_event_preserves_actual_old_status(task_db, monkeypatch):
    task = await _task(task_db, status="ready", generation_hash="existing")
    task.source = "readiness_generated"
    await task_db.commit()

    async def state(*args):
        return {}

    candidate = {"trip_id": "trip_atomic", "agency_id": "agency_atomic", "task_type": "custom",
                 "blocker_code": "MISSING_DETAIL"}
    monkeypatch.setattr(service, "_fetch_trip_state", state)
    monkeypatch.setattr(service, "_compute_task_candidates", lambda *args: [candidate])
    result = await service.generate_tasks(task_db, "trip_atomic", "agency_atomic", "operator")
    assert result.reconciled[0].old_status == "ready"
    transitions = [e for e in await _rows(task_db, ExecutionEvent) if e.event_type == "task_blocked"]
    assert len(transitions) == 1
    assert transitions[0].status_from == "ready"
    assert transitions[0].status_to == "blocked"
