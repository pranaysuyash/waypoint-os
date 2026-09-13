"""
intake.geography — Geography database for origin/destination extraction.

Combines GeoNames (CC-BY 4.0) + world-cities.json (ODbL-1.0) + accumulated cities.

**ATTRIBUTION REQUIRED**: GeoNames data is CC-BY 4.0 licensed.
Any UI using location data must include:
  "Location data © <a href="https://www.geonames.org/">GeoNames</a>"

Files:
- data/cities5000.txt: GeoNames dump (cities with population > 5000)
- data/cities.json: world-cities.json supplemental dataset
- data/accumulated_cities.json: Organic additions from user messages
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import FrozenSet, Set, Optional, Dict, Any, List, Tuple

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl


# =============================================================================
# CONFIGURATION
# =============================================================================

# Population threshold to filter out very small places
_MIN_POPULATION = 5000

# Paths (relative to this file's parent/data/)
_DATA_PATH = Path(__file__).parent.parent.parent / "data"
_GEONAMES_PATH = _DATA_PATH / "cities5000.txt"
_WORLDCITIES_PATH = _DATA_PATH / "cities.json"
_ACCUMULATED_PATH = _DATA_PATH / "accumulated_cities.json"

# Non-cities that commonly appear in travel text
# These are words that look like they could be places but aren't
_BLACKLIST: Set[str] = {
    # Prepositions/common words
    "from", "starting", "departing", "via", "viaing",
    "next", "this", "last", "text", "message", "booking",
    # Trip-related
    "trip", "vacation", "holiday", "planning", "help",
    "tour", "travel", "journey", "visit", "stay",
    # Ambiguous terms
    "place", "somewhere", "anywhere", "destination",
    "spot", "location", "area", "region",
    # Month names (can be place names but should be excluded in travel context)
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
    # Days of week (some might be place names)
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    # Common non-place capitalized words in travel
    "Family", "Budget", "Group", "Team", "Client", "Customer",
    # Pronouns (should never be destinations)
    "We", "I", "My", "Our", "The", "This", "That", "It",
    "They", "He", "She", "Us", "You",
}

_BLACKLIST_LOWER: Optional[Set[str]] = None

def _get_blacklist_lower() -> Set[str]:
    """Return blacklist normalized to lowercase (cached)."""
    global _BLACKLIST_LOWER
    if _BLACKLIST_LOWER is None:
        _BLACKLIST_LOWER = {b.lower() for b in _BLACKLIST}
    return _BLACKLIST_LOWER

# Country names commonly used as destination synonyms
# When travelers say "Japan", they mean "Japan (main destinations like Tokyo)"
# This is a minimal set for common patterns, not exhaustive country coverage
_COUNTRY_DESTINATIONS: Set[str] = {
    # Asia
    "Japan", "Singapore", "Thailand", "Malaysia", "Vietnam",
    "Indonesia", "Philippines", "South Korea", "Taiwan",
    "Maldives", "Sri Lanka", "Nepal", "Bhutan",
    # Europe
    "France", "Italy", "Spain", "Germany", "Switzerland",
    "UK", "United Kingdom", "England", "Scotland", "Ireland",
    "Netherlands", "Belgium", "Austria", "Portugal", "Greece",
    # Americas
    "USA", "United States", "Canada", "Mexico", "Brazil",
    "Argentina", "Peru", "Chile",
    # Middle East
    "UAE", "Dubai", "Abu Dhabi", "Qatar", "Oman", "Turkey",
    # Indian territories/regions commonly used as destinations
    "Andaman",
    # Africa
    "South Africa", "Egypt", "Morocco", "Kenya", "Tanzania", "Mauritius", "Seychelles",
    "Namibia", "Botswana", "Rwanda", "Uganda", "Zimbabwe", "Tunisia", "Iceland",
    "Georgia", "Azerbaijan", "Uzbekistan", "Kazakhstan", "Bahrain", "Saudi Arabia",
    "Nigeria", "Ethiopia", "Ghana", "Senegal", "Croatia", "Serbia", "Slovenia",
    "Slovakia", "Czech Republic", "Hungary", "Moldova",
    # Oceania
    "Australia", "New Zealand", "Fiji", "Maldives",
    # Long multi-word
    "United Arab Emirates",
}

# Pre-built lowercase lookup for O(1) membership tests
_COUNTRY_LOWER: Set[str] = {c.lower() for c in _COUNTRY_DESTINATIONS}

# Canonical display casing: lowercase alias -> curated canonical name
# ("uk" -> "UK", "south korea" -> "South Korea").
COUNTRY_CANONICAL_ALIASES: Dict[str, str] = {c.lower(): c for c in _COUNTRY_DESTINATIONS}

# ISO 3166-1 alpha-2 code per country alias. Powers destination containment
# (D-03 / D-04 research): a city "is inside" a mentioned country when
# get_city_country(city) == get_country_iso_code(country_alias).
_COUNTRY_NAME_TO_ISO: Dict[str, str] = {
    # Asia
    "japan": "JP", "singapore": "SG", "thailand": "TH", "malaysia": "MY",
    "vietnam": "VN", "indonesia": "ID", "philippines": "PH",
    "south korea": "KR", "taiwan": "TW", "maldives": "MV",
    "sri lanka": "LK", "nepal": "NP", "bhutan": "BT",
    # Europe
    "france": "FR", "italy": "IT", "spain": "ES", "germany": "DE",
    "switzerland": "CH", "uk": "GB", "united kingdom": "GB",
    "england": "GB", "scotland": "GB", "ireland": "IE",
    "netherlands": "NL", "belgium": "BE", "austria": "AT",
    "portugal": "PT", "greece": "GR",
    # Americas
    "usa": "US", "united states": "US", "canada": "CA", "mexico": "MX",
    "brazil": "BR", "argentina": "AR", "peru": "PE", "chile": "CL",
    # Middle East
    "uae": "AE", "dubai": "AE", "abu dhabi": "AE", "qatar": "QA",
    "oman": "OM", "turkey": "TR", "united arab emirates": "AE",
    # Indian territories/regions
    "andaman": "IN",
    # Africa / Eurasia / Oceania (mirrors _COUNTRY_DESTINATIONS entries)
    "south africa": "ZA", "egypt": "EG", "morocco": "MA", "kenya": "KE",
    "tanzania": "TZ", "mauritius": "MU", "seychelles": "SC",
    "namibia": "NA", "botswana": "BW", "rwanda": "RW", "uganda": "UG",
    "zimbabwe": "ZW", "tunisia": "TN", "iceland": "IS", "georgia": "GE",
    "azerbaijan": "AZ", "uzbekistan": "UZ", "kazakhstan": "KZ",
    "bahrain": "BH", "saudi arabia": "SA", "nigeria": "NG",
    "ethiopia": "ET", "ghana": "GH", "senegal": "SN", "croatia": "HR",
    "serbia": "RS", "slovenia": "SI", "slovakia": "SK",
    "czech republic": "CZ", "hungary": "HU", "moldova": "MD",
    "australia": "AU", "new zealand": "NZ", "fiji": "FJ",
}

# Country aliases that are themselves city-level destinations (city-states /
# primary cities). A mention of these is a city commitment, never a
# containing-country scope, so they are excluded from D-03 containment
# resolution even though they live in _COUNTRY_DESTINATIONS.
_CITY_LEVEL_COUNTRY_ALIASES: FrozenSet[str] = frozenset({
    "dubai", "abu dhabi", "singapore",
})


# =============================================================================
# MODULE STATE (lazy-loaded, cached)
# =============================================================================

_geonames_cities: Optional[Set[str]] = None
_worldcities_cities: Optional[Set[str]] = None
_all_known_cities: Optional[Set[str]] = None
_accumulated_cities: Set[str] = set()

# City -> Country Code mapping (from GeoNames only)
# For duplicate city names, stores the entry with highest population
_city_to_country: Optional[Dict[str, str]] = None


# =============================================================================
# DATASET LOADERS
# =============================================================================

def _load_geonames() -> Set[str]:
    """
    Load cities from GeoNames dump.

    GeoNames format (tab-separated):
    geonameid,name,asciiname,alternatenames,feature,class,featurecode,
    countrycode,cc2,admin1,admin2,admin3,admin4,admin5,population,elevation,dem,timezone

    Only loads cities with population >= _MIN_POPULATION.
    Stores name, asciiname, and all alternate names.

    Note: Alternate names field is comma-separated and includes many variations
    including native spellings, transliterations, and historical names.

    Side effect: Also builds _city_to_country mapping for domestic/intl classification.
    For duplicate city names (e.g., "London" in UK and US), uses the one with higher population.
    """
    global _geonames_cities, _city_to_country
    if _geonames_cities is not None:
        return _geonames_cities

    cities: Set[str] = set()
    # Store (name, country, population) tuples to resolve duplicates later
    city_entries: List[Tuple[str, str, int]] = []

    if not _GEONAMES_PATH.exists():
        _geonames_cities = cities
        return cities

    with open(_GEONAMES_PATH, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 15:
                name = parts[1]  # Native name
                asciiname = parts[2]  # ASCII name
                alternatenames = parts[3] if len(parts) > 3 else ""  # Comma-separated
                countrycode = parts[8]  # Country code (e.g., "IN", "US")
                pop_str = parts[14]
                population = int(pop_str) if pop_str else 0

                if population >= _MIN_POPULATION:
                    if name:
                        cities.add(name)
                        city_entries.append((name, countrycode, population))
                    if asciiname:
                        cities.add(asciiname)
                        city_entries.append((asciiname, countrycode, population))
                    # Add all alternate names (includes "Bangalore" for Bengaluru)
                    if alternatenames:
                        for alt_name in alternatenames.split(","):
                            alt_name = alt_name.strip()
                            if alt_name:
                                cities.add(alt_name)
                                city_entries.append((alt_name, countrycode, population))

    _geonames_cities = cities

    # Build city_to_country by preferring higher population for duplicates
    city_country: Dict[str, str] = {}
    city_pop: Dict[str, int] = {}
    for name, country, pop in city_entries:
        if name not in city_pop or pop > city_pop[name]:
            city_country[name] = country
            city_pop[name] = pop

    _city_to_country = city_country
    return cities


def _load_worldcities() -> Set[str]:
    """
    Load cities from world-cities.json (supplemental dataset).

    Format: JSON array of country objects, each with nested 'cities' array.
    [{ "name": "Afghanistan", "cities": ["City1", "City2", ...] }, ...]
    """
    global _worldcities_cities
    if _worldcities_cities is not None:
        return _worldcities_cities

    cities: Set[str] = set()

    if not _WORLDCITIES_PATH.exists():
        return cities

    with open(_WORLDCITIES_PATH) as f:
        data = json.load(f)
        # Handle nested format: countries -> cities array
        for country in data:
            city_list = country.get("cities", [])
            if isinstance(city_list, list):
                for city in city_list:
                    if isinstance(city, str) and city:
                        cities.add(city)

    _worldcities_cities = cities
    return cities


def _load_accumulated() -> Set[str]:
    """
    Load accumulated cities from previous sessions.

    Returns set of city names that have been organically added.
    """
    global _accumulated_cities
    if _ACCUMULATED_PATH.exists():
        with open(_ACCUMULATED_PATH) as f:
            _accumulated_cities = set(json.load(f))
    return _accumulated_cities


def _build_union() -> Set[str]:
    """
    Build union of all city sources (computed once, cached).

    This is the primary lookup - combines all three sources.
    All values are normalized to lowercase for case-insensitive matching.
    """
    global _all_known_cities
    if _all_known_cities is not None:
        return _all_known_cities

    geonames = _load_geonames()
    worldcities = _load_worldcities()
    accumulated = _load_accumulated()

    # Union of all sources, normalized to lowercase
    _all_known_cities = {c.lower() for c in (geonames | worldcities | accumulated)}
    return _all_known_cities


# =============================================================================
# PUBLIC API
# =============================================================================

def is_known_city(name: str) -> bool:
    """
    Check if name is a known city (any source).

    Args:
        name: City name to check

    Returns:
        True if name is in any of our city datasets

    Examples:
        >>> is_known_city("Bangalore")
        True
        >>> is_known_city("from")
        False
        >>> is_known_city("NonExistentCity123")
        False
    """
    if not name or name.lower() in _get_blacklist_lower():
        return False
    return name.lower() in _build_union()


def is_known_city_normalized(name: str) -> bool:
    """
    Check if name is a known city, with basic normalization.

    Handles case insensitivity and common spelling variations.
    """
    if not name:
        return False

    name_lower = name.lower()
    if name_lower in _get_blacklist_lower():
        return False

    # Check against normalized lookup (already lowercase)
    all_cities = _build_union()
    return name_lower in all_cities


def record_seen_city(city: str, confidence: float = 0.5) -> bool:
    """
    Add newly seen city if confidence is high enough.

    Only accumulates if:
    - confidence > 0.7 (reasonably sure it's a city)
    - Not already in baseline datasets
    - Not a blacklisted term

    Args:
        city: City name to record
        confidence: Confidence score 0.0-1.0

    Returns:
        True if city was added, False otherwise

    Examples:
        >>> record_seen_city("Munnar", 0.9)  # High confidence
        True
        >>> record_seen_city("maybeplace", 0.3)  # Low confidence
        False
    """
    global _all_known_cities, _accumulated_cities

    if confidence <= 0.7:
        return False

    if not city or city.lower() in _get_blacklist_lower():
        return False

    if city in _build_union():
        return False  # Already known

    # Add to accumulated and persist
    _accumulated_cities.add(city)

    # Invalidate cache so next lookup includes this
    _all_known_cities = None

    _persist_accumulated()
    return True


def _persist_accumulated() -> None:
    """
    Save accumulated cities to disk with exclusive file locking.

    Uses flock (POSIX) on macOS/Linux, and a lock file with msvcrt on Windows.
    Advisory locking only — works within the same process and between processes
    on the same host. Not a distributed lock.
    """
    lock_path = _ACCUMULATED_PATH.with_suffix(".lock")
    if sys.platform == "win32":
        with open(lock_path, "w") as lock_f:
            try:
                msvcrt.locking(lock_f.fileno(), msvcrt.LK_LOCK, 1)
                try:
                    with open(_ACCUMULATED_PATH, "w") as f:
                        json.dump(sorted(_accumulated_cities), f, indent=2)
                finally:
                    msvcrt.locking(lock_f.fileno(), msvcrt.LK_UNLCK, 1)
            except (IOError, OSError):
                pass
    else:
        with open(lock_path, "w") as lock_f:
            fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX)
            try:
                with open(_ACCUMULATED_PATH, "w") as f:
                    json.dump(sorted(_accumulated_cities), f, indent=2)
            finally:
                fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)


def get_dataset_info() -> Dict[str, Any]:
    """
    Return stats about loaded datasets.

    Useful for debugging, monitoring, and health checks.

    Returns:
        Dict with counts from each dataset and total

    Examples:
        >>> get_dataset_info()
        {
            'geonames_count': 68316,
            'worldcities_count': 152851,
            'accumulated_count': 12,
            'total_unique': 213456
        }
    """
    return {
        "geonames_count": len(_load_geonames()),
        "worldcities_count": len(_load_worldcities()),
        "accumulated_count": len(_load_accumulated()),
        "total_unique": len(_build_union()),
        "blacklist_count": len(_BLACKLIST),
        "min_population_threshold": _MIN_POPULATION,
    }


def get_attribution_notice() -> str:
    """
    Return attribution notice for GeoNames data.

    Use this in UI footers or API responses.

    Returns:
        HTML string with attribution

    Examples:
        >>> get_attribution_notice()
        'Location data © <a href="https://www.geonames.org/">GeoNames</a>'
    """
    return 'Location data © <a href="https://www.geonames.org/">GeoNames</a>'


def clear_cache() -> None:
    """
    Clear all cached datasets.

    Forces reload from disk on next access.
    Useful for testing or after external data updates.
    """
    global _geonames_cities, _worldcities_cities, _all_known_cities, _city_to_country
    _geonames_cities = None
    _worldcities_cities = None
    _all_known_cities = None
    _city_to_country = None


def get_city_country(name: str) -> Optional[str]:
    """
    Get country code for a city (from GeoNames only).

    Args:
        name: City name to look up

    Returns:
        ISO 3166-1 alpha-2 country code (e.g., "IN", "US", "GB")
        None if city not found in GeoNames (world-cities and accumulated
        don't have country info)

    Examples:
        >>> get_city_country("Bangalore")
        'IN'
        >>> get_city_country("New York")
        'US'
        >>> get_city_country("UnknownCity")
        None
    """
    global _city_to_country
    if _city_to_country is None:
        _load_geonames()  # Builds the mapping

    return _city_to_country.get(name) if _city_to_country else None


def get_country_iso_code(name: str) -> Optional[str]:
    """
    Get the ISO 3166-1 alpha-2 code for a country alias ("japan" -> "JP").

    Powers containment checks (D-03): a city belongs to a mentioned country
    when ``get_city_country(city) == get_country_iso_code(country_alias)``.

    Args:
        name: Country alias (any casing), e.g. "Japan", "UK", "south korea"

    Returns:
        ISO alpha-2 code, or None when the alias is unknown or is a
        city-level destination (Dubai/Abu Dhabi/Singapore).
    """
    lower = (name or "").strip().lower()
    if lower in _CITY_LEVEL_COUNTRY_ALIASES:
        return None
    return _COUNTRY_NAME_TO_ISO.get(lower)


def is_known_destination(name: str) -> bool:
    """
    Check if name is a known destination (city or commonly-used country).

    This is the primary filter for destination extraction.

    Args:
        name: Destination name to check

    Returns:
        True if name is a known city or commonly-used country name

    Examples:
        >>> is_known_destination("Bangalore")
        True
        >>> is_known_destination("Japan")
        True
        >>> is_known_destination("from")
        False
    """
    if not name:
        return False

    lower = name.lower()

    # Case-insensitive blacklist check (for month names etc.)
    if lower in _get_blacklist_lower():
        return False

    return lower in _build_union() or lower in _COUNTRY_LOWER


# =============================================================================
# COUNTRY TO GATEWAY CITIES HIERARCHY (D-03)
# =============================================================================

COUNTRY_GATEWAYS: Dict[str, Dict[str, Any]] = {
    "italy": {
        "country_code": "IT",
        "canonical_name": "Italy",
        "primary_hubs": ["FCO", "MXP", "VCE", "FLR"],
        "recommended_cities": ["Rome", "Florence", "Venice", "Milan"],
        "is_country_level": True,
    },
    "japan": {
        "country_code": "JP",
        "canonical_name": "Japan",
        "primary_hubs": ["HND", "NRT", "KIX"],
        "recommended_cities": ["Tokyo", "Kyoto", "Osaka"],
        "is_country_level": True,
    },
    "france": {
        "country_code": "FR",
        "canonical_name": "France",
        "primary_hubs": ["CDG", "ORY", "NCE"],
        "recommended_cities": ["Paris", "Nice", "Lyon"],
        "is_country_level": True,
    },
    "switzerland": {
        "country_code": "CH",
        "canonical_name": "Switzerland",
        "primary_hubs": ["ZRH", "GVA", "BSL"],
        "recommended_cities": ["Zurich", "Geneva", "Lucerne", "Zermatt"],
        "is_country_level": True,
    },
    "united kingdom": {
        "country_code": "GB",
        "canonical_name": "United Kingdom",
        "primary_hubs": ["LHR", "LGW", "EDI"],
        "recommended_cities": ["London", "Edinburgh"],
        "is_country_level": True,
    },
    "uk": {
        "country_code": "GB",
        "canonical_name": "United Kingdom",
        "primary_hubs": ["LHR", "LGW", "EDI"],
        "recommended_cities": ["London", "Edinburgh"],
        "is_country_level": True,
    },
    "spain": {
        "country_code": "ES",
        "canonical_name": "Spain",
        "primary_hubs": ["MAD", "BCN", "AGP"],
        "recommended_cities": ["Madrid", "Barcelona", "Seville"],
        "is_country_level": True,
    },
    "greece": {
        "country_code": "GR",
        "canonical_name": "Greece",
        "primary_hubs": ["ATH", "JMK", "JTR"],
        "recommended_cities": ["Athens", "Santorini", "Mykonos"],
        "is_country_level": True,
    },
}


def resolve_destination_hierarchy(destination_name: str) -> Dict[str, Any]:
    """
    Resolves whether a destination query is a high-level country vs specific city.
    If country-level, provides recommended committed gateway cities and hubs.
    """
    clean = (destination_name or "").strip().lower()
    if clean in COUNTRY_GATEWAYS:
        return {
            "type": "country",
            "name": clean,
            **COUNTRY_GATEWAYS[clean],
        }

    return {
        "type": "city",
        "name": destination_name,
        "is_country_level": False,
        "country": get_city_country(destination_name) if is_known_city(destination_name) else None,
    }


# =============================================================================
# MACRO TRAVEL REGIONS (preference inference)
# =============================================================================

# Macro travel regions for preference inference ("went to japan, korea…
# loved it" → East Asia affinity). Country-canonical names only; city
# inputs resolve through get_city_country first.
COUNTRY_MACRO_REGIONS: Dict[str, str] = {
    # East Asia
    "japan": "East Asia", "south korea": "East Asia", "korea": "East Asia",
    "china": "East Asia", "taiwan": "East Asia", "hong kong": "East Asia",
    "mongolia": "East Asia",
    # Southeast Asia
    "thailand": "Southeast Asia", "vietnam": "Southeast Asia",
    "indonesia": "Southeast Asia", "malaysia": "Southeast Asia",
    "singapore": "Southeast Asia", "philippines": "Southeast Asia",
    "cambodia": "Southeast Asia", "laos": "Southeast Asia",
    "myanmar": "Southeast Asia", "brunei": "Southeast Asia",
    # South Asia
    "india": "South Asia", "sri lanka": "South Asia", "nepal": "South Asia",
    "bhutan": "South Asia", "bangladesh": "South Asia",
    "maldives": "South Asia", "pakistan": "South Asia",
    # Middle East
    "united arab emirates": "Middle East", "uae": "Middle East",
    "saudi arabia": "Middle East", "qatar": "Middle East",
    "oman": "Middle East", "jordan": "Middle East", "israel": "Middle East",
    "turkey": "Middle East", "turkiye": "Middle East",
    # Europe
    "france": "Europe", "italy": "Europe", "spain": "Europe",
    "portugal": "Europe", "germany": "Europe", "switzerland": "Europe",
    "austria": "Europe", "netherlands": "Europe", "belgium": "Europe",
    "united kingdom": "Europe", "uk": "Europe", "ireland": "Europe",
    "greece": "Europe", "croatia": "Europe", "czech republic": "Europe",
    "hungary": "Europe", "poland": "Europe", "iceland": "Europe",
    "norway": "Europe", "sweden": "Europe", "denmark": "Europe",
    "finland": "Europe",
    # Americas
    "united states": "North America", "usa": "North America",
    "us": "North America", "canada": "North America",
    "mexico": "Latin America", "brazil": "Latin America",
    "argentina": "Latin America", "peru": "Latin America",
    "colombia": "Latin America", "chile": "Latin America",
    "costa rica": "Latin America",
    # Africa
    "south africa": "Africa", "kenya": "Africa", "tanzania": "Africa",
    "egypt": "Africa", "morocco": "Africa", "namibia": "Africa",
    # Oceania
    "australia": "Oceania", "new zealand": "Oceania", "fiji": "Oceania",
}


def get_macro_region(place: str) -> Optional[str]:
    """Macro travel region for a place name. City names resolve through
    their country first (Tokyo → Japan → East Asia); unknown places return
    None rather than guessing."""
    if not place:
        return None
    key = place.strip().lower()
    region = COUNTRY_MACRO_REGIONS.get(key)
    if region:
        return region
    country = get_city_country(key)
    if country:
        return COUNTRY_MACRO_REGIONS.get(country.lower())
    return None


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "is_known_city",
    "is_known_city_normalized",
    "is_known_destination",
    "record_seen_city",
    "get_dataset_info",
    "get_attribution_notice",
    "clear_cache",
    "get_city_country",
    "get_country_iso_code",
    "get_macro_region",
    "resolve_destination_hierarchy",
    "COUNTRY_GATEWAYS",
    "COUNTRY_CANONICAL_ALIASES",
    "COUNTRY_MACRO_REGIONS",
    "_BLACKLIST",
    "_MIN_POPULATION",
]
