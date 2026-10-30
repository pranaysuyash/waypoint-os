"""
intake.safety_band — the C1+C2 band engine from the safety-scoring spec.

Implements the advisory-first banded composite
(Docs/research/AW3_SAFETY_SCORING_METHODOLOGY_SPEC_2026-10-30.md):

  - C1 (advisory gate) GATES, not weights: any government "do not travel"
    ⇒ band 4 regardless of other components.
  - C2 (national violent-crime rate) annotates inside the band and can
    raise band 2 → 3 only when BOTH top-global-decile AND an active
    events pulse are present (C4 — caller-supplied until the GDELT/ACLED
    fetcher lands).
  - Uncovered components are listed as coverage gaps — they never lower
    the band and never invent a neutral score (honest-abstain rule).

Bands are strings "1".."4" matching the FCDO normalizer output.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

BAND_LABELS = {
    "1": "Normal precautions",
    "2": "Increased caution",
    "3": "Reconsider travel",
    "4": "Do not travel",
}

# Rough global decile reference for homicides/100k (World Bank national data):
# ~10/100k is around the global 90th percentile. A fetched reference table
# would be better long-term (BD2.3 cross-check), kept explicit here.
TOP_DECILE_HOMICIDES_PER_100K = 10.0


def advisory_consensus(advisories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """C1 consensus across N issuing governments (BD matrix rule: divergence
    is a confidence flag, never a silent merge; spec rule: worst band wins —
    sovereign "do not travel" gates regardless of other issuers).

    Each entry: ``{"issuer": str, "band": "1".."4", "provenance": dict}``.
    Returns ``{"band", "divergence", "issuers", "provenance"}``.
    Single-entry input = that band, no divergence (the 1-source case is
    valid — coverage-honest, per the live finding that no single
    government advises about its own country).
    """
    if not advisories:
        raise ValueError("advisory_consensus requires at least one advisory")
    bands: List[str] = []
    issuers: List[str] = []
    provenance: List[Dict[str, Any]] = []
    for a in advisories:
        b = str(a["band"])
        if b not in BAND_LABELS:
            raise ValueError(f"invalid advisory band from {a.get('issuer')!r}: {b!r}")
        bands.append(b)
        issuers.append(str(a.get("issuer", "unknown")))
        provenance.append(a.get("provenance", {}))
    worst = max(bands)
    return {
        "band": worst,
        "divergence": len(set(bands)) > 1,
        "issuers": issuers,
        "provenance": provenance,
    }


def assess_safety_band(
    *,
    advisory_band: Optional[str] = None,
    advisory_provenance: Optional[Dict[str, Any]] = None,
    advisories: Optional[List[Dict[str, Any]]] = None,
    homicide: Optional[Dict[str, Any]] = None,
    events: Optional[Dict[str, Any]] = None,
    events_pulse: bool = False,
    neighborhood: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Combine components into a banded verdict with an honest coverage map.

    C1 input, two forms (consensus form preferred):
      - ``advisories``: list for ``advisory_consensus`` (multi-government).
      - legacy ``advisory_band`` + ``advisory_provenance`` (single source).
    ``homicide``: C2 output from fetch_worldbank_homicide (or None = gap).
    ``events``: C4 GDELT result dict from fetch_gdelt_protest_pulse — pulse =
    ``article_count > 0`` derived at this one seam (or None = gap).
    ``events_pulse``: legacy boolean form of C4.
    ``neighborhood``: C3 output from fetch_uk_street_crime (or None = gap).
    C3 ANNOTATES ONLY — it never moves the band (spec: within-band text).
    """
    if advisories:
        consensus = advisory_consensus(advisories)
        band = consensus["band"]
        c1_prov = {"source_id": "+".join(consensus["issuers"]), "divergence": consensus["divergence"], **{"sources": consensus["provenance"]}}
        if consensus["divergence"]:
            c1_prov["confidence_flag"] = "issuing-governments-diverge"
    elif advisory_band is not None and advisory_provenance is not None:
        band = str(advisory_band)
        c1_prov = advisory_provenance
    else:
        raise ValueError("provide either advisories= or advisory_band+advisory_provenance")
    if band not in BAND_LABELS:
        raise ValueError(f"invalid advisory band: {band!r}")

    components: Dict[str, Any] = {
        "c1_advisory": {"band": band, **{"source": c1_prov.get("source_id")}},
    }
    coverage: List[str] = ["c1_advisory"]

    c2 = None
    if homicide is not None:
        c2 = {
            "rate_per_100k": homicide["rate_per_100k"],
            "year": homicide.get("year"),
            "granularity": "national",
            "source": homicide.get("provenance", {}).get("source_id"),
        }
        components["c2_violent_crime"] = c2
        coverage.append("c2_violent_crime")

    if neighborhood is not None:
        components["c3_neighborhood"] = {
            "total_crimes": neighborhood.get("total_crimes"),
            "month": neighborhood.get("month"),
            "traveler_relevance": neighborhood.get("traveler_relevance"),
            "granularity": "point-radius",
            "source": neighborhood.get("provenance", {}).get("source_id"),
        }
        coverage.append("c3_neighborhood")

    events_active = bool(events_pulse)
    if events is not None:
        # Canonical C4 seam: derive the pulse from the GDELT result dict.
        events_active = int(events.get("article_count") or 0) > 0
        components["c4_events"] = {
            "active": events_active,
            "article_count": events.get("article_count"),
            "sample_titles": (events.get("sample_titles") or [])[:3],
            "source": events.get("provenance", {}).get("source_id"),
        }
        coverage.append("c4_events")
    elif events_pulse:
        coverage.append("c4_events")
        components["c4_events"] = {"active": True}

    # --- band resolution: C1 gates; C2 may raise 2→3 only with C4 ---
    if band == "4":
        pass  # gate: do-not-travel is terminal regardless of C2/C4
    elif band == "2" and c2 and c2["rate_per_100k"] >= TOP_DECILE_HOMICIDES_PER_100K and events_active:
        band = "3"

    gaps = [name for name in ("c2_violent_crime", "c3_neighborhood", "c4_events") if name not in coverage]

    return {
        "band": band,
        "label": BAND_LABELS[band],
        "components": components,
        "coverage": coverage,
        "coverage_gaps": gaps,
        "provenance": [c1_prov]
        + ([homicide["provenance"]] if homicide else [])
        + ([neighborhood["provenance"]] if neighborhood else [])
        + ([events["provenance"]] if events is not None else []),
    }
