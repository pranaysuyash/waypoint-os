"""Currency agreement and repeated-symbol range contracts for budget extraction."""

from src.intake.extractors import PLATFORM_DEFAULT_CURRENCY, _extract_budget
from src.intake.currency_registry import CURRENCY_TOKENS, resolve_currency_token


def test_currency_registry_is_single_source_of_truth():
    """Every token in the registry resolves; the registry carries the full
    legacy table (FND-0341 map extraction — no consumer forked the data)."""
    for token, code in CURRENCY_TOKENS.items():
        assert resolve_currency_token(token) == code, token
        assert resolve_currency_token(token.upper()) == code, token
        assert resolve_currency_token(f"  {token}  ") == code, token
    assert resolve_currency_token("not-a-currency") is None
    assert resolve_currency_token(None) is None
    assert resolve_currency_token("") is None
    # the geography-parity members that must never regress
    for token, code in (
        ("rupees", "INR"), ("₹", "INR"), ("$", "USD"), ("euro", "EUR"), ("gbp", "GBP")
    ):
        assert CURRENCY_TOKENS[token] == code


def test_repeated_currency_symbol_is_preserved_across_range():
    result = _extract_budget("Budget: $4,000 to $6,000 total")

    assert result is not None
    assert result["min"] == 4000
    assert result["max"] == 6000
    assert result["currency"] == "USD"


# ---------------------------------------------------------------------------
# FND-0341: unmarked amounts take the agency/platform default (INR), never
# bare USD. Explicit markers and the lakh/crore market signal stay dominant.
# ---------------------------------------------------------------------------

def test_platform_default_currency_is_inr():
    """India-first platform constant; AgencySettings.default_currency agrees."""
    from src.intake.config.agency_settings import AgencySettings

    assert PLATFORM_DEFAULT_CURRENCY == "INR"
    assert AgencySettings(agency_id="a1").default_currency == "INR"


def test_unmarked_amount_defaults_to_inr():
    """The finding's own case: '60k total max' is rupees, not dollars."""
    result = _extract_budget("60k total max")
    assert result is not None
    assert result["currency"] == "INR"

    result2 = _extract_budget("budget is around 5000 for the trip")
    assert result2 is not None
    assert result2["currency"] == "INR"


def test_unmarked_amount_honors_agency_override():
    """The agency-locale seam: extract/normalize can carry a non-default."""
    result = _extract_budget("60k total max", default_currency="USD")
    assert result is not None
    assert result["currency"] == "USD"


def test_rupee_word_is_explicit_inr():
    """'rupees' matched the token pattern but was missing from the map —
    it must resolve INR explicitly (FACT-grade evidence), not fall through."""
    result = _extract_budget("budget 5000 rupees for everything")
    assert result is not None
    assert result["currency"] == "INR"


def test_lakh_signal_beats_default():
    result = _extract_budget("budget 3 lakhs for the wedding trip")
    assert result is not None
    assert result["currency"] == "INR"
    assert result["min"] == 300000


def test_explicit_usd_marker_still_wins():
    result = _extract_budget("budget is around 5000 USD for the trip")
    assert result is not None
    assert result["currency"] == "USD"


def test_mixed_currency_range_abstains_instead_of_converting():
    assert _extract_budget("Budget: $4,000 to €6,000 total") is None


def test_unmarked_range_defaults_to_inr():
    result = _extract_budget("Budget: 4,000 to 6,000 total")
    assert result is not None
    assert result["min"] == 4000
    assert result["max"] == 6000
    assert result["currency"] == "INR"


def test_repeated_currency_code_is_preserved_across_range():
    result = _extract_budget("Budget: USD 4,000 to USD 6,000 total")

    assert result is not None
    assert result["min"] == 4000
    assert result["max"] == 6000
    assert result["currency"] == "USD"


def test_single_currency_and_shared_suffix_range_remains_supported():
    result = _extract_budget("Budget: $4k-$6k total")

    assert result is not None
    assert result["min"] == 4000
    assert result["max"] == 6000
    assert result["currency"] == "USD"
