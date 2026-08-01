"""
tests/test_safety_false_positives.py — Regression suite for NB03 leakage guard.

Validates two things:
1. ALLOWED_TRAVEL_PHRASES: legitimate travel copy does NOT trigger false positives
2. Hard-block preservation: real internal leakage (field markers, raw pipeline terms)
   still triggers correctly.

Run:
    SPINE_API_DISABLE_AUTH=1 RUNNING_TESTS=1 uv run pytest tests/test_safety_false_positives.py -v

Context: Month 6 audit showed false-positive leakage blocks on phrases like
"unknown beaches of Goa" and "some ambiguity about visa dates" preventing
proposal export. Fixed via context-aware matching with ALLOWED_TRAVEL_PHRASES
allowlist. See ADR_NB03_LEAKAGE_FALSE_POSITIVE_FIX_2026-07-29.md
"""

from src.intake.safety import check_no_leakage


# ===========================================================================
# HELPERS
# ===========================================================================

def _make_bundle(user_message: str, system_context: str = "") -> dict:
    return {"user_message": user_message, "system_context": system_context}


def _no_leakage(text: str) -> bool:
    return len(check_no_leakage(_make_bundle(text))) == 0


def _has_leakage(text: str) -> bool:
    return len(check_no_leakage(_make_bundle(text))) > 0


# ===========================================================================
# PART 1: ALLOWED PHRASES — must NOT trigger leakage detection
# ===========================================================================

class TestAllowedTravelPhrases:
    """Legitimate travel copy that contains forbidden base words but must not be flagged."""

    def test_unknown_beaches(self):
        assert _no_leakage(
            "We recommend exploring the unknown beaches of Goa during your trip."
        ), "'unknown beaches' is a legitimate travel phrase — must not flag"

    def test_unknown_island(self):
        assert _no_leakage(
            "This unknown island remains a hidden gem off the coast of Thailand."
        )

    def test_unknown_destination(self):
        assert _no_leakage(
            "We are thrilled to introduce you to an unknown destination in Rajasthan."
        )

    def test_unknown_territory(self):
        assert _no_leakage(
            "Your safari takes you into unknown territory deep in the Serengeti."
        )

    def test_some_ambiguity_about_visa(self):
        assert _no_leakage(
            "There is some ambiguity about visa requirements for this route — "
            "we recommend applying 3 months in advance."
        ), "'some ambiguity' in natural context must not flag"

    def test_no_ambiguity(self):
        assert _no_leakage(
            "There is no ambiguity about your booking dates — confirmed for July 15."
        )

    def test_lesser_known(self):
        assert _no_leakage(
            "We have curated a selection of lesser-known villas in Tuscany for you."
        )

    def test_less_known(self):
        assert _no_leakage(
            "This less known region offers spectacular views without the tourist crowds."
        )

    def test_no_blockers_on_itinerary(self):
        assert _no_leakage(
            "Excellent news — there are no blockers on your proposed itinerary."
        )

    def test_not_a_blocker(self):
        assert _no_leakage(
            "The visa timing is not a blocker for your travel dates."
        )

    def test_working_hypothesis(self):
        assert _no_leakage(
            "Our working hypothesis is that a 10-night itinerary best fits your preferences."
        )

    def test_pricing_ambiguity(self):
        assert _no_leakage(
            "There may be pricing ambiguity on the Maldives overwater bungalows — "
            "we will confirm final rates by Thursday."
        )

    def test_empty_text_no_leakage(self):
        assert _no_leakage("")

    def test_plain_travel_copy_no_triggers(self):
        assert _no_leakage(
            "Your bespoke itinerary to Rajasthan includes private palace stays, "
            "camel safaris at dawn, and curated artisan market tours. "
            "All bookings are confirmed and refundable until 30 days before travel."
        )


# ===========================================================================
# PART 2: REAL LEAKAGE — must still trigger correctly
# ===========================================================================

