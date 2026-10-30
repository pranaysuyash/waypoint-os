"""Tests for the C1+C2 band engine (safety-scoring spec implementation)."""

import pytest

from src.intake.safety_band import BAND_LABELS, assess_safety_band

_ADVISORY_PROV = {"source_id": "fcdo-content-api", "retrieved_at": "2026-10-30T00:00:00+00:00"}
_HOMICIDE = {
    "rate_per_100k": 2.815,
    "year": "2022",
    "provenance": {"source_id": "worldbank-api", "retrieved_at": "2026-10-30T00:00:00+00:00"},
}


def test_c1_gate_do_not_travel_is_terminal():
    out = assess_safety_band(advisory_band="4", advisory_provenance=_ADVISORY_PROV)
    assert out["band"] == "4" and out["label"] == "Do not travel"


def test_band1_all_clear_with_c2_annotation():
    out = assess_safety_band(advisory_band="1", advisory_provenance=_ADVISORY_PROV, homicide=_HOMICIDE)
    assert out["band"] == "1"
    assert out["components"]["c2_violent_crime"]["rate_per_100k"] == 2.815
    assert "c2_violent_crime" in out["coverage"]
    assert out["coverage_gaps"] == ["c3_neighborhood", "c4_events"]


def test_band2_never_raises_on_crime_alone():
    hot = dict(_HOMICIDE, rate_per_100k=25.0)  # way above the decile line
    out = assess_safety_band(advisory_band="2", advisory_provenance=_ADVISORY_PROV, homicide=hot)
    assert out["band"] == "2"  # C2 alone cannot raise


def test_band2_raises_to_3_only_with_crime_and_events():
    hot = dict(_HOMICIDE, rate_per_100k=25.0)
    out = assess_safety_band(
        advisory_band="2", advisory_provenance=_ADVISORY_PROV, homicide=hot, events_pulse=True
    )
    assert out["band"] == "3"
    assert "c4_events" in out["coverage"]


def test_gaps_honest_when_c2_missing():
    out = assess_safety_band(advisory_band="1", advisory_provenance=_ADVISORY_PROV)
    assert "c2_violent_crime" in out["coverage_gaps"]
    assert "c2_violent_crime" not in out["components"]


def test_neighborhood_annotates_but_never_moves_band():
    hood = {
        "total_crimes": 5024,
        "month": "2025-09",
        "traveler_relevance": {"theft": 1664, "theft_pickpocket": 1254},
        "provenance": {"source_id": "data.police.uk", "retrieved_at": "2026-10-30T00:00:00+00:00"},
    }
    # Even a very high-crime neighborhood cannot raise the band (C3 annotates)
    out = assess_safety_band(
        advisory_band="1", advisory_provenance=_ADVISORY_PROV, neighborhood=hood
    )
    assert out["band"] == "1"
    assert out["components"]["c3_neighborhood"]["total_crimes"] == 5024
    assert "c3_neighborhood" in out["coverage"]
    assert "c3_neighborhood" not in out["coverage_gaps"]
    assert out["provenance"][-1]["source_id"] == "data.police.uk"


def test_provenance_always_carried():
    out = assess_safety_band(advisory_band="3", advisory_provenance=_ADVISORY_PROV, homicide=_HOMICIDE)
    assert out["provenance"][0]["source_id"] == "fcdo-content-api"
    assert out["provenance"][1]["source_id"] == "worldbank-api"


def test_invalid_band_rejected():
    with pytest.raises(ValueError, match="invalid advisory band"):
        assess_safety_band(advisory_band="9", advisory_provenance=_ADVISORY_PROV)


def test_band_labels_complete():
    assert set(BAND_LABELS) == {"1", "2", "3", "4"}
