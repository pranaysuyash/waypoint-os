"""Evidence for the Workbench's internal-language indicator across a saved trip."""

from copy import deepcopy
from dataclasses import asdict
from types import SimpleNamespace

import pytest

from spine_api import persistence
from spine_api.contract import SafetyResult, TripPatchRequest, TripResponse
from src.intake import orchestration
from src.intake.gates import GateResult, GateVerdict
from src.intake.packet_models import SourceEnvelope


NOTE = (
    "We are planning a family leisure trip from Bangalore to Singapore around "
    "9 to 14 February 2027. We are 2 adults with budget around 3L."
)


def _checked_result(monkeypatch, decision_state="ASK_FOLLOWUP", opening="When will you arrive?", mode="normal_intake"):
    # Pin the two variables under test while retaining the actual bundle builder,
    # Phase 8 scanner, and checkpoint protocol.
    original = orchestration.build_session_strategy

    def controlled_strategy(decision, *args, **kwargs):
        decision.set_decision_state(decision_state)
        strategy = original(decision, *args, **kwargs)
        strategy.suggested_opening = opening
        return strategy

    monkeypatch.setattr(orchestration, "build_session_strategy", controlled_strategy)
    return orchestration.run_spine_once(
        [SourceEnvelope.from_freeform(NOTE)], operating_mode=mode, strict_leakage=False, stage_callback=lambda *_: None,
    )


def _trip(result):
    return persistence._build_processed_trip(
        {"run_id": "run-proof", "packet": {"facts": {"party_size": {"value": 2}}},
         "decision": {"decision_state": result.decision.decision_state, "operating_mode": result.decision.operating_mode},
         "strategy": asdict(result.strategy), "safety": result.leakage_result,
         "traveler_bundle": result.traveler_bundle.to_traveler_dict(),
         "meta": {"submission": {"raw_note": NOTE}}},
        source="test", user_id=None, follow_up_due_date=None, party_composition=None,
        pace_preference=None, date_year_confidence=None, lead_source=None, activity_provenance=None,
        trip_status="new",
    )


@pytest.mark.parametrize(("opening", "status"), [
    ("When will you arrive?", "passed"), ("The blocker is still open.", "failed"),
])
def test_phase8_check_roundtrips_with_its_exact_draft(monkeypatch, tmp_path, opening, status):
    result = _checked_result(monkeypatch, opening=opening)
    proof = result.leakage_result["draft_check"]
    assert proof["status"] == status
    assert proof["version"] == 2 and len(proof["digest_sha256"]) == 64
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path)
    store = persistence.FileTripStore
    trip_id = store.save_trip(_trip(result), agency_id="agency-proof")

    def reopen():
        return TripResponse.from_dict(store.get_trip_for_agency(trip_id, "agency-proof"))

    reopened = reopen()
    assert reopened.run_id == "run-proof"
    assert reopened.safety["draft_check"] == proof
    assert reopened.traveler_bundle["user_message"] == result.traveler_bundle.user_message
    assert "internal_notes" not in reopened.traveler_bundle

    original = store.get_trip_for_agency(trip_id, "agency-proof")
    changes = [
        ("traveler_bundle", {**original["traveler_bundle"], "user_message": "Edited message"}),
        ("traveler_bundle", {**original["traveler_bundle"], "system_context": "Edited instructions"}),
        ("raw_input", {"submission": {"raw_note": "Travelers now leave on a different day."}}),
        ("extracted", {"facts": {"party_size": {"value": 7}}}),
        ("decision", {"decision_state": "PROCEED_INTERNAL_DRAFT"}),
        ("run_id", "different-run"),
    ]
    for field, value in changes:
        edited = deepcopy(original)
        edited[field] = value
        store.save_trip(edited, agency_id="agency-proof")
        assert not reopen().safety.get("draft_check"), field
    store.save_trip({**original, "status": "assigned"}, agency_id="agency-proof")
    assert reopen().safety["draft_check"] == proof


@pytest.mark.parametrize("state", ["STOP_NEEDS_REVIEW", "PROCEED_INTERNAL_DRAFT"])
def test_internal_or_stopped_output_never_gets_customer_check(monkeypatch, state):
    result = _checked_result(monkeypatch, decision_state=state)
    assert result.traveler_bundle.user_message and "traveler_bundle_leaks" in result.leakage_result
    assert not result.leakage_result.get("draft_check")


