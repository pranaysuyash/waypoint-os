"""
FND-0328 (Sim #4): traveler answers must land in extracted.facts as canonical
slots (dict of field -> slot) — never ``list(dict)`` which corrupts the
container into bare key strings — and must produce the trip-column aliases the
reassessment overlay consumes. Corrupted legacy rows heal in place.
"""

from __future__ import annotations

from spine_api.routers.public_asks import _apply_answers_to_facts

NOW = "2026-10-21T00:00:00+00:00"
TOKEN = "prop_trip_x_agency_1_ask_" + "a" * 24


def _answers(*pairs):
    return [{"field_name": f, "answer": a} for f, a in pairs]


def test_canonical_dict_facts_get_explicit_user_slots():
    extracted = {"facts": {"origin_city": {"value": None, "confidence": 0.0, "authority_level": "system", "extraction_mode": "direct_extract"}}}
    aliases, rejected = _apply_answers_to_facts(
        extracted, _answers(("origin_city", "kolkata"), ("date_window", "nov 16 to nov 19")), TOKEN, NOW
    )
    assert rejected == []
    slot = extracted["facts"]["origin_city"]
    assert slot["value"] == "kolkata"
    assert slot["authority_level"] == "explicit_user"
    assert slot["epistemic_status"] == "FACT"
    assert slot["extraction_mode"] == "traveler_ask_link"
    assert slot["evidence_refs"][0]["evidence_type"] == "manual_entry"
    assert slot["evidence_refs"][0]["metadata"]["channel"] == "ask_link"
    assert slot["supersedes"] == "direct_extract"  # prior slot's extraction context
    # aliases the reassessment overlay consumes
    assert aliases["origin"] == "kolkata"
    assert aliases["dateWindow"] == "nov 16 to nov 19"


def test_corrupted_list_facts_heal_in_place():
    # shape produced by the pre-fix write: bare key strings + one answer dict
    corrupted = ["origin_city", "date_window", "trip_purpose",
                 {"field": "origin_city", "value": "kolkata", "source": "traveler_ask"}]
    extracted = {"facts": corrupted}
    _apply_answers_to_facts(extracted, _answers(("trip_purpose", "anniversary pilgrimage")), TOKEN, NOW)
    facts = extracted["facts"]
    assert isinstance(facts, dict)
    assert facts["trip_purpose"]["value"] == "anniversary pilgrimage"
    # the surviving dict item is normalized to a slot with the answer's shape
    assert facts["origin_city"]["value"] == "kolkata"


def test_missing_facts_container_creates_dict():
    extracted = {}
    _apply_answers_to_facts(extracted, _answers(("origin_city", "delhi")), TOKEN, NOW)
    assert extracted["facts"]["origin_city"]["value"] == "delhi"


def test_budget_and_party_aliases():
    extracted = {"facts": {}}
    aliases, rejected = _apply_answers_to_facts(
        extracted, _answers(("budget", "1.9 lakh"), ("party_size", "5")), TOKEN, NOW
    )
    assert rejected == []
    assert aliases["budget"] == "1.9 lakh"
    assert aliases["party"] == 5
    assert extracted["facts"]["budget_raw_text"]["value"] == "1.9 lakh"


def test_answer_rejected_when_slot_holds_higher_authority():
    """inv-2 fact-store tranche (2026-11-03): a traveler answer (explicit_user)
    must never regress an operator's manual_override correction — the write is
    rejected and reported, the operator's value preserved."""
    extracted = {"facts": {
        "origin_city": {
            "value": "jaipur (operator-corrected)", "confidence": 1.0,
            "authority_level": "manual_override",
            "extraction_mode": "manual_entry",
        },
    }}
    aliases, rejected = _apply_answers_to_facts(
        extracted, _answers(("origin_city", "kolkata")), TOKEN, NOW
    )
    # Operator's manual correction survives untouched.
    assert extracted["facts"]["origin_city"]["value"] == "jaipur (operator-corrected)"
    assert extracted["facts"]["origin_city"]["authority_level"] == "manual_override"
    # No alias leaked — the reassessment overlay must not consume the answer.
    assert "origin" not in aliases
    # The rejection is reported honestly with the preserved value named.
    assert len(rejected) == 1
    assert rejected[0]["field_name"] == "origin_city"
    assert "manual_override" in rejected[0]["reason"]


def test_answer_at_equal_authority_still_updates():
    """Same-authority rewrite (traveler corrects their own earlier answer) applies."""
    extracted = {"facts": {
        "origin_city": {
            "value": "kolkata", "confidence": 1.0,
            "authority_level": "explicit_user",
            "extraction_mode": "traveler_ask_link",
        },
    }}
    aliases, rejected = _apply_answers_to_facts(
        extracted, _answers(("origin_city", "delhi")), TOKEN, NOW
    )
    assert rejected == []
    assert extracted["facts"]["origin_city"]["value"] == "delhi"
    assert aliases["origin"] == "delhi"
