"""
src/intake/currency_registry.py — canonical currency-token registry (ISO 4217
subset + symbols + regional spellings).

The geography precedent (GeoNames data + `is_known_city_normalized`) applied to
currencies: one data table, one O(1) resolution API, every consumer shares it.
FND-0341's default-currency POLICY (unmarked → agency locale, platform INR)
lives in extractors/orchestration; this module is only the token→code DATA —
what a marker IS, never what an unmarked amount means.

Consumers: src/intake/extractors.py (budget extraction). Extensible to
proposal compilation and commercial analytics without new forks of the table.
"""

from __future__ import annotations

from typing import Dict, Optional

# token (lowercased, stripped) -> ISO 4217 code. Symbols included: budget
# text mixes "$4k" and "5000 rupees" freely. Keep sorted by code for review.
CURRENCY_TOKENS: Dict[str, str] = {
    "$": "USD",
    "usd": "USD",
    "dollar": "USD",
    "dollars": "USD",
    "buck": "USD",
    "bucks": "USD",
    "€": "EUR",
    "eur": "EUR",
    "euro": "EUR",
    "euros": "EUR",
    "£": "GBP",
    "gbp": "GBP",
    "₹": "INR",
    "rs": "INR",
    "rupee": "INR",
    "rupees": "INR",
    "inr": "INR",
    "₦": "NGN",
    "ngn": "NGN",
    "r": "ZAR",
    "zar": "ZAR",
    "kes": "KES",
    "ghs": "GHS",
    "aed": "AED",
    "sar": "SAR",
    "jpy": "JPY",
    "cny": "CNY",
    "npr": "NPR",
    "lkr": "LKR",
    "php": "PHP",
    "myr": "MYR",
    "thb": "THB",
    "idr": "IDR",
    "mxn": "MXN",
    "brl": "BRL",
    "aud": "AUD",
    "cad": "CAD",
    "sgd": "SGD",
}


def resolve_currency_token(token: Optional[str]) -> Optional[str]:
    """Token → ISO 4217 code, or None when the token is not a currency
    marker (an unmarked amount is a POLICY decision, never made here)."""
    normalized = (token or "").strip().lower()
    return CURRENCY_TOKENS.get(normalized)
