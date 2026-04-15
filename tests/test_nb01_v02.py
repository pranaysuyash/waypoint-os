"""
NB01 v0.2 Tests — Pattern-based extraction against real module imports.

These test the ExtractionPipeline producing CanonicalPacket v0.2 from raw text.
All tests exercise extraction, NOT packet construction.

Run: uv run python -m pytest tests/test_nb01_v02.py -v
"""

import sys
import os
from datetime import datetime, timedelta

# Ensure src/ is on the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import pytest
from intake.packet_models import (
    Ambiguity,
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    OwnerConstraint,
    Slot,
    SourceEnvelope,
    SubGroup,
)
from intake.normalizer import Normalizer
from intake.extractors import ExtractionPipeline
from intake.validation import (
    DERIVED_ONLY_FIELDS,
    LEGACY_FIELD_NAMES,
    validate_packet,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def extract(text: str, source: str = "agency_notes", actor: str = "agent") -> CanonicalPacket:
    """Convenience: raw text → CanonicalPacket via ExtractionPipeline."""
    envelope = SourceEnvelope.from_freeform(text, source, actor)
    pipeline = ExtractionPipeline()
    return pipeline.extract([envelope])


# ===========================================================================
# TEST 1: Freeform + Ambiguity
# "Andaman or Sri Lanka" → destination_candidates list + destination_status + ambiguity
# ===========================================================================

class TestFreeformAmbiguity:
    def test_destination_candidates_from_or_pattern(self):
        text = "Family of 4 from Bangalore, want to go to Andaman or Sri Lanka, budget 3L, April dates."
        pkt = extract(text)

        # Must have destination_candidates as a list
        assert "destination_candidates" in pkt.facts, "destination_candidates not extracted"
        dests = pkt.facts["destination_candidates"].value
        assert isinstance(dests, list), f"destination_candidates should be list, got {type(dests)}"
        assert len(dests) == 2, f"Expected 2 candidates, got {len(dests)}"
        assert "Andaman" in dests
        assert "Sri Lanka" in dests

        # Must have destination_status
        assert "destination_status" in pkt.facts
        status = pkt.facts["destination_status"].value
        assert status == "semi_open", f"Expected semi_open, got {status}"

        # Must have ambiguity
        amb_matches = [a for a in pkt.ambiguities if a.field_name == "destination_candidates"]
        assert len(amb_matches) > 0, "No ambiguity detected for 'Andaman or Sri Lanka'"
        assert any(a.ambiguity_type == "unresolved_alternatives" for a in amb_matches)


# ===========================================================================
# TEST 2: Structured Budget
# "around 4-5L, can stretch" → budget_min, budget_max, budget_flexibility
# ===========================================================================

class TestStructuredBudget:
    def test_budget_parsed_as_numeric(self):
        text = "Family of 4, Singapore, 5 nights. Budget is 4-5L total, can stretch if it's good."
        pkt = extract(text)

        # budget_raw_text must exist
        assert "budget_raw_text" in pkt.facts
        raw = pkt.facts["budget_raw_text"].value
        assert "4" in str(raw) or "5" in str(raw)

        # budget_min and budget_max must be integers
        assert "budget_min" in pkt.facts, "budget_min not extracted"
        assert "budget_max" in pkt.facts, "budget_max not extracted"
        assert isinstance(pkt.facts["budget_min"].value, int), \
            f"budget_min should be int, got {type(pkt.facts['budget_min'].value)}"
        assert isinstance(pkt.facts["budget_max"].value, int), \
            f"budget_max should be int, got {type(pkt.facts['budget_max'].value)}"
        assert pkt.facts["budget_min"].value == 400000
        assert pkt.facts["budget_max"].value == 500000

        # budget_flexibility
        assert "budget_flexibility" in pkt.facts
        assert pkt.facts["budget_flexibility"].value == "stretch", \
            f"Expected stretch, got {pkt.facts['budget_flexibility'].value}"

        # budget_stretch_present ambiguity
        stretch_amb = [a for a in pkt.ambiguities if a.ambiguity_type == "budget_stretch_present"]
        assert len(stretch_amb) > 0, "budget_stretch_present ambiguity not detected"

    def test_budget_does_not_parse_from_date_tokens(self):
        text = (
            "2 adults from Bangalore to Singapore, 2026-05-12 to 2026-05-18, "
            "budget 3 lakhs, leisure."
        )
        pkt = extract(text)

        assert "budget_raw_text" in pkt.facts, "budget_raw_text not extracted"
        assert "budget_min" in pkt.facts, "budget_min not extracted"
        assert pkt.facts["budget_raw_text"].value in ("3 lakh", "3 lakhs"), \
            f"Unexpected budget_raw_text: {pkt.facts['budget_raw_text'].value}"
        assert pkt.facts["budget_min"].value == 300000, \
            f"Expected budget_min=300000, got {pkt.facts['budget_min'].value}"
        assert pkt.facts.get("date_start") and pkt.facts["date_start"].value == "2026-05-12"
        assert pkt.facts.get("date_end") and pkt.facts["date_end"].value == "2026-05-18"


# ===========================================================================
# TEST 3: Structured Dates
# "2026-03-15 to 2026-03-22" → date_start, date_end, date_confidence
# ===========================================================================

class TestStructuredDates:
    def test_iso_dates_parsed(self):
        text = "Bangalore to Singapore, 2026-03-15 to 2026-03-22, family of 4."
        pkt = extract(text)

        assert "date_window" in pkt.facts
        assert "date_start" in pkt.facts, "date_start not extracted"
        assert "date_end" in pkt.facts, "date_end not extracted"
        assert pkt.facts["date_start"].value == "2026-03-15"
        assert pkt.facts["date_end"].value == "2026-03-22"
        assert pkt.facts["date_confidence"].value == "exact"


# ===========================================================================
# TEST 4: Party Composition
# "2 adults, 2 kids ages 8 and 12, 1 elderly" → composition, child_ages, party_size
# ===========================================================================

class TestPartyComposition:
    def test_composition_and_ages(self):
        text = "Trip for 2 adults, 2 kids ages 8 and 12, and 1 elderly parent from Bangalore to Goa."
        pkt = extract(text)

        assert "party_composition" in pkt.facts, "party_composition not extracted"
        comp = pkt.facts["party_composition"].value
        assert comp.get("adults") == 2
        assert comp.get("children") == 2
        assert comp.get("elderly") == 1

        assert "child_ages" in pkt.facts, "child_ages not extracted"
        assert pkt.facts["child_ages"].value == [8, 12]

        # party_size should be derived from composition
        assert "party_size" in pkt.facts
        assert pkt.facts["party_size"].value == 5


# ===========================================================================
# TEST 5: Owner Constraints + Visibility
# "never book Hotel X" → OwnerConstraint with internal_only visibility
# ===========================================================================

class TestOwnerConstraintsVisibility:
    def test_internal_only_constraint(self):
        text = "Family of 4, Singapore trip. Note: never book Hotel Marina, their service is terrible."
        pkt = extract(text)

        assert "owner_constraints" in pkt.facts, "owner_constraints not extracted"
        constraints = pkt.facts["owner_constraints"].value
        assert isinstance(constraints, list)
        assert len(constraints) > 0

        # At least one constraint should be internal_only
        internal_ones = [c for c in constraints if c.visibility == "internal_only"]
        assert len(internal_ones) > 0, "No internal_only constraint found"
        assert any("Hotel Marina" in c.text or "hotel marina" in c.text.lower() for c in constraints)

    def test_traveler_safe_transformable(self):
        text = "Family of 4, Japan. They always prefer shorter layovers and ground-floor rooms."
        pkt = extract(text)

        assert "owner_constraints" in pkt.facts, "owner_constraints not extracted"
        constraints = pkt.facts["owner_constraints"].value
        transformable = [c for c in constraints if c.visibility == "traveler_safe_transformable"]
        assert len(transformable) > 0, "No traveler_safe_transformable constraint found"


# ===========================================================================
# TEST 6: Repeat Customer — Fact vs Derived Split
# customer_id in facts, is_repeat_customer ONLY in derived_signals
# ===========================================================================

class TestRepeatCustomerSplit:
    def test_fact_vs_derived(self):
        text = ("Past customer, Gupta family. They went to Dubai last time and loved it. "
                "Now want Japan, family of 4, budget 5L, March 2026.")
        pkt = extract(text)

        # is_repeat_customer must be in derived_signals, NOT in facts
        assert "is_repeat_customer" in pkt.derived_signals, \
            "is_repeat_customer should be a derived signal"
        assert pkt.derived_signals["is_repeat_customer"].value is True

        # It must NOT be in facts
        assert "is_repeat_customer" not in pkt.facts, \
            "is_repeat_customer must NOT be in facts — it is derived"

        # agency_notes should capture the past customer context
        assert "agency_notes" in pkt.facts, "agency_notes should capture repeat context"


# ===========================================================================
# TEST 7: Multi-Party Structure
# "3 families, different budgets" → SubGroup objects
# ===========================================================================

class TestMultiPartyStructure:
    def test_sub_groups_extracted(self):
        text = ("Coordinating trip for 3 families. Family A: 4 people, budget 3L. "
                "Family B: 3 people, budget 2.5L. Family C: 4 people, budget 2L. "
                "All going to Singapore in May.")
        pkt = extract(text)

        assert "sub_groups" in pkt.facts, "sub_groups not extracted"
        sub_groups = pkt.facts["sub_groups"].value
        assert isinstance(sub_groups, dict), f"sub_groups should be dict, got {type(sub_groups)}"
        assert len(sub_groups) > 0, "No sub-groups found"

        # Each sub-group should be a SubGroup instance
        for gid, group in sub_groups.items():
            assert isinstance(group, SubGroup), \
                f"Sub-group '{gid}' should be SubGroup, got {type(group)}"
            assert group.group_id == gid
            assert group.label
            assert group.size > 0

        # Should detect coordinator_group mode
        assert pkt.operating_mode == "coordinator_group", \
            f"Expected coordinator_group mode, got {pkt.operating_mode}"


# ===========================================================================
# TEST 8: Operating Mode — Top-Level, Not in Facts
# "medical emergency in Singapore" → packet.operating_mode, NOT facts["intake_mode"]
# ===========================================================================

class TestOperatingModeTopLevel:
    def test_emergency_mode(self):
        text = "URGENT: Medical emergency! Elderly father chest pain in Singapore. Need help NOW."
        pkt = extract(text)

        # operating_mode is top-level
        assert pkt.operating_mode == "emergency", \
            f"Expected emergency mode, got {pkt.operating_mode}"

        # Must NOT be in facts
        assert "intake_mode" not in pkt.facts, \
            "operating_mode must NOT be stored as a fact"

    def test_normal_intake_default(self):
        text = "Family of 4, Bangalore to Goa, weekend trip, budget 50K."
        pkt = extract(text)
        assert pkt.operating_mode == "normal_intake"


# ===========================================================================
# TEST 9: Urgency from date_end — Relative to Execution Date
# date_end = today + 5 days → urgency = "high"
# ===========================================================================

class TestUrgencyRelative:
    def test_high_urgency(self):
        future = datetime.now() + timedelta(days=5)
        date_str = future.strftime("%Y-%m-%d")
        text = f"Urgent trip! Singapore from {date_str} to {date_str}, family of 2."
        pkt = extract(text)

        assert "urgency" in pkt.derived_signals, "urgency derived signal not computed"
        urgency = pkt.derived_signals["urgency"].value
        assert urgency == "high", f"Expected high urgency (5 days), got {urgency}"
        assert pkt.derived_signals["urgency"].maturity == "verified"

    def test_medium_urgency(self):
        future = datetime.now() + timedelta(days=14)
        date_str = future.strftime("%Y-%m-%d")
        text = f"Singapore trip {date_str} to {date_str}, 2 adults."
        pkt = extract(text)

        assert "urgency" in pkt.derived_signals, "urgency derived signal not computed"
        urgency = pkt.derived_signals["urgency"].value
        assert urgency == "medium", f"Expected medium urgency (14 days), got {urgency}"


# ===========================================================================
# TEST 10: Schema Validation
# Packet missing date_window → validation report lists it
# ===========================================================================

class TestSchemaValidation:
    def test_missing_mvb_flagged(self):
        pkt = CanonicalPacket(packet_id="test_no_date")
        pkt.set_fact("origin_city", Slot(
            value="Bangalore", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="Bangalore")],
        ))
        # Missing: destination_candidates, date_window, party_size, budget_raw_text, trip_purpose

        report = validate_packet(pkt)
        assert not report.is_valid, "Packet missing MVB fields should be invalid"
        assert any(e.field == "destination_candidates" for e in report.errors)
        assert any(e.field == "date_window" for e in report.errors)
        assert any(e.field == "party_size" for e in report.errors)

    def test_valid_packet(self):
        pkt = CanonicalPacket(packet_id="test_valid")
        for name in ["destination_candidates", "origin_city", "date_window",
                      "party_size", "budget_raw_text", "trip_purpose"]:
            pkt.set_fact(name, Slot(
                value="test", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER,
                evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="test")],
            ))

        report = validate_packet(pkt)
        assert report.is_valid, f"Valid packet should pass: {report.errors}"
        assert report.error_count == 0