@pytest.mark.parametrize(("mode", "state"), [
    ("owner_review", "ASK_FOLLOWUP"), ("owner_review", "PROCEED_TRAVELER_SAFE"),
    ("emergency", "PROCEED_TRAVELER_SAFE"),
])
def test_modes_whose_openings_are_internal_or_placeholders_cannot_pass(monkeypatch, mode, state):
    result = _checked_result(monkeypatch, decision_state=state, mode=mode)
    assert "traveler_bundle_leaks" in result.leakage_result
    assert not result.leakage_result.get("draft_check")


def test_legacy_boolean_does_not_certify_a_reopened_draft():
    response = TripResponse.from_dict({
        "id": "legacy", "status": "assigned",
        "decision": {"decision_state": "ASK_FOLLOWUP"},
        "traveler_bundle": {"audience": "traveler", "user_message": "Legacy text", "internal_notes": "staff"},
        "safety": {"leakage_passed": True},
    })
    assert response.traveler_bundle["user_message"] == "Legacy text"
    assert "internal_notes" not in response.traveler_bundle
    assert not response.safety.get("draft_check")


@pytest.mark.parametrize("gate", [GateVerdict.ESCALATE, GateVerdict.DEGRADE])
def test_unscanned_paths_have_no_check(monkeypatch, gate):
    monkeypatch.setattr(
        orchestration.NB01CompletionGate, "evaluate",
        lambda *_: GateResult(verdict=gate, score=0, reasons=["test_missing_fields"]),
    )
    completed = {}
    def collect(stage, event):
        if event["event"] == "completed":
            completed[stage] = event["data"]

    result = orchestration.run_spine_once([SourceEnvelope.from_freeform(NOTE)], stage_callback=collect)
    assert result.early_exit or result.partial_intake
    assert "safety" not in completed
    assert not result.traveler_bundle.user_message
    assert SafetyResult.model_validate(result.leakage_result).draft_check is None
    assert SafetyResult.model_validate(result.leakage_result).leakage_passed is None


def test_sanitized_view_failure_is_scoped_separately_from_draft(monkeypatch):
    monkeypatch.setattr(orchestration, "_check_sanitized_view_leakage", lambda _: ["sanitized issue"])
    result = _checked_result(monkeypatch)
    assert result.leakage_result["leakage_passed"] is False
    assert result.leakage_result["leakage_errors"] == ["sanitized issue"]
    assert result.leakage_result["draft_check"]["status"] == "passed"


def test_unbound_and_contradictory_historical_evidence_abstains(monkeypatch):
    trip = _trip(_checked_result(monkeypatch))
    for edits in (
        {"draft_check_source_sha256": None},
        {"traveler_bundle_leaks": ["subsequent flag"]},
        {"draft_check": {**trip["safety"]["draft_check"], "version": 1}},
        {"draft_check": {**trip["safety"]["draft_check"], "version": 99}},
    ):
        assert not TripResponse.from_dict({**trip, "safety": {**trip["safety"], **edits}}).safety.get("draft_check")

    old_safety = {**trip["safety"], "draft_check": {**trip["safety"]["draft_check"], "version": 1}}
    assert SafetyResult.model_validate(old_safety).draft_check is None


def test_workbench_edit_then_reassessment_replaces_the_check_on_the_same_trip(monkeypatch, tmp_path, file_tripstore):
    from spine_api.server import AgencySettingsStore, get_trip, patch_trip
    from spine_api.services.trip_lifecycle_service import persist_reassessment_result

    result = _checked_result(monkeypatch)
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path)
    monkeypatch.setattr(AgencySettingsStore, "load", lambda _: SimpleNamespace(
        autonomy=SimpleNamespace(auto_reprocess_on_edit=False),
    ))
    agency = SimpleNamespace(id="test-agency")
    operator = SimpleNamespace(id="test-operator")
    store = persistence.TripStore
    trip_id = store.save_trip(_trip(result), agency_id=agency.id)
    assert get_trip(trip_id, agency).safety["draft_check"]["status"] == "passed"
    edited_note = NOTE + " We prefer a later departure."
    patched = patch_trip(trip_id, TripPatchRequest.model_validate({"customerMessage": edited_note, "agentNotes": ""}), agency, operator)
    assert patched.reassess is None and get_trip(trip_id, agency).reassess is None
    assert patched.customerMessage == edited_note and not patched.safety.get("draft_check")
    assert not get_trip(trip_id, agency).safety.get("draft_check")

    new_result = orchestration.run_spine_once(
        [SourceEnvelope.from_freeform(edited_note)], strict_leakage=False, stage_callback=lambda *_: None,
    )
    new_output = {
        "run_id": "run-after-edit", "packet": new_result.packet.to_dict(),
        "decision": asdict(new_result.decision), "strategy": new_result.strategy.to_dict(),
        "safety": new_result.leakage_result, "traveler_bundle": new_result.traveler_bundle.to_traveler_dict(),
        "meta": {"fixture_id": "test-draft-reassessment", "submission": {"raw_note": edited_note}},
    }
    stored = store.get_trip_for_agency(trip_id, agency.id)
    persist_reassessment_result(
        stored, new_output, agency_id=agency.id, user_id=operator.id, trip_store=store,
        audit_store=SimpleNamespace(log_event=lambda *_: None),
    )
    refreshed = get_trip(trip_id, agency)
    assert refreshed.id == trip_id and refreshed.run_id == "run-after-edit"
    assert refreshed.safety["draft_check"] == new_result.leakage_result["draft_check"]


