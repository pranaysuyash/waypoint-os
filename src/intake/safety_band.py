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


def assess_safety_band(
    *,
    advisory_band: str,
    advisory_provenance: Dict[str, Any],
    homicide: Optional[Dict[str, Any]] = None,
    events_pulse: bool = False,
    neighborhood: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Combine components into a banded verdict with an honest coverage map.

    ``advisory_band``: C1 output ("1".."4" from normalize_fcdo_status).
    ``homicide``: C2 output from fetch_worldbank_homicide (or None = gap).
    ``events_pulse``: C4 boolean from the events fetcher (False = gap).
    ``neighborhood``: C3 output from fetch_uk_street_crime (or None = gap).
    C3 ANNOTATES ONLY — it never moves the band (spec: within-band text).
    """
    band = str(advisory_band)
    if band not in BAND_LABELS:
        raise ValueError(f"invalid advisory band: {advisory_band!r}")

    components: Dict[str, Any] = {
        "c1_advisory": {"band": band, **{"source": advisory_provenance.get("source_id")}},
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
    if events_pulse:
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
        "provenance": [advisory_provenance]
        + ([homicide["provenance"]] if homicide else [])
        + ([neighborhood["provenance"]] if neighborhood else []),
    }
