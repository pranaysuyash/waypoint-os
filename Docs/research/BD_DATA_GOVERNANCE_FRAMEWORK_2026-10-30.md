# BD — Data Governance Framework for Destination Intelligence (2026-10-30)

Cluster #3 of the Destination Intelligence program (master list category BD, governance block ~2836-2842). READ-FIRST order followed; supersedes the destination-intelligence dimension of `Docs/INTEGRATIONS_AND_DATA_SOURCES.md` (2026-04-14) — see §Supersedence.

## Shared provenance contract

Every served external datapoint is a fact carrying `{source_id, retrieved_at (ISO-8601 UTC), as_of/effective, license_tier, approximate|confidence}`. It lands through the existing `SourceEnvelope` pattern (`src/intake/packet_models.py:313`) and application mirrors `AUTHORITATIVE_FACT_SNAPSHOT` (`src/intake/fact_overrides.py:53`, applied in `src/intake/extractors.py:3445-3580` with `authoritative_fact_applied` audit events). Snapshot writes chain through the existing RULE_015 hash-chained audit path (`spine_api/core/audit.py`, `spine_api/services/audit_chain_hash.py`) — **one ledger, no parallel system**.

## Per-data-type governance matrix

| Type | Freshness (stale threshold) | Normalization | Verification | License/attribution | Provenance |
|---|---|---|---|---|---|
| Weather/AQI | forecast ≤6h; baselines annual | °C; AQI scale as declared enum (US-EPA/WHO/CPC differ); PM2.5 μg/m³ | daily spot-sample vs govt station | CC-BY / attribution-required; show provider + fetch time | provider, station id, issue-time, retrieved_at |
| Safety/advisories | advisories ≤7d; crowd ≤90d low-confidence | keep per-issuing-body level (US 1-4, FCDO wording) — no blended score without provenance; crime as rate/100k | US+UK/AU cross-check; divergence = confidence flag, never silent merge | public domain (US) / OGL (UK); show issuing govt + effective date + "check your government" | issuing govt, level, effective date, divergence flag |
| Visa/entry | ≤30d; mandatory re-check when departure <90d | ISO-3166 nationality×destination; enum {visa_free, eta, evisa, voa, required}; passport-validity months | **Timatic = authority of record**; gov pages secondary monthly; conflict → abstain to human | restricted/commercial; never scrape; display "verified vs Timatic as-of DATE" | authority tier, effective date, retrieved_at — user-visible by default |
| Holidays/events | exact dates recompute yearly; events ≤14d pre-trip | canonical already: `src/intake/holiday_registry.py` (package exact > curated approximate-flagged > honest abstain) | `holidays` package = computation authority; annual lunar cross-check | package public; curated internal | `source` + `approximate` on every result — **the pattern to generalize** |
| Currency/FX | token registry annual ISO-4217 review; FX ≤24h (≤1h on booked trips) | ISO-4217 only; unmarked amounts = policy (FND-0341), never registry (`src/intake/currency_registry.py`) | daily drift vs central-bank reference; >2% flagged | OXR per-tier attribution; ECB public domain | rate source, base/quote, retrieved_at |
| Connectivity/eSIM | catalog ≤90d; coverage ≤180d; **price never served >48h (live-or-omit)** | band enum; coverage {2G..5G}; one internal provider registry | quarterly sweep + traveler-verified activations (Year-1 proprietary layer) | provider ToS-gated; own contributions owned w/ consent | provider, plan id, price-as-of, catalog version |
| Health/vaccination | requirements ≤30d (outbreak-sensitive); routine annual | destination×nationality; {required, recommended, routine}; WHO disease vocab | WHO IHR / CDC primary; UK NaTHNaC monthly cross-check | public domain; mandatory clinician disclaimer + issuing body | issuing body, requirement, effective date, disclaimer flag |
| Costs/prices | index quarterly; live ≤90d w/ sample size; never >180d as current | ISO-4217 + trip-time FX w/ rate provenance; one price-category enum; per-capita explicit | crowd sample vs 2nd source quarterly; **publish sample size** | Numbeo restricted for redistribution — verify ToS or replace w/ agent-reported (the moat) | sample size + window + method (crowd/official/agent) |
| Laws/cultural | baseline ≤365d; high-stakes (drugs/drones/photography) ≤90d | {category, severity {prohibited/restricted/advisory}, scope}; verbatim quote + plain-language summary | official gov/embassy primary; **prohibited-severity needs 2 sources** | law text public domain; "not legal advice" disclaimer + source link | source url, effective date, severity, confidence |

