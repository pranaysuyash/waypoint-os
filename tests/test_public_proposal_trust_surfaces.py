"""Gap-4 trust surfaces on the public proposal (2026-11-03; confidence-clause
removal per sim-pass red-team finding 2026-11-07).

why_this_fits is deterministic — built only from persisted decision facts —
and open_questions carries field names so the repair state is visible to the
traveler it protects. Internal planning confidence is NEVER rendered to
travelers (agent-model metric).
"""

from __future__ import annotations

from spine_api.routers.public_proposals import _public_open_questions, _why_this_fits


def _trip(decision: dict) -> dict:
    return {"decision": decision}


def test_why_this_fits_built_from_persisted_rationale():
    trip = _trip({
        "rationale": {
            "feasibility": "feasible",
            "budget_verdict": "within_budget",
            "budget_total_low": 180_000,
            "budget_total_high": 220_000,
            "soft_blockers": [{"field_name": "origin_city"}],
        },
    })
    text = _why_this_fits(trip)
    assert text is not None
    assert "feasibility check: feasible" in text
    assert "within_budget" in text
    assert "≈180,000–220,000" in text
    assert "1 item(s) need your confirmation" in text


def test_confidence_never_renders_on_public_page():
    """Sim-pass red-team finding (2026-11-07): internal planning confidence is
    an agent-model metric — telling a traveler 'the model is 62% sure'
    undermines trust. Never rendered, in any combination."""
    trip = _trip({"rationale": {"confidence": 0.856}})
    text = _why_this_fits(trip)
    # confidence-only rationale has no traveler-safe clause -> None
    assert text is None

    trip2 = _trip({"rationale": {"confidence": 0.4, "feasibility": "feasible"}})
    text2 = _why_this_fits(trip2)
    assert text2 is not None
    assert "confidence" not in text2.lower()


def test_empty_rationale_returns_none():
    assert _why_this_fits(_trip({})) is None
    assert _why_this_fits(_trip({"rationale": {}})) is None
    assert _why_this_fits(_trip({"rationale": "not-a-dict"})) is None


def test_why_this_fits_skips_absent_clauses():
    trip = _trip({"rationale": {"soft_blockers": [{"field_name": "origin_city"}]}})
    text = _why_this_fits(trip)
    assert text == (
        "This plan was selected for you: 1 item(s) need your confirmation before booking."
    )


def test_open_questions_public_safe_projection():
    trip = _trip({
        "follow_up_questions": [
            {"field_name": "origin_city", "question": "Which city would you fly out from?", "priority": "high", "internal": "metadata-must-not-leak"},
            {"field_name": "", "question": "no field name — dropped"},
            {"field_name": "dates", "question": ""},
            "not-a-dict",
        ],
    })
    out = _public_open_questions(trip)
    assert len(out) == 1
    q = out[0]
    assert q["field_name"] == "origin_city"
    assert q["question"] == "Which city would you fly out from?"
    assert q["priority"] == "high"
    assert "internal" not in q  # internal metadata never reaches the public page


def test_open_questions_empty_without_decision():
    assert _public_open_questions(_trip({})) == []
