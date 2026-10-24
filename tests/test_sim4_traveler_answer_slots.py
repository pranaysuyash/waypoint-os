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
    aliases = _apply_answers_to_facts(
        extracted, _answers(("origin_city", "kolkata"), ("date_window", "nov 16 to nov 19")), TOKEN, NOW
    )
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
    aliases = _apply_answers_to_facts(
        extracted, _answers(("budget", "1.9 lakh"), ("party_size", "5")), TOKEN, NOW
    )
    assert aliases["budget"] == "1.9 lakh"
    assert aliases["party"] == 5
    assert extracted["facts"]["budget_raw_text"]["value"] == "1.9 lakh"
