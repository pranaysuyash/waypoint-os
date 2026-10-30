# AW3 — Safety Scoring Methodology Spec + Temporal-Safety Proxies (2026-10-30)

Closes the last data-layer blocker for the "Is It Safe?" free tool (AX2478), the
"Is [City] Safe?" programmatic template (AW10), and index BA2705: the composite
scoring spec. Ingredients were fully mapped in
`AW3_SAFETY_CRIME_SOURCE_EVALUATION_2026-10-30.md`; this doc defines how they
combine — honestly, with provenance, and without fabricating precision.

## Design principles (from the project doctrines + BD governance framework)

1. **No blended score without provenance.** Every component carries its source,
   retrieval date, and license tier (`ExternalFactReference`); the composite
   exposes components, never a single opaque number alone.
2. **Advisory levels are never averaged.** A US Level 4 and an FCDO
   "advise against all travel" are categorical statements from sovereign
   authorities — they are displayed as-is and gate the score band, not blended.
3. **Coarse is honest.** Bands, not decimals: the tool says "exercise increased
   caution (band 2 of 4)" — never "safety 73.4/100".
4. **Missing data abstains.** A city with no crime data shows the advisory
   picture + "incident data unavailable for this city" — never a fabricated
   neutral score (holiday_registry honest-abstain precedent).

## The composite: four components, banded

| # | Component | Source (tier) | What it measures | Weight behavior |
|---|---|---|---|---|
| C1 | **Advisory gate** | 4-gov consensus (FCDO API live-verified; State/DFAT/Canada) | Sovereign "do not travel" signals | **Gate, not weight**: any gov at "do not travel" ⇒ band 4 regardless of C2-C4 |
| C2 | **Violent-crime rate** | World Bank homicides/100k + UNODC (national, 2yr lag) | Background lethal violence | Static weight inside band; national granularity labeled as such |
| C3 | **Local incident density** | data.police.uk / Socrata city portals (street-level, monthly) | Neighborhood + category-tagged street crime | City granularity; UK/US first — absent elsewhere (component omits, labeled) |
| C4 | **Current-events pulse** | GDELT cached + ACLED (free tier) | Protests, unrest, disruptions **right now** | Time-decayed; can raise a band temporarily with an explicit "recent events" flag |

**Band derivation** (4 bands, advisory-first):
- Band 4 "Do not travel" — any C1 source at its top level.
- Band 3 "Reconsider" — C1 "reconsider travel"/equivalent, or C2 in the top
  global decile AND C4 active.
- Band 2 "Increased caution" — default for covered cities; C3 percentiles
  annotate within-band text ("higher-than-median street crime vs. country").
- Band 1 "Normal precautions" — C1 all-clear AND C2 below-median AND no C4
  activity for 30d.

Uncovered components don't lower the score; they're listed as gaps (honest
coverage map per city: "advisory ✓ · national rate ✓ · street crime —(UK/US
only) · events pulse ✓").

## Temporal-safety proxies (the "time-of-day" item)

No public temporal-safety source exists (verified in the AW3 sweep), so the
methodology uses proxies, clearly labeled:
1. **Hour-binned street crime** (data.police.uk monthly data includes timestamps
   in some datasets; Socrata city sets mostly do) → "incidents cluster 22:00-03:00
   in district X" from real distributions, never invented curves.
2. **GDELT event timestamps** → current-day activity windows ("demonstrations
   expected this afternoon near [landmark]").
3. **Transit operating hours** (GTFS feeds — free, structured) → "after-dark
   transit gap" flag per city: when the last safe-frequency service runs.
   Unconventional but fully licensed and refreshable.
Rule: every temporal claim cites its bin source + month; no "safe after dark"
verdicts without a bin dataset for that exact city.

## Traveler-type deltas (the "by traveler type" item — scoped honestly)

Free global sources for women-safety/LGBTQ+ scoring do not exist (GeoSure is
paid/licensed). Interim: SAS/uni research compilations + gov advisory
sub-indicators (e.g., State Dept "LGBTQI+ Travelers" risk indicators exist as
separate fields) surfaced as **per-type advisory excerpts**, not scores. The
Year-1 proprietary layer (traveler-reported ratings via the federated pool —
now durable) is the moat path for per-type scores.

## What this unlocks (per Content Prism)

- AX2478 "Is It Safe?" tool: C1+C2+C4 on day one (all free, verified sources);
  C3 lights up per UK/US city.
- 500-city programmatic template: band + coverage map + advisory excerpts + the
  coverage-gap honesty block ("what we can't tell you yet") — the trust angle no
  competitor takes.
- BA2705 index: bands are the index; components are the methodology page.

## Verification + governance

- Every component rides `ExternalFactReference` provenance + freshness TTLs
  (advisory 7d, incident 14d, WB/UNODC annual, GDELT live-cached).
- Weekly cross-check: FCDO vs State divergence → confidence flag, never silent
  merge (BD matrix rule).
- Bands recomputed on fetch; no cached band older than its stalest component's
  TTL — else the page renders the stale-notice variant.
