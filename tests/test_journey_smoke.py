"""Journey smoke — the one user-visible contract, end to end, in CI (G-07).

Closes the "journey-level tests absent from CI" gap called out by
``Docs/exploration/AGENTIC_DEEP_AUDIT_SYNTHESIS_2026-08-31.md`` §3 (G-07) and
the ADR §5 journey-test plan:

    agency user signs up → submits a note missing the basics → the pipeline
    refuses quote generation → the inquiry is still PERSISTED as an
    incomplete lead → the lead surfaces in the agency inbox → the operator
    can see WHY it is blocked (validation banner data).

Everything runs **in-process**: no live server, no PostgreSQL. The real
pipeline (`run_spine_once`), the real pipeline execution service
(`execute_spine_pipeline` — the code ``POST /run`` runs), the real
``save_processed_trip`` persistence path, the real file-backed
TripStore/DraftStore/RunLedger/AuditStore are exercised; only the SSE emit
callbacks are stubbed (they fan out to an HTTP event bus that does not exist
without a server). Store isolation follows the established patterns:
``tests/test_draft_store_linked_trip.py`` (DRAFTS_DIR monkeypatch) and the
conftest ``reset_global_singletons`` fixture (persistence dir monkeypatching).
``TRIPSTORE_BACKEND=file`` is pinned per-test so the sanctioned SQL test
database is never touched (no DB rows are written by this file).

The full signup journey against a real database (HTTP 201, hashed password at
rest, membership row) is covered by the DB-backed auth tests; this file
mirrors ``auth_service.signup``'s principal shape in-memory so the smoke
stays DB-free while still attributing the run to a real-shaped agency/user.
"""

from __future__ import annotations

from dataclasses import is_dataclass, asdict
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

# ---------------------------------------------------------------------------
# Isolation fixture — every store this journey touches points at tmp_path.
# ---------------------------------------------------------------------------


@pytest.fixture
def journey_env(tmp_path, monkeypatch):
    """Isolate every file-backed store under tmp_path and pin the file backend.

    ``TRIPSTORE_BACKEND=file`` is forced per-test: the developer .env pins
    ``TRIPSTORE_BACKEND=sql`` and ``TripStore._backend()`` reads the env var
    on every call, so without this the journey would silently write to the
    shared Postgres (the exact 2026-05-03 split-brain failure mode).
    """
    import spine_api.persistence as persistence
    import spine_api.run_ledger as run_ledger
    import spine_api.draft_store as draft_store

    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")
    monkeypatch.setenv("ENVIRONMENT", "development")

    trips_dir = tmp_path / "trips"
    trips_dir.mkdir()
    monkeypatch.setattr(persistence, "TRIPS_DIR", trips_dir)
    audit_dir = tmp_path / "audit"
    audit_dir.mkdir()
    monkeypatch.setattr(persistence, "AUDIT_DIR", audit_dir)
    checker_dir = tmp_path / "public_checker"
    monkeypatch.setattr(persistence, "PUBLIC_CHECKER_DIR", checker_dir)
    monkeypatch.setattr(persistence, "PUBLIC_CHECKER_UPLOADS_DIR", checker_dir / "uploads")
    monkeypatch.setattr(persistence, "PUBLIC_CHECKER_MANIFESTS_DIR", checker_dir / "manifests")

    runs_dir = tmp_path / "runs"
    monkeypatch.setattr(run_ledger, "RUNS_DIR", runs_dir)

    drafts_dir = tmp_path / "drafts"
    drafts_dir.mkdir()
    monkeypatch.setattr(draft_store, "DRAFTS_DIR", drafts_dir)
    monkeypatch.setattr(draft_store, "INDEX_FILE", drafts_dir / "index.json")

    return SimpleNamespace(root=tmp_path)


# ---------------------------------------------------------------------------
# Principal fixture — mirrors spine_api/services/auth_service.py::signup
# (User + Agency + owner Membership) without a database.
# ---------------------------------------------------------------------------


