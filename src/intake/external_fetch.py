"""
intake.external_fetch — the ONE governed pipeline for external data fetches.

Every external destination-intelligence fetch goes through here so that
provenance (``ExternalFactReference``), freshness (per-category TTL), and
host discipline (https-only, fixed allowlist, no redirects) are structural
rather than per-source habits. Sources themselves live in
``intake.external_sources``; this module is the transport + governance seam.

Failure semantics (RAG-pattern alignment): ``fetch_json`` RAISES
``ExternalFetchError`` on failure — ingesting external data is a
raise-on-index operation, never a silent pass-through. Callers decide their
own degradation on the query side.

No audit event fires per fetch: fetching is not a state change; the RULE_015
chain covers application/incident events (BD provenance contract rides on the
payload, not the transport).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional
from urllib.parse import urlsplit

import httpx

from src.intake.external_reference import (
    DataCategory,
    ExternalFactReference,
    LicenseTier,
)

# Fixed allowlist — extend deliberately per new source, never widely.
ALLOWED_HOST_SUFFIXES = (
    "open-meteo.com",
    "gov.uk",
    "data.gov.au",
    "smartraveller.gov.au",
    "api.worldbank.org",
    "worldbank.org",
    "aqicn.org",
    "api.openaq.org",
    "suggestqueries.google.com",
    "gdeltproject.org",
    "data.police.uk",
)

DEFAULT_TIMEOUT_SECONDS = 20.0
USER_AGENT = "waypoint-os-research/1.0 (destination-intelligence; contact: owner)"


class ExternalFetchError(RuntimeError):
    """A governed fetch failed — callers must degrade explicitly."""


@dataclass(slots=True)
class FetchResult:
    """Payload + provenance, ready to attach to facts."""

    url: str
    payload: Any  # parsed JSON (dict/list) or raw text
    reference: ExternalFactReference
    category: DataCategory

    def is_stale(self, now: Optional[Any] = None) -> bool:
        return self.reference.is_stale(self.category, now)


def _validated_url(url: str) -> None:
    parts = urlsplit(url)
    if parts.scheme != "https":
        raise ExternalFetchError(f"only https is allowed: {url}")
    host = (parts.hostname or "").lower().rstrip(".")
    if not host or parts.username or parts.password:
        raise ExternalFetchError(f"invalid or credentialed URL: {url}")
    if not any(host == s or host.endswith("." + s) for s in ALLOWED_HOST_SUFFIXES):
        raise ExternalFetchError(
            f"host {host} is not on the external-fetch allowlist"
        )


def fetch_json(
    url: str,
    *,
    source_id: str,
    category: DataCategory,
    license_tier: LicenseTier = LicenseTier.UNKNOWN,
    as_of: Optional[str] = None,
    approximate: bool = False,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
) -> FetchResult:
    """Fetch a JSON document through the governed pipeline.

    Raises ``ExternalFetchError`` on transport failure, non-2xx, or
    unparseable JSON — never returns a half-valid result.
    """
    _validated_url(url)
    response = httpx.get(
        url,
        timeout=timeout,
        follow_redirects=False,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    if response.status_code >= 400:
        raise ExternalFetchError(f"{url} returned HTTP {response.status_code}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise ExternalFetchError(f"{url} returned non-JSON body: {exc}") from exc

    return FetchResult(
        url=url,
        payload=payload,
        reference=ExternalFactReference.capture(
            source_id,
            license_tier=license_tier,
            as_of=as_of,
            approximate=approximate,
            url=url,
        ),
        category=category,
    )
