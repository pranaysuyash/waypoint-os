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

**Differentiation sharpening (2026-10-30, post SERP mining —** `AE_KEYWORD_CLUSTERS_MINING_2026-10-30.md`**):** the safety-SERP is already crowded with scored tools (isitsafetotravel.org — 248 countries daily; travelriskcalculator.com; warmonit.com multi-gov consensus). The defensible angles are narrower than "nobody does trust": (a) per-datapoint provenance display (source+date on every component via `ExternalFactReference`), (b) operator/agency duty-of-care framing, (c) coverage-gap honesty per city, (d) the group/agent integration no consumer tool has. Band semantics unchanged; the FCDO normalizer in `src/intake/external_sources.py` implements C1 against the real `details.alert_status` slug list (live-verified: Japan=[]→1, Russia=[avoid_all_travel_to_whole_country]→4, Israel=parts-variants→3).

**C1+C2 implementation note (2026-10-30, later):** the band engine is SHIPPED —
`src/intake/safety_band.py` (C1 gates, C2 raises 2→3 only with active events,
honest coverage map incl. c3 as a standing gap) and `fetch_worldbank_homicide`
in `src/intake/external_sources.py` (C2 source; live-verified: India 2023 =
0.229/100k). End-to-end live chain verified: FCDO band + WB rate →
`assess_safety_band` → Japan = band 1 "Normal precautions" with explicit gaps.
C3 (data.police.uk) and C4 (GDELT/ACLED) fetchers are the remaining build
before the free tool frontend can render all four components.

**C3+C4 shipped (2026-10-30, evening):** `fetch_uk_street_crime` (data.police.uk — live-verified 5,024 category-tagged crimes central London 2025-09; UK categories mapped to traveler-relevance classes theft/pickpocket/violent/disorder — the "crime type mapping" master-list item implemented) and `fetch_gdelt_protest_pulse` (pacing contract documented: 1 req/5s hard limit, verified 429; callers degrade to events_pulse=False — honest gap). Band engine extended: C3 annotates and never moves the band. Live UK full-chain ran with C2 (GBR 1.2/100k-class) + C3 (London point).

**C1 consensus is REQUIRED, not optional (live finding):** FCDO has no page for the UK itself — no government advises about its own country. Every destination is some traveler's home market, so single-source C1 structurally cannot cover them; the 4-gov consensus (or travel-advisory.info free tier as mirror) is the correct first-principles shape, now recorded as a spec requirement rather than redundancy.

**Consensus + seams shipped (2026-10-30, night):** `advisory_consensus()` — C1 across N issuing governments (worst band wins; divergence = `confidence_flag: issuing-governments-diverge` on provenance, never a silent merge). `assess_safety_band` now takes `advisories=[...]` (canonical multi-source form) or the legacy single-source pair, and `events=` (GDELT result dict; pulse = article_count>0 derived at one seam — zero articles = reported-calm, NOT a gap). Second live C1 source: **travel-advisory.info DEAD** (broken TLS on both hosts — struck from the stack), **Smartraveller unreachable from this env (000)**, State Dept CF-gated (browser-mediated, not runtime-grade), Canada = registered feed (owner credential). Consensus ships source-ready for N; the next reachable fetcher plugs in without engine changes. Normalization enums for the 7 unregistried types: `src/intake/data_normalization.py` (BD2.2 complete). Live end-to-end: Russia = band 4 w/ C2 6.765/100k, C4 paced-out honestly as gap.
