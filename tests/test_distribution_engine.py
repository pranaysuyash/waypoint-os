"""
Distribution & GDS/NDC Engine Tests (PER-950887, PER-950895, PER-0967).
"""

from src.distribution.edifact_parser import EDIFACTParser
from src.distribution.ndc_client import NDCProtocolEngine
from src.distribution.fare_rules_engine import FareRulesEngine
from src.distribution.gds_models import GDSSystem, SegmentStatus


def test_edifact_amadeus_parsing():
    raw_dump = """
    RP/NYC1A0982/NYC1A0982            AA/SU 30AUG26/0842Z   6XY7ZQ
    1.MORGAN/ALEX MR  2.MORGAN/TAYLOR MS
    1  BA 178 J 15OCT LHRJFK HK2  1140 1425  *1A/E*
    SSR VGML BA HK1/S1
    OSI BA VIP REPEAT TRAVELER
    TK TL15SEP/NYC1A0982
    """
    pnr = EDIFACTParser.parse_amadeus_dump(raw_dump, pcc="NYC1A0982")

    assert pnr.record_locator == "6XY7ZQ"
    assert pnr.gds_system == GDSSystem.AMADEUS
    assert len(pnr.passengers) == 2
    assert pnr.passengers[0] == "MORGAN/ALEX MR"
    assert len(pnr.segments) == 1
    assert pnr.segments[0].carrier == "BA"
    assert pnr.segments[0].flight_number == "178"
    assert pnr.segments[0].status == SegmentStatus.HK
    assert len(pnr.ssrs) == 1
    assert pnr.ssrs[0].code == "VGML"
    assert len(pnr.osis) == 1
    assert "VIP" in pnr.osis[0].text


def test_edifact_cryptic_command_generation():
    pax = ["Morgan/Alex Mr", "Morgan/Taylor Ms"]
    segs = [{"carrier": "DL", "flight_number": "404", "booking_class": "Y", "date": "20NOV", "origin": "JFK", "destination": "LAX"}]
    cmds = EDIFACTParser.generate_booking_cryptics(pax, segs, ticketing_limit="10NOV")

    assert len(cmds) >= 5
    assert "NM1MORGAN/ALEX MR" in cmds
    assert "NM1MORGAN/TAYLOR MS" in cmds
    assert "SS DL 404 Y 20NOV JFKLAX 1" in cmds
    assert "TK TL10NOV" in cmds


def test_ndc_air_shopping_and_order_create():
    req = NDCProtocolEngine.create_air_shopping_request(
        origin="LHR", destination="JFK", departure_date="2026-10-15", passengers_count=2, cabin_preference="BUSINESS"
    )
    assert req["AirShoppingRQ"]["Document"]["ReferenceVersion"] == "21.3"
    assert req["AirShoppingRQ"]["CoreQuery"]["OriginDest"][0]["Origin"]["AirportCode"] == "LHR"

    order = NDCProtocolEngine.execute_order_create(
        offer_id="OFF-BA-9941",
        airline_code="BA",
        passengers=["Alex Morgan", "Taylor Morgan"],
        segments=[{"carrier": "BA", "flight_number": "178", "booking_class": "J", "origin": "LHR", "destination": "JFK"}],
        total_amount=5400.0,
    )
    assert order.order_id.startswith("ORD-NDC-BA-")
    assert order.status == "CONFIRMED"
    assert len(order.segments) == 1
    assert order.segments[0].carrier == "BA"


def test_fare_rules_category_16_and_35():
    # Cat 16 unrestricted
    eval_flex = FareRulesEngine.evaluate_penalties("YFULLFLEX")
    assert eval_flex["is_refundable"] is True
    assert eval_flex["cancellation_fee"] == 0.0

    # Cat 16 restricted
    eval_promo = FareRulesEngine.evaluate_penalties("BASICPROMO")
    assert eval_promo["is_refundable"] is False
    assert eval_promo["change_fee"] == 200.0

    # Cat 35 markup
    cat35 = FareRulesEngine.evaluate_cat35_negotiated_markup(
        net_fare=2000.0,
        agency_markup_percent=0.15,  # 15% markup
        contract_code="CORP-BA-2026",
    )
    assert cat35["selling_fare"] == 2300.0
    assert cat35["agency_commission_profit"] == 300.0
    assert cat35["is_adm_risk_free"] is True
