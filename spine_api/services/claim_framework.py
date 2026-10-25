"""spine_api.services.claim_framework — ONE canonical statutory claim-framework resolver (FND-0312).

Before this module, the evaluate endpoint, the generate-claim letter, and the
ghost-concierge draft EACH classified the disruption independently and could
disagree (live defect: TG318 BKK→BOM CANCELLED evaluated as ``US_DOT`` while
the generated claim letter was headed ``EU261/2004`` — neither applies, because
a Thai-carrier Bangkok→Mumbai flight has no EU/UK/US touchpoint).

This module is the single classification surface. All three consumers must
resolve through :func:`resolve_framework`.

Rules (EC 261/2004 Art. 3; UK AIR (APR) Regs; 14 CFR Part 259/250):

- EU261: departure airport in the EU/EEA (any carrier), OR arrival in the
  EU/EEA on an EU/EEA-licensed carrier.
- UK261: same shape for the UK post-Brexit (departure in the UK, or arrival in
  the UK on a UK-licensed carrier). Amounts in GBP.
- US_DOT: a US airport endpoint (departures any carrier; foreign carriers only
  on flights to/from the US per Part 259).
- NONE: no statutory scheme attaches — the truthful path is the Montreal
  Convention 1999 Art. 19 (delay/cancellation damages, liability-limited)
  pursued via the carrier's own claims process. We never fabricate a
  statutory amount for this lane (compensation is 0 statutory).

Country names are normalized lowercase; common aliases ("USA", "UK", ...) are
accepted. Geography the caller does not have is ``None`` — never guessed —
except the carrier license, which may be inferred from the flight-number
prefix (see ``AIRLINE_PREFIX_COUNTRY``) per the historical evaluate contract.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

# --- Jurisdiction membership sets (extendable config) -----------------------

# 27 EU member states + the EEA/EFTA states whose airports trigger Art. 3(1)
# departures under EC 261/2004 as incorporated (Norway, Iceland, Switzerland,
# Liechtenstein). The UK is deliberately NOT here — post-Brexit it is its own
# regime (UK261, GBP amounts).
EU_EEA_COUNTRIES = frozenset(
    {
        "austria", "belgium", "bulgaria", "croatia", "cyprus", "czech republic",
        "czechia", "denmark", "estonia", "finland", "france", "germany",
        "greece", "hungary", "iceland", "ireland", "italy", "latvia",
        "liechtenstein", "lithuania", "luxembourg", "malta", "netherlands",
        "norway", "poland", "portugal", "romania", "slovakia", "slovenia",
        "spain", "sweden", "switzerland",
    }
)

UNITED_KINGDOM = "united kingdom"
UNITED_STATES = "united states"

_COUNTRY_ALIASES: Dict[str, str] = {
    "uk": UNITED_KINGDOM,
    "great britain": UNITED_KINGDOM,
    "britain": UNITED_KINGDOM,
    "england": UNITED_KINGDOM,
    "usa": UNITED_STATES,
    "us": UNITED_STATES,
    "u.s.": UNITED_STATES,
    "united states of america": UNITED_STATES,
    "america": UNITED_STATES,
}

# Flight-number IATA prefix → carrier licensing country. Extendable config —
# a minimal set covering the repo's test/sim carriers; unknown prefixes fall
# through as ``None`` (never guessed).
AIRLINE_PREFIX_COUNTRY: Dict[str, str] = {
    # EU/EEA carriers
    "AF": "france", "LH": "germany", "KL": "netherlands", "AZ": "italy",
    "IB": "spain", "TP": "portugal", "LX": "switzerland", "OS": "austria",
    "EI": "ireland", "SN": "belgium", "SK": "denmark", "AY": "finland",
    "LO": "poland", "A3": "greece",
    # UK carriers
    "BA": UNITED_KINGDOM, "VS": UNITED_KINGDOM, "U2": UNITED_KINGDOM,
    # US carriers
    "DL": UNITED_STATES, "UA": UNITED_STATES, "AA": UNITED_STATES,
    "B6": UNITED_STATES, "WN": UNITED_STATES, "AS": UNITED_STATES,
    # Other-regime carriers (deliberately listed so NONE resolution is
    # carrier-aware rather than a bare unknown)
    "TG": "thailand", "AI": "india", "IX": "india", "EK": "united arab emirates",
    "EY": "united arab emirates", "SQ": "singapore", "CX": "hong kong",
    "QF": "australia", "JL": "japan", "NH": "japan", "CA": "china",
    "KE": "south korea", "ET": "ethiopia", "MS": "egypt",
}

# Minimal IATA airport → country map (extendable config). Unknown airports
# resolve to ``None`` — the framework rules simply do not fire on them.
AIRPORT_COUNTRY: Dict[str, str] = {
    # EU/EEA
    "FRA": "germany", "MUC": "germany", "BER": "germany", "MUN": "germany",
    "CDG": "france", "ORY": "france", "NCE": "france",
    "AMS": "netherlands", "FCO": "italy", "MXP": "italy", "LIN": "italy",
    "MAD": "spain", "BCN": "spain", "LIS": "portugal",
    "VIE": "austria", "ZRH": "switzerland", "GVA": "switzerland",
    "DUB": "ireland", "ATH": "greece", "ARN": "sweden", "CPH": "denmark",
    "OSL": "norway", "HEL": "finland", "BRU": "belgium", "WAW": "poland",
    "BUD": "hungary", "PRG": "czech republic",
    # UK
    "LHR": UNITED_KINGDOM, "LGW": UNITED_KINGDOM, "MAN": UNITED_KINGDOM,
    "EDI": UNITED_KINGDOM, "BHX": UNITED_KINGDOM, "STN": UNITED_KINGDOM,
    # US
    "JFK": UNITED_STATES, "LGA": UNITED_STATES, "EWR": UNITED_STATES,
    "BOS": UNITED_STATES, "IAD": UNITED_STATES, "ORD": UNITED_STATES,
    "DFW": UNITED_STATES, "ATL": UNITED_STATES, "MIA": UNITED_STATES,
    "LAX": UNITED_STATES, "SFO": UNITED_STATES, "SEA": UNITED_STATES,
    # Asia / other (sim + regression coverage)
    "BKK": "thailand", "BOM": "india", "DEL": "india", "BLR": "india",
    "DXB": "united arab emirates", "SIN": "singapore", "HKG": "hong kong",
    "NRT": "japan", "HND": "japan", "SYD": "australia", "JNB": "south africa",
}

MONTREAL_ARTICLE_19 = "Montreal Convention 1999, Article 19"

ROUTE_UNKNOWN_REASON = (
    "Route geography unknown — no EU261/UK261/US DOT statutory scheme can be "
    "confirmed without it"
)

_MONTREAL_REASON = (
    "Outside EU261/UK261/US DOT statutory scope. Damages for the disruption "
    f"are claimable under the {MONTREAL_ARTICLE_19} (delay/cancellation "
    "damages, subject to the convention's liability limits) via the carrier's "
    "own claims/customer-relations process. No statutory compensation "
    "ceiling applies; the letter demands proven documented losses."
)


def normalize_country(country: Optional[str]) -> Optional[str]:
    """Normalize a country name to the resolver's canonical lowercase form."""
    if not country:
        return None
    c = str(country).strip().lower()
    if not c:
        return None
    return _COUNTRY_ALIASES.get(c, c)


