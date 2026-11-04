"""Effective-dated India compliance engine (R2-C tranche, 2026-11-03).

S2 evidence: the pre-tranche engine hard-coded the stale Budget-2024 TCS
figure (5%/20% over ₹7L) as THE law; every test below fails against that
engine (wrong regime dispatch / wrong thresholds / missing GST 2.0 split).
Rate sources: Docs/research/INDIA_COMPLIANCE_RATES_TCS_GST_2026-11-03.md.
"""

from __future__ import annotations

from datetime import date

import pytest

from src.fees.tax_compliance import (
    GSTTaxScheme,
    TaxComplianceEngine,
    select_tcs_regime,
)


# ── TCS regime dispatch ────────────────────────────────────────────────

def test_budget2026_flat_2pct_from_first_rupee():
    b = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=500_000.0,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        as_of=date(2026, 11, 3),
    )
    assert b.is_applicable
    assert b.regime_name == "budget2026"
    # Flat 2% on the whole amount — no threshold, no 5%/20% split.
    assert b.total_tcs_amount_inr == 10_000.0
    assert b.effective_tcs_rate_pct == 2.0
    assert b.tier_5pct_taxable_amount_inr == 500_000.0
    assert b.tier_20pct_taxable_amount_inr == 0.0
    assert "3941" in b.source_url or "tdsman" in b.source_url
    assert b.source_url.startswith("http")


def test_budget2025_window_uses_10l_threshold():
    b = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=1_200_000.0,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        cumulative_fy_spend_inr=0.0,
        as_of=date(2025, 12, 1),
    )
    assert b.regime_name == "budget2025"
    # 5% on first ₹10L + 20% on the ₹2L above.
    assert b.tier_5pct_tcs_amount_inr == 50_000.0
    assert b.tier_20pct_tcs_amount_inr == 40_000.0
    assert b.total_tcs_amount_inr == 90_000.0


def test_budget2024_window_keeps_7l_threshold():
    b = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=800_000.0,
        is_overseas_trip=True,
        pan_number="ABCDE1234F",
        as_of=date(2025, 1, 15),
    )
    assert b.regime_name == "budget2024"
    assert b.tier_5pct_taxable_amount_inr == 700_000.0
    assert b.tier_20pct_taxable_amount_inr == 100_000.0


def test_regime_boundary_2026_03_31_vs_04_01():
    before = select_tcs_regime(date(2026, 3, 31))
    after = select_tcs_regime(date(2026, 4, 1))
    assert before.name == "budget2025"
    assert after.name == "budget2026"


def test_budget2026_no_pan_applies_standard_rate_with_advisory_note():
    b = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=300_000.0,
        is_overseas_trip=True,
        pan_number=None,
        as_of=date(2026, 11, 3),
    )
    # Sources silent on a no-PAN penalty for this regime: standard rate,
    # explicit advisory note — never a fabricated 20% penalty.
    assert b.effective_tcs_rate_pct == 2.0
    assert b.total_tcs_amount_inr == 6_000.0
    assert "Verify" in b.rationale or "verify" in b.rationale
    assert "advisor" in b.no_pan_note


def test_budget2026_no_pan_rate_can_be_pinned_by_config():
    b = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=300_000.0,
        is_overseas_trip=True,
        pan_number=None,
        as_of=date(2026, 11, 3),
        no_pan_rate_override_pct=5.0,
    )
    assert b.effective_tcs_rate_pct == 5.0
    assert b.total_tcs_amount_inr == 15_000.0
    assert "config override" in b.no_pan_note


def test_budget2025_no_pan_keeps_statutory_20pct():
    b = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=300_000.0,
        is_overseas_trip=True,
        pan_number=None,
        as_of=date(2025, 12, 1),
    )
    assert b.effective_tcs_rate_pct == 20.0
    assert b.no_pan_note == ""  # statutory rate; no advisory needed


def test_domestic_trips_and_zero_amounts_still_not_applicable():
    b = TaxComplianceEngine.calculate_tcs(
        current_amount_inr=100_000.0, is_overseas_trip=False, as_of=date(2026, 11, 3)
    )
    assert not b.is_applicable
    assert b.regime_name == "budget2026"


# ── GST 2.0 service matrix ─────────────────────────────────────────────

def test_gst2_hotel_le_7500_is_5pct_no_itc():
    g = TaxComplianceEngine.estimate_service_gst(
        "hotel", amount_inr=40_000.0, per_night_rate_inr=7_500.0,
        is_inter_state=True, as_of=date(2026, 11, 3),
    )
    assert g.gst_rate_pct == 5.0
    assert g.igst_amount_inr == 2_000.0
    assert g.itc_eligible is False
    assert g.rate_basis == "gst2_hotel_le_7500"


def test_gst2_hotel_over_7500_is_18pct_with_itc():
    g = TaxComplianceEngine.estimate_service_gst(
        "hotel", amount_inr=100_000.0, per_night_rate_inr=7_500.01,
        is_inter_state=False, as_of=date(2026, 11, 3),
    )
    assert g.gst_rate_pct == 18.0
    assert g.cgst_amount_inr == 9_000.0
    assert g.sgst_amount_inr == 9_000.0
    assert g.itc_eligible is True
    assert g.rate_basis == "gst2_hotel_gt_7500"


def test_pre_gst2_hotel_keeps_12pct_low_band():
    g = TaxComplianceEngine.estimate_service_gst(
        "hotel", amount_inr=40_000.0, per_night_rate_inr=7_000.0,
        is_inter_state=True, as_of=date(2025, 9, 21),
    )
    assert g.gst_rate_pct == 12.0
    assert g.rate_basis == "pre_gst2_hotel_le_7500"


def test_air_classes_and_restaurant_rates():
    eco = TaxComplianceEngine.estimate_service_gst(
        "flight_economy", 10_000.0, is_inter_state=True, as_of=date(2026, 11, 3)
    )
    biz = TaxComplianceEngine.estimate_service_gst(
        "flight_business", 10_000.0, is_inter_state=True, as_of=date(2026, 11, 3)
    )
    rest = TaxComplianceEngine.estimate_service_gst(
        "restaurant", 10_000.0, is_inter_state=False, as_of=date(2026, 11, 3)
    )
    assert (eco.gst_rate_pct, eco.itc_eligible) == (5.0, True)
    assert (biz.gst_rate_pct, biz.itc_eligible) == (12.0, True)
    assert (rest.gst_rate_pct, rest.itc_eligible) == (5.0, False)


def test_unknown_service_type_raises_never_guesses():
    with pytest.raises(ValueError, match="Unknown service_type"):
        TaxComplianceEngine.estimate_service_gst(
            "houseboat_cruise", 10_000.0, as_of=date(2026, 11, 3)
        )


def test_hotel_without_nightly_rate_raises_under_gst2():
    with pytest.raises(ValueError, match="per_night_rate_inr"):
        TaxComplianceEngine.estimate_service_gst(
            "hotel", 40_000.0, is_inter_state=True, as_of=date(2026, 11, 3)
        )


def test_scheme_path_unchanged_for_legacy_callers():
    g = TaxComplianceEngine.calculate_gst(10_000.0, scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT)
    assert g.gst_rate_pct == 5.0
    assert g.itc_eligible is False
    assert g.rate_basis == ""  # legacy path carries no matrix provenance