# ===========================================================================
# TEST 11: Legacy Field Rejection
# Packet with destination_city in facts → validation warning
# ===========================================================================

class TestLegacyFieldRejection:
    def test_legacy_names_warned(self):
        pkt = CanonicalPacket(packet_id="test_legacy")
        # Simulate v0.1 field leaking through
        pkt.facts["destination_city"] = Slot(
            value="Singapore", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="Singapore")],
        )
        pkt.set_fact("origin_city", Slot(
            value="Bangalore", confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="Bangalore")],
        ))
        pkt.set_fact("date_window", Slot(
            value="March 2026", confidence=0.8, authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="March 2026")],
        ))
        pkt.set_fact("party_size", Slot(
            value=4, confidence=0.9, authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="4")],
        ))
        pkt.set_fact("budget_raw_text", Slot(
            value="3L", confidence=0.8, authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="3L")],
        ))
        pkt.set_fact("trip_purpose", Slot(
            value="family", confidence=0.8, authority_level=AuthorityLevel.EXPLICIT_USER,
            evidence_refs=[EvidenceRef(envelope_id="test", evidence_type="text_span", excerpt="family")],
        ))

        report = validate_packet(pkt)
        assert not report.is_valid, "Packet with legacy field should be invalid"
        assert any("destination_city" in e.message for e in report.errors)


