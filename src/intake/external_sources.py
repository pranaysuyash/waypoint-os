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


# ---- C3: neighborhood street crime (data.police.uk — England/Wales) ----

DATA_POLICE_BASE = "https://data.police.uk/api/crimes-street"

# UK police category → traveler-relevance class (master-list item "crime type
# mapping for travelers"): what a visitor actually needs to weight.
_TRAVELER_RELEVANCE = {
    "theft-from-the-person": "theft_pickpocket",
    "other-theft": "theft",
    "burglary": "theft",
    "shoplifting": "theft",
    "bicycle-theft": "theft",
    "violent-crime": "violent",
    "robbery": "violent",
    "public-order": "disorder",
    "anti-social-behaviour": "disorder",
    "criminal-damage-arson": "disorder",
    "drugs": "other",
    "possession-of-weapons": "violent",
    "vehicle-crime": "other",
    "other-crime": "other",
}


def fetch_uk_street_crime(lat: float, lng: float, year_month: str) -> Dict[str, Any]:
    """C3 component source: street-level crime around a point (data.police.uk,
    England/Wales only — the granularity gold standard per the AW3 source
    evaluation). Live-verified 2026-10-30: 5,024 category-tagged crimes for
    central London in one month.

    ``year_month``: "YYYY-MM" (data.police.uk requires the month parameter).
    Returns totals, category breakdown, traveler-relevance classes, and
    provenance with the data month as ``as_of``. OGL — attribution required
    on display.
    """
    if not (len(year_month) == 7 and year_month[4] == "-" and year_month[:4].isdigit()):
        raise ExternalFetchError(f"year_month must be YYYY-MM: {year_month!r}")
    result: FetchResult = fetch_json(
        f"{DATA_POLICE_BASE}/all-crime?lat={lat}&lng={lng}&date={year_month}",
        source_id="data.police.uk",
        category=DataCategory.SAFETY_ADVISORY,
        license_tier=LicenseTier.ATTRIBUTION,  # OGL
        approximate=False,
        as_of=year_month,
    )
    crimes = result.payload if isinstance(result.payload, list) else []
    categories: Dict[str, int] = {}
    relevance: Dict[str, int] = {}
    for crime in crimes:
        cat = str(crime.get("category", "unknown"))
        categories[cat] = categories.get(cat, 0) + 1
        rel = _TRAVELER_RELEVANCE.get(cat, "other")
        relevance[rel] = relevance.get(rel, 0) + 1
    return {
        "point": {"lat": lat, "lng": lng},
        "month": year_month,
        "total_crimes": len(crimes),
        "categories": dict(sorted(categories.items(), key=lambda kv: -kv[1])),
        "traveler_relevance": relevance,
        "provenance": result.reference.to_metadata()
        | {"category": result.category.value},
    }


# ---- C4: current-events pulse (GDELT) ----

GDELT_DOC_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"


def fetch_gdelt_protest_pulse(location_query: str, timespan: str = "1w") -> Dict[str, Any]:
    """C4 component source: protest/unrest article pulse via the GDELT DOC
    API. PACING CONTRACT: GDELT hard-limits 1 request / 5 seconds (verified
    429 body) — callers must pace; the governed pipeline does NOT retry, so
    a 429 surfaces as ``ExternalFetchError`` and callers degrade to
    ``events_pulse=False`` (honest coverage gap, never a fabricated calm).
    """
    result: FetchResult = fetch_json(
        f"{GDELT_DOC_BASE}/doc?query=%28protest%20OR%20demonstration%20OR%20unrest%29%20{location_query.strip()}&mode=artlist&format=json&maxrecords=10&timespan={timespan}&sort=datedesc",
        source_id="gdelt-doc-api",
        category=DataCategory.EVENTS,
        license_tier=LicenseTier.UNKNOWN,  # resolve GDELT usage terms before product display
        approximate=True,
    )
    payload = result.payload
    articles = payload.get("articles", []) if isinstance(payload, dict) else []
    return {
        "location_query": location_query,
        "timespan": timespan,
        "article_count": len(articles),
        "sample_titles": [a.get("title") for a in articles[:5] if a.get("title")],
        "provenance": result.reference.to_metadata()
        | {"category": result.category.value},
    }


# ---- Weather: Open-Meteo trip-window daily forecast (AW12 stack) ----

OPEN_METEO_FORECAST_BASE = "https://api.open-meteo.com"


def fetch_open_meteo_trip_weather(
    lat: float,
    lng: float,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """Daily forecast slice for a trip window via the governed pipeline
    (Open-Meteo — the AW12 standardized stack's primary; CC BY 4.0,
    attribution required).

    ``start_date``/``end_date``: ISO "YYYY-MM-DD". Open-Meteo's live horizon
    is ~16 days — the suitability gate treats dates beyond it honestly
    (see ``weather_suitability.assess_trip_date_suitability``).
    """
    for name, value in (("start_date", start_date), ("end_date", end_date)):
        if not (len(value) == 10 and value[4] == "-" and value[7] == "-"):
            raise ExternalFetchError(f"{name} must be ISO YYYY-MM-DD: {value!r}")
    daily = "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code,uv_index_max"
    result: FetchResult = fetch_json(
        f"{OPEN_METEO_FORECAST_BASE}/v1/forecast?latitude={lat}&longitude={lng}"
        f"&daily={daily}&timezone=auto&start_date={start_date}&end_date={end_date}",
        source_id="open-meteo-forecast",
        category=DataCategory.WEATHER,
        license_tier=LicenseTier.ATTRIBUTION,  # CC BY 4.0 — display provider + fetch time
        approximate=True,  # forecast, not observation
    )
    payload = result.payload
    daily_payload = payload.get("daily", {}) if isinstance(payload, dict) else {}
    return {
        "point": {"lat": lat, "lng": lng},
        "start_date": start_date,
        "end_date": end_date,
        "timezone": payload.get("timezone"),
        "daily": daily_payload,
        "provenance": result.reference.to_metadata()
        | {"category": result.category.value},
    }
