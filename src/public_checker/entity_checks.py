"""Public-checker entity-existence checks — the "Ghost Hotel Test" (WOBS 2026-09-09, P1).

LLM-generated itineraries routinely name hotels and attractions that do not
exist. This module extracts likely lodging entities from an itinerary and
verifies them against a free public gazetteer (OpenStreetMap Nominatim).

Design constraints (deliberate):
- v1 findings are ADVISORY ONLY. A false "this hotel does not exist" destroys
  more trust than a missed hallucination, so a miss is reported as "no public
  record found — verify your booking", never as "this place is fake".
- The transport is injected; tests never touch the network.
- Env vars are read at call time so tests/operators can reconfigure freely.
- Nominatim usage policy: max 1 req/s, descriptive User-Agent. Both enforced.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

_DEFAULT_BASE_URL = "https://nominatim.openstreetmap.org"
_USER_AGENT = "waypoint-os-itinerary-checker/1.0 (entity-existence advisory check)"
_MIN_INTERVAL_SECONDS = 1.0
_CACHE_TTL_SECONDS = 6 * 60 * 60
_MAX_ENTITIES_PER_RUN = 5
_TIMEOUT_SECONDS = 6.0

Transport = Callable[[str], Any]

_last_request_at: float = 0.0
_cache: Dict[Tuple[str, str], Tuple[float, "EntityCheckResult"]] = {}


@dataclass(slots=True)
class EntityCheckResult:
    """One lodging entity's existence verdict. Advisory by design."""

    name: str
    place_query: str
    status: str  # "verified" | "not_found" | "unverified"
    confidence: float  # 0..1 — weak by design; consumers must not hard-block
    message: str
    source: str = "openstreetmap-nominatim"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "place_query": self.place_query,
            "status": self.status,
            "confidence": self.confidence,
            "message": self.message,
            "source": self.source,
        }


def entity_checks_enabled() -> bool:
    """Call-time kill switch so operators/tests can disable without reload."""
    return os.environ.get("ENTITY_CHECK_ENABLED", "1").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


# Keyword parts are case-insensitive; NAME parts are case-sensitive so a
# lowercase fragment ("at", "the") can never be captured as the entity name.
_AT_FORM = re.compile(
    r"(?:check-?in(?:g)?|check\s?in|staying?|stay|overnight)\s+(?:at|in)\s+"
    r"((?:The\s+|Hotel\s+|Resort\s+)?[A-Z][A-Za-z0-9&'\-]+(?:\s+[A-Z][A-Za-z0-9&'\-]+){0,3})",
    re.IGNORECASE,
)
_PREFIX_FORM = re.compile(
    r"\b(?:The\s+)?(?:Hotel|Resort|Hostel|Inn|Lodge)\s+([A-Z][A-Za-z0-9&'\-]+(?:\s+[A-Z][A-Za-z0-9&'\-]+){0,3})"
)
_SUFFIX_FORM = re.compile(
    r"\b([A-Z][A-Za-z0-9&'\-]+(?:\s+[A-Z][A-Za-z0-9&'\-]+){0,3})\s+(?:Hotel|Resort|Hostel|Inn|Lodge)\b"
)
_LODGING_PATTERNS = [_AT_FORM, _PREFIX_FORM, _SUFFIX_FORM]
_STOP_NAME_TOKENS = {"the", "hotel", "resort", "hostel", "inn", "lodge", "a", "and"}


def _dedupe_names(names: List[str]) -> List[str]:
    """Drop exact dupes and token-set subsets ("Taj Palace" ⊂ "Taj Palace Hotel")."""
    unique: List[str] = []
    for name in names:
        tokens = set(name.lower().split()) - _STOP_NAME_TOKENS
        if not tokens:
            continue
        drop = False
        for existing in unique:
            existing_tokens = set(existing.lower().split()) - _STOP_NAME_TOKENS
            if tokens == existing_tokens:
                drop = True
                break
            if tokens < existing_tokens:
                drop = True
                break
            if existing_tokens < tokens:
                unique.remove(existing)
                break
        if not drop:
            unique.append(name)
    return unique


