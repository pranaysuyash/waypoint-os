# Geography Extraction Design Decision

**Date**: 2026-04-15
**Status**: DECIDED - Hybrid approach with GeoNames + world-cities.json
**Context**: Hardcoded geography lists causing extraction bugs

---

## The Problem

Current extraction uses hardcoded city lists (`DOMESTIC_DESTINATIONS`, `INTERNATIONAL_DESTINATIONS`) that:

- Are India-biased and limited
- Cause real bugs when common cities aren't recognized
- Mix origin-city and destination concerns
- Don't scale organically

Example bug: "from Pune" failed to extract because Pune wasn't in any list.

---

## Question

How do we fix geography extraction without hardcoding every city?

---

## Datasets Compared

| Dataset                       | Cities             | License   | Attribution           | Notes                                                        |
| ----------------------------- | ------------------ | --------- | --------------------- | ------------------------------------------------------------ |
| **GeoNames**                  | ~200k (pop > 1000) | CC-BY 4.0 | Required              | Larger, includes small towns, has alternate names + lat/long |
| **world-cities.json** (dr5hn) | ~150k              | ODbL-1.0  | Required, share-alike | Major cities + countries, single JSON file                   |

**⚠️ world-cities.json is ODbL-1.0, not MIT.** Previously misattributed. ODbL-1.0 has share-alake
obligations that conflict with proprietary licensing. Consider replacing with a CC0/MIT-licensed alternative
if proprietary distribution is required.

**CC-BY 4.0 is commercial-allowed.** Attribution means a footer credit, not per-call.

---

## Decision

**Hybrid approach: Combine both datasets + accumulate**

Use GeoNames as primary (coverage of smaller tourist spots), supplement with world-cities.json (catches any gaps), and accumulate organic additions.

**Rationale:**

- Travelers mention smaller places ("Munnar", "Pushkar", "Hampi") that major-city lists miss
- GeoNames CC-BY attribution is trivial (footer link)
- Combining both = maximum coverage from day one
- Union of both datasets covers edge cases either might miss individually

---

## Implementation Plan

### 1. Download Data

```bash
# GeoNames cities with population > 5000 (~50k cities)
curl -o data/cities5000.txt \
  https://download.geonames.org/export/dump/cities5000.zip

# world-cities.json as supplement
curl -o data/cities.json \
  https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/main/cities.json
```

### 2. Create `src/intake/geography.py`