# Every country the resolver recognizes across its membership sets and
# config maps — used to tell an actual carrier country apart from an IATA
# carrier code that happens to arrive in a carrier field ("TG" is Thai
# Airways, not a country).
KNOWN_COUNTRIES = frozenset(
    EU_EEA_COUNTRIES
    | {UNITED_KINGDOM, UNITED_STATES}
    | set(AIRLINE_PREFIX_COUNTRY.values())
    | set(AIRPORT_COUNTRY.values())
)


def resolve_carrier_country(
    carrier_field: Optional[str], flight_number: Optional[str]
) -> Optional[str]:
    """Carrier licensing country: an explicit country name if the field holds
    one, else the flight-number IATA prefix (carrier-license rule only). An
    IATA code ("TG", "LH") is never mistaken for a country."""
    if carrier_field:
        normalized = normalize_country(carrier_field)
        if normalized in KNOWN_COUNTRIES:
            return normalized
    if flight_number:
        return normalize_country(AIRLINE_PREFIX_COUNTRY.get(flight_number[:2].upper()))
    return None


def resolve_framework(
    departure_country: Optional[str],
    arrival_country: Optional[str],
    carrier_country: Optional[str],
    distance_km: float,
    delay_hours: float,
    disruption_type: str,
) -> Dict[str, Any]:
    """Classify ONE flight disruption into its statutory claim framework.

    Returns ``{framework, basis, montreal_applies, reason}`` where framework
    is ``'EU261' | 'UK261' | 'US_DOT' | 'NONE'``. ``distance_km`` and
    ``delay_hours`` do not change *applicability* (they gate eligibility and
    amounts) but are accepted so the signature stays stable for callers that
    hold them.
    """
    dep = normalize_country(departure_country)
    arr = normalize_country(arrival_country)
    car = normalize_country(carrier_country)
    del distance_km, delay_hours, disruption_type  # applicability inputs only

    # 1. EU departure airport — any carrier (Art. 3(1)(a)).
    if dep in EU_EEA_COUNTRIES:
        return {
            "framework": "EU261",
            "basis": "eu_departure",
            "montreal_applies": False,
            "reason": f"Departure airport in the EU/EEA ({dep.title()}) — EU261 applies to any carrier.",
        }
    # 2. EU arrival on an EU/EEA-licensed carrier (Art. 3(1)(b)).
    if arr in EU_EEA_COUNTRIES and car in EU_EEA_COUNTRIES:
        return {
            "framework": "EU261",
            "basis": "eu_arrival_eu_carrier",
            "montreal_applies": False,
            "reason": f"Arrival in the EU/EEA ({arr.title()}) on an EU/EEA-licensed carrier ({car.title()}) — EU261 applies.",
        }
    # 3. UK departure airport — any carrier (UK261).
    if dep == UNITED_KINGDOM:
        return {
            "framework": "UK261",
            "basis": "uk_departure",
            "montreal_applies": False,
            "reason": "Departure airport in the UK — UK261 applies to any carrier.",
        }
    # 4. UK arrival on a UK-licensed carrier (UK261).
    if arr == UNITED_KINGDOM and car == UNITED_KINGDOM:
        return {
            "framework": "UK261",
            "basis": "uk_arrival_uk_carrier",
            "montreal_applies": False,
            "reason": "Arrival in the UK on a UK-licensed carrier — UK261 applies.",
        }
    # 5. US airport endpoint (14 CFR Part 259/250 covered flights).
    if dep == UNITED_STATES or arr == UNITED_STATES:
        endpoint = "departure" if dep == UNITED_STATES else "arrival"
        return {
            "framework": "US_DOT",
            "basis": "us_route",
            "montreal_applies": False,
            "reason": f"US airport {endpoint} — US DOT passenger-protection rules apply.",
        }
    # 6. Endpoint-unknown carrier-license inference (historical evaluate
    #    contract: EU/UK carrier prefix → EU261 hint lane; US carrier → DOT).
    if dep is None and arr is None and car is not None:
        if car in EU_EEA_COUNTRIES or car == UNITED_KINGDOM:
            return {
                "framework": "EU261",
                "basis": "carrier_license_inference",
                "montreal_applies": False,
                "reason": (
                    f"Carrier licensed in {car.title()} with unknown route — resolved on the "
                    "historical EU/UK carrier-prefix lane; provide route geography for a "
                    "definitive EU261/UK261 determination."
                ),
            }
        if car == UNITED_STATES:
            return {
                "framework": "US_DOT",
                "basis": "carrier_license_inference",
                "montreal_applies": False,
                "reason": (
                    "US-licensed carrier with unknown route — resolved to the US DOT lane; "
                    "provide route geography for a definitive determination."
                ),
            }
        # Carrier from a jurisdiction with no such statutory scheme.
        return {
            "framework": "NONE",
            "basis": "route_unknown",
            "montreal_applies": True,
            "reason": (
                f"{ROUTE_UNKNOWN_REASON}; carrier {car.title()} operates under no "
                "EU261/UK261/US DOT scheme. "
                f"Claimable under the {MONTREAL_ARTICLE_19} via the carrier's claims process."
            ),
        }
    # 7. Geography resolved, no rule fired (or unresolvable without geography).
    #    D7 enrichment: name any known NATIONAL departure/arrival regime so the
    #    operator sees the honest local avenue alongside the Montreal path.
    #    Amounts stay unset until the regulation texts are cited (web-search
    #    quota) — this registry NEVER fabricates statutory numbers.
    national_regime = (
        _NATIONAL_DEPARTURE_REGIMES.get(dep)
        or _NATIONAL_DEPARTURE_REGIMES.get(arr)
    )
    if national_regime:
        return {
            "framework": "NONE",
            "basis": "outside_regulated_jurisdictions",
            "montreal_applies": True,
            "reason": (
                f"{_MONTREAL_REASON} National regime on the route: "
                f"{national_regime} (amounts not encoded — verify the "
                "regulation text before quoting statutory figures)."
            ),
        }
    return {
        "framework": "NONE",
        "basis": "outside_regulated_jurisdictions",
        "montreal_applies": True,
        "reason": _MONTREAL_REASON,
    }


