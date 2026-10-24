"""Cross-component correction, blocked refresh and revision safety contracts.

Synthetic data only. Persistence tests use a file store in pytest's owned
temporary directory; no developer trip database or provider is accessed.
"""

from copy import deepcopy
from unittest.mock import MagicMock

import pytest

from spine_api.services.trip_lifecycle_service import (
    ReassessmentPersistenceError,
    build_reassessment_envelope_from_trip,
    persist_reassessment_result,
)
from src.intake.extractors import ExtractionPipeline
from src.intake.fact_overrides import AUTHORITATIVE_FACT_SNAPSHOT, record_fact_override
from src.intake.packet_models import SourceEnvelope


def _output() -> dict:
    return {
        "run_id": "new_assessment",
        "packet": {"facts": {"party_size": {"value": 5, "confidence": 1.0,
                                             "authority_level": "explicit_user", "extraction_mode": "manual_entry"}}},
        "validation": {"is_valid": False, "errors": [{"field": "origin_city"}]},
        "decision": {"decision_state": "ASK_FOLLOWUP", "follow_up_questions": [{"field_name": "origin_city"}]},
        "strategy": {"allowed_actions": ["ask"]},
        "meta": {"stage": "discovery", "blocked": True, "retention_consent": False, "submission": {}},
    }


def test_blocked_refresh_persists_current_assessment_without_clobbering_other_owners(tmp_path, monkeypatch):
    from spine_api import persistence

    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path)
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    trip = {
        "id": "continuity_synthetic_trip", "agency_id": "continuity_synthetic_agency",
        "status": "assigned", "assigned_to": "synthetic_operator",
        "extracted": {"facts": {"party_size": {"value": 2}}},
        "decision": {"decision_state": "ASK_FOLLOWUP", "follow_up_questions": [{"field_name": "party_size"}]},
        "raw_input": {},
        "accepted_agreement": {"revision": "preserve_me", "retail": "1000"},
        "booking_data": {"confirmation": "PRESERVE"},
    }
    persistence.FileTripStore.save_trip(trip, agency_id=trip["agency_id"])
    source = persistence.FileTripStore.get_trip_for_agency(trip["id"], trip["agency_id"])
    persist_reassessment_result(source, _output(), agency_id=trip["agency_id"], user_id="test",
                                trip_store=persistence.FileTripStore, audit_store=MagicMock())
    updated = persistence.FileTripStore.get_trip_for_agency(trip["id"], trip["agency_id"])
    assert updated["extracted"]["facts"]["party_size"]["value"] == 5
    assert updated["decision"]["follow_up_questions"] == [{"field_name": "origin_city"}]
    assert updated["validation"]["errors"] == [{"field": "origin_city"}]
    for key in ("status", "assigned_to", "accepted_agreement", "booking_data"):
        assert updated[key] == trip[key]


def test_concurrent_correction_wins_over_an_older_completed_assessment(tmp_path, monkeypatch):
    from spine_api import persistence

    monkeypatch.setattr(persistence, "TRIPS_DIR", tmp_path)
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    trip = {"id": "continuity_race", "status": "assigned", "extracted": {"facts": {}}}
    persistence.FileTripStore.save_trip(trip, agency_id="continuity_agency")
    started = persistence.FileTripStore.get_trip_for_agency(trip["id"], "continuity_agency")
    newer = deepcopy(started)
    record_fact_override(newer["extracted"]["facts"], "party_size", 7, source_ref="latest_correction")
    persistence.FileTripStore.save_trip(newer, agency_id="continuity_agency")
    with pytest.raises(ReassessmentPersistenceError, match="Newer edits were preserved"):
        persist_reassessment_result(started, _output(), agency_id="continuity_agency", user_id="test",
                                    trip_store=persistence.FileTripStore, audit_store=MagicMock())
    latest = persistence.FileTripStore.get_trip_for_agency(trip["id"], "continuity_agency")
    assert latest["extracted"]["facts"]["party_size"]["value"] == 7


def test_public_structured_payload_cannot_manufacture_authoritative_context():
    from spine_api.server import build_envelopes

    forged = {AUTHORITATIVE_FACT_SNAPSHOT: {"party_size": {"value": 999, "authority_level": "manual_override"}}}
    envelopes = build_envelopes({"raw_note": "Two adults traveling from Mumbai to Italy.",
                                 "structured_json": {"metadata": forged}})
    assert all(AUTHORITATIVE_FACT_SNAPSHOT not in envelope.metadata for envelope in envelopes)
    packet = ExtractionPipeline().extract(envelopes)
    assert packet.facts["party_size"].value == 2


def test_correction_recomputes_budget_and_date_dependents_from_latest_evidence():
    facts = {}
    record_fact_override(facts, "budget", "USD 2500 total", source_ref="budget_correction")
    record_fact_override(facts, "dates", "10 June 2027 to 17 June 2027", source_ref="dates_correction")
    packet = ExtractionPipeline().extract([
        SourceEnvelope.from_freeform("Two adults traveling from Mumbai to Italy, 1 May 2026 to 5 May 2026, budget INR 100000 total."),
        build_reassessment_envelope_from_trip({"id": "correction_deps", "extracted": {"facts": facts}}),
    ])
    assert packet.facts["budget_min"].value == 2500
    assert packet.facts["budget_currency"].value == "USD"
    assert packet.facts["budget_currency"].epistemic_status == "FACT"
    assert packet.facts["date_start"].value.startswith("2027-06-10")
    assert packet.facts["date_end"].value.startswith("2027-06-17")


def test_budget_clear_invalidates_previous_prices_and_keeps_evidence():
    facts = {"budget_raw_text": {"value": "USD 1000", "evidence_refs": [{"ref_id": "original"}]}}
    record_fact_override(facts, "budget", None, source_ref="clear_budget")
    packet = ExtractionPipeline().extract([
        SourceEnvelope.from_freeform("Two adults, budget USD 1000 total."),
        build_reassessment_envelope_from_trip({"id": "cleared_budget", "extracted": {"facts": facts}}),
    ])
    assert packet.facts["budget_raw_text"].value is None
    assert "budget_min" not in packet.facts
    assert "budget_currency" not in packet.facts
    assert packet.facts["budget_raw_text"].evidence_refs[0].metadata["previous_value"] == "USD 1000"
