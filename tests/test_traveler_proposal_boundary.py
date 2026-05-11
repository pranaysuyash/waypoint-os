"""
Tests for the traveler_proposal public/internal boundary contract.

These tests intentionally cover the safety rails before any proposal generator
is implemented.
"""

import pytest

from intake.traveler_proposal import (
    InternalQuoteSheet,
    TravelerActivity,
    TravelerPriceComponent,
    TravelerPricing,
    TravelerProposal,
    TravelerProposalBoundaryResult,
    VendorContact,
    assert_traveler_payload_safe,
)


def _proposal() -> TravelerProposal:
    return TravelerProposal(
        proposal_id="prop_001",
        packet_id="packet_001",
        title="Singapore Family Adventure",
        summary="A five-night family-friendly Singapore plan.",
        highlights=["Gardens by the Bay", "Universal Studios"],
        activities=[
            TravelerActivity(
                name="Gardens by the Bay",
                description="Evening garden visit.",
                duration="3 hours",
                why_included="Matches the family preference for nature.",
            )
        ],
        pricing=TravelerPricing(
            currency="INR",
            total_per_person=79000,
            total_for_group=237000,
            components=[
                TravelerPriceComponent(
                    category="Activities",
                    description="Gardens and zoo tickets",
                    price=24000,
                )
            ],
            includes=["Hotels", "Transfers"],
            excludes=["Visa fees"],
            cancellation_policy="Subject to supplier terms.",
        ),
        why_this_fits="Balanced pacing for a family trip.",
        next_steps=["Review the proposal", "Confirm preferred hotel tier"],
        expiry_date="2026-10-01",
        assumptions_made=["Flight fares are indicative until ticketed."],
    )


def _internal_quote_sheet() -> InternalQuoteSheet:
    return InternalQuoteSheet(
        proposal_id="prop_001",
        vendors=[
            VendorContact(
                supplier_type="hotel",
                supplier_name="Pan Pacific",
                contact_name="Ops Manager",
                phone="+91-99999-00000",
                email="ops@example.test",
                booking_ref="BR-SECRET-123",
                net_rate=68000,
                margin_percent=12.5,
                reliability_score=0.94,
                notes="Preferred supplier.",
            )
        ],
        total_margin_amount=15000,
        total_margin_percent=6.3,
        margin_by_component={"hotel": 12.5},
    )


def test_traveler_projection_uses_semantic_stage_and_gate():
    result = TravelerProposalBoundaryResult(
        traveler_proposal=_proposal(),
        internal_quote_sheet=_internal_quote_sheet(),
        data_sources_used=["supplier_sheet", "crm_history"],
        completeness_score=0.91,
        personalization_score=0.88,
    )

    payload = result.to_traveler_dict()

    assert payload["stage"] == "traveler_proposal"
    assert payload["gate"] == "proposal_quality"
    assert payload["traveler_proposal"]["title"] == "Singapore Family Adventure"


@pytest.mark.parametrize(
    "forbidden_text",
    [
        "internal_quote_sheet",
        "supplier_name",
        "contact_name",
        "phone",
        "email",
        "booking_ref",
        "net_rate",
        "margin_percent",
        "margin_by_component",
        "data_sources_used",
    ],
)
def test_traveler_projection_excludes_internal_quote_sheet_fields(forbidden_text):
    result = TravelerProposalBoundaryResult(
        traveler_proposal=_proposal(),
        internal_quote_sheet=_internal_quote_sheet(),
        data_sources_used=["supplier_sheet", "crm_history"],
    )

    assert forbidden_text not in str(result.to_traveler_dict())


def test_internal_projection_retains_vendor_contacts_and_margins():
    result = TravelerProposalBoundaryResult(
        traveler_proposal=_proposal(),
        internal_quote_sheet=_internal_quote_sheet(),
        data_sources_used=["supplier_sheet"],
    )

    payload = result.to_internal_dict()

    vendor = payload["internal_quote_sheet"]["vendors"][0]
    assert vendor["supplier_name"] == "Pan Pacific"
    assert vendor["phone"] == "+91-99999-00000"
    assert vendor["email"] == "ops@example.test"
    assert vendor["booking_ref"] == "BR-SECRET-123"
    assert vendor["margin_percent"] == 12.5
    assert payload["internal_quote_sheet"]["margin_by_component"]["hotel"] == 12.5
    assert payload["audit"]["sources"] == ["supplier_sheet"]


@pytest.mark.parametrize(
    "payload,path",
    [
        ({"price": {"margin_percent": 12.5}}, "price.margin_percent"),
        ({"activities": [{"booking_ref": "BR-123"}]}, "activities[0].booking_ref"),
        ({"vendor_contacts": [{"phone": "+91-99999-00000"}]}, "vendor_contacts"),
        ({"raw_research_sources": ["crm note"]}, "raw_research_sources"),
    ],
)
def test_assert_traveler_payload_safe_rejects_restricted_nested_fields(payload, path):
    with pytest.raises(ValueError) as excinfo:
        assert_traveler_payload_safe(payload)

    assert path in str(excinfo.value)
