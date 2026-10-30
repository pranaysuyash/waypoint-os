# AY — Laws & Culture Source Evaluation (2026-10-30, first tranche)

Cluster #4 of the Destination Intelligence program (master list AY "what Google
doesn't tell you" block: country laws, dress codes, drug/LGBTQ+ status,
etiquette — items AX2520-2533 + AZ2667-2676). The full 127-item block stays
open; this tranche locks the SOURCE LAYER, which was the unknown.

## The unlock: FCDO already ships laws/culture per country — via the verified API

Cluster #1 live-verified the GOV.UK Content API for advisories. The SAME
per-country payload carries structured sections incl. **"Laws and cultural
differences"** (drug penalties, dress codes, LGBTQ+, photography rules,
camouflage/cultural offences, ID requirements), "Safety and security",
"Entry requirements", "Health". Zero new integration: one API, no key, clean
JSON, `public_updated_at` per country. That converts the AY block from
"no machine-readable source exists" to "one fetcher + normalization".

- Endpoint shape: `https://www.gov.uk/api/content/foreign-travel-advice/<country>`
  (details → links to per-section documents incl. `.../laws-and-customs`).
- License: OGL — attribution required (display "Source: FCDO, updated DATE").
- Granularity: country-level, UK-traveler-oriented phrasing (fine for content;
  for in-product rules use the severity enum from the BD governance matrix).

## Complementary sources (per BD governance matrix laws/cultural row)

| Source | Covers | Access | Role |
|---|---|---|---|
| FCDO laws-and-customs (GOV.UK API) | drugs, dress, LGBTQ+, photography, ID, local customs | free API (verified class) | **Primary** — refresh ≤365d, high-stakes ≤90d |
| US State Dept country pages (CF-gated feed; browser-mediated fetch) | local laws special circumstances, penalties | public domain | **Cross-check** (2-source rule for `prohibited` severity) |
| Smartraveller (data.gov.au files) | laws, cultural etiquette | free files | Third consensus source |
| IATA Travel Centre public pages | entry/exit rules, currency-declaration limits | page-only | Entry-adjacent context (Timatic remains authority for visa — license decision = DP-04a-adjacent) |
| WHO / CDC travelers' health | health entry rules | free | Health type (own matrix row) |
| Government open-data portals (data.gov.in etc.) | local ordinances, permits | per-country survey (BD1.3 open item) | India launch-market depth |

## Honest gaps

- Etiquette/dress-code nuance beyond gov phrasing (e.g., temple dress specifics)
  is editorial content, not a data feed — Content Prism writer lane, sourced to
  the gov sections above.
- No per-country machine feed for India MEA advisories (known gap, spawned
  item from cluster #1).
- LGBTQ+ legal-status structured datasets (e.g., ILGA world database) exist
  but licensing must be checked before product use — flagged verify.

## Verdicts

- **AY source layer: READY** — FCDO primary + 2-source cross-check satisfies
  the BD laws/cultural governance row.
- Master-list AY items: laws/dress/drugs/LGBTQ+/photography sub-items become
  build-tranche work (fetcher + severity enum + provenance) — the data blocker
  is lifted. Etiquette content items remain editorial-lane.
- New dependency to honor: OGL attribution display + "not legal advice"
  disclaimer (BD matrix), and the 2-source rule for prohibited-severity items.

## Sources

https://www.gov.uk/api/content/foreign-travel-advice (API class live-verified in
cluster #1, 2026-10-30) · https://www.smartraveller.gov.au ·
https://travel.state.gov (CF-gated) · https://www.iatatravelcentre.com ·
https://wwwnc.cdc.gov/travel · ILGA world database (license: verify)