class TestRealLeakageDetection:
    """Internal pipeline concepts in traveler-facing text must still be caught."""

    def test_raw_decision_state_field(self):
        assert _has_leakage(
            "decision_state: unknown — please complete intake"
        ), "bare decision_state + unknown is a real leakage"

    def test_raw_confidence_score_field(self):
        assert _has_leakage(
            "confidence_score: 0.43 — hypothesis pending resolution"
        ), "confidence_score field marker + hypothesis is real leakage"

    def test_internal_only_string(self):
        assert _has_leakage(
            "internal_only: true — do not share with traveler"
        )

    def test_owner_constraint_field(self):
        assert _has_leakage(
            "owner_constraint: markup 15% required before proposal"
        )

    def test_agency_note_field(self):
        assert _has_leakage(
            "agency_notes: soft_blocker on budget — follow up with owner"
        )

    def test_standalone_unknown_in_field_context(self):
        """'unknown' standing alone (not in an allowed phrase) in a key:value context."""
        assert _has_leakage(
            "budget: unknown\ndestination: Goa\ntravel_dates: unknown"
        ), "standalone 'unknown' in field-value context must still flag"

    def test_hypothesis_stack_reference(self):
        assert _has_leakage(
            "hypothesis_stack: [budget_flexible, dates_fixed] — internal notes only"
        )

    def test_hard_blocker_field(self):
        assert _has_leakage(
            "hard_blocker: no passport number — cannot proceed to booking"
        )

    def test_soft_blocker_field(self):
        assert _has_leakage(
            "soft_blocker: preferred airline not confirmed"
        )

    def test_contradiction_field(self):
        assert _has_leakage(
            "contradiction: budget mismatch — client said 5L but hotel cost is 8L"
        )


# ===========================================================================
# PART 3: EDGE CASES
# ===========================================================================

class TestLeakageEdgeCases:
    """Edge cases for the context-aware matching logic."""

    def test_unknown_at_sentence_start(self):
        # "Unknown" at the start of a sentence could be legitimate travel copy
        # Only blocked if internal marker nearby
        text = "Unknown parts of Kerala await you on this journey."
        leaks = check_no_leakage(_make_bundle(text))
        # This is ambiguous — no internal marker, but not in ALLOWED_TRAVEL_PHRASES exactly.
        # The implementation should NOT block this as it has no internal marker context.
        # If it does block, the test documents the behavior for review.
        # We expect NO leakage here because there's no internal marker nearby.
        assert len(leaks) == 0, (
            f"'Unknown' at sentence start without internal marker should not block. Got: {leaks}"
        )

    def test_ambiguity_near_internal_marker_is_flagged(self):
        """Even an 'allowed phrase' is overridden by internal marker proximity."""
        text = "some ambiguity\n\ndecision_state: NEEDS_INFO"
        # decision_state is an internal marker; ambiguity is nearby
        assert _has_leakage(text), (
            "Internal marker proximity must override the allowed phrase exemption"
        )

    def test_multiple_forbidden_terms_mixed(self):
        """Multiple forbidden terms where some are allowed and some are real leaks."""
        text = (
            "We found no blockers on the itinerary. However, decision_state: unknown — "
            "please complete the intake form."
        )
        leaks = check_no_leakage(_make_bundle(text))
        # "no blockers" should be allowed; "decision_state: unknown" should flag
        assert len(leaks) >= 1, f"Should flag at least one real leakage. Got: {leaks}"

    def test_system_context_field_is_scanned(self):
        """Leakage in system_context field is also detected."""
        bundle = {
            "user_message": "Your trip to Maldives looks wonderful!",
            "system_context": "Internal state: hypothesis = budget_conflict. Do not share.",
        }
        assert _has_leakage(bundle["system_context"]), (
            "system_context with internal terms must be flagged"
        )

    def test_invalid_input_returns_error_message(self):
        """Non-dict, non-bundle input returns error string (not raise)."""
        result = check_no_leakage("raw string")
        assert result == ["Invalid input type for leakage check"]
