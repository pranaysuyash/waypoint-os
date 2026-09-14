"""airport_codes — IATA code → canonical city resolution (P-F, Addendum 8/9).

Blueprint phase P-F: destination extraction misses cities named only by
their IATA code ("flying into SIN next week"). This table is the guard:
a 3-letter token is treated as an airport code ONLY on exact membership —
unknown 3-letter words can never become destinations through this path.

Curated for the agency's markets (India-heavy + major international).
City names match the geography vocabulary so downstream containment
(get_city_country / macro regions) resolves normally.
"""

from __future__ import annotations

from typing import Dict, Optional

# IATA -> (canonical_city, country_iso)
AIRPORT_CODE_CITIES: Dict[str, Dict[str, str]] = {
    # India
    "DEL": {"city": "Delhi", "country": "IN"},
    "BOM": {"city": "Mumbai", "country": "IN"},
    "BLR": {"city": "Bangalore", "country": "IN"},
    "MAA": {"city": "Chennai", "country": "IN"},
    "HYD": {"city": "Hyderabad", "country": "IN"},
    "CCU": {"city": "Kolkata", "country": "IN"},
    "GOI": {"city": "Goa", "country": "IN"},
    "COK": {"city": "Kochi", "country": "IN"},
    "AMD": {"city": "Ahmedabad", "country": "IN"},
    "PNQ": {"city": "Pune", "country": "IN"},
    "JAI": {"city": "Jaipur", "country": "IN"},
    # Southeast / East Asia
    "SIN": {"city": "Singapore", "country": "SG"},
    "BKK": {"city": "Bangkok", "country": "TH"},
    "HKT": {"city": "Phuket", "country": "TH"},
    "DPS": {"city": "Bali", "country": "ID"},
    "KUL": {"city": "Kuala Lumpur", "country": "MY"},
    "HAN": {"city": "Hanoi", "country": "VN"},
    "SGN": {"city": "Ho Chi Minh City", "country": "VN"},
    "HKG": {"city": "Hong Kong", "country": "HK"},
    "NRT": {"city": "Tokyo", "country": "JP"},
    "HND": {"city": "Tokyo", "country": "JP"},
    "KIX": {"city": "Osaka", "country": "JP"},
    "ICN": {"city": "Seoul", "country": "KR"},
    "MNL": {"city": "Manila", "country": "PH"},
    "PNH": {"city": "Phnom Penh", "country": "KH"},
    # Middle East
    "DXB": {"city": "Dubai", "country": "AE"},
    "AUH": {"city": "Abu Dhabi", "country": "AE"},
    "DOH": {"city": "Doha", "country": "QA"},
    "RUH": {"city": "Riyadh", "country": "SA"},
    "IST": {"city": "Istanbul", "country": "TR"},
    # Europe
    "LHR": {"city": "London", "country": "GB"},
    "LGW": {"city": "London", "country": "GB"},
    "CDG": {"city": "Paris", "country": "FR"},
    "FRA": {"city": "Frankfurt", "country": "DE"},
    "AMS": {"city": "Amsterdam", "country": "NL"},
    "BCN": {"city": "Barcelona", "country": "ES"},
    "MAD": {"city": "Madrid", "country": "ES"},
    "FCO": {"city": "Rome", "country": "IT"},
    "VCE": {"city": "Venice", "country": "IT"},
    "ZRH": {"city": "Zurich", "country": "CH"},
    "VIE": {"city": "Vienna", "country": "AT"},
    "ATH": {"city": "Athens", "country": "GR"},
    "LIS": {"city": "Lisbon", "country": "PT"},
    # Americas
    "JFK": {"city": "New York", "country": "US"},
    "EWR": {"city": "New York", "country": "US"},
    "LAX": {"city": "Los Angeles", "country": "US"},
    "SFO": {"city": "San Francisco", "country": "US"},
    "ORD": {"city": "Chicago", "country": "US"},
    "YYZ": {"city": "Toronto", "country": "CA"},
    "YVR": {"city": "Vancouver", "country": "CA"},
    "MEX": {"city": "Mexico City", "country": "MX"},
    # Oceania / Africa
    "SYD": {"city": "Sydney", "country": "AU"},
    "MEL": {"city": "Melbourne", "country": "AU"},
    "AKL": {"city": "Auckland", "country": "NZ"},
    "CPT": {"city": "Cape Town", "country": "ZA"},
    "JNB": {"city": "Johannesburg", "country": "ZA"},
    "NBO": {"city": "Nairobi", "country": "KE"},
}


def resolve_airport_code(token: str) -> Optional[Dict[str, str]]:
    """Resolve an exact 3-letter IATA code to city metadata.

    Exact membership IS the guard: unknown 3-letter words resolve to None
    and can never become destinations through this path.
    """
    if not token or len(token) != 3 or not token.isalpha():
        return None
    return AIRPORT_CODE_CITIES.get(token.strip().upper())
