from src.public_checker.live_checks import _seasonal_hint, _regional_advisory_hint


def test_seasonal_hint_flags_bali_monsoon_december():
    hint = _seasonal_hint("Bali", 12)
    assert hint is not None
    assert hint["risk_type"] == "monsoon"
    assert 3 in hint["better_months"]


def test_seasonal_hint_none_for_non_risk_month():
    hint = _seasonal_hint("Bali", 4)
    assert hint is None


def test_regional_advisory_hint_known_destination():
    hint = _regional_advisory_hint("Israel")
    assert hint is not None
    assert "advisories" in hint.lower()
