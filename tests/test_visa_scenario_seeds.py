"""Visa scenario seeds + visa extraction regressions (2026-09-09 visa document audit).

Covers, against the REAL pipeline (no mocks):
- SC-960 / SC-961 corpus seeds (VA-04, VE-03): fixture-driven extraction +
  deterministic decision routing, expectations frozen from live behavior.
- VA-06: negation-aware visa_status extraction ("No visas yet" must mean
  required/not_applied, "no visa required" must mean not_required).
- VA-07: destination extraction must not leak the negation token "No" as a
  destination candidate (it is a real GeoNames city, so geography validation
  alone cannot filter it).
- visa_timeline rule high/medium urgency paths (the rule only engages via the
  credential-gated hybrid engine in the full spine, so its risk ladder is
  pinned here at the rule level).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.intake.decision import run_gap_and_decision
from src.intake.extractors import ExtractionPipeline
from src.intake.packet_models import CanonicalPacket, Slot, SourceEnvelope
from src.decision.rules import rule_visa_timeline_risk

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "scenarios"
SEED_FIXTURES = [
    "SC-960_visa_timeline_japan_business.json",
    "SC-961_visa_digital_nomad_portugal.json",
]


def _run_seed(fixture_name: str):
    payload = json.loads((FIXTURES_DIR / fixture_name).read_text(encoding="utf-8"))
    envelope = SourceEnvelope.from_freeform(
        payload["inputs"]["raw_note"], source="agency_notes", actor="agent"
    )
    packet = ExtractionPipeline().extract([envelope], stage=payload["stage"])
    result = run_gap_and_decision(packet)
    return payload, packet, result


@pytest.mark.parametrize("fixture_name", SEED_FIXTURES)
def test_seed_fixture_contract(fixture_name):
    """Each seed fixture's declared expectations hold on the live pipeline."""
    payload, packet, result = _run_seed(fixture_name)

    for field_name in payload["expected"]["required_packet_fields"]:
        slot = packet.facts.get(field_name)
        assert slot is not None and slot.value is not None, (
            f"{fixture_name}: required packet field {field_name} missing"
        )

    assert result.decision_state in payload["expected"]["allowed_decision_states"], (
        f"{fixture_name}: decision {result.decision_state} not in "
        f"{payload['expected']['allowed_decision_states']}"
    )


def test_sc960_visa_required_not_applied():
    """'No visas yet' must extract as required/not_applied (VA-06)."""
    _, packet, _ = _run_seed(SEED_FIXTURES[0])
    assert packet.facts["visa_status"].value == {
        "requirement": "required",
        "status": "not_applied",
    }


def test_sc960_destination_not_polluted_by_negation():
    """The 'No' negation token must not appear as a destination (VA-07)."""
    _, packet, _ = _run_seed(SEED_FIXTURES[0])
    destinations = packet.facts["destination_candidates"].value
    assert destinations == ["Japan"]


def test_sc961_digital_nomad_seed():
    _, packet, result = _run_seed(SEED_FIXTURES[1])
    assert packet.facts["destination_candidates"].value == ["Portugal"]
    assert packet.facts["visa_status"].value["requirement"] == "required"
    assert result.decision_state == "ASK_FOLLOWUP"