def extract_lodging_names(text: str) -> List[str]:
    """Extract likely lodging names from freeform itinerary text.

    Deliberately conservative: a missed hotel is fine (advisory check), a
    garbage extraction would manufacture a false "ghost". Requires a lodging
    keyword and a Capitalized proper-noun name; near-duplicate captures
    (same place via different patterns) collapse to the longest form.
    """
    if not text:
        return []
    found: List[str] = []
    for pattern in _LODGING_PATTERNS:
        for match in pattern.finditer(text):
            raw = re.sub(r"\s+", " ", match.group(1)).strip(" .,-")
            if not raw:
                continue
            found.append(raw)
    return _dedupe_names(found)


def _http_get_json(url: str) -> Any:
    from src.security.url_guard import guarded_urlopen

    with guarded_urlopen(
        url,
        timeout=_TIMEOUT_SECONDS,
        headers={"User-Agent": _USER_AGENT, "Accept": "application/json"},
    ) as response:
        return json.loads(response.read().decode("utf-8"))


def _looks_like_lodging(result: Dict[str, Any]) -> bool:
    label = str(result.get("class", "")).lower()
    typ = str(result.get("type", "")).lower()
    if label == "tourism" and typ in {"hotel", "motel", "hostel", "guest_house", "apartment", "resort"}:
        return True
    if label == "amenity" and typ in {"hotel", "pub"}:
        return typ == "hotel"
    return False


def verify_entity(
    name: str,
    city: Optional[str],
    *,
    transport: Optional[Transport] = None,
) -> EntityCheckResult:
    """Query the gazetteer for one entity. Fails OPEN (unverified) on any error."""
    global _last_request_at
    base_url = os.environ.get("NOMINATIM_BASE_URL", _DEFAULT_BASE_URL).rstrip("/")
    place_query = " ".join(part for part in (name, city) if part)
    url = (
        f"{base_url}/search?"
        + urllib.parse.urlencode({"q": place_query, "format": "jsonv2", "limit": "5", "addressdetails": "0"})
    )
    fetch = transport or _http_get_json

    # Nominatim usage policy: at most 1 request per second.
    elapsed = time.monotonic() - _last_request_at
    if elapsed < _MIN_INTERVAL_SECONDS:
        time.sleep(_MIN_INTERVAL_SECONDS - elapsed)
    try:
        _last_request_at = time.monotonic()
        results = fetch(url)
    except Exception:
        return EntityCheckResult(
            name=name,
            place_query=place_query,
            status="unverified",
            confidence=0.0,
            message="Could not check this place against public records right now.",
        )

    if not isinstance(results, list):
        return EntityCheckResult(
            name=name, place_query=place_query, status="unverified", confidence=0.0,
            message="Could not check this place against public records right now.",
        )

    lodging_hits = [r for r in results if isinstance(r, dict) and _looks_like_lodging(r)]
    if lodging_hits:
        display = str(lodging_hits[0].get("display_name", ""))[:160]
        return EntityCheckResult(
            name=name,
            place_query=place_query,
            status="verified",
            confidence=0.7,
            message=f"Found a public record for “{name}” ({display}).",
        )
    if results:
        # A place matched but not as lodging — weak signal, report as unverified
        # so we never call a real business a ghost on thin evidence.
        return EntityCheckResult(
            name=name,
            place_query=place_query,
            status="unverified",
            confidence=0.2,
            message=f"“{name}” matched a public place record, but not as lodging — verify your booking details.",
        )
    return EntityCheckResult(
        name=name,
        place_query=place_query,
        status="not_found",
        confidence=0.5,
        message=(
            f"No public record found for “{name}”"
            + (f" in {city}" if city else "")
            + ". LLM-planned trips sometimes include places that don't exist — double-check this booking."
        ),
    )


def run_entity_checks(
    text: str,
    *,
    city: Optional[str] = None,
    transport: Optional[Transport] = None,
    max_entities: int = _MAX_ENTITIES_PER_RUN,
) -> List[EntityCheckResult]:
    """Extract + verify lodging entities. Returns advisory results, never raises."""
    if not entity_checks_enabled() or not text:
        return []
    names = extract_lodging_names(text)[: max(0, max_entities)]
    results: List[EntityCheckResult] = []
    now = time.monotonic()
    for name in names:
        cache_key = (name.lower(), (city or "").lower())
        cached = _cache.get(cache_key)
        if cached and now - cached[0] < _CACHE_TTL_SECONDS:
            results.append(cached[1])
            continue
        result = verify_entity(name, city, transport=transport)
        _cache[cache_key] = (now, result)
        results.append(result)
    return results
