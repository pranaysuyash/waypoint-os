# AW3 — Traveler Safety / Crime Data Source Evaluation (2026-10-30)

Cluster #1 of the Destination Intelligence program (`RESEARCH_OPPORTUNITY_MASTER_LIST_2026-04-25.md` category AW, safety/crime block). Executed per the READ-FIRST order (`Docs/research/README.md`): vision doc read; master-list items mapped. Sources marked **live-verified** were fetched successfully on 2026-10-30.

## Per-source verdicts (a = free tool/programmatic, b = in-product signal)

- **US State Dept advisories** — 4-level advisories + risk indicators, ~200 countries. JSON feed exists (`travel.state.gov/_res/Feeds/TrafficAdvisories.json`) but is **Cloudflare 403-gated for non-browser clients** (verified). Public domain. a=4 b=4 — best single advisory signal; friction is reliability, not legality.
- **UK FCDO** — **live-verified**: GOV.UK Content API, no key, clean JSON, per-country `public_updated_at` + `change_description`. a=5 b=5. https://www.gov.uk/api/content/foreign-travel-advice
- **Canada (travel.gc.ca)** — no open API path discoverable (404 probes); official XML feed requires registration. a=3 b=3.
- **Australia Smartraveller** — machine-readable files via data.gov.au. a=4 b=4.
- **UNODC** — downloadable country datasets; ~1-2yr lag. a=3 b=2 (background index).
- **Numbeo** — the only global city-level crime index (~500 cities) but **no free API (commercial license) and ToS prohibits scraping**. a=2 b=3 — paid-later, or supersede with self-computed index (vision-doc Year-1 moat).
- **OSAC** — strong country reports, bot-guarded portal, no API. a=3 b=3.
- **GeoNames (CC BY 4.0) + OSM (ODbL share-alike)** — geo/neighborhood infrastructure. a=5 b=4.
- **World Bank indicators** — **live-verified** (`VC.IHR.PSRC.P5` homicides/100k, no key); 2yr lag. a=3 b=2.
- **Global Peace Index** — CC BY-NC-ND (non-commercial), bot-guarded. Content/blog only.
- **data.police.uk** — **live-verified**: street-level category-tagged crime by lat/lng, monthly, free, OGL — England/Wales. The gold standard for neighborhood granularity; US cities extendable via Socrata portals (NYPD, Chicago). a=5 b=5 (UK only).
- **ACLED** — geo-precise conflict/protest events, weekly; free non-commercial license w/ registration. Paid-later for product use.
- **GDELT** — **live-verified** (1 req/5s hard limit); global news event index w/ protest detection. a=4 b=3 (cache aggressively).
- **Reddit city subs / NewsAPI** — ToS-risk / dev-only tier. Avoid as primary.
- **India**: NCRB annual "Crime in India" has city-wise tables (~53 cities, 2yr lag); data.gov.in free API keys; **MEA advisories have no machine feed (page-monitoring only) — India gap noted as new item**.
- **Commercial tier (2025-26)**: travel-advisory.info (free tier + attribution), Sitata, Safeture, Crisis24/Riskline, **GeoSure** (the only ready-made neighborhood-granularity scorer incl. women-safety).

## Recommended 3-tier stack

1. **Free-now**: FCDO API + State Dept (browser-mediated) + Smartraveller + Canada registered feed → unified 4-way advisory consensus; data.police.uk + Socrata → neighborhood crime; World Bank + UNODC → national context; GDELT (cached) + ACLED → unrest signals; NCRB → India baseline.
2. **Free-tier**: travel-advisory.info mirror/fallback, data.gov.in key, GPI (content-only, NC license).
3. **Paid-later**: Numbeo license or self-computed index, GeoSure, Sitata alerts, ACLED commercial.

## Per-master-list-item verdicts (AW3 block)

- ✅ Crime data sources by market — READY (this doc).
- ✅ Crime type mapping for travelers — READY (category-tagged street crime verified; curation is editorial, not a data gap).
- ✅ Real-time safety alerts integration — READY **with caveat**: spawns new item "MEA (India) machine feed absent".
- 🔴 Safety scoring methodology — open (composite-score spec needed; ingredients now fully mapped).
- 🔴 Time-of-day safety variation — open (proxy methodology decision).
- 🔴 Safety data by traveler type — open (only GeoSure, paid).
- 🔴 Historical incident mapping — open (UK/US feasible; no global dataset).
- Gated: AX "Is It Safe?" tool + AW10 "Is [City] Safe?" template — data-feasible now, blocked only by the scoring-spec item.

## Product/tool ideas unlocked

1. **"Is It Safe?" checker**: 4-gov advisory consensus + World Bank homicide + GDELT pulse → per-destination Safety Card (powers free tool + ~500 programmatic pages at once).
2. **Neighborhood safety for accommodation**: data.police.uk + OSM neighborhoods → hotel-area ratings (UK/US first) — beyond Numbeo's country index.
3. **Protest/unrest early-warning**: ACLED+GDELT fused feed → agent alerts + traveler briefing (duty-of-care differentiator).

## Nontraditional signals

Allianz travel-claims annual reports (destination incident-frequency proxy); Uber US Safety Reports (metro risk); transit-police open data (MTA, British Transport Police); Google Trends "is X safe" spikes (leading indicator). Honest dead-ends: STEP enrollment counts not public; hotel-review safety scoring via Google/TripAdvisor APIs is ToS-prohibited.

## Sources

gov.uk API (live-verified) · travel.state.gov (CF-gated, verified) · data.police.uk (live-verified) · api.worldbank.org (live-verified) · dataunodc.un.org · acleddata.com · api.gdeltproject.org (rate-limit verified) · numbeo.com/api · travel.gc.ca · osac.gov