# ---------------------------------------------------------------------------
# VA-06: negation-aware visa_status extraction (pipeline-level, booking stage)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("note", "expected"),
    [
        # required / not applied
        ("Trip to Tokyo June 10 to 12 2027. No visas yet.", {"requirement": "required", "status": "not_applied"}),
        ("Trip to Tokyo June 10 to 12 2027. We don't have a visa yet.", {"requirement": "required", "status": "not_applied"}),
        # required / pending (applied, in process — must NOT be the critical
        # not_applied state; review cycle 1)
        ("Trip to Tokyo June 10 to 12 2027. Visa pending with the consulate.", {"requirement": "required", "status": "pending"}),
        # not required (must not be inverted by the 'required' substring)
        ("Trip to Paris June 10 to 12 2027. No visa required for our passports.", {"requirement": "not_required"}),
        ("Trip to Paris June 10 to 12 2027. Visa not required.", {"requirement": "not_required"}),
        # negated visa-free: the traveler does NOT have visa-free access, so
        # a visa IS required (review cycle 1 — ordering alone inverted this)
        ("Trip to London June 10 to 12 2027. We don't have visa-free transit.", {"requirement": "required", "status": "not_applied"}),
        # approved
        ("Trip to Tokyo June 10 to 12 2027. Visa approved last week.", {"requirement": "required", "status": "approved"}),
    ],
)
def test_visa_status_negation_forms(note, expected):
    envelope = SourceEnvelope.from_freeform(note, source="agency_notes", actor="agent")
    packet = ExtractionPipeline().extract([envelope], stage="booking")
    assert packet.facts["visa_status"].value == expected


@pytest.mark.parametrize(
    "note",
    [
        # VA-07 across ALL destination passes, not just the capitalized
        # regex pass (review cycle 1): verbless and verb-gated passes also
        # promoted "No" (a GeoNames city — alternate name of Ho, Ghana).
        "No trip booked yet, still deciding between Japan and Korea.",
        "Going to no particular destination, open to ideas for June 2027.",
        "No holiday planned this year, maybe next year.",
    ],
)
def test_negation_token_never_a_destination(note):
    envelope = SourceEnvelope.from_freeform(note, source="agency_notes", actor="agent")
    packet = ExtractionPipeline().extract([envelope], stage="booking")
    destinations = packet.facts.get("destination_candidates")
    values = destinations.value if destinations else []
    assert "No" not in values, f"negation token leaked into destinations: {values}"


def test_visa_status_discovery_stage_is_concern_flag_only():
    """Discovery/shortlist must keep the lightweight boolean gate, not full extraction."""
    envelope = SourceEnvelope.from_freeform(
        "Trip to Tokyo June 10 to 12 2027. No visas yet.",
        source="agency_notes",
        actor="agent",
    )
    packet = ExtractionPipeline().extract([envelope], stage="discovery")
    assert packet.facts.get("visa_status") is None


# ---------------------------------------------------------------------------
# visa_timeline rule risk ladder (rule-level; hybrid engine is credential-gated)
# ---------------------------------------------------------------------------

def _visa_packet(destination: str, urgency: str) -> CanonicalPacket:
    return CanonicalPacket(
        packet_id="test",
        facts={
            "visa_status": Slot(
                value={"requirement": "required", "status": "not_applied"},
                authority_level="explicit_user",
            ),
            "resolved_destination": Slot(value=destination, authority_level="explicit_user"),
        },
        derived_signals={"urgency": Slot(value=urgency, authority_level="derived")},
    )


def test_visa_timeline_high_urgency_long_lead_time_is_high_risk():
    result = rule_visa_timeline_risk(_visa_packet("China", "high"))
    assert result is not None
    assert result["risk_level"] == "high"
    assert result["visa_lead_time_days"] == 30


def test_visa_timeline_high_urgency_short_lead_time_is_medium_risk():
    # Japan lead time is 14 days — not > 14, so high urgency stays medium.
    result = rule_visa_timeline_risk(_visa_packet("Japan", "high"))
    assert result is not None
    assert result["risk_level"] == "medium"


def test_visa_timeline_low_urgency_is_low_risk():
    result = rule_visa_timeline_risk(_visa_packet("Japan", "low"))
    assert result is not None
    assert result["risk_level"] == "low"


def test_visa_timeline_domestic_is_low_risk():
    packet = CanonicalPacket(
        packet_id="test",
        facts={
            "visa_status": Slot(
                value={"requirement": "required", "status": "not_applied"},
                authority_level="explicit_user",
            ),
        },
        derived_signals={
            "domestic_or_international": Slot(value="domestic", authority_level="derived"),
        },
    )
    result = rule_visa_timeline_risk(packet)
    assert result is not None
    assert result["risk_level"] == "low"
