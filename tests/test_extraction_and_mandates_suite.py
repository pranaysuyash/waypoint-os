"""
tests/test_extraction_and_mandates_suite.py — Unit Tests for Extraction Truth (NEW-01/NEW-02/F-21), Payment Mandates (F-04), and Retention SLAs (F-05).
"""

from datetime import datetime, timedelta, timezone

from src.intake.extractors import (
    ExtractionPipeline,
    _extract_party,
    _extract_budget_scope,
)
from src.intake.packet_models import EpistemicStatus
from src.financial.payment_mandates import (
    MandatePurpose,
    MandateStatus,
    PaymentMandateEngine,
)
from src.security.retention_enforcer import (
    RetentionCategory,
    RetentionEnforcer,
)


# ---------------------------------------------------------------------------
# 1. Extraction Truth & Colloquial Parsing Tests (NEW-01, NEW-02, F-21)
# ---------------------------------------------------------------------------

def test_party_extraction_colloquial_companions():
    """Verify 'me and 3 friends' or 'me and 3 colleagues' extracts party_size=4 (not 1)."""
    p1 = _extract_party("Looking for a trip to Japan for me and 3 friends")
    assert p1["party_size"] == 4

    p2 = _extract_party("Planning an executive retreat for me and 4 colleagues")
    assert p2["party_size"] == 5

    p3 = _extract_party("Trip for me, my wife and two kids")
    assert p3["party_size"] == 4
    assert p3["party_composition"]["adults"] == 2
    assert p3["party_composition"]["children"] == 2


def test_budget_scope_colloquial_per_person():
    """Verify '5k each', '3500 pp', '4000 per head' correctly resolves to per_person."""
    assert _extract_budget_scope("We have a budget of $5k each") == "per_person"
    assert _extract_budget_scope("Budget is 4000 pp for the flight and stay") == "per_person"
    assert _extract_budget_scope("Looking at 3000 USD per head") == "per_person"
    assert _extract_budget_scope("Total budget for the whole family is 10000 USD") == "total"


def test_epistemic_authority_calibration_on_defaulted_budget():
    """Verify defaulted budget scope emits AuthorityLevel.INFERRED, not EXPLICIT_USER (NEW-01)."""
    from src.intake.packet_models import SourceEnvelope

    pipeline = ExtractionPipeline()
    envelope = SourceEnvelope.from_freeform("I want to visit Rome with a budget of $5000")
    packet = pipeline.extract([envelope])

    scope_slot = packet.facts.get("budget_scope")
    assert scope_slot is not None
    assert scope_slot.value == "total"
    # Epistemic honesty: since scope was defaulted by golden convention, epistemic status is ASSUMED!
    assert scope_slot.epistemic_status == EpistemicStatus.ASSUMED

    flex_slot = packet.facts.get("budget_flexibility")
    assert flex_slot is not None
    assert flex_slot.value == "soft"
    # Epistemic honesty: defaulted flexibility is ASSUMED!
    assert flex_slot.epistemic_status == EpistemicStatus.ASSUMED





# ---------------------------------------------------------------------------
# 2. Customer Payment Authorization Mandate Tests (F-04)
# ---------------------------------------------------------------------------

