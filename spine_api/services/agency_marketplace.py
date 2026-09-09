"""Agency marketplace — profiles, relevance matching, demand capture (WOBS P2).

Design per WOBS Part 3.3/3.3-A (owner ruling 2026-09-09):
- Matched choice, never single-routing and never a browsable directory: the
  report close shows the top N agencies matched to the brief's needs, and the
  user-owned brief ("take it to any agent") always remains an alternative.
- Match dimensions = brief needs × structured agency profile: places covered,
  customer types served, services offered, languages, response SLA.
- Demand capture at ANY supply level: when no profile matches (or none exists),
  the consented request is stored as a waitlist lead — the lead pool recruits
  supply instead of dead-ending the user.

Storage is additive JSON under ``data/agency_marketplace/`` (file-backed like
the other dev stores; SQL migration is the durable-store endgame, not this).
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

_MATCH_LIMIT = 3

_CUSTOMER_TYPE_KEYWORDS = {
    "toddler": "families",
    "child": "families",
    "kid": "families",
    "family": "families",
    "elderly": "seniors",
    "senior": "seniors",
    "wheelchair": "accessible travel",
    "luxury": "luxury",
    "budget": "budget",
}
_SERVICE_KEYWORDS = {
    "visa": "visa assistance",
    "passport": "visa assistance",
    "insurance": "insurance",
    "monsoon": "trip planning",
    "weather": "trip planning",
    "season": "trip planning",
    "transfer": "logistics",
    "connection": "logistics",
    "timing": "logistics",
    "budget": "budget planning",
    "cost": "budget planning",
    "pace": "trip planning",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_DIGITS_RE = re.compile(r"\d")


@dataclass(slots=True)
class AgencyMarketplaceProfile:
    agency_id: str
    display_name: str
    places_covered: List[str] = field(default_factory=list)
    customer_types: List[str] = field(default_factory=list)
    services: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    response_sla_hours: int = 48
    blurb: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class MatchedAgency:
    profile: AgencyMarketplaceProfile
    score: int
    match_reasons: List[str]

    def as_dict(self) -> Dict[str, Any]:
        return {
            "agency_id": self.profile.agency_id,
            "display_name": self.profile.display_name,
            "response_sla_hours": self.profile.response_sla_hours,
            "blurb": self.profile.blurb,
            "score": self.score,
            "match_reasons": self.match_reasons,
        }


def derive_brief_needs(
    packet: Optional[Dict[str, Any]],
    blocker_texts: List[str],
) -> Dict[str, Any]:
    """Derive structured brief needs from a stored trip (no raw text required)."""
    from src.public_checker.live_checks import extract_destination

    packet = packet or {}
    destination = extract_destination(packet, "")
    customer_types: set[str] = set()
    services: set[str] = set()
    corpus = " ".join(str(item) for item in blocker_texts).lower()
    for keyword, label in _CUSTOMER_TYPE_KEYWORDS.items():
        if keyword in corpus:
            customer_types.add(label)
    for keyword, label in _SERVICE_KEYWORDS.items():
        if keyword in corpus:
            services.add(label)
    return {
        "destination": destination,
        "customer_types": sorted(customer_types),
        "services": sorted(services),
    }


def match_agencies_for_needs(
    needs: Dict[str, Any],
    profiles: List[AgencyMarketplaceProfile],
    *,
    limit: int = _MATCH_LIMIT,
) -> List[MatchedAgency]:
    """Score profile overlap against brief needs. Only score > 0 is returned."""
    destination = str(needs.get("destination") or "").strip().lower()
    dest_tokens = {token for token in re.split(r"[\s,\-]+", destination) if len(token) > 2}
    customer_types = {str(item).lower() for item in needs.get("customer_types") or []}
    services = {str(item).lower() for item in needs.get("services") or []}

    matches: List[MatchedAgency] = []
    for profile in profiles:
        score = 0
        reasons: List[str] = []
        profile_places = {place.strip().lower() for place in profile.places_covered}
        for place in profile_places:
            place_tokens = {token for token in re.split(r"[\s,\-]+", place) if len(token) > 2}
            overlap = dest_tokens & place_tokens
            if overlap:
                score += 2 * len(overlap)
                reasons.append(f"Covers {place.title()}")
        profile_types = {item.strip().lower() for item in profile.customer_types}
        for want in customer_types:
            if want in profile_types:
                score += 1
                reasons.append(f"Serves {want}")
        profile_services = {item.strip().lower() for item in profile.services}
        for want in services:
            if want in profile_services:
                score += 1
                reasons.append(f"Offers {want}")
        if score > 0:
            matches.append(
                MatchedAgency(profile=profile, score=score, match_reasons=reasons[:4])
            )
    matches.sort(key=lambda item: item.score, reverse=True)
    return matches[: max(1, limit)]


def valid_contact(contact: str) -> bool:
    value = (contact or "").strip()
    if not value:
        return False
    if _EMAIL_RE.match(value):
        return True
    return len(_PHONE_DIGITS_RE.findall(value)) >= 7


class AgencyMarketplaceStore:
    """JSON-file persistence for marketplace profiles + captured route leads."""

    DATA_DIR = Path("data") / "agency_marketplace"
    PROFILES_FILE = DATA_DIR / "profiles.json"
    LEADS_FILE = DATA_DIR / "route_leads.jsonl"

    @classmethod
    def _ensure_dirs(cls) -> None:
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def list_profiles(cls) -> List[AgencyMarketplaceProfile]:
        if not cls.PROFILES_FILE.exists():
            return []
        try:
            raw = json.loads(cls.PROFILES_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        profiles = []
        for item in raw if isinstance(raw, list) else []:
            if isinstance(item, dict) and item.get("agency_id"):
                profiles.append(AgencyMarketplaceProfile(**{**item}))
        return profiles

    @classmethod
    def upsert_profile(cls, profile: AgencyMarketplaceProfile) -> None:
        cls._ensure_dirs()
        profiles = [p for p in cls.list_profiles() if p.agency_id != profile.agency_id]
        profiles.append(profile)
        cls.PROFILES_FILE.write_text(
            json.dumps([p.as_dict() for p in profiles], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @classmethod
    def capture_route_lead(
        cls,
        *,
        trip_id: str,
        contact: str,
        agency_id: Optional[str],
        needs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persist a consented route request. Routed when agency_id matches a
        known profile; otherwise a waitlist capture (demand recruits supply)."""
        cls._ensure_dirs()
        known_ids = {p.agency_id for p in cls.list_profiles()}
        routed = bool(agency_id and agency_id in known_ids)
        lead_id = f"lead_{uuid.uuid4().hex[:12]}"
        record = {
            "lead_id": lead_id,
            "trip_id": trip_id,
            "agency_id": agency_id if routed else None,
            "status": "routed" if routed else "captured",
            "contact": contact,
            "needs": needs,
            "captured_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(cls.LEADS_FILE, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record

    @classmethod
    def list_route_leads(cls) -> List[Dict[str, Any]]:
        if not cls.LEADS_FILE.exists():
            return []
        rows: List[Dict[str, Any]] = []
        with open(cls.LEADS_FILE, "r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    parsed = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(parsed, dict):
                    rows.append(parsed)
        return rows