# --- National departure regimes (D7, knowledge-based — amounts UNENCODED) ---
# Each entry names the local statutory avenue a traveler on that route can
# pursue IN ADDITION to the Montreal Convention claim. Entries carry no
# compensation figures: adding numbers requires the regulation text cited
# (web-search quota — SIM3 meta-audit D7). Add a country ONLY with its
# statute name; extend to amounts in the same change as the citation.
# --- National departure regimes (D7, knowledge-based — amounts UNENCODED) ---
# Each entry names the local statutory avenue a traveler on that route can
# pursue IN ADDITION to the Montreal Convention claim. Keys use the resolver's
# canonical lowercase country names (normalize_country output). Entries carry
# no compensation figures: adding numbers requires the regulation text cited
# (web-search quota — SIM3 meta-audit D7). Add a country ONLY with its
# statute name; extend to amounts in the same change as the citation.
_NATIONAL_DEPARTURE_REGIMES = {
    "thailand": "Thailand air passenger protection rules (2021, Office of the Consumer Protection Board)",
    "india": "India DGCA CAR Section 3, Series M, Part IV (carriage by air — passenger entitlements)",
}

# --- Statutory amount tables (framework banding) ----------------------------

EU261_EUR_TIERS = (250.0, 400.0, 600.0)     # <1500 / <=3500 / >3500 km
UK261_GBP_TIERS = (220.0, 350.0, 520.0)     # <1500 / <=3500 / >3500 km
US_DOT_COMPENSATION_USD = 300.0             # historical DOT-lane flat amount


def compensation_band(distance_km: float) -> str:
    """EU261/UK261 distance band label."""
    if distance_km < 1500:
        return "short (<=1500 km)"
    if distance_km <= 3500:
        return "medium (1500-3500 km)"
    return "long (>3500 km)"


def _band_amount(tiers, distance_km: float) -> float:
    if distance_km < 1500:
        return tiers[0]
    if distance_km <= 3500:
        return tiers[1]
    return tiers[2]


def eu261_compensation_eur(distance_km: float) -> float:
    """EU261 distance-banded statutory compensation (EUR)."""
    return _band_amount(EU261_EUR_TIERS, distance_km)


def uk261_compensation_gbp(distance_km: float) -> float:
    """UK261 distance-banded statutory compensation (GBP)."""
    return _band_amount(UK261_GBP_TIERS, distance_km)


def statutory_amount(framework: str, distance_km: float) -> tuple:
    """(amount, currency) for a resolved framework at the given distance."""
    if framework == "EU261":
        return eu261_compensation_eur(distance_km), "EUR"
    if framework == "UK261":
        return uk261_compensation_gbp(distance_km), "GBP"
    if framework == "US_DOT":
        return US_DOT_COMPENSATION_USD, "USD"
    return 0.0, "NONE"
