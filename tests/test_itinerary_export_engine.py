"""Tests for Luxury Itinerary and E-Voucher Vector Document Compiler."""

from src.compilers.itinerary_export_engine import (
    LuxuryItineraryExportEngine,
    ExportDocumentPayload,
    ItineraryDayItem,
)


def test_luxury_itinerary_html_compilation():
    days = [
        ItineraryDayItem(
            day_number=1,
            date_str="April 10, 2027",
            title="Tokyo Arrival & Private Aman Check-in",
            location="Tokyo Haneda / Otemachi",
            description="Private Alphard transfer from Haneda to Aman Tokyo. Evening sake tasting.",
            vouchers=["AMAN-TYO-88219", "TRF-HND-01"],
            meal_plan="Breakfast Included",
            dress_code="Smart Casual",
        ),
        ItineraryDayItem(
            day_number=2,
            date_str="April 11, 2027",
            title="Tsukiji Outer Market & Private Sushi Masterclass",
            location="Tsukiji / Ginza",
            description="Hands-on sushi preparation with Master Chef Jiro trainee.",
            vouchers=["ACT-SUSHI-994"],
            meal_plan="Breakfast & Lunch Included",
        ),
    ]

    payload = ExportDocumentPayload(
        trip_id="TRIP-JP-2027",
        client_name="Alex & Taylor Morgan",
        destination_title="10-Day Japan Cultural Immersion",
        travel_dates="April 10 - April 20, 2027",
        total_cost_usd=14500.0,
        allergies=["Severe peanut allergy (Leo)"],
        emergency_contact="+1 (800) 555-WAYPOINT",
        days=days,
        vouchers={
            "AMAN-TYO-88219": "Aman Tokyo — Deluxe Palace View Suite (4 Nights)",
            "TRF-HND-01": "Tokyo VIP Transfers — Toyota Alphard Executive",
            "ACT-SUSHI-994": "Ginza Sushi Workshop — Private Session",
        },
    )

    html = LuxuryItineraryExportEngine.compile_html(payload)

    # Verifications
    assert "<!DOCTYPE html>" in html
    assert "WAYPOINT PRIVATE TRAVEL" in html
    assert "Alex & Taylor Morgan" in html
    assert "10-Day Japan Cultural Immersion" in html
    assert "Severe peanut allergy (Leo)" in html
    assert "DAY 01" in html
    assert "DAY 02" in html
    assert "AMAN-TYO-88219" in html
    assert "CONFIRMED" in html
    assert "$14,500.00 USD" in html
