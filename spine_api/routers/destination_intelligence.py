"""
spine_api.routers.destination_intelligence — operator-facing reads over the
destination-intelligence data layer.

Exposes the governed fetch + grading stack built 2026-10-30
(src/intake/external_{fetch,sources}.py, safety_band.py,
weather_suitability.py, federated_intelligence.py) as the workbench surface:

  GET /api/v1/destination-intelligence/safety/{country_slug}
      FCDO advisory band (+ optional national homicide rate with iso3,
      optional neighborhood crime with lat/lng/month, optional events pulse
      with include_events=1 — GDELT is hard-paced 1req/5s, so it degrades
      to a coverage gap rather than blocking the verdict).
  GET /api/v1/destination-intelligence/weather-suitability
      Trip-window grading; dispatches forecast (<=16d) vs ERA5 climate
      baseline (>16d) — see grade_trip_conditions.
  GET /api/v1/destination-intelligence/ratings/{location}
      Aggregated anonymized traveler ratings (read; write surface waits on
      the consent flow — Docs/DECISIONS_PENDING.md TRV-DP-06 lineage).

Auth: registered with the house `_auth_or_skip` dependency (operator
workbench surface). Data is the anonymized global pool; agency DI binds
the read to an operator session per the B2B posture.

Caching: advisories change weekly and upstreams are slow/rate-limited, so
verdicts are cached in-process with a TTL (single-worker stage; revisit
with the multi-worker/deploy tranche).
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from spine_api.core.auth import get_current_agency_id

from src.intake.external_fetch import ExternalFetchError
from src.intake.external_sources import (
    fetch_fcdo_country,
    fetch_gdelt_protest_pulse,
    fetch_worldbank_homicide,
    fetch_uk_street_crime,
)
from src.intake.federated_intelligence import intelligence_service
from src.intake.safety_band import assess_safety_band
from src.intake.weather_suitability import grade_trip_conditions

logger = logging.getLogger("destination_intel")

router = APIRouter(prefix="/api/v1/destination-intelligence", tags=["destination-intelligence"])

_SAFETY_CACHE_TTL_SECONDS = 3600.0  # advisories change on weekly cadence; 1h is fresh
_safety_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}


def _cached(key: str, ttl: float, build):
    now = time.monotonic()
    hit = _safety_cache.get(key)
    if hit and now - hit[0] < ttl:
        return hit[1], True
    value = build()
    _safety_cache[key] = (now, value)
    return value, False


class SafetyVerdictResponse(BaseModel):
    destination_slug: str
    requested_slug: Optional[str] = None
    alias_note: Optional[str] = None
    band: str
    label: str
    components: Dict[str, Any]
    coverage: list[str]
    coverage_gaps: list[str]
    provenance: list[Dict[str, Any]]
    cached: bool = False


class WeatherSuitabilityResponse(BaseModel):
    mode: str
    activity: str
    status: str
    verdict: Optional[str] = None
    days: Optional[list[Dict[str, Any]]] = None
    summary: Optional[Dict[str, Any]] = None
    normals: Optional[Dict[str, Any]] = None
    confidence_note: Optional[str] = None
    coverage: Optional[list[str]] = None
    coverage_gaps: Optional[list[str]] = None
    provenance: Optional[list[Dict[str, Any]]] = None
    timezone: Optional[str] = None


class RatingsResponse(BaseModel):
    location: str
    dimensions: Dict[str, Any]
    total_ratings: int


def _build_safety_verdict(country_slug: str, iso3: Optional[str], lat: Optional[float],
                          lng: Optional[float], month: Optional[str], include_events: bool) -> Dict[str, Any]:
    advisory = fetch_fcdo_country(country_slug)
    homicide: Optional[Dict[str, Any]] = None
    if iso3:
        homicide = fetch_worldbank_homicide(iso3)
    neighborhood: Optional[Dict[str, Any]] = None
    if lat is not None and lng is not None and month:
        neighborhood = fetch_uk_street_crime(lat, lng, month)
    events: Optional[Dict[str, Any]] = None
    if include_events:
        try:
            events = fetch_gdelt_protest_pulse(country_slug.replace("-", " "))
            time.sleep(5.0)  # GDELT pacing contract: 1 req / 5 s
        except ExternalFetchError as exc:
            logger.info("events pulse unavailable for %s (honest gap): %s", country_slug, exc)
    verdict = assess_safety_band(
        advisory_band=advisory["advisory_band"],
        advisory_provenance=advisory["provenance"],
        homicide=homicide,
        neighborhood=neighborhood,
        events=events,
    )
    if advisory.get("alias_note"):
        verdict["alias_note"] = advisory["alias_note"]
    return verdict


@router.get("/safety/{country_slug}", response_model=SafetyVerdictResponse)
def get_safety_verdict(
    country_slug: str,
    agency_id: str = Depends(get_current_agency_id),
    iso3: Optional[str] = Query(default=None, description="ISO-3 code for the national homicide component (C2)"),
    lat: Optional[float] = Query(default=None, description="C3 neighborhood crime: point latitude (England/Wales)"),
    lng: Optional[float] = Query(default=None, description="C3 neighborhood crime: point longitude"),
    month: Optional[str] = Query(default=None, description="C3 data month, YYYY-MM"),
    include_events: bool = Query(default=False, description="Include the paced GDELT events pulse (C4)"),
):
    """Banded safety verdict for a destination from governed sources.

    C1 gates (FCDO advisory band); optional C2/C3/C4 annotate or raise per
    the safety-scoring spec. Components without data are listed in
    ``coverage_gaps`` — never a fabricated verdict.
    """
    key = f"safety:{country_slug}:{iso3}:{lat}:{lng}:{month}:{include_events}"
    try:
        verdict, cached = _cached(key, _SAFETY_CACHE_TTL_SECONDS,
                                  lambda: _build_safety_verdict(country_slug, iso3, lat, lng, month, include_events))
    except ExternalFetchError as exc:
        raise HTTPException(status_code=502, detail={"error": "upstream_fetch_failed", "detail": str(exc)})
    return SafetyVerdictResponse(
        destination_slug=country_slug, cached=cached, **{k: v for k, v in verdict.items()}
    )


@router.get("/weather-suitability", response_model=WeatherSuitabilityResponse)
def get_weather_suitability(
    lat: float = Query(...),
    lng: float = Query(...),
    start_date: str = Query(..., description="ISO YYYY-MM-DD"),
    end_date: str = Query(..., description="ISO YYYY-MM-DD"),
    activity: str = Query(..., description="beach | hiking | city"),
    agency_id: str = Depends(get_current_agency_id),
):
    """Trip-window weather grading. Within the ~16-day forecast horizon this
    grades the live forecast; beyond it, ERA5 climate baselines (mode
    declares which)."""
    try:
        out = grade_trip_conditions(lat, lng, start_date, end_date, activity=activity)
    except ExternalFetchError as exc:
        raise HTTPException(status_code=502, detail={"error": "upstream_fetch_failed", "detail": str(exc)})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "invalid_request", "detail": str(exc)})
    # Normalize provenance to a list at the API boundary: the forecast path
    # emits a single metadata dict, the climate path a per-year list. The
    # API contract is always a list (live-run-caught divergence).
    prov = out.get("provenance")
    if isinstance(prov, dict):
        out["provenance"] = [prov]
    return WeatherSuitabilityResponse(**out)


@router.get("/ratings/{location}", response_model=RatingsResponse)
def get_destination_ratings(
    location: str,
    dimension: Optional[str] = Query(default=None),
    agency_id: str = Depends(get_current_agency_id),
):
    """Aggregated anonymized traveler ratings from the federated pool.
    Zero contributions = empty dimensions (never a fabricated score).
    Write surface ships with the consent flow (TRV-DP-06 lineage)."""
    out = intelligence_service.query_ratings(location, dimension=dimension)
    return RatingsResponse(**out)


# ---- Ratings write surface (TRV-DP-07 consent contract) ----

_NOTE_MAX_CHARS = 280

# v1 contact-pattern scrub: the classic contact vectors, redacted before a
# note enters the pool. Known limit (documented in TRV-DP-07): pattern-based
# scrubbing cannot catch free-form personal references — the pool's
# non-reversible anonymization + operator review remain the backstops.
_CONTACT_PATTERNS = [
    r"[\w.+-]+@[\w-]+\.[\w.]+",  # emails
    r"(?:\+?\d[\d\s().-]{7,}\d)",  # phone-like sequences
    r"https?://\S+|www\.\S+",  # URLs
]


def _scrub_note(note: str) -> str:
    import re

    scrubbed = note
    for pattern in _CONTACT_PATTERNS:
        scrubbed = re.sub(pattern, "[removed]", scrubbed)
    return scrubbed[:_NOTE_MAX_CHARS]


class RatingSubmission(BaseModel):
    dimension: str
    score: int
    consent: bool  # per-act explicit consent — TRV-DP-07
    trip_month: Optional[str] = None  # "YYYY-MM"
    note: Optional[str] = None


class RatingSubmissionResponse(BaseModel):
    ok: bool
    record_id: str
    location: str
    dimension: str
    score: int


@router.post("/ratings/{location}", response_model=RatingSubmissionResponse)
def submit_destination_rating(
    location: str,
    submission: RatingSubmission,
    agency_id: str = Depends(get_current_agency_id),
):
    """Record a consented traveler rating in the federated pool.

    TRV-DP-07 contract: consent is explicit per submission (rejected 422
    otherwise — no server-side remembered consent); identity is never
    accepted or stored (agency source hash-anonymized in the service);
    notes are contact-scrubbed and capped at 280 chars.
    """
    from src.intake.federated_intelligence import DestinationRating

    if submission.consent is not True:
        raise HTTPException(
            status_code=422,
            detail={"error": "consent_required", "detail": "Traveler consent must be explicit per submission."},
        )
    note = submission.note or ""
    try:
        record = intelligence_service.report_rating(
            agency_id,
            DestinationRating(
                location=location,
                dimension=submission.dimension,
                score=submission.score,
                trip_month=submission.trip_month,
                note=_scrub_note(note),
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail={"error": "invalid_rating", "detail": str(exc)})
    return RatingSubmissionResponse(
        ok=True, record_id=record["record_id"], location=record["location"],
        dimension=record["dimension"], score=record["score"],
    )