def test_payment_mandate_creation_and_charge_cap():
    """Verify mandate ledger records consent and blocks charges above authorized limit."""
    mandate = PaymentMandateEngine.register_mandate(
        trip_id="trip_man_1",
        customer_id="cust_101",
        customer_name="Bruce Wayne",
        customer_email="bruce@waynecorp.com",
        max_authorized_cents=500000,  # $5,000.00
        purpose=MandatePurpose.INITIAL_DEPOSIT,
        consent_text="I authorize Waypoint OS to charge my card up to $5,000 for travel bookings.",
        client_ip_address="198.51.100.42",
        currency="USD",
    )

    assert mandate.status == MandateStatus.ACTIVE
    assert len(mandate.consent_sha256) == 64

    # 1. Partial charge within limit: $2,000
    res1 = PaymentMandateEngine.verify_and_charge(mandate.mandate_id, 200000)
    assert res1["authorized"] is True
    assert res1["remaining_authorized_cents"] == 300000
    assert res1["status"] == "ACTIVE"

    # 2. Attempt charge exceeding remaining authorization: $3,500 ($350,000 cents > $300,000 cents)
    res2 = PaymentMandateEngine.verify_and_charge(mandate.mandate_id, 350000)
    assert res2["authorized"] is False
    assert "exceeds" in res2["reason"].lower()

    # 3. Final charge consuming the remaining balance: $3,000
    res3 = PaymentMandateEngine.verify_and_charge(mandate.mandate_id, 300000)
    assert res3["authorized"] is True
    assert res3["status"] == "CONSUMED"


def test_payment_mandate_revocation():
    """Verify customer mandate revocation blocks subsequent charges."""
    mandate = PaymentMandateEngine.register_mandate(
        trip_id="trip_man_2",
        customer_id="cust_102",
        customer_name="Diana Prince",
        customer_email="diana@themyscira.org",
        max_authorized_cents=300000,
        purpose=MandatePurpose.SPLIT_INSTALLMENT,
        consent_text="I authorize split installments up to $3,000.",
    )

    PaymentMandateEngine.revoke_mandate(mandate.mandate_id, reason="Customer cancelled split payment plan")
    res = PaymentMandateEngine.verify_and_charge(mandate.mandate_id, 50000)
    assert res["authorized"] is False
    assert "REVOKED" in res["reason"]


# ---------------------------------------------------------------------------
# 3. Data Privacy Retention & Erasure SLA Enforcement Tests (F-05)
# ---------------------------------------------------------------------------

def test_retention_enforcer_statutory_sweep():
    """Verify automated sweep erases expired passport data past 30 days."""
    now = datetime.now(timezone.utc)

    # 1. Passport asset created 45 days ago (SLA is 30 days -> should be purged)
    old_date = (now - timedelta(days=45)).isoformat()
    asset1 = RetentionEnforcer.register_asset(
        asset_id="asset_pass_001",
        trip_id="trip_ret_1",
        customer_id="cust_201",
        category=RetentionCategory.PASSPORT_MRZ,
        created_at_iso=old_date,
    )

    # 2. Financial invoice created 45 days ago (SLA is 7 years / 2555 days -> should NOT be purged)
    asset2 = RetentionEnforcer.register_asset(
        asset_id="asset_inv_001",
        trip_id="trip_ret_1",
        customer_id="cust_201",
        category=RetentionCategory.FINANCIAL_INVOICE,
        created_at_iso=old_date,
    )

    certificates = RetentionEnforcer.sweep_and_enforce_erasure(now_dt=now)

    erased_ids = [c.asset_id for c in certificates]
    assert "asset_pass_001" in erased_ids
    assert "asset_inv_001" not in erased_ids

    # Verify certificate details
    cert = certificates[0]
    assert cert.category == RetentionCategory.PASSPORT_MRZ
    assert len(cert.tombstone_sha256) == 64
    assert asset1.is_erased is True
    assert asset2.is_erased is False


def test_retention_enforcer_manual_erasure_right():
    """Verify GDPR Art 17 Right-to-Erasure execution issues valid certificate."""
    asset = RetentionEnforcer.register_asset(
        asset_id="asset_chat_001",
        trip_id="trip_ret_2",
        customer_id="cust_202",
        category=RetentionCategory.COMMUNICATION_LOGS,
    )

    cert = RetentionEnforcer.execute_erasure(asset.asset_id, reason="Customer GDPR Art 17 request")
    assert cert.asset_id == "asset_chat_001"
    assert "GDPR" in cert.reason
    assert RetentionEnforcer.get_certificate(cert.certificate_id) is not None
