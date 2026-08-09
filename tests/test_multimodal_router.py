"""
tests/test_multimodal_router.py — Unit & Integration tests for Omnichannel Multimodal Extraction Engine.
"""

import os
import pytest

os.environ["RUNNING_TESTS"] = "1"


@pytest.fixture(autouse=True)
def setup_test_env(monkeypatch):
    monkeypatch.setenv("DATA_PRIVACY_MODE", "beta")
    monkeypatch.setenv("SPINE_API_DISABLE_AUTH", "1")
    monkeypatch.setenv("TRIPSTORE_BACKEND", "file")


def test_voice_note_and_image_ocr_extraction_end_to_end(session_client):
    """Test extracting structured travel facts from voice notes and screenshot image OCR text."""

    # 1. Test voice note transcript parsing
    vn_res = session_client.post(
        "/api/v1/multimodal/voice-note",
        json={
            "transcript_text": "Hey, we are planning a trip to Tokyo for 2 adults. We want to fly EK201 and stay at Four Seasons with an ocean view. Total budget $15,000. Vegan meals required.",
            "speaker_name": "Marcus Vance",
            "audio_duration_seconds": 24.5,
        },
        headers={"X-Agency-ID": "agency_multi_test"},
    )

    assert vn_res.status_code == 200
    vn_data = vn_res.json()
    assert vn_data["ok"] is True
    assert vn_data["source_type"] == "voice_note"
    assert vn_data["confidence_tier"] == "HIGH"
    assert vn_data["updated_packet_facts"]["flight_number"] == "EK201"
    assert vn_data["updated_packet_facts"]["hotel_name"] == "Four Seasons"
    assert vn_data["updated_packet_facts"]["budget_usd"] == 15000
    assert vn_data["updated_packet_facts"]["passenger_count"] == 2
    assert "Vegan" in vn_data["updated_packet_facts"]["dietary_requirements"]

    # 2. Create a trip
    inbound_res = session_client.post(
        "/api/v1/inbound/parse",
        json={
            "channel": "email",
            "raw_text": "Need flight and hotel confirmation.",
            "customer_name": "Sophia Martinez",
        },
        headers={"X-Agency-ID": "agency_multi_test"},
    ).json()

    trip_id = inbound_res["trip_id"]

    # 3. Test screenshot image OCR fact extraction linked to trip
    ocr_res = session_client.post(
        "/api/v1/multimodal/image-ocr",
        json={
            "trip_id": trip_id,
            "ocr_text": "Flight Confirmation BA178 for 4 guests. Staying at Ritz-Carlton high floor suite. Total price USD 20000.",
            "image_type": "flight_confirmation",
        },
        headers={"X-Agency-ID": "agency_multi_test"},
    )

    assert ocr_res.status_code == 200
    ocr_data = ocr_res.json()
    assert ocr_data["ok"] is True
    assert ocr_data["trip_id"] == trip_id
    assert ocr_data["source_type"] == "image_ocr"
    assert ocr_data["updated_packet_facts"]["flight_number"] == "BA178"
    assert ocr_data["updated_packet_facts"]["hotel_name"] == "Ritz-Carlton"
    assert ocr_data["updated_packet_facts"]["passenger_count"] == 4
    assert ocr_data["updated_packet_facts"]["budget_usd"] == 20000
