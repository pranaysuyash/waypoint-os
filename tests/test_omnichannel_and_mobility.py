from spine_api.services.messaging_webhooks import (
    InboundMessage,
    OutboundConciergeReply,
    process_inbound_traveler_message,
)
from spine_api.services.pass_generator import (
    ApplePassManifest,
    generate_hotel_pass_manifest,
)
from spine_api.services.expense_ocr import (
    ExpenseItem,
    ExpenseLedgerReport,
    compile_expense_report,
    parse_receipt_text,
)


def test_messaging_webhook_flight_query():
    msg = InboundMessage(
        message_id="msg_101",
        channel="whatsapp",
        from_phone="+14155552671",
        to_phone="+18005559297",
        body="What gate is my flight leaving from?",
    )
    reply: OutboundConciergeReply = process_inbound_traveler_message(
        msg,
        active_trip_lookup={"+14155552671": "trip_italy_99"},
    )
    assert reply.action_taken == "flight_status_dispatched"
    assert "Gate B28" in reply.reply_text
    assert reply.trip_id == "trip_italy_99"


def test_apple_pass_generator_hotel():
    pass_manifest: ApplePassManifest = generate_hotel_pass_manifest(
        trip_id="trip_2333bff6434d",
        traveler_name="Priya Sharma",
        hotel_name="Hotel de Russie",
        confirmation_number="RUS-8821",
        check_in_date="2026-09-01",
        check_out_date="2026-09-05",
        address="Via del Babuino 9, Rome, Italy",
    )
    d = pass_manifest.to_dict()
    assert d["formatVersion"] == 1
    assert d["passTypeIdentifier"] == "pass.com.waypoint.hotel"
    assert d["barcode"]["message"] == "WAYPOINT:HTL:RUS-8821"
    assert len(d["generic"]["primaryFields"]) == 1
    assert d["generic"]["primaryFields"][0]["value"] == "Hotel de Russie"


def test_receipt_ocr_parsing_and_expense_report():
    raw_ocr = "Trattoria Da Enzo\nVia dei Vascellari 29, Roma\n2x Pasta Carbonara € 36.00\n1x Vino Rosso € 18.00\nTOTAL: € 54.00"
    item: ExpenseItem = parse_receipt_text("trip_italy_99", raw_ocr)
    assert item.merchant_name == "Trattoria Da Enzo"
    assert item.original_currency == "EUR"
    assert item.original_amount == 54.0
    assert item.category == "Meals"
    assert item.amount_usd > 54.0  # EUR converted to USD

    report: ExpenseLedgerReport = compile_expense_report("trip_italy_99", [item])
    assert report.items_count == 1
    assert report.total_expense_usd == item.amount_usd
