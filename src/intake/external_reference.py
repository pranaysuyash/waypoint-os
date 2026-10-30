"""
intake.external_reference — provenance + freshness contract for external data.

Implements the provenance envelope mandated by
Docs/research/BD_DATA_GOVERNANCE_FRAMEWORK_2026-10-30.md: every external
destination-intelligence datapoint (weather, AQI, advisories, visa rules,
holidays, FX, ...) carries {source_id, retrieved_at, as_of, license_tier}
plus an approximate flag, and can be evaluated for staleness against the
per-category freshness thresholds defined by the same framework.

Design constraints honored:
- ONE canonical home — this module is the single provenance/freshness
  authority; fetchers attach its output to facts, they do not invent
  parallel envelope shapes.
- Generalizes the in-repo ``HypothesisState.STALE`` semantics
  (``src/intake/packet_models.py``) to reference data: stale is an
  evaluated property, never a silent pass-through.
- Dependency-free (stdlib only) so it is importable from both src/ and
  spine_api/ without cycle risk.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Dict, Optional


class LicenseTier(StrEnum):
    """Licensing posture of an external source (BD2.7)."""

    PUBLIC_DOMAIN = "public_domain"
    ATTRIBUTION = "attribution"  # usable with mandatory display
    SHARE_ALIKE = "share_alike"  # ODbL-class: derived data inherits obligations
    RESTRICTED = "restricted"  # licensed/commercial; redistribution limited
    UNKNOWN = "unknown"  # must be resolved before the data reaches product surfaces


class DataCategory(StrEnum):
    """Destination-intelligence data types (BD governance matrix rows)."""

    WEATHER = "weather"
    AQI = "aqi"
    SAFETY_ADVISORY = "safety_advisory"
    VISA_RULES = "visa_rules"
    HOLIDAYS = "holidays"
    FX_RATE = "fx_rate"
    CONNECTIVITY = "connectivity"
    HEALTH = "health"
    COSTS = "costs"
    LAWS_CULTURAL = "laws_cultural"
    EVENTS = "events"
    INCIDENT = "incident"


# Staleness thresholds (seconds) — from the BD governance matrix
# (Docs/research/BD_DATA_GOVERNANCE_FRAMEWORK_2026-10-30.md §matrix).
FRESHNESS_TTL_SECONDS: Dict[DataCategory, int] = {
    DataCategory.WEATHER: 6 * 3600,
    DataCategory.AQI: 6 * 3600,
    DataCategory.SAFETY_ADVISORY: 7 * 86400,
    DataCategory.VISA_RULES: 30 * 86400,
    DataCategory.HOLIDAYS: 365 * 86400,  # exact dates recompute per year
    DataCategory.FX_RATE: 24 * 3600,
    DataCategory.CONNECTIVITY: 90 * 86400,
    DataCategory.HEALTH: 30 * 86400,
    DataCategory.COSTS: 90 * 86400,
    DataCategory.LAWS_CULTURAL: 365 * 86400,
    DataCategory.EVENTS: 14 * 86400,
    DataCategory.INCIDENT: 14 * 86400,
}


def _parse_utc(value: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp; Naive values are treated as UTC."""
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(slots=True)
class ExternalFactReference:
    """Provenance envelope attached to every external datapoint."""

    source_id: str
    retrieved_at: str  # ISO-8601, UTC
    as_of: Optional[str] = None  # effective/as-of date when the source declares one
    license_tier: LicenseTier = LicenseTier.UNKNOWN
    approximate: bool = False
    url: Optional[str] = None

    def age_seconds(self, now: Optional[datetime] = None) -> Optional[float]:
        retrieved = _parse_utc(self.retrieved_at)
        if retrieved is None:
            return None
        current = now or datetime.now(timezone.utc)
        return max(0.0, (current - retrieved).total_seconds())

    def is_stale(self, category: DataCategory, now: Optional[datetime] = None) -> bool:
        """True when the reference exceeds its category TTL (or is undated).

        Undated provenance is stale BY DEFAULT — an unverifiable freshness
        claim must not masquerade as fresh (honesty over convenience).
        """
        ttl = FRESHNESS_TTL_SECONDS[category]
        age = self.age_seconds(now)
        if age is None:
            return True
        return age > ttl

    def to_metadata(self) -> Dict[str, object]:
        """Metadata dict for attaching to facts/packets — the shape the
        governance contract promises consumers."""
        return {
            "source_id": self.source_id,
            "retrieved_at": self.retrieved_at,
            "as_of": self.as_of,
            "license_tier": str(self.license_tier.value),
            "approximate": self.approximate,
            "url": self.url,
        }

    @classmethod
    def capture(cls, source_id: str, *, license_tier: LicenseTier = LicenseTier.UNKNOWN,
                as_of: Optional[str] = None, approximate: bool = False,
                url: Optional[str] = None) -> "ExternalFactReference":
        """Capture provenance at fetch time (retrieved_at = now, UTC)."""
        return cls(
            source_id=source_id,
            retrieved_at=datetime.now(timezone.utc).isoformat(),
            as_of=as_of,
            license_tier=license_tier,
            approximate=approximate,
            url=url,
        )