# ===========================================================================
# TEST 12: Derived-Only Fields Not in Facts
# is_repeat_customer never appears in packet.facts
# ===========================================================================

class TestDerivedOnlyNotInFacts:
    def test_derived_only_fields_absent_from_facts(self):
        text = "Past customer, Gupta family, Dubai 2025, now want Japan, 5L, family of 4."
        pkt = extract(text)

        for field_name in DERIVED_ONLY_FIELDS:
            assert field_name not in pkt.facts, \
                f"Derived-only field '{field_name}' found in facts — must be in derived_signals only"


# ===========================================================================
# TEST 13: Destination Candidates Valid Without resolved_destination
# NB01 never sets resolved_destination
# ===========================================================================

class TestDestinationCandidatesNoResolved:
    def test_no_resolved_destination_from_nb01(self):
        text = "Andaman or Sri Lanka, family of 4, April, budget 3L."
        pkt = extract(text)

        # destination_candidates must be set
        assert "destination_candidates" in pkt.facts

        # resolved_destination must NOT be set by NB01
        assert "resolved_destination" not in pkt.facts, \
            "NB01 must never set resolved_destination — that's NB02's job"


# ===========================================================================
# TEST 14: Owner Fields with internal_only Visibility Preserved
# owner fields are in packet but clearly marked for later sanitization
# ===========================================================================

