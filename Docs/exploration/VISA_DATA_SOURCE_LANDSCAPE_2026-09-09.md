# Visa Data-Source Landscape — Research (VE-01)

**Date**: 2026-09-09
**Status**: EXPLORE complete (web-researched; live-verification of quotes still owed — both leading vendors price by negotiation only)
**Source**: Random document audit seed 20260909 → `AREA_DEEP_DIVE_VISA_IMMIGRATION.md` "live API (e.g., Sherpa or VisaCentral)" claim + `frontend/docs/VISA_01/02_*.md` (April 2026 unanswered question lists — this doc supersedes them as the current answer).
**Register refs**: VE-01; feeds VD-02 (live data-source decision). **DECIDE-gated: off the marketplace-pilot critical path per PER-0100 council lens.**

Research conditions note: primary search tooling was rate-limited; findings come from direct fetches of provider sites and official government pages (URLs per claim). Where a fact could not be verified from a fetched source it is marked **unverified**.

---

## 1. Provider landscape

### Sherpa° (joinsherpa.com) — aggregator, best-documented API
- **Authority**: aggregator of 2,000+ sources (government, travel orgs, data-sharing agreements), NOT an authority itself. Sources cited incl. Australian Home Affairs, Singapore MoH, UK Government, US CDC. (docs.joinsherpa.io/requirements-api/*)
- **API**: public REST Requirements API (`/v3/trips`), JSON:API-style, API-key auth, sandbox + production, 100 req/s, 10 MB cap. Includes an "LLM Friendly" trips variant. Endpoints: Trips, Restrictions, Procedures, Countries, Regions.
- **Pricing**: **not public** — contact-form/enterprise negotiation, volume-based.
- **Coverage**: 200+ countries, 30 languages; visa/eTA, passport validity, blank pages, vaccination/quarantine. Passport×destination pair count not published.
- **Freshness**: ingested 24/7, pushed hourly after QC; vendor says do not cache >1h. **No documented webhook** — monitoring is poll-hourly.
- **Monetization angle**: sells eVisa/eTA checkout as ancillary revenue (claims up to 14.6% conversion, +31% booking value) — relevant to the agency-marketplace GTM.
- **Customers**: Condor, Vueling (2026 partnership), G Adventures, TTC, TripActions.
- **India-outbound fit**: Indian passport (`IND`) is a supported input; India eVisa already marketed. **Good fit.**

### IATA Timatic — the airline-grade authority
- **Authority**: de-facto airline check-in standard; what gate agents actually board against.
- **Access**: licensed via IATA (timatic.iata.org, login-gated) or resellers. Timatic-derived B2B checker verified live: **TravelDoc** (ICTS Europe) — 200+ countries, ~1B checks/yr, 40+ airline customers (traveldoc.aero). TravelDoc's Timatic basis is widely reported but not stated on the fetched pages (**unverified on-page**).
- **Pricing**: **not public** — enterprise negotiation. Budget unknown until quoted.
- **API**: exists (airline DCS/check-in integrations); public docs behind licensing. Refresh cadence: continuously updated per IATA marketing, no citable public number (**unverified**).
- **India-outbound fit**: full coverage (airlines must board Indians correctly); cost/eligibility for a startup SaaS is the barrier.

### Consumer visa marketplaces (iVisa / VisaHQ / CIBT / Atlys)
- **iVisa**: site unreachable from research environment; affiliate/partner program historically exists, India eVisa marketed — **current partner API/commission terms unverified**.
- **VisaHQ**: corporate portal with "AI Compliance Engine" real-time monitoring claim, 200+ countries; **no public API** — service relationship, not a data feed (visahq.com/corporate).
- **CIBTvisas**: full-service expediting, client portal, **no public API** (cibtvisas.com).
- **Atlys**: moving B2B to "Atlys Enterprise" — workflow/dashboard for TMCs, 150+ destinations, 2M+ visas; not a public requirements API. Strong India-market focus (atlys.com/business).
- **Revenue model**: commission/service fees per completed application (verified indirectly via product pages); exact rates not public anywhere.

### Government e-visa portals (India-outbound reality check)
- **UK ETA**: fully live since April 2025, £20, 6-month visits — but for **non-visa nationals**; **Indian citizens need a standard UK visa, not ETA** (gov.uk/guidance/electronic-travel-authorisation-eta). Note: our hardcoded registry has ("US","GB")→ETA which is correct; ("IN","GB") would correctly be CONSULAR_VISA class.
- **EU ETIAS**: **not yet operational Sept 2026** — revised timeline endorsed March 2026, expected operational Q4 2026, then ≥6-month transition + ≥6-month grace (travel-europe.europa.eu). €20 for visa-exempt nationals. **Irrelevant for Indian passports** (Schengen visa-required); matters only for our US/EU-passport travelers.
- **Japan eVisa**: official portal evisa.mofa.go.jp (bot-restricted when fetched); India among eligible nationalities (widely documented — verify at portal before relying).
- **Schengen via VFS**: no API; appointment flows via vfslobal country sites.

### Free/open datasets — inadequate for compliance
- Passport Index (Arton): no public API. Henley: monthly rankings only, no rule detail, no free API. Wikidata-derived visa data: stale, unstructured. Verdict: fine for "how strong is a passport" heuristics; **inadequate** for per-trip compliance (validity rules, transit, blank pages, procedures).

## 2. Recommendations

**(a) MVP heuristic product** (if/when visa lane activates):
1. **Sherpa Requirements API** — best-documented public REST, hourly freshness, trip-context queries (origin/destination/date/passports), LLM-friendly endpoint; barrier is a negotiated key, not engineering.
2. Passport Index/Henley aggregates + curated official portals for the top ~20 India-outbound corridors as a free fallback tier.

**(b) Compliance-grade product**:
1. **Timatic** (direct or via TravelDoc-class reseller) — the authority gate decisions are made against.
2. **Sherpa as the operational layer** — developer experience + embeddable eVisa monetization for Indian outbound. Dual-source (Timatic + Sherpa) cross-check is the defensible architecture.

**Costs are unknowns by design** — both vendors price by negotiation; any budget figure is a guess until quoted. ETIAS timing has slipped repeatedly; do not build Schengen visa-free logic around it for non-Indian passports before Q4-2026+transition.

## 3. Product-map implications for Waypoint OS

- Current `VISA_RULES_REGISTRY` (7 pairs, now honestly badged VA-02/03) is a fine stopgap for demo/pilot; the registry's conservative unknown-pair default already fails safe.
- Sherpa's eVisa checkout monetization maps directly onto the agency-marketplace revenue thesis (agencies receive demand; ancillary visa fees are a natural adjacent line) — worth revisiting **after** the marketplace pilot gate rather than before.
- VE-02 (transit-visa inference) is confirmed blocked on a data source: no free dataset models transit rules; Sherpa/Timatic do.