def test_queued_edit_reopens_tracks_newest_revision_and_drops_failed_check(monkeypatch, tmp_path, file_tripstore):
    from spine_api import run_ledger, server
    from spine_api.services import pipeline_execution_service, trip_lifecycle_service, work_intake

    result = _checked_result(monkeypatch)
    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path)
    monkeypatch.setattr(run_ledger, "RUNS_DIR", tmp_path / "runs")
    monkeypatch.setattr(run_ledger, "_checkpoint_store", lambda: None)
    monkeypatch.setattr(server.AuditStore, "log_event", lambda *_: None)
    monkeypatch.setattr(work_intake, "classify_and_record", lambda *_, **__: None)
    monkeypatch.setattr(server.AgencySettingsStore, "load", lambda _: SimpleNamespace(
        autonomy=SimpleNamespace(auto_reprocess_on_edit=True, auto_reprocess_stages={"discovery": True}),
    ))
    # A generated UUID can contain a phone-shaped numeric tail.
    run_ids = iter(("aaaaaaaa-bbbb-4ccc-8ddd-123456789012", "aaaaaaaa-bbbb-4ccc-8ddd-123456789013"))
    monkeypatch.setattr(trip_lifecycle_service, "uuid", SimpleNamespace(uuid4=lambda: next(run_ids)))
    # Hold dispatch so both edits land before the first worker gets CPU time.
    real_worker = server._execute_spine_pipeline
    monkeypatch.setattr(server, "_execute_spine_pipeline", lambda *_: None)
    monkeypatch.setattr(server, "_close_inherited_lock_fds", lambda: None)
    monkeypatch.setattr(pipeline_execution_service, "_acquire_trip_run_lock", lambda *_: (None, None))
    agency = SimpleNamespace(id="test-agency")
    operator = SimpleNamespace(id="test-operator")
    store = persistence.TripStore
    trip_id = store.save_trip(_trip(result), agency_id=agency.id)

    def edit(note):
        return server.patch_trip(trip_id, TripPatchRequest.model_validate(
            {"customerMessage": note, "agentNotes": ""},
        ), agency, operator)

    original = edit(NOTE + " Our travel dates have changed.")
    queued_id = original.reassess["run_id"]
    reopened = server.get_trip(trip_id, agency)
    assert reopened.reassess == original.reassess and not reopened.safety.get("draft_check")
    assert run_ledger.RunLedger.get_meta(queued_id)["auto_edit_source_revision"] == reopened.updated_at

    newer = edit(NOTE + " We want to arrive in March.")
    assert newer.reassess["run_id"] != queued_id
    real_worker(queued_id, {"raw_note": original.customerMessage}, agency.id, operator.id, trip_id)
    failure = run_ledger.RunLedger.get_meta(queued_id)
    assert failure["state"] == "failed" and "superseded" in failure["error_message"]
    assert server.get_trip(trip_id, agency).reassess == newer.reassess
    run_ledger.RunLedger.fail(newer.reassess["run_id"], "test", "Simulated failure")
    failed = server.get_trip(trip_id, agency)
    assert failed.reassess is None and not failed.safety.get("draft_check")
    assert failed.customerMessage == newer.customerMessage and failed.run_id == "run-proof"