def _make_principal() -> SimpleNamespace:
    from spine_api.models.tenant import Agency, Membership, User

    # SQLAlchemy column defaults (uuid4) only fire at flush time; signup's
    # db.flush() would materialize these ids. Assign them explicitly so the
    # in-memory fixture carries the same shape a persisted principal has.
    user = User(
        id=str(uuid4()),
        email="owner@journey-smoke.test",
        password_hash="not-a-real-hash-smoke-only",
        name="Journey Owner",
    )
    agency = Agency(
        id=str(uuid4()),
        name="Journey Smoke Travel",
        slug=f"journey-smoke-{uuid4().hex[:8]}",
        email="owner@journey-smoke.test",
        is_test=True,
    )
    membership = Membership(
        id=str(uuid4()), user_id=user.id, agency_id=agency.id, role="owner"
    )
    return SimpleNamespace(user=user, agency=agency, membership=membership, role=membership.role)


# ---------------------------------------------------------------------------
# Serde helper — byte-for-byte the conversion ``POST /run`` uses
# (spine_api/server.py::_to_dict) so the persisted payload is identical.
# ---------------------------------------------------------------------------


def _to_dict(obj):
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if is_dataclass(obj):
        return asdict(obj)
    if hasattr(obj, "__dict__"):
        return {k: _to_dict(v) for k, v in obj.__dict__.items() if not k.startswith("_")}
    if isinstance(obj, (list, tuple)):
        return [_to_dict(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_dict(v) for k, v in obj.items()}
    return obj


# ---------------------------------------------------------------------------
# The journey
# ---------------------------------------------------------------------------


def test_signup_intake_missing_basics_blocked_lead_reaches_inbox(journey_env) -> None:
    """The four-gap journey: signup → intake (missing basics) → blocked → inbox."""
    from spine_api.draft_store import DraftStore
    from spine_api.persistence import AuditStore, TripStore, save_processed_trip
    from spine_api.run_ledger import RunLedger
    from spine_api.run_state import RunState
    from spine_api.routers.inbox import _INBOX_STATUSES
    from spine_api.services.pipeline_execution_service import execute_spine_pipeline
    from src.intake.config.agency_settings import AgencySettingsStore
    from src.intake.orchestration import run_spine_once
    from src.intake.packet_models import SourceEnvelope

    # -- Step 1: an agency user exists (signup principal) -------------------
    principal = _make_principal()
    agency_id, user_id = principal.agency.id, principal.user.id
    assert principal.role == "owner"
    assert principal.membership.agency_id == agency_id

    # -- Step 2: the customer note is missing the basics --------------------
    # No destination, no dates, no party size, no budget — the canonical
    # "blocked at intake" input.
    raw_note = "Hi! We are finally ready to start planning. Please take a look when you can."

    # The advisor opens a draft for the inquiry (the POST /run pre-step).
    draft = DraftStore.create(
        agency_id=agency_id,
        created_by=user_id,
        name="Journey smoke intake",
        customer_message=raw_note,
    )

    run_id = f"run_{uuid4().hex[:12]}"
    RunLedger.create(
        run_id,
        trip_id=None,
        stage="discovery",
        operating_mode="normal_intake",
        agency_id=agency_id,
        draft_id=draft.id,
    )

    emit_blocked = MagicMock()
    emit_completed = MagicMock()

    # -- Step 3: the pipeline runs in-process with REAL dependencies --------
    # (execute_spine_pipeline is exactly what spine_api POST /run drives;
    # only the SSE emit callbacks are stubbed — there is no HTTP layer here.)
    execute_spine_pipeline(
        run_id=run_id,
        request_dict={
            "raw_note": raw_note,
            "stage": "discovery",
            "operating_mode": "normal_intake",
            "strict_leakage": False,
            "retention_consent": True,
            "scenario_id": None,
        },
        agency_id=agency_id,
        user_id=user_id,
        build_envelopes=lambda data: [
            # server.build_envelopes' raw_note branch: one freeform envelope.
            SourceEnvelope.from_freeform(data["raw_note"], "agency_notes", "agent"),
        ],
        load_fixture_expectations=lambda _scenario_id: None,
        to_dict=_to_dict,
        close_inherited_lock_fds=lambda: None,
        save_processed_trip=save_processed_trip,
        trip_store=TripStore,
        audit_store=AuditStore,
        run_spine_once_fn=run_spine_once,
        logger=__import__("logging").getLogger("test_journey_smoke"),
        otel_tracer=SimpleNamespace(
            start_as_current_span=lambda _name: __import__("contextlib", fromlist=["nullcontext"]).nullcontext(
                SimpleNamespace(set_attribute=lambda *_a, **_k: None)
            )
        ),
        run_ledger=RunLedger,
        run_state_running=RunState.RUNNING,
        draft_store=DraftStore,
        # Settings store is SQLite-backed; defaults() is the pure no-store
        # path a fresh agency would receive on its first run anyway.
        agency_settings_store=SimpleNamespace(load=AgencySettingsStore.defaults),
        build_live_checker_signals_fn=lambda _packet, _raw: None,
        emit_run_started_fn=MagicMock(),
        emit_run_completed_fn=emit_completed,
        emit_run_failed_fn=MagicMock(),
        emit_run_blocked_fn=emit_blocked,
        emit_stage_entered_fn=MagicMock(),
        emit_stage_completed_fn=MagicMock(),
    )

    # -- Step 4: the run blocks, quoting is refused, and the lead persists --
    emit_blocked.assert_called_once()
    blocked_kwargs = emit_blocked.call_args.kwargs
    trip_id = blocked_kwargs["trip_id"]
    assert trip_id, "ESCALATE must persist the inquiry and surface its trip id"
    assert blocked_kwargs["block_reason"], "the operator-facing block reason must be present"
    emit_completed.assert_not_called()

    run_meta = RunLedger.get_meta(run_id)
    assert run_meta["state"] == RunState.BLOCKED.value
    assert run_meta["trip_id"] == trip_id
    assert run_meta["draft_id"] == draft.id

    trip = TripStore.get_trip(trip_id)
    assert trip is not None, "the incomplete lead must be persisted"
    assert trip.get("status") == "incomplete"
    assert trip.get("agency_id") == agency_id, "the lead must be scoped to the owning agency"

    # -- Step 5: the lead surfaces in the agency inbox projection -----------
    inbox_summaries = TripStore.list_trip_summaries(
        status=_INBOX_STATUSES, agency_id=agency_id
    )
    inbox_ids = {t.get("id") for t in inbox_summaries}
    assert trip_id in inbox_ids, (
        "a blocked intake must appear in the inbox statuses the "
        f"agency inbox reads ({_INBOX_STATUSES})"
    )
    persisted_summary = next(t for t in inbox_summaries if t.get("id") == trip_id)
    assert persisted_summary.get("status") == "incomplete"

    # -- Step 6: the user-visible banner data is on the run -----------------
    # (a) validation report: invalid, with human-readable error issues
    validation = trip.get("validation") or {}
    assert validation.get("is_valid") is False
    errors = validation.get("errors") or []
    assert errors, "a missing-basics intake must carry validation error issues"
    for issue in errors:
        assert issue.get("message"), "each banner issue must be human-readable"

    # (b) the run ledger checkpoints the same banner data for the UI
    # (get_all_steps wraps each checkpoint payload under "data")
    steps = RunLedger.get_all_steps(run_id)
    blocked_step = (steps.get("blocked_result") or {}).get("data") or {}
    assert blocked_step.get("early_exit_reason"), "the run must record why it was blocked"
    assert blocked_step.get("trip_id") == trip_id
    ledger_validation = blocked_step.get("validation") or {}
    assert ledger_validation.get("is_valid") is False

    # (c) the draft records the linkage so reprocesses reuse the same lead
    updated_draft = DraftStore.get(draft.id)
    assert updated_draft is not None
    assert updated_draft.linked_trip_ids == [trip_id]