class TestOwnerFieldsInternalOnly:
    def test_owner_constraints_have_visibility(self):
        text = ("Family trip to Maldives. "
                "Note: never book Resort X — plumbing broke last monsoon. "
                "Also: they prefer ground-floor rooms.")
        pkt = extract(text)

        if "owner_constraints" in pkt.facts:
            constraints = pkt.facts["owner_constraints"].value
            assert isinstance(constraints, list)
            for c in constraints:
                assert isinstance(c, OwnerConstraint), \
                    f"Owner constraint should be OwnerConstraint, got {type(c)}"
                assert c.visibility in ("internal_only", "traveler_safe_transformable"), \
                    f"Owner constraint must have visibility, got {c.visibility}"

            # At least one should be internal_only
            internal = [c for c in constraints if c.visibility == "internal_only"]
            assert len(internal) > 0, "No internal_only constraints found"


# ===========================================================================
# TEST 15: Every Derived Signal Has Maturity Tag
# No downstream code should treat stub as verified
# ===========================================================================

class TestDerivedSignalMaturityTags:
    def test_all_derived_signals_have_maturity(self):
        text = (
            "Past customer, Gupta family. They went to Dubai last time. "
            "Now want Japan trip, family of 4, 2 adults 2 kids, budget 4-5L, "
            "dates 2026-03-15 to 2026-03-22. Medical emergency — father has chest pain!"
        )
        pkt = extract(text)

        for name, slot in pkt.derived_signals.items():
            assert slot.maturity is not None, \
                f"Derived signal '{name}' has no maturity tag — must be stub/heuristic/verified"
            assert slot.maturity in ("stub", "heuristic", "verified"), \
                f"Derived signal '{name}' has invalid maturity: {slot.maturity}"

    def test_stub_signals_are_marked(self):
        text = "Singapore trip, family of 4, budget 3L."
        pkt = extract(text)

        assert "sourcing_path" in pkt.derived_signals, "sourcing_path derived signal not computed"
        assert pkt.derived_signals["sourcing_path"].maturity == "stub", \
            "sourcing_path should be tagged as stub (no real supplier data)"

    def test_verified_signals_are_marked(self):
        future = datetime.now() + timedelta(days=5)
        date_str = future.strftime("%Y-%m-%d")
        text = f"Urgent: Singapore {date_str} to {date_str}."
        pkt = extract(text)

        # urgency should be verified (computed from date math)
        if "urgency" in pkt.derived_signals:
            assert pkt.derived_signals["urgency"].maturity == "verified", \
                "urgency should be tagged as verified"



