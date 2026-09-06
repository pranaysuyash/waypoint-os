"""
tests/test_pdf_proposal_generator.py — Tests for Proposal Document HTML/PDF Generator.
"""

from src.proposals.pdf_generator import ProposalDaySpec, ProposalDocumentGenerator, ProposalDocumentSpec


def test_proposal_document_generator_html():
    """Verify ProposalDocumentGenerator compiles responsive HTML markup with all required fields."""
    spec = ProposalDocumentSpec(
        trip_title="10-Day Classic Italian Renaissance",
        traveler_name="Eleanor Vance",
        traveler_email="eleanor@example.com",
        agency_name="Waypoint Luxury Travel",
        currency="EUR",
        total_price=7850.0,
        departure_date="2026-10-05",
        return_date="2026-10-15",
        destination_summary="Rome, Florence & Venice",
        verification_token="prop_test_token_999",
        days=[
            ProposalDaySpec(
                day_number=1,
                title="Arrival in the Eternal City",
                location="Rome",
                highlights=["Private luxury transfer to Hotel de Russie", "Evening aperitivo overlooking Piazza del Popolo"],
                accommodation="Hotel de Russie (Executive Suite)",
                meals_included=["Dinner"],
            ),
            ProposalDaySpec(
                day_number=2,
                title="Vatican & Colosseum VIP Exploration",
                location="Rome",
                highlights=["Before-hours Vatican Museums tour", "Private Colosseum arena floor access"],
                accommodation="Hotel de Russie",
                meals_included=["Breakfast", "Lunch"],
            ),
        ],
        supplier_terms=["30% deposit due on e-signature", "Full refund if cancelled 30 days prior to departure"],
    )

    markup = ProposalDocumentGenerator.generate_html(spec)
    assert "<!DOCTYPE html>" in markup
    assert "10-Day Classic Italian Renaissance" in markup
    assert "Eleanor Vance" in markup
    assert "EUR 7,850.00" in markup
    assert "Hotel de Russie" in markup
    assert "prop_test_token_999" in markup
    assert "30% deposit due" in markup
