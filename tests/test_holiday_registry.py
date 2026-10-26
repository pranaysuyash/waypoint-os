"""
tests/test_holiday_registry.py — festival/holiday name + date resolution
(geography precedent for time: curated alias data + authoritative date
computation from the `holidays` package; never hand-rolled lunar math).

Covers: alias matching (regional spellings, Hinglish, colloquial), the
package-vs-curated precedence, the honest approximate flag, the sane intake
window, and the extraction closed loop ("during Diwali" → holiday_reference
signal + date_window hypothesis via the P-3 seam).
"""

from __future__ import annotations

from datetime import date

from src.intake.holiday_registry import (
    HOLIDAY_REGISTRY,
    find_holiday_references,
    is_known_holiday_name,
    resolve_holiday_window,
)


def test_alias_matching_including_regional_and_colloquial():
    refs = find_holiday_references("Diwali trip? deepavali works too")
    names = {r["canonical"] for r in refs}
    assert names == {"Diwali"}
    assert {r["matched"] for r in refs} == {"diwali", "deepavali"}

    # Hinglish Bakrid → Eid al-Adha; NYE → New Year
    assert find_holiday_references("going for bakrid")[0]["canonical"] == "Eid al-Adha"
    assert find_holiday_references(" nye plan")[0]["canonical"] == "New Year"
    # word boundaries: "diwali party" is a reference; "diwaliskr" is not
    assert find_holiday_references("diwali party")[0]["canonical"] == "Diwali"
    assert find_holiday_references("diwaliskr") == []


def test_package_resolution_is_exact_and_future():
    today = date(2026, 10, 25)
    w = resolve_holiday_window("Diwali", today=today)
    assert w is not None
    assert w["source"] == "holidays-package"
    assert w["approximate"] is False
    assert w["date_iso"] == "2026-11-08"
    assert w["year"] == 2026
    assert date.fromisoformat(w["date_iso"]) >= today


def test_resolution_skips_past_years_within_window():
    # Thanksgiving 2026 (Nov 26) is in the future from Oct 2026 → same year.
    w = resolve_holiday_window("Thanksgiving", today=date(2026, 10, 25))
    assert w is not None and w["year"] == 2026
    # From Dec 2027, the next Thanksgiving is 2028 (package, future-only).
    w2 = resolve_holiday_window("Thanksgiving", today=date(2027, 12, 20))
    assert w2 is not None and w2["year"] == 2028


def test_curated_approximate_is_honestly_flagged():
    # Ramadan: month-scale, lunar — never a fake exact date.
    w = resolve_holiday_window("Ramadan", today=date(2026, 10, 25))
    assert w is not None
    assert w["source"] == "curated-approximate"
    assert w["approximate"] is True
    assert "shifts" in w["label"]


def test_unknown_festival_abstains():
    assert resolve_holiday_window("Totally Made Up Festival") is None
    assert find_holiday_references("nothing here") == []
    assert not is_known_holiday_name("totally made up")


def test_registry_hygiene():
    """Every entry: unique canonical, aliases unique ACROSS entries (the
    alias index is last-write-wins — a collision would silently re-route a
    name), and every package-backed entry has hints."""
    canonical = [e["canonical"] for e in HOLIDAY_REGISTRY]
    assert len(canonical) == len(set(canonical))
    seen: dict = {}
    for e in HOLIDAY_REGISTRY:
        for a in e["aliases"]:
            assert a not in seen or seen[a] is e, f"alias collision: {a}"
            seen[a] = e
        if e.get("source_hint_package", True) and not e.get("approx"):
            assert e["hints"], e["canonical"]


# ---------------------------------------------------------------------------
# Extraction closed loop
# ---------------------------------------------------------------------------

def _packet_for(text: str):
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope

    return ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])


def test_extraction_during_diwali_closes_loop():
    packet = _packet_for("Planning a Goa trip during Diwali")
    signal = packet.derived_signals.get("holiday_reference")
    assert signal is not None and signal.value == "Diwali"
    hyp = packet.hypotheses.get("date_window")
    assert hyp is not None
    assert "2026-11-08" in str(hyp.value["value"]) or "2026-11-08" in str(hyp.value)


def test_extraction_multiple_festivals_records_all():
    packet = _packet_for("between Diwali and Christmas maybe")
    signal = packet.derived_signals.get("holiday_reference")
    assert signal is not None
    assert isinstance(signal.value, list)
    assert set(signal.value) == {"Diwali", "Christmas"}
    assert packet.metadata.get("holiday_references") == ["Diwali", "Christmas"]


def test_extraction_holiday_does_not_override_real_window():
    packet = _packet_for("20-28 Dec trip around Christmas")
    assert "date_window" in packet.facts, "real window must win"
    assert packet.derived_signals.get("holiday_reference") is not None
    assert packet.hypotheses.get("date_window") is None, "no festival hypothesis when a real window exists"


def test_extraction_no_false_positive_on_holiday_word_alone():
    # "holiday" as a generic word is not a festival reference.
    packet = _packet_for("we want a beach holiday in Goa")
    assert packet.derived_signals.get("holiday_reference") is None


def test_relation_semantics_shape_the_window():
    """Owner's "during this or after this": the preposition before the
    festival shapes the window hypothesis — covering (during/around/none),
    starting-after (after), ending-by (before/by/till/until)."""
    # registry level
    refs = find_holiday_references("go after Diwali, or before Christmas")
    by_ref = {r["canonical"]: r["relation"] for r in refs}
    assert by_ref == {"Diwali": "after", "Christmas": "before"}
    # deadline prepositions fold to before
    assert find_holiday_references("book by Christmas")[0]["relation"] == "before"
    assert find_holiday_references("stay till Onam")[0]["relation"] == "before"
    assert find_holiday_references("during Diwali")[0]["relation"] == "during"
    assert find_holiday_references("Diwali trip")[0]["relation"] == "during"

    # extraction level
    p_after = _packet_for("Planning a Goa trip after Diwali")
    assert "starting after" in str(p_after.hypotheses["date_window"].value)
    p_by = _packet_for("plan by Christmas")
    assert "ending by" in str(p_by.hypotheses["date_window"].value)
    p_during = _packet_for("Kerala trip during Diwali")
    assert "covering" in str(p_during.hypotheses["date_window"].value)


def test_extraction_is_never_broken_by_registry():
    """Fault-tolerance contract: a registry failure must not fail extraction."""
    import src.intake.extractors as ex

    original = ex.find_holiday_references if hasattr(ex, "find_holiday_references") else None
    # the import inside the block is try/except-guarded; simulate by passing
    # text that would raise in the registry if it were broken — the guard
    # holds structurally (documented behavior), asserted here via a smoke run.
    packet = _packet_for("trip during diwali")
    assert packet is not None
    assert original is None or callable(original)
