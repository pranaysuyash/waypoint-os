# AE — Keyword Cluster Mining, First Tranche (2026-10-30)

First tranche of the AE (SEO keyword) cluster research, executed via the
TinyFish/public-endpoint route (owner directive: quota-blocked research →
TinyFish, never defer). Method note — this is **relative-demand + competitive**
evidence, not volume data: Google autosuggest presence (autocomplete reflects
aggregate query patterns), SERP composition, and competitor footprint. True
volume metrics (Keyword Planner/Ahrefs) still need credentialed tools.

Evidence: `Docs/sims/assets/ae_autosuggest_mining_2026-10-30.txt` (100
autosuggest lines, 10 seed phrases), `ae_paa_safety_2026-10-30.jsonl`,
`ae_paa_besttime_2026-10-30.jsonl` (TinyFish/DDG runs), `ae_paa_visa_*` (empty —
rate-limited; retriable).

## Cluster 1 — "Is it safe to travel to X" (safety)

Autosuggest: `is it safe to travel to` fans out heavily (mexico/cancun/jamaica/
egypt/bali/colombia/south africa/kenya/…). SERP is the most monetized cluster:
**isitsafetotravel.org** (248 countries, daily recalc, "30+ public sources",
free downloadable data), **travelriskcalculator.com** (241 countries, 0-100),
**worldlens.live** (live advisory overlays), **warmonit.com** (multi-gov
consensus: "US, UK and Canadian governments advise against all travel to 25,
reconsider for 27 more; 94 of 237 at normal precautions; 1 level changed in the
last 7 days" — live market numbers, Oct 30 2026), plus State Dept/USA.gov.

**Implication for the scoring spec:** the "nobody takes the trust angle" framing
needs sharpening — competitors DO publish scores and methodologies. The defensible
angles that remain: (a) **per-datapoint provenance display** (source + date on
every component, not a methodology page alone), (b) **operator/agency framing**
(duty-of-care for client portfolios, not consumer curiosity), (c) **coverage-gap
honesty blocks**, (d) the group/agent consensus layer no consumer tool has.
Spec doc note added there.

## Cluster 2 — "Best time to visit X" (weather/climate)

Autosuggest: heavy per-destination fan-out. SERP: **Best Time to Visit
Calculator** tools, **ClimateWhen** (865 destinations by month), 300+-
destination comparison pages, **SunnyTiming** (SunScore™ per destination).
Implication: the AW12 "Best Time to Visit generator" (6,000 programmatic pages)
enters a crowded field — differentiation = AQI layer (no competitor merges air
quality into best-time), monsoon/season windows for India, and agency-side
trip-date suitability (booking-aware, not just content).

## Cluster 3 — Visa/entry ("do i need a visa")

Autosuggest (from seeds): `do i need a visa for` fans to specific
destination-nationality pairs (bali, dubai, japan, vietnam, thailand, schengen).
SERP mining (evidence `ae_paa_visa_2026-10-30.jsonl` — **correction 2026-10-30
PM: the run was never empty; the agent returned a `position/site_name/url`
extraction shape my first digest didn't parse. Lesson recorded: verify the
extraction shape, not just run status**). The SERP is AUTHORITY-dominated:
travel.state.gov (advisory + entry docs), Wikipedia's structured
"Visa requirements for Indian citizens" table, **Passport Index** (India
Mobility Score 70, visa-free 25), official portals (indianvisaonline.gov.in,
mea.gov.in, cgisf.gov.in), airlines (Air India, IndiGo) — and **Sherpa**
charging **$79.89 for an India eVisa assist**: the commercial-assist margin is
visible in the SERP itself. The agency-angle wedge stands and is sharpened:
**per-client passport × itinerary visa checking inside the workflow**
(Timatic-backed — license = DP-04a family), plus e-visa-fee transparency vs
the $80 assist class — not public SEO head terms.

## Cross-cluster tool patterns observed

Every ranking tool in these SERPs shares the shape: **destination × month/score
matrix + free interactive checker + downloadable data** — exactly the
Content Prism triple. The moat differentiators available to us: provenance
transparency, agency/operator surfaces, India-market depth (CPCB AQI, MEA
advisory monitoring, NCRB), and the group-consensus integration.

## Next tranches

1. Visa-cluster SERP mining (retriable now — add inter-run delay).
2. India-launch-market cluster (Hinglish queries: "bali trip package",
   "schengen visa appointment") — after quota reset for volume data.
3. Volume-grade metrics when credentialed tools are available; until then this
   tranche's relative-demand evidence stands.

## Sources

Google autosuggest endpoint (public JSON, mined 2026-10-30) ·
duckduckgo.com/html SERPs via TinyFish (2 productive runs, 1 rate-limited) ·
isitsafetotravel.org · travelriskcalculator.com · worldlens.live · warmonit.com ·
climatewhen.com · sunnytiming.com (all as-cited in mined SERP evidence)
