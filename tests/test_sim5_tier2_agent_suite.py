"""
tests/test_sim5_tier2_agent_suite.py — Unit & Regression tests for Sim #5 Tier-2 Indian Travel Agent Suite.

Validates the first-principles remediations for:
1. GAP-01: Vernacular Hindi count nouns ("6 bade", "2 bacche"), infant handling ("ek 7 mahine ka infant"),
   saal ages, and senior age cross-contamination prevention (no age > 17 in child_ages).
2. GAP-02: Route regex false-positive prevention ("dikkat hai to airport") and Hindi ablative
   postposition origin extraction ("Indore se" -> origin_city="Indore").
3. GAP-03: Gazetteer stopword filtering (preventing "Hum", "Hume", "Khana" from becoming destination candidates).
4. GAP-04: Hinglish date range extraction ("December 22 se 28 tak").
5. Section 206C(1G) TCS and Tour Package GST calculation for Indian outbound travel.
"""

from __future__ import annotations

from src.fees.tax_compliance import GSTTaxScheme, TaxComplianceEngine
from src.intake.extractors import (
    ExtractionPipeline,
    SourceEnvelope,
    _extract_dates,
    _extract_destination_candidates,
    _extract_party,
)


class TestSim5PartyExtraction:
    def test_hinglish_multi_gen_family_count_nouns(self):
        """Verify '6 bade, 2 bacche, 1 infant' extracts exact party breakdown."""
        text = (
            "Hum 6 bade hain aur 2 bacche (ek 8 saal aur ek 3 saal) plus ek 7 mahine ka infant. "
            "Mummy ji (age 72) ko chalne me dikkat hai."
        )
        party = _extract_party(text)

        assert party["party_size"] == 9
        comp = party["party_composition"]
        assert comp.get("adults") == 6
        assert comp.get("children") == 2
        assert comp.get("infants") == 1

        # Check ages: 8, 3, and 7/12 (~0.58) years; 72 must NOT be present
        ages = party["child_ages"]
        assert 8 in ages
        assert 3 in ages
        assert any(abs(a - 0.58) < 0.05 for a in ages)
        assert 72 not in ages, "Senior age 72 must not leak into child_ages"

    def test_hindi_count_words_singular_and_plural(self):
        """Verify 'bade'/'bada' and 'bacche'/'bachhe'/'bache' count tokens."""
        assert _extract_party("4 bade aur 1 baccha")["party_size"] == 5
        assert _extract_party("do bade aur teen bacche")["party_size"] == 5
        assert _extract_party("family trip for 5 bade 3 bache")["party_size"] == 8


class TestSim5DateAndGeographyExtraction:
    def test_hinglish_date_range_se_tak(self):
        """Verify 'December 22 se 28 tak' extracts start and end dates."""
        text = "Hume December 22 se 28 tak Dubai ka family trip karna hai Indore se."
        res = _extract_dates(text)
        assert res is not None
        raw, start_iso, end_iso, confidence = res
        assert start_iso.endswith("-12-22")
        assert end_iso.endswith("-12-28")
        assert "December 22 se 28 tak" in raw

    def test_destination_candidates_filters_hindi_pronouns(self):
        """Verify 'Hum', 'Hume', 'Khana' are not treated as destinations."""
        text = (
            "Bhaiya namaste. Hum 6 bade hain. Hume December 22 se 28 tak Dubai ka family trip karna hai. "
            "Khana pure vegetarian chahiye."
        )
        candidates, status, raw = _extract_destination_candidates(text)
        assert candidates == ["Dubai"]
        assert "Hum" not in candidates
        assert "Hume" not in candidates
        assert "Khana" not in candidates

    def test_origin_city_extraction_indore_se(self):
        """Verify 'Indore se' extracts Indore and prevents 'Hai' false positive."""
        text = (
            "Hume December 22 se 28 tak Dubai ka family trip karna hai Indore se. "
            "Mummy ji (age 72) ko chalne me dikkat hai to airport aur sightseeing pe wheelchair assistance compulsory chahiye."
        )
        pipeline = ExtractionPipeline()
        env = SourceEnvelope.from_freeform(text, source="whatsapp_web")
        packet = pipeline.extract([env])
        origin_slot = packet.facts.get("origin_city")
        assert origin_slot is not None
        assert origin_slot.value == "Indore"
        assert origin_slot.value != "Hai"


class TestSim5TaxCompliance:
    def test_tcs_under_threshold_is_five_percent(self):
        """Under Section 206C(1G), LRS packages under ₹7L incur 5% TCS."""
        res = TaxComplianceEngine.calculate_tcs(
            current_amount_inr=450000.0,
            is_overseas_trip=True,
            pan_number="AAACA1234F",
            cumulative_fy_spend_inr=0.0,
        )
        assert res.is_applicable is True
        assert res.effective_tcs_rate_pct == 5.0
        assert res.total_tcs_amount_inr == 22500.0

    def test_tour_package_gst_five_percent_split(self):
        """Tour package GST without ITC is 5% with 2.5% CGST + 2.5% SGST intra-state."""
        res = TaxComplianceEngine.calculate_gst(
            taxable_base_inr=450000.0,
            scheme=GSTTaxScheme.TOUR_PACKAGE_5PCT,
            is_inter_state=False,
        )
        assert res.gst_rate_pct == 5.0
        assert res.total_gst_amount_inr == 22500.0
        assert res.cgst_amount_inr == 11250.0
        assert res.sgst_amount_inr == 11250.0
        assert res.igst_amount_inr == 0.0
