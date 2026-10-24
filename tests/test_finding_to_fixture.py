"""
Invariant 5 flywheel (FND-0329 follow-through): finding→fixture in one action.
The builder is pure; the corpus schema (scenarios + summary.total) is preserved.
"""
from __future__ import annotations

from tools.finding_to_fixture import apply_scenario, build_scenario


def test_build_scenario_carries_finding_provenance():
    s = build_scenario("FND-0329", "solo trip to japan for 12 days.", "destinations == ['Japan']", "registered")
    assert s["finding_id"] == "FND-0329"
    assert s["input"] == "solo trip to japan for 12 days."
    assert s["expected_properties"] == ["destinations == ['Japan']"]
    assert s["provenance"]["origin"] == "finding_flywheel"
    assert s["status"] == "unverified"


def test_apply_scenario_appends_and_bumps_total():
    corpus = {"corpus": "x", "summary": {"total": 1}, "scenarios": [{"id": "s1"}]}
    scenario = build_scenario("FND-0329", "6 guys to goa.", "party_size == 6", "verified_fix")
    out = apply_scenario(corpus, scenario)
    assert out["summary"]["total"] == 2
    assert out["scenarios"][-1]["id"] == scenario["id"]
    # input corpus never mutated
    assert corpus["summary"]["total"] == 1


def test_apply_scenario_replaces_same_id():
    corpus = {"scenarios": [{"id": "f_1", "old": True}], "summary": {"total": 1}}
    scenario = build_scenario("FND-0001", "new input", "prop", "registered")
    scenario["id"] = "f_1"
    out = apply_scenario(corpus, scenario)
    assert len(out["scenarios"]) == 1
    assert out["scenarios"][0]["input"] == "new input"
