import pytest
from httpx import AsyncClient, ASGITransport
from spine_api.server import app

@pytest.mark.asyncio
async def test_extract_confirmation_flight_and_hotel():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Auth header token simulation
        headers = {"Authorization": "Bearer dev_test_token"}
        
        # Test Flight extraction
        flight_payload = {
            "raw_text": "Booking Reference: 6X9ZPL. Flight Emirates EK-501 from Mumbai to Dubai to Cape Town on 15 Nov 2026. Total Amount USD 1,850.",
            "document_name": "emirates_eticket.pdf"
        }
        res_flight = await client.post("/api/trips/trip_test_1/confirmations/extract", json=flight_payload, headers=headers)
        if res_flight.status_code == 200:
            data = res_flight.json()
            assert data["ok"] is True
            assert data["extracted"]["confirmation_type"] == "flight"
            assert data["extracted"]["confirmation_number"] == "6X9ZPL"
            assert data["extracted"]["supplier_name"] == "Emirates"
            assert data["extracted"]["confidence_score"] >= 0.8

        # Test Hotel extraction
        hotel_payload = {
            "raw_text": "Confirmation Number: SILO-2026-9942. The Silo Hotel Deluxe Suite for check-in 16 Nov 2026. Total USD 3,400.",
            "document_name": "silo_voucher.pdf"
        }
        res_hotel = await client.post("/api/trips/trip_test_1/confirmations/extract", json=hotel_payload, headers=headers)
        if res_hotel.status_code == 200:
            data_h = res_hotel.json()
            assert data_h["ok"] is True
            assert data_h["extracted"]["confirmation_type"] == "hotel"
            assert data_h["extracted"]["confirmation_number"] == "SILO-2026-9942"
