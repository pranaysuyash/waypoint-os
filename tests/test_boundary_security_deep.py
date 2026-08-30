"""
tests/test_boundary_security_deep.py — Unit tests for PER-0933/0927 boundary security and PII masking.
"""

from src.services.pii_masker import PIIMasker


def test_pii_masking_functions():
    """Verify masking passport numbers, emails, and phone numbers."""
    assert PIIMasker.mask_passport_number("L898902C3") == "L8*****C3"
    assert PIIMasker.mask_email("john.doe@example.com") == "j******e@example.com"
    assert PIIMasker.mask_phone_number("+1 (555) 123-4567") == "+*******4567"


def test_sanitize_trip_payload():
    """Verify recursive data scrubbing across complex trip dictionaries."""
    raw_payload = {
        "trip_id": "trip_sec_99",
        "traveler": {
            "name": "Jane Smith",
            "passport_number": "A12345678",
            "contact_email": "jane@smith.org",
            "card_number": "4111222233334444",
        },
        "flights": [
            {"carrier": "Delta", "price": 450.0}
        ]
    }

    sanitized = PIIMasker.sanitize_trip_payload(raw_payload)
    assert sanitized["trip_id"] == "trip_sec_99"
    assert sanitized["traveler"]["passport_number"] == "A1*****78"
    assert sanitized["traveler"]["contact_email"] == "j**e@smith.org"
    assert sanitized["traveler"]["card_number"] == "[REDACTED_SECRET]"
    assert sanitized["flights"][0]["price"] == 450.0