## Precedents — borrow/skip

1. **Wikidata references** — BORROW the statement-level reference triple {stated-in, reference-URL, retrieved}; refuse unsourced imports. SKIP archive-URL machinery (hash chain covers integrity).
2. **OSM `source=*`** — BORROW per-attribute sub-keys (`source:date`) and the re-confirmation-states-source rule. SKIP import bureaucracy; adopt object-tags-rot → snapshot-level freshness.
3. **W3C DCAT 3 / DCAT-US** — BORROW `accrualPeriodicity` (freshness as first-class metadata — literally BD2.1), `license` vs `accessRights` separation (Timatic), `spdx:checksum` on distributions. SKIP full RDF machinery.
4. **IATA Timatic** — BORROW "one authoritative tier per high-stakes type" + liability-aligned provenance display. SKIP hand-building the 38K matrix — license, don't compete.
5. **Numbeo methodology disclosure** — BORROW published-methodology + sample-size disclosure for every derived index. SKIP treating it as primary cost source (verification source only).

## Three highest-leverage codebase gaps (verified by direct read)

1. **No provenance envelope for external data** — `SourceEnvelope.source_system` (`src/intake/packet_models.py:316`) is a Literal over internal channels; zero external fetchers exist in the tree. Fix: add an `"external_reference"` variant with required `{source_id, retrieved_at, as_of, license_tier}` — extends the canonical envelope, no parallel system.
2. **No freshness/TTL contract** — no `valid_until`/`as_of` staleness flag on any datapoint. In-repo precedent to generalize: `HypothesisState.STALE` + `mark_hypothesis_staled` (`src/intake/packet_models.py:419,759`).
3. **Licensing unowned + moat data layer is a mock** — `src/intake/attribution.py` is speaker attribution, not data licensing; `src/intake/federated_intelligence.py` holds the intelligence pool in a plain in-memory list (provenance dies on restart). Fix: durable append-only store chained through the audit ledger.

## Supersedence note (for INTEGRATIONS_AND_DATA_SOURCES.md)

The 2026-04-14 doc framed reference data as MVP scarcity ("every integration is debt"). Its booking/GDS/CRM/WhatsApp "don't integrate" verdicts remain valid; reference data has since graduated to a governed platform layer (this framework + the vision doc). Retain as historical MVP context with a header pointer; do not treat its P1/P2 API table as current scope.

## Per-BD-item verdicts

READY-TO-MARK: BD1.1 (open-data APIs), BD1.4 (governance half — Numbeo = secondary + ToS-risk), BD2.1 (freshness), BD2.3 (verification), BD2.7 (licensing). PARTIAL: BD2.2 (normalization in principle; code has currency+holiday only), BD2.6 (append-only exists; retention policy undefined). OPEN: BD1.2 (Timatic license decision — the concrete next step), BD1.3 (per-country DCAT survey), BD1.5 (social — defer, no consent model), BD1.6 (tourism boards, commercial), BD1.7 (traveler-contributed — gated on gap #3), BD1.8/1.9/1.10 (defer P2), BD2.4 (missing-data: interim rule = abstain honestly per holiday_registry precedent), BD2.5 (multilingual — alias-table template), BD3.x (monetization — gated on provenance + verification shipping).

## Sources

wikidata.org/wiki/Help:Sources · wiki.openstreetmap.org/wiki/Key:source · w3.org/TR/vocab-dcat/ · resources.data.gov/resources/dcat-us/ · iatatravelcentre.com · numbeo.com/common/about.jsp
In-repo evidence: src/intake/{packet_models,fact_overrides,extractors,currency_registry,holiday_registry,federated_intelligence,attribution}.py · spine_api/core/audit.py · spine_api/services/audit_chain_hash.py
