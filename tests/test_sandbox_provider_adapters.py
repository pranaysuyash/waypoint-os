"""Automated tests for Sandbox Provider Adapters (Stripe, Twilio, Amadeus).

Previously named ``test_production_provider_adapters.py`` — renamed as part of
GM-02: these adapters are in-process simulators, not production clients.
"""

import hashlib
import hmac
import logging
import time

import pytest

import spine_api.providers.amadeus_enterprise_adapter as amadeus_module
import spine_api.providers.stripe_issuing_adapter as stripe_module
import spine_api.providers.twilio_telephony_adapter as twilio_module
from spine_api.providers.amadeus_enterprise_adapter import AmadeusEnterpriseAdapter
from spine_api.providers.stripe_issuing_adapter import StripeIssuingAdapter
from spine_api.providers.stripe_issuing_adapter import (
    VirtualCardIssuanceRequest,
)
from spine_api.providers.twilio_telephony_adapter import IVRCallRequest
from spine_api.providers.twilio_telephony_adapter import TwilioTelephonyAdapter

WEBHOOK_SIGNING_SECRET = "whsec_test_signing_secret_0123456789abcdef"


def _sign_stripe_payload(payload: bytes, secret: str, timestamp: int) -> str:
    """Compute the Stripe v1 signature for a payload (test helper)."""
    signed_payload = f"{timestamp}.".encode("utf-8") + payload
    return hmac.new(
        secret.encode("utf-8"), signed_payload, hashlib.sha256
    ).hexdigest()


def _make_sig_header(payload: bytes, secret: str, timestamp: int) -> str:
    """Build a realistic ``Stripe-Signature`` header for a payload."""
    signature = _sign_stripe_payload(payload, secret, timestamp)
    return f"t={timestamp},v1={signature}"


VALID_PAYLOAD = b'{"id":"evt_test_1","type":"issuing_authorization.request"}'


@pytest.mark.asyncio
async def test_stripe_issuing_single_use_card():
    adapter = StripeIssuingAdapter(api_key="sk_test_mock_sandbox")
    req = VirtualCardIssuanceRequest(
        amount_cents=250000,
        currency="USD",
        trip_id="TRIP-VIP-001",
        merchant_name="The Ritz-Carlton Paris",
    )
    card = await adapter.issue_single_use_card(req)

    assert card.card_id.startswith("ic_")
    assert card.spending_limit_cents == 250000
    assert card.currency == "USD"
    assert card.status == "active"
    assert len(card.last4) == 4
    assert len(card.cvc) == 3


@pytest.mark.asyncio
async def test_stripe_issuing_last4_zero_pads_low_decimal_value(monkeypatch):
    class _FixedUUID:
        hex = "00010000000000000000000000000000"

    monkeypatch.setattr(stripe_module.uuid, "uuid4", lambda: _FixedUUID())
    card = await StripeIssuingAdapter(api_key="sk_test_mock_sandbox").issue_single_use_card(
        VirtualCardIssuanceRequest(
            amount_cents=1,
            currency="USD",
            trip_id="TRIP-LOW-DIGIT",
            merchant_name="Example Merchant",
        )
    )

    assert card.last4 == "0001"
    assert card.ephemeral_pan.endswith("-0001")


def test_stripe_webhook_processing():
    adapter = StripeIssuingAdapter()
    payload = {
        "type": "issuing_authorization.request",
        "data": {
            "object": {
                "id": "iauth_123",
                "amount": 250000,
                "card": {"id": "ic_test_456"},
            }
        },
    }
    result = adapter.process_authorization_event(payload)
    assert result["approved"] is True
    assert result["card_id"] == "ic_test_456"
    assert result["authorized_amount"] == 250000


# --- GM-03: real Stripe webhook signature verification --------------------


def test_stripe_webhook_signature_valid_passes():
    adapter = StripeIssuingAdapter()
    header = _make_sig_header(
        VALID_PAYLOAD, WEBHOOK_SIGNING_SECRET, int(time.time())
    )
    assert (
        adapter.verify_webhook_signature(VALID_PAYLOAD, header, WEBHOOK_SIGNING_SECRET)
        is True
    )


def test_stripe_webhook_signature_valid_via_env_secret(monkeypatch):
    adapter = StripeIssuingAdapter()
    monkeypatch.setenv("STRIPE_WEBHOOK_SIGNING_KEY", WEBHOOK_SIGNING_SECRET)
    header = _make_sig_header(VALID_PAYLOAD, WEBHOOK_SIGNING_SECRET, int(time.time()))
    assert adapter.verify_webhook_signature(VALID_PAYLOAD, header, "") is True


def test_stripe_webhook_signature_tampered_payload_fails():
    adapter = StripeIssuingAdapter()
    header = _make_sig_header(
        VALID_PAYLOAD, WEBHOOK_SIGNING_SECRET, int(time.time())
    )
    tampered = VALID_PAYLOAD.replace(b"evt_test_1", b"evt_evil_9")
    assert tampered != VALID_PAYLOAD
    assert (
        adapter.verify_webhook_signature(tampered, header, WEBHOOK_SIGNING_SECRET)
        is False
    )


