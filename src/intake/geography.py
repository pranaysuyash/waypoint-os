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
import os
import sys
from pathlib import Path
from typing import Set, Optional, Dict, Any, List, Tuple

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
    "South Africa", "Egypt", "Morocco", "Kenya", "Tanzania",
    # Oceania
    "Australia", "New Zealand", "Fiji", "Maldives",
    # Long multi-word
    "United Arab Emirates",
}

# Pre-built lowercase lookup for O(1) membership tests
_COUNTRY_LOWER: Set[str] = {c.lower() for c in _COUNTRY_DESTINATIONS}


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
    "_BLACKLIST",
    "_MIN_POPULATION",
]
