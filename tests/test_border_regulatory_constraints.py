"""
Border & Regulatory Constraint Engine Tests (PER-0711, PER-0706).
"""

from datetime import date
from src.decision.constraint_engine import ConstraintEngine


def test_schengen_rolling_90_180_calculation():
    # Case 1: Prior 30-day trip in Jan, new 45-day trip in May (Total: 75 days in 180-day window -> Compliant)
    hist = [(date(2026, 1, 1), date(2026, 1, 30))]
    plan = (date(2026, 5, 1), date(2026, 6, 14))
    res = ConstraintEngine.calculate_schengen_rolling_90_180(hist, plan)
    assert res["is_valid"] is True
    assert res["max_days_in_any_180_window"] <= 90
    assert res["overstay_days"] == 0

    # Case 2: Prior 70-day trip, new 35-day trip (Total: 105 days in 180-day window -> Violation)
    hist2 = [(date(2026, 1, 1), date(2026, 3, 11))]  # 70 days
    plan2 = (date(2026, 4, 1), date(2026, 5, 5))    # 35 days
    res2 = ConstraintEngine.calculate_schengen_rolling_90_180(hist2, plan2)
    assert res2["is_valid"] is False
    assert res2["overstay_days"] > 0
    assert res2["earliest_violation_date"] is not None


def test_terminal_mct_lookup():
    # LHR T2 to T5 is 90 mins
    mct_lhr_2_5 = ConstraintEngine.get_terminal_mct("LHR", "T2", "T5")
    assert mct_lhr_2_5 == 90

    # LHR T2 to T2 is 45 mins
    mct_lhr_2_2 = ConstraintEngine.get_terminal_mct("LHR", "T2", "T2")
    assert mct_lhr_2_2 == 45

    # CDG 2E to 2F is 75 mins
    mct_cdg = ConstraintEngine.get_terminal_mct("CDG", "2E", "2F")
    assert mct_cdg == 75
