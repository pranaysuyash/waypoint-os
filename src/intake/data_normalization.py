"""
intake.data_normalization — the normalization enums for destination-
intelligence data types (BD2.2 completion, per the governance matrix in
Docs/research/BD_DATA_GOVERNANCE_FRAMEWORK_2026-10-30.md).

The currency registry (``src/intake/currency_registry.py``) and holiday
registry (``src/intake/holiday_registry.py``) already cover their types;
this module covers the 7 types that had no in-repo enum contract. Each
enum's docstring states the matrix row it implements. These are value
contracts for NORMALIZED data — fetchers translate source vocabulary into
these before anything enters a packet or a page.
"""

from __future__ import annotations

from enum import StrEnum


class AQIScale(StrEnum):
    """Weather/AQI row: 'AQI scale declared as enum (US-EPA vs WHO vs CPC
    differ)' — an AQI number is meaningless without naming its scale."""

    US_EPA = "us_epa"
    WHO = "who"
    CPCB = "cpcb"  # India launch market
    EU_EEA = "eu_eea"


class VisaStatus(StrEnum):
    """Visa/entry row: 'enum {visa_free, eta, evisa, voa, required}'."""

    VISA_FREE = "visa_free"
    ETA = "eta"  # electronic travel authorisation
    EVISA = "evisa"
    VOA = "voa"  # visa on arrival
    REQUIRED = "required"
    RESTRICTED = "restricted"  # entry refused/suspended — worse than required


class CoverageGeneration(StrEnum):
    """Connectivity row: 'coverage {2G..5G}'."""

    G2 = "2g"
    G3 = "3g"
    G4 = "4g"
    G5 = "5g"


class HealthRequirement(StrEnum):
    """Health row: 'enum {required, recommended, routine}'."""

    REQUIRED = "required"  # entry-mandatory (e.g., yellow fever for listed countries)
    RECOMMENDED = "recommended"  # clinician-advised for itinerary
    ROUTINE = "routine"  # standard schedule, not destination-driven


class RuleSeverity(StrEnum):
    """Laws/cultural row: 'severity {prohibited/restricted/advisory}' —
    ``prohibited`` requires the 2-source rule (matrix) and blocks
    auto-display."""

    PROHIBITED = "prohibited"
    RESTRICTED = "restricted"
    ADVISORY = "advisory"


class PriceMethod(StrEnum):
    """Costs row: provenance 'method (crowd/official/agent)' — every price
    datapoint declares how it was collected (sample-size disclosed)."""

    CROWD = "crowd"
    OFFICIAL = "official"
    AGENT_REPORTED = "agent_reported"


class CrimeClass(StrEnum):
    """Safety row: traveler-relevance classes (implemented by the UK
    category map in ``external_sources._TRAVELER_RELEVANCE`` — this enum is
    the normalized contract those raw classes resolve to)."""

    THEFT = "theft"
    THEFT_PICKPOCKET = "theft_pickpocket"
    VIOLENT = "violent"
    DISORDER = "disorder"
    OTHER = "other"


class AdvisoryBand(StrEnum):
    """Safety row: the 4-band scale shared by normalize_fcdo_status and
    assess_safety_band — declared here so the vocabulary has one home."""

    BAND_1 = "1"  # normal precautions
    BAND_2 = "2"  # increased caution
    BAND_3 = "3"  # reconsider travel
    BAND_4 = "4"  # do not travel