# ===========================================================================
# TEST: Schema roundtrip
# Extract → serialize → validate against schema
# ===========================================================================

class TestSchemaRoundtrip:
    def test_extracted_packet_serializes_and_validates(self):
        """Full roundtrip: extraction → to_dict() → schema validation."""
        text = (
            "Family of 4 from Bangalore, 2 adults 2 kids ages 8 and 12. "
            "Want Andaman or Sri Lanka, budget 4-5L, dates 2026-03-15 to 2026-03-22. "
            "Family vacation with kid-friendly activities. "
            "Note: never book Hotel X. Past customer, loved Dubai."
        )
        pkt = extract(text)

        # Serialize
        data = pkt.to_dict()

        # Verify schema version
        assert data["schema_version"] == "0.2"

        # Verify operating_mode is present
        assert "operating_mode" in data

        # Verify maturity tags on all derived signals
        for name, signal in data.get("derived_signals", {}).items():
            assert "maturity" in signal, f"Derived signal '{name}' missing maturity in serialized form"
            assert signal["maturity"] in ("stub", "heuristic", "verified"),                 f"Derived signal '{name}' has invalid maturity: {signal['maturity']}"

        # Validate with our validation layer
        report = validate_packet(pkt)
        # The packet should be valid (no errors) — warnings are OK
        assert report.error_count == 0, f"Schema roundtrip produced errors: {[e.message for e in report.errors]}"


# ===========================================================================
# REGRESSION: Hedging-extraction order and stop-word filter
# ===========================================================================

