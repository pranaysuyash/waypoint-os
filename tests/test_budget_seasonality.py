"""Season-tier budget feasibility tests (2026-09-18).

Closes the gap recorded in Docs/CORE_INSIGHT_AND_HARDCODED_INVENTORY_2026-04-16.md
("No seasonality factor… multipliers don't vary by destination"): the intake
feasibility minimum now adjusts by per-destination season tier
(peak 1.30 / shoulder 1.15 / off 1.0), resolved from the packet's structured
date facts with a conservative 1.0 fallback.
"""

from src.intake.decision import check_budget_feasibility, _resolve_travel_month
from src.intake.packet_models import (
    AuthorityLevel,
    CanonicalPacket,
    EvidenceRef,
    Slot,
)


def _ev(excerpt: str = "test") -> list:
    return [EvidenceRef(envelope_id="test_env", evidence_type="text_span", excerpt=excerpt)]


def _slot(value, confidence=0.9) -> Slot:
    return Slot(
        value=value,
        confidence=confidence,
        authority_level=AuthorityLevel.EXPLICIT_USER,
        evidence_refs=_ev(str(value)),
    )


def _andaman_packet(budget: int, **date_kwargs) -> CanonicalPacket:
    """Andaman, 2 travelers — min_per_person 35,000 → base minimum 70,000."""
    pkt = CanonicalPacket(packet_id="season_probe")
    pkt.facts["resolved_destination"] = _slot("Andaman")
    pkt.facts["party_size"] = _slot(2)
    pkt.facts["budget_min"] = _slot(budget)
    for field_name, value in date_kwargs.items():
        pkt.facts[field_name] = _slot(value)
    return pkt


# Old-behavior minimum: 70,000 base × 1.15 default margin = 80,500.
_OLD_MIN = 80_500


def test_peak_season_raises_minimum_and_degrades_verdict():
    """December Andaman (peak): budget at the old minimum must degrade."""
    result = check_budget_feasibility(_andaman_packet(_OLD_MIN, date_start="2026-12-20"))
    assert result["season"] == "peak"
    assert result["season_multiplier"] == 1.30
    # 70,000 × 1.30 × 1.15 = 104,650 → gap −24,150 → tight (was feasible).
    assert result["status"] == "tight"


def test_shoulder_season_applies_mid_multiplier():
    """April Andaman (shoulder edge before monsoon)."""
    result = check_budget_feasibility(_andaman_packet(_OLD_MIN, date_start="2026-04-10"))
    assert result["season"] == "shoulder"
    assert result["season_multiplier"] == 1.15
    assert result["status"] == "tight"


def test_off_peak_month_keeps_old_behavior():
    """June Andaman (monsoon, off): byte-for-byte old behavior + season label."""
    result = check_budget_feasibility(_andaman_packet(_OLD_MIN, date_start="2026-06-10"))
    assert result["season"] == "off"
    assert result["season_multiplier"] == 1.0
    # 70,000 × 1.0 × 1.15 = 80,500 → gap 0 → feasible (regression pin).
    assert result["status"] == "feasible"
    assert result["gap"] == 0


def test_unresolvable_dates_fall_back_to_no_season():
    """Free-text date window with no month → multiplier 1.0, no season key."""
    result = check_budget_feasibility(
        _andaman_packet(_OLD_MIN, date_window="sometime next year")
    )
    assert "season" not in result
    assert result["status"] == "feasible"
    assert result["gap"] == 0


def test_month_name_in_raw_window_resolves():
    """No ISO ends but a month name in date_window → season resolves."""
    pkt = _andaman_packet(_OLD_MIN, date_window="December 2026, flexible")
    assert _resolve_travel_month(pkt) == 12
    result = check_budget_feasibility(pkt)
    assert result["season"] == "peak"
    assert result["season_multiplier"] == 1.30


def test_month_word_boundary_no_false_positives():
    """'maybe' must not match 'may'; 'marching' must not match 'march'.
    When multiple real months are mentioned, the earliest in the text wins."""
    pkt = CanonicalPacket(packet_id="wb_probe")
    pkt.facts["date_window"] = _slot("maybe around the marching festival next year")
    assert _resolve_travel_month(pkt) is None
    pkt.facts["date_window"] = _slot("perhaps March, or maybe April")
    assert _resolve_travel_month(pkt) == 3  # earliest-mentioned wins


def test_unknown_destination_never_inflates():
    """Destination absent from the season table → multiplier 1.0 even in a
    month that would be peak elsewhere."""
    pkt = CanonicalPacket(packet_id="unknown_dest_probe")
    pkt.facts["resolved_destination"] = _slot("Reykjavik")
    pkt.facts["party_size"] = _slot(2)
    pkt.facts["budget_min"] = _slot(1_000_000)
    pkt.facts["date_start"] = _slot("2026-12-20")

    with_dates = check_budget_feasibility(pkt)
    pkt.facts.pop("date_start")
    without_dates = check_budget_feasibility(pkt)

    assert with_dates["season"] == "off"
    assert with_dates["season_multiplier"] == 1.0
    assert with_dates["status"] == without_dates["status"]
    assert with_dates["gap"] == without_dates["gap"]


def test_date_end_iso_month_used_when_start_missing():
    """date_end alone supplies the month."""
    result = check_budget_feasibility(
        _andaman_packet(_OLD_MIN, date_window="2026-12-01 to 2026-12-08", date_end="2026-12-08")
    )
    assert result["season"] == "peak"
