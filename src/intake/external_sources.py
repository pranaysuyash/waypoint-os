"""
intake.external_sources — concrete fetchers over the governed pipeline.

Each function returns ``(payload, FetchResult)``-style data with provenance
attached. First source: FCDO (GOV.UK Content API — live-verified 2026-10-30
in Docs/research/AW3_SAFETY_CRIME_SOURCE_EVALUATION_2026-10-30.md; OGL
license, attribution required). One endpoint covers BOTH the safety-advisory
cluster and the AY laws/culture block ("Laws and cultural differences"
sections), which is why it is source #1.
"""

from __future__ import annotations

from typing import Any, Dict

from src.intake.external_fetch import ExternalFetchError, FetchResult, fetch_json
from src.intake.external_reference import DataCategory, LicenseTier

FCDO_CONTENT_BASE = "https://www.gov.uk/api/content/foreign-travel-advice"
WORLDBANK_INDICATOR_BASE = "https://api.worldbank.org/v2/country"


def fetch_worldbank_homicide(country_iso3: str) -> Dict[str, Any]:
    """C2 component source (safety-scoring spec): homicides per 100k from the
    World Bank indicator ``VC.IHR.PSRC.P5`` — live-verified 2026-10-30
    (entries are newest-first; years with no data carry ``value: null``).

    Returns the most recent non-null observation with provenance. National
    granularity, ~2yr publication lag — consumers must label it as such
    (BD governance matrix: national context, never presented as city truth).
    Raises ``ExternalFetchError`` per pipeline semantics.
    """
    iso3 = country_iso3.strip().upper()
    if len(iso3) != 3 or not iso3.isalpha():
        raise ExternalFetchError(f"invalid ISO-3 code: {country_iso3!r}")
    result: FetchResult = fetch_json(
        f"{WORLDBANK_INDICATOR_BASE}/{iso3}/indicator/VC.IHR.PSRC.P5?format=json&per_page=10",
        source_id="worldbank-api",
        category=DataCategory.SAFETY_ADVISORY,  # national safety context (C2)
        license_tier=LicenseTier.PUBLIC_DOMAIN,  # CC BY 4.0 / World Bank open terms
        approximate=True,  # statistical estimate, lagged
    )
    payload = result.payload
    entries = payload[1] if isinstance(payload, list) and len(payload) > 1 else []
    for entry in entries:
        value = entry.get("value")
        if value is not None:
            return {
                "country_iso3": iso3,
                "rate_per_100k": round(float(value), 3),
                "year": entry.get("date"),
                "indicator": "VC.IHR.PSRC.P5",
                "provenance": result.reference.to_metadata()
                | {"category": result.category.value},
            }
    raise ExternalFetchError(f"no non-null homicide observations for {iso3}")


# FCDO alert_status slug → severity rank (live-verified 2026-10-30:
# russia=['avoid_all_travel_to_whole_country'], israel=['avoid_all_travel_to_parts',
# 'avoid_all_but_essential_travel_to_parts'], japan=[] — the field is a LIST of
# slugs under details.alert_status, NOT the prose alert_level string).
_FCDO_STATUS_SEVERITY = {
    "avoid_all_travel_to_whole_country": 4,
    "avoid_all_travel_to_parts": 3,
    "avoid_all_but_essential_travel_to_whole_country": 3,
    "avoid_all_but_essential_travel_to_parts": 2,
    "no_advisory": 1,
}


def normalize_fcdo_status(status_entries) -> str:
    """Map FCDO ``details.alert_status`` (a LIST of slugs) onto the 4-band
    scale of the safety-scoring spec. Band = MAX severity across entries;
    whole-country variants outrank parts variants. Empty list → band 1 (no
    advisory). Unknown slugs → cautious band 3 with the slug preserved in the
    payload (never dropped, never invented).
    """
    entries = status_entries or []
    if not entries:
        return "1"  # no advisory at all
    worst = 1
    unknown = False
    for entry in entries:
        severity = _FCDO_STATUS_SEVERITY.get(str(entry).strip().lower())
        if severity is None:
            unknown = True  # unrecognized slug: cautious handling, slug kept in payload
        else:
            worst = max(worst, severity)
    if unknown:
        return str(max(worst, 3))
    return str(worst)


def fetch_fcdo_country(country_slug: str) -> Dict[str, Any]:
    """Fetch one country's FCDO foreign-travel-advice payload, governed.

    Returns a dict with the raw content payload + provenance + the normalized
    advisory band. Raises ``ExternalFetchError`` per pipeline semantics.
    """
    slug = country_slug.strip().lower().replace(" ", "-")
    result: FetchResult = fetch_json(
        f"{FCDO_CONTENT_BASE}/{slug}",
        source_id="fcdo-content-api",
        category=DataCategory.SAFETY_ADVISORY,
        license_tier=LicenseTier.SHARE_ALIKE,  # OGL: attribution + share-alike display duties
        approximate=False,
    )
    payload = result.payload
    details = payload.get("details", {}) if isinstance(payload, dict) else {}
    alert_status = details.get("alert_status") or []
    return {
        "country_slug": slug,
        "content_payload": payload,
        "advisory_band": normalize_fcdo_status(alert_status),
        "raw_alert_status": alert_status,
        "public_updated_at": payload.get("public_updated_at"),
        "provenance": result.reference.to_metadata()
        | {"category": result.category.value},
    }