class TestHedgingExtractionOrder:
    """
    Bug: 'maybe Singapore' extracted as definite instead of semi_open
    because the single-destination regex matched before the hedging pattern.

    Fix: Hedging patterns (maybe, thinking about, perhaps, considering)
    are now checked BEFORE the general destination regex.
    """

    def test_maybe_pattern_produces_semi_open(self):
        """"maybe Singapore" → semi_open, not definite."""
        text = "maybe Singapore from Bangalore, 4 people"
        env = SourceEnvelope.from_freeform(text, "test_hedge_maybe")
        pkt = ExtractionPipeline().extract([env])
        ds = pkt.facts.get("destination_status")
        dc = pkt.facts.get("destination_candidates")
        assert ds is not None, "Should have destination_status"
        assert ds.value == "semi_open", f"Expected semi_open, got {ds.value}"
        assert dc.value == ["Singapore"], f"Expected ['Singapore'], got {dc.value}"

    def test_thinking_about_pattern_produces_semi_open(self):
        """"thinking about Singapore" → semi_open."""
        text = "thinking about Singapore from Bangalore, 4 people"
        env = SourceEnvelope.from_freeform(text, "test_hedge_think")
        pkt = ExtractionPipeline().extract([env])
        ds = pkt.facts.get("destination_status")
        assert ds is not None
        assert ds.value == "semi_open", f"Expected semi_open, got {ds.value}"

    def test_perhaps_pattern_produces_semi_open(self):
        """"perhaps Singapore" → semi_open."""
        text = "perhaps Singapore in March from Bangalore"
        env = SourceEnvelope.from_freeform(text, "test_hedge_perhaps")
        pkt = ExtractionPipeline().extract([env])
        ds = pkt.facts.get("destination_status")
        assert ds is not None
        assert ds.value == "semi_open", f"Expected semi_open, got {ds.value}"

    def test_definite_destination_still_definite(self):
        """Plain "Singapore from Bangalore" → still definite."""
        text = "Singapore from Bangalore, 4 people, March 2026"
        env = SourceEnvelope.from_freeform(text, "test_definite")
        pkt = ExtractionPipeline().extract([env])
        ds = pkt.facts.get("destination_status")
        dc = pkt.facts.get("destination_candidates")
        assert ds.value == "definite", f"Expected definite, got {ds.value}"
        assert dc.value == ["Singapore"], f"Expected ['Singapore'], got {dc.value}"

    def test_or_pattern_still_sem_open(self):
        """"Andaman or Sri Lanka" → semi_open (regression check)."""
        text = "Andaman or Sri Lanka from Bangalore, 4 people"
        env = SourceEnvelope.from_freeform(text, "test_or")
        pkt = ExtractionPipeline().extract([env])
        dc = pkt.facts.get("destination_candidates")
        assert dc.value == ["Andaman", "Sri Lanka"], f"Expected 2 candidates, got {dc.value}"


class TestStopWordFilter:
    """
    Bug: "We want to go somewhere nice" extracted "We" as a destination.

    Fix: Common pronouns and stop words filtered before is_known_destination.
    """

    def test_we_pronoun_filtered(self):
        """"We want to go somewhere nice" → no destination, not "We"."""
        text = "We want to go somewhere nice from Bangalore"
        env = SourceEnvelope.from_freeform(text, "test_stop_we")
        pkt = ExtractionPipeline().extract([env])
        dc = pkt.facts.get("destination_candidates")
        if dc and dc.value:
            assert "We" not in dc.value, f'"We" should be filtered, got {dc.value}'

    def test_real_destination_after_pronoun(self):
        """"I want to visit Singapore" → Singapore, not "I"."""
        text = "I want to visit Singapore from Bangalore"
        env = SourceEnvelope.from_freeform(text, "test_stop_i")
        pkt = ExtractionPipeline().extract([env])
        dc = pkt.facts.get("destination_candidates")
        assert dc is not None
        assert "I" not in dc.value, f'"I" should be filtered, got {dc.value}'
        assert "Singapore" in dc.value


# ===========================================================================
# Run
# ===========================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