def test_stripe_webhook_signature_stale_timestamp_fails():
    adapter = StripeIssuingAdapter()
    stale_timestamp = int(time.time()) - 400  # beyond 5-minute tolerance
    header = _make_sig_header(
        VALID_PAYLOAD, WEBHOOK_SIGNING_SECRET, stale_timestamp
    )
    assert (
        adapter.verify_webhook_signature(VALID_PAYLOAD, header, WEBHOOK_SIGNING_SECRET)
        is False
    )


def test_stripe_webhook_signature_missing_secret_fails_closed(
    monkeypatch, caplog
):
    adapter = StripeIssuingAdapter()
    monkeypatch.delenv("STRIPE_WEBHOOK_SIGNING_KEY", raising=False)
    header = _make_sig_header(
        VALID_PAYLOAD, WEBHOOK_SIGNING_SECRET, int(time.time())
    )
    with caplog.at_level(logging.WARNING, logger="spine_api.providers.stripe_issuing_adapter"):
        assert adapter.verify_webhook_signature(VALID_PAYLOAD, header, "") is False
    assert any(
        "no signing secret configured" in record.message for record in caplog.records
    )


def test_stripe_webhook_signature_wrong_secret_fails(monkeypatch):
    adapter = StripeIssuingAdapter()
    header = _make_sig_header(VALID_PAYLOAD, "whsec_other_secret", int(time.time()))
    assert (
        adapter.verify_webhook_signature(VALID_PAYLOAD, header, WEBHOOK_SIGNING_SECRET)
        is False
    )


def test_stripe_webhook_signature_malformed_header_fails():
    adapter = StripeIssuingAdapter()
    # Missing v1 scheme entirely.
    assert (
        adapter.verify_webhook_signature(
            VALID_PAYLOAD, "t=1,v0=deadbeef", WEBHOOK_SIGNING_SECRET
        )
        is False
    )
    # No timestamp.
    assert (
        adapter.verify_webhook_signature(VALID_PAYLOAD, "v1=deadbeef", WEBHOOK_SIGNING_SECRET)
        is False
    )


def test_stripe_webhook_signature_multiple_v1_rolling_secret():
    """Header with a rolled-secret signature list still verifies via any match."""
    adapter = StripeIssuingAdapter()
    now = int(time.time())
    old_sig = _sign_stripe_payload(VALID_PAYLOAD, "whsec_rotated_out", now)
    new_sig = _sign_stripe_payload(VALID_PAYLOAD, WEBHOOK_SIGNING_SECRET, now)
    header = f"t={now},v1={old_sig},v1={new_sig}"
    assert (
        adapter.verify_webhook_signature(VALID_PAYLOAD, header, WEBHOOK_SIGNING_SECRET)
        is True
    )


# --- GM-02: Production -> Sandbox rename consistency ----------------------


def test_sandbox_adapter_modules_import_and_no_production_naming():
    assert isinstance(StripeIssuingAdapter(), StripeIssuingAdapter)
    assert isinstance(TwilioTelephonyAdapter(), TwilioTelephonyAdapter)
    assert isinstance(AmadeusEnterpriseAdapter(), AmadeusEnterpriseAdapter)

    for module in (amadeus_module, stripe_module, twilio_module):
        assert module.__doc__ is not None
        assert "Production" not in module.__doc__, (
            f"{module.__name__} docstring still claims 'Production'"
        )


@pytest.mark.asyncio
async def test_twilio_ivr_call_initialization():
    adapter = TwilioTelephonyAdapter(account_sid="AC_test", auth_token="tok_test")
    req = IVRCallRequest(
        carrier_name="British Airways",
        target_phone_number="+18002479297",
        pnr="6XY7ZQ",
        passenger_last_name="Morgan",
        desired_action="Seat Upgrade & Re-ticketing",
    )
    session = await adapter.initiate_airline_ivr_call(req)

    assert session.call_sid.startswith("CA")
    assert session.carrier_name == "British Airways"
    assert session.status == "navigating_ivr_tree"
    assert session.dtmf_sequence_sent == ["3", "w", "2", "w", "1"]
    assert "stream.waypoint.ai" in session.audio_stream_url


@pytest.mark.asyncio
async def test_amadeus_enterprise_search_and_pnr():
    adapter = AmadeusEnterpriseAdapter(client_id="mock_id", client_secret="mock_secret")
    offers = await adapter.search_flight_offers(
        origin="JFK", destination="LHR", departure_date="2026-10-15"
    )

    assert len(offers) == 2
    assert offers[0].carrier_code == "BA"
    assert offers[0].flight_number == "178"
    assert offers[0].cabin_class == "BUSINESS"

    pnr_result = await adapter.create_pnr_order(
        offer_id=offers[0].offer_id,
        passenger_details=[{"first_name": "Alex", "last_name": "Morgan"}],
    )
    assert pnr_result["status"] == "CONFIRMED"
    assert pnr_result["pnr"].startswith("1A")
    assert "MORGAN/ALEX" in pnr_result["passengers"]
