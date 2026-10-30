"""Tests for the C1 consensus combiner, C4 dict-seam wiring, and the
BD2.2 normalization enums."""

import pytest

from src.intake.data_normalization import (
    AdvisoryBand,
    AQIScale,
    CoverageGeneration,
    CrimeClass,
    HealthRequirement,
    PriceMethod,
    RuleSeverity,
    VisaStatus,
)
from src.intake.safety_band import advisory_consensus, assess_safety_band

_PROV = {"source_id": "s", "retrieved_at": "2026-10-30T00:00:00+00:00"}


# ---- advisory_consensus ----


def test_consensus_worst_band_wins():
    out = advisory_consensus([
        {"issuer": "fcdo", "band": "1", "provenance": _PROV},
        {"issuer": "statedept", "band": "3", "provenance": _PROV},
    ])
    assert out["band"] == "3"
    assert out["divergence"] is True
    assert out["issuers"] == ["fcdo", "statedept"]


def test_consensus_single_source_no_divergence():
    out = advisory_consensus([{"issuer": "fcdo", "band": "2", "provenance": _PROV}])
    assert out["band"] == "2" and out["divergence"] is False


def test_consensus_empty_rejected():
    with pytest.raises(ValueError, match="at least one"):
        advisory_consensus([])


def test_consensus_invalid_band_rejected():
    with pytest.raises(ValueError, match="invalid advisory band"):
        advisory_consensus([{"issuer": "x", "band": "9"}])


def test_consensus_do_not_travel_gates_even_if_others_clear():
    out = advisory_consensus([
        {"issuer": "a", "band": "1", "provenance": _PROV},
        {"issuer": "b", "band": "4", "provenance": _PROV},
        {"issuer": "c", "band": "1", "provenance": _PROV},
    ])
    assert out["band"] == "4"


# ---- assess_safety_band: consensus + events-dict seams ----


def test_assess_with_consensus_flags_divergence():
    out = assess_safety_band(
        advisories=[
            {"issuer": "fcdo", "band": "1", "provenance": {"source_id": "fcdo"}},
            {"issuer": "statedept", "band": "3", "provenance": {"source_id": "statedept"}},
        ]
    )
    assert out["band"] == "3"
    c1 = out["components"]["c1_advisory"]
    assert c1["source"] == "fcdo+statedept"
    assert out["provenance"][0]["confidence_flag"] == "issuing-governments-diverge"


def test_assess_with_consensus_agreement_no_flag():
    out = assess_safety_band(
        advisories=[
            {"issuer": "fcdo", "band": "2", "provenance": {"source_id": "fcdo"}},
            {"issuer": "smartraveller", "band": "2", "provenance": {"source_id": "smartraveller"}},
        ]
    )
    assert out["band"] == "2"
    assert "confidence_flag" not in out["provenance"][0]


def test_assess_events_dict_derives_pulse():
    events = {
        "article_count": 7,
        "sample_titles": ["Protest in central Tokyo"],
        "provenance": {"source_id": "gdelt-doc-api"},
    }
    out = assess_safety_band(advisory_band="1", advisory_provenance=_PROV, events=events)
    assert out["components"]["c4_events"]["active"] is True
    assert out["components"]["c4_events"]["article_count"] == 7
    assert "c4_events" in out["coverage"]


def test_assess_events_dict_zero_articles_is_honest_gap():
    events = {"article_count": 0, "sample_titles": [], "provenance": {"source_id": "gdelt-doc-api"}}
    out = assess_safety_band(advisory_band="1", advisory_provenance=_PROV, events=events)
    # zero articles = quiet, NOT a gap (the fetch succeeded and reported calm)
    assert out["components"]["c4_events"]["active"] is False
    assert "c4_events" in out["coverage"]


def test_assess_c2_raises_only_via_events_dict():
    hot = {"rate_per_100k": 25.0, "year": "2022", "provenance": {"source_id": "worldbank-api"}}
    events = {"article_count": 3, "sample_titles": [], "provenance": {"source_id": "gdelt"}}
    out = assess_safety_band(advisory_band="2", advisory_provenance=_PROV, homicide=hot, events=events)
    assert out["band"] == "3"


def test_assess_requires_c1_input():
    with pytest.raises(ValueError, match="advisories= or advisory_band"):
        assess_safety_band()


def test_legacy_single_source_form_still_works():
    out = assess_safety_band(advisory_band="2", advisory_provenance=_PROV)
    assert out["band"] == "2"


# ---- normalization enums ----


def test_enum_vocabulary_matches_governance_matrix():
    assert set(VisaStatus) == {
        VisaStatus.VISA_FREE, VisaStatus.ETA, VisaStatus.EVISA,
        VisaStatus.VOA, VisaStatus.REQUIRED, VisaStatus.RESTRICTED,
    }
    assert set(RuleSeverity) == {RuleSeverity.PROHIBITED, RuleSeverity.RESTRICTED, RuleSeverity.ADVISORY}
    assert set(HealthRequirement) == {
        HealthRequirement.REQUIRED, HealthRequirement.RECOMMENDED, HealthRequirement.ROUTINE,
    }
    assert set(PriceMethod) == {PriceMethod.CROWD, PriceMethod.OFFICIAL, PriceMethod.AGENT_REPORTED}
    assert set(AQIScale) == {AQIScale.US_EPA, AQIScale.WHO, AQIScale.CPCB, AQIScale.EU_EEA}
    assert set(CoverageGeneration) == {CoverageGeneration.G2, CoverageGeneration.G3, CoverageGeneration.G4, CoverageGeneration.G5}
    assert set(CrimeClass) == {CrimeClass.THEFT, CrimeClass.THEFT_PICKPOCKET, CrimeClass.VIOLENT, CrimeClass.DISORDER, CrimeClass.OTHER}
    assert {b.value for b in AdvisoryBand} == {"1", "2", "3", "4"}
