"""Currency agreement and repeated-symbol range contracts for budget extraction."""

from src.intake.extractors import _extract_budget


def test_repeated_currency_symbol_is_preserved_across_range():
    result = _extract_budget("Budget: $4,000 to $6,000 total")

    assert result is not None
    assert result["min"] == 4000
    assert result["max"] == 6000
    assert result["currency"] == "USD"


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


def test_mixed_currency_range_abstains_instead_of_converting():
    assert _extract_budget("Budget: $4,000 to €6,000 total") is None
