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


def test_hinglish_outbound_and_late_hotel_arrival():
    from dataclasses import asdict

    from spine_api.services.live_checker_service import overnight_hotel_finding
    from src.intake.extractors import ExtractionPipeline
    from src.intake.packet_models import SourceEnvelope
    from src.public_checker.live_checks import _extract_destination, _geocode_destination

    text = (
        "Delhi se Goa jana hai bhai, 2 adults + ek 5 yr ka kid. "
        "18 Dec 2026 ki flight Delhi 23:55 to Goa 02:25 next day. "
        "Hotel check-in 18 Dec likha hai, North Goa side, hotel abhi final nahi. "
        "19th ko Baga + Dudhsagar + Old Goa ek hi din kar lenge? "
        "35k max total sabka, flights included. Return ka date abhi decide nahi. Veg food chahiye."
    )
    packet = ExtractionPipeline().extract([SourceEnvelope.from_freeform(text)])
    assert packet.facts["destination_candidates"].value == ["Goa"]
    assert packet.facts["date_start"].value == "2026-12-18"
    assert "date_end" not in packet.facts

    serialized = asdict(packet)
    assert _extract_destination(serialized, text) == "Goa"
    assert _geocode_destination("Goa") is None
    finding = overnight_hotel_finding(serialized, text)
    assert finding and "02:25 on 19 December" in finding
    assert "18 December hotel check-in" in finding
    assert "confirm it will hold the room" in finding
    assert overnight_hotel_finding(serialized, text.replace("check-in 18 Dec", "check-in 19 Dec")) is None
    assert overnight_hotel_finding(serialized, text.replace(" next day", "")) is None


def test_destination_lookup_does_not_use_other_facts_or_pick_an_ambiguous_candidate():
    from src.public_checker.live_checks import _extract_destination

    assert _extract_destination({"facts": {"origin_city": {"value": "Delhi"}}}, "") is None
    packet = {"facts": {"destination_candidates": {"value": ["Baga", "Old Goa"]}}}
    assert _extract_destination(packet, "Go to Goa.") is None


def test_goa_pacing_requires_three_stops_on_the_same_day():
    from spine_api.services.live_checker_service import goa_day_pacing_finding

    packet = {"facts": {"destination_candidates": {"value": ["Goa"]}}}
    hinglish = "19th ko Baga + Dudhsagar + Old Goa ek hi din kar lenge?"
    finding = goa_day_pacing_finding(packet, hinglish)
    assert finding and "Collem" in finding and "Baga, Dudhsagar and Old Goa" in finding
    assert goa_day_pacing_finding(packet, "Day 2: Dudhsagar, Baga and Old Goa.")
    assert goa_day_pacing_finding(packet, "Day 2: Baga and Old Goa. Day 3: Dudhsagar.") is None
    assert goa_day_pacing_finding(packet, "Some ideas: Baga, Dudhsagar and Old Goa.") is None
    assert goa_day_pacing_finding({}, hinglish) is None