```python
"""
Geography database for origin/destination extraction.

Combines GeoNames (CC-BY 4.0) + world-cities.json (MIT) + accumulated.
Attribution required for GeoNames: add footer credit to any UI using this.
"""

import json
from pathlib import Path
from typing import Set, Optional

# Population threshold to filter out very small places
_MIN_POPULATION = 5000

# Loaded from GeoNames format (cities5000.txt)
_GEONAMES_CITIES: Optional[Set[str]] = None

# Loaded from world-cities.json (supplement)
_WORLDCITIES_CITIES: Optional[Set[str]] = None

# Union cache (computed once)
_ALL_KNOWN_CITIES: Optional[Set[str]] = None

# Accumulated from real user messages
_ACCUMULATED_CITIES: Set[str] = set()
_ACCUMULATED_PATH = Path("data/accumulated_cities.json")

# Non-cities that commonly appear in travel text
BLACKLIST = {
    "from", "starting", "departing", "via", "viaing",
    "next", "this", "last", "text", "message", "booking",
    "trip", "vacation", "holiday", "planning", "help",
}


def _load_geonames() -> Set[str]:
    """Load cities from GeoNames dump.

    Format: geonameid,name,asciiname,alternatenames,feature,class,featurecode,
           countrycode,cc2,admin1,admin2,admin3,admin4,admin5,population,elevation,dem,timezone
    """
    global _GEONAMES_CITIES
    if _GEONAMES_CITIES is not None:
        return _GEONAMES_CITIES

    cities = set()
    path = Path(__file__).parent.parent / "data" / "cities5000.txt"

    if not path.exists():
        return cities

    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.strip().split("\t")
            if len(parts) >= 15:
                name = parts[1]  # name
                asciiname = parts[2]  # asciiname
                pop_str = parts[14]
                population = int(pop_str) if pop_str else 0

                if population >= _MIN_POPULATION:
                    cities.add(name)
                    cities.add(asciiname)

    _GEONAMES_CITIES = cities
    return cities


def _load_worldcities() -> Set[str]:
    """Load cities from world-cities.json (supplemental dataset)."""
    global _WORLDCITIES_CITIES
    if _WORLDCITIES_CITIES is not None:
        return _WORLDCITIES_CITIES

    cities = set()
    path = Path(__file__).parent.parent / "data" / "cities.json"

    if not path.exists():
        return cities

    with open(path) as f:
        data = json.load(f)
        for city in data:
            cities.add(city.get("name", ""))

    _WORLDCITIES_CITIES = cities
    return cities


def _build_union() -> Set[str]:
    """Build union of all city sources (computed once)."""
    global _ALL_KNOWN_CITIES
    if _ALL_KNOWN_CITIES is not None:
        return _ALL_KNOWN_CITIES

    geonames = _load_geonames()
    worldcities = _load_worldcities()
    accumulated = load_accumulated()

    # Union of all sources + accumulated
    _ALL_KNOWN_CITIES = geonames | worldcities | accumulated
    return _ALL_KNOWN_CITIES


def load_accumulated() -> Set[str]:
    """Load accumulated cities from previous sessions."""
    global _ACCUMULATED_CITIES
    if _ACCUMULATED_PATH.exists():
        with open(_ACCUMULATED_PATH) as f:
            _ACCUMULATED_CITIES = set(json.load(f))
    return _ACCUMULATED_CITIES


def persist_accumulated():
    """Save accumulated cities to disk."""
    with open(_ACCUMULATED_PATH, "w") as f:
        json.dump(sorted(_ACCUMULATED_CITIES), f, indent=2)


def is_known_city(name: str) -> bool:
    """Check if name is a known city (any source)."""
    if not name or name.lower() in BLACKLIST:
        return False
    return name in _build_union()


def record_seen_city(city: str, confidence: float = 0.5):
    """Add newly seen city if confidence is high enough.

    Only accumulates if:
    - confidence > 0.7 (reasonably sure it's a city)
    - Not already in baseline datasets
    """
    global _ALL_KNOWN_CITIES, _ACCUMULATED_CITIES

    if confidence > 0.7 and city not in _build_union():
        _ACCUMULATED_CITIES.add(city)
        _ALL_KNOWN_CITIES.add(city)  # Invalidate cache
        persist_accumulated()


def get_dataset_info() -> dict:
    """Return stats about loaded datasets (useful for debugging/monitoring)."""
    return {
        "geonames_count": len(_load_geonames()),
        "worldcities_count": len(_load_worldcities()),
        "accumulated_count": len(load_accumulated()),
        "total_unique": len(_build_union()),
    }
```

### 3. Add Attribution to Product

**Required for GeoNames (CC-BY 4.0).**

In any UI that uses location data, add:

```html
<footer>
  Location data © <a href="https://www.geonames.org/">GeoNames</a>
</footer>
```

Or in API responses:

```json
{
  "data": { ... },
  "attribution": "Location data © GeoNames (https://www.geonames.org/)"
}
```

### 4. Update `extractors.py`

- Replace `DOMESTIC_DESTINATIONS | INTERNATIONAL_DESTINATIONS` with `is_known_city()`
- Split `KNOWN_ORIGIN_CITIES` from `KNOWN_DESTINATIONS` conceptually

### 5. Add Regression Tests

- Major Indian origin cities (Pune, Ahmedabad, etc.)
- Smaller tourist spots (Munnar, Pushkar, Hampi)
- Non-Indian origin city
- Origin not leaking into destination candidates
- Destination not mistaken for origin
- Past-trip mention + current origin + current destination in messy text

---

## Open Questions

- When to persist accumulated cities? (Every N messages, on shutdown, periodic?)
- Should accumulated cities be manually curated or auto-pruned?
- Do we need country/state context for disambiguation? (e.g., "Springfield")
- Population threshold appropriate? 5k catches most tourist spots, 10k is safer

---

## License Summary

| Component                 | License         | Attribution Required?   |
| ------------------------- | --------------- | ----------------------- |
| GeoNames                  | CC-BY 4.0       | **Yes** (footer credit) |
| world-cities.json (dr5hn) | ODbL-1.0        | **Yes** + share-alike   |
| Our code (geography.py)   | Project license | No                      |
| Accumulated cities        | Project license | No                      |

**⚠️ world-cities.json ODbL-1.0 share-alike obligation means any derivative database must also
be shared under ODbL-1.0. This conflicts with proprietary licensing.**

---

## References

- Original discussion: Session with Claude, 2026-04-15
- GeoNames: https://www.geonames.org/ (download: https://download.geonames.org/export/dump/)
- world-cities.json: https://github.com/dr5hn/countries-states-cities-database
- CC-BY 4.0: https://creativecommons.org/licenses/by/4.0/
- Related spec: `Docs/NB01_V02_SPEC.md` (destination_candidates, origin_city fields)
