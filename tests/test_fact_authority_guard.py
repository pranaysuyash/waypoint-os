"""Authority-ranked fact-slot writes (inv-2 fact-store tranche, 2026-11-03).

Pins the invariant "answers can never regress": every canonical slot write
declares its authority level, and a write is rejected — returned as a
conflict, value preserved — when the stored slot carries strictly higher
authority. S2 evidence: the rejection path failed-before/passes-after is
covered by test_sim4_traveler_answer_slots.py's rejection test (the write
previously clobbered manual_override slots unconditionally).
"""

from __future__ import annotations

import pytest

from src.intake.fact_overrides import (
    explicit_fact_override,
    record_fact_override,
    slot_authority_rank,
    try_record_fact_override,
)


def _slot(value, authority="explicit_user", mode="traveler_ask_link"):
    return {
        "value": value,
        "confidence": 1.0,
        "authority_level": authority,
        "extraction_mode": mode,
        "evidence_refs": [{"metadata": {}}],
    }


def test_rejects_lower_authority_write_over_manual_override():
    facts = {"origin_city": _slot("jaipur", authority="manual_override")}
    slot, conflict = try_record_fact_override(facts, "origin_city", "kolkata", source_ref="ask_x")
    assert slot is None
    assert conflict is not None
    assert "manual_override" in conflict
    assert "jaipur" in conflict  # kept value preserved in the reason
    # The stored slot is untouched.
    assert facts["origin_city"]["value"] == "jaipur"


def test_allows_higher_authority_write_over_extracted_fact():
    facts = {"origin_city": _slot("kolkata", authority="explicit_user")}
    slot, conflict = try_record_fact_override(
        facts, "origin_city", "jaipur (operator)", authority_level="manual_override", source_ref="op_x"
    )
    assert conflict is None
    assert slot["value"] == "jaipur (operator)"
    assert slot["authority_level"] == "manual_override"


def test_equal_authority_rewrite_applies():
    facts = {"origin_city": _slot("kolkata", authority="explicit_user")}
    slot, conflict = try_record_fact_override(facts, "origin_city", "delhi", source_ref="ask_x")
    assert conflict is None
    assert facts["origin_city"]["value"] == "delhi"


def test_missing_slot_is_always_writable():
    facts = {}
    slot, conflict = try_record_fact_override(
        facts, "room_preference", "high floor", authority_level="explicit_owner", source_ref="mem_x"
    )
    assert conflict is None
    assert facts["room_preference"]["value"] == "high floor"
    assert facts["room_preference"]["authority_level"] == "explicit_owner"


def test_explicit_owner_adopt_over_derived_signal_applies():
    facts = {"dietary_requirements": _slot(None, authority="derived_signal")}
    slot, conflict = try_record_fact_override(
        facts, "dietary_requirements", "jain", authority_level="explicit_owner", source_ref="mem_x"
    )
    assert conflict is None
    assert facts["dietary_requirements"]["value"] == "jain"


def test_dependents_invalidated_on_applied_root_write():
    facts = {"budget_raw_text": _slot("2 lakh"), "budget_min": _slot(200000, authority="derived_signal")}
    slot, conflict = try_record_fact_override(
        facts, "budget_raw_text", "3 lakh", source_ref="ask_test_root"
    )
    assert conflict is None
    invalidated = facts["budget_min"]
    assert invalidated["value"] is None
    assert invalidated["extraction_mode"] == "invalidated_by_override"
    assert invalidated["derived_from"] == ["budget_raw_text"]


def test_record_fact_override_raises_on_conflict():
    facts = {"origin_city": _slot("jaipur", authority="manual_override")}
    with pytest.raises(ValueError, match="manual_override"):
        record_fact_override(facts, "origin_city", "kolkata")
    assert facts["origin_city"]["value"] == "jaipur"


def test_alias_canonicalization_in_guard():
    facts = {"budget_raw_text": _slot("2 lakh", authority="manual_override")}
    slot, conflict = try_record_fact_override(facts, "budget", "3 lakh", source_ref="ask_x")
    assert slot is None
    assert "budget_raw_text" in conflict


def test_slot_authority_rank_defaults_to_unknown():
    assert slot_authority_rank(None) == 7
    assert slot_authority_rank({"value": 1}) == 7
    assert slot_authority_rank({"authority_level": "manual_override"}) == 1


def test_explicit_fact_override_rejects_non_fact_authority():
    with pytest.raises(ValueError, match="fact authority"):
        explicit_fact_override(
            "origin_city", "kolkata", source_ref="x", authority_level="derived_signal"
        )


def test_explicit_fact_override_rejects_unknown_mode():
    with pytest.raises(ValueError, match="correction mode"):
        explicit_fact_override(
            "origin_city", "kolkata", source_ref="x", mode="telepathy"
        )


def test_adopted_from_memory_mode_is_valid_and_channeled():
    slot = explicit_fact_override(
        "room_preference", "high floor", source_ref="mem_1", mode="adopted_from_memory",
        authority_level="explicit_owner",
    )
    assert slot["extraction_mode"] == "adopted_from_memory"
    assert slot["evidence_refs"][0]["metadata"]["channel"] == "memory"
    assert slot["authority_level"] == "explicit_owner"
