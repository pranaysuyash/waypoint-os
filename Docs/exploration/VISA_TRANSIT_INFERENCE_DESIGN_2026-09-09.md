# Transit-Visa Inference — Design Exploration (VE-02)

**Date**: 2026-09-09
**Status**: EXPLORE (researched + documented; no implementation)
**Source**: Random document audit seed 20260909 → `Docs/personas_scenarios/AREA_DEEP_DIVE_VISA_IMMIGRATION.md` §1 (transit visas "often overlooked for 1-stop flights in countries like China or the UK") + `Docs/research/REG_SPEC_VISA_AUTOMATION.md` Rule 2 ("Transit-Visa-Inference: identify Hidden-Transit-Visas, e.g. needing a Schengen visa for a layover in Frankfurt even if the destination is Turkey").
**Register refs**: VE-02 (exploration), depends on VD-02 (live data source decision).

---

## 1. Problem statement

A traveler's visa obligations are determined not only by the destination country but by every **transit country** on the routing (air-side layovers, terminal changes, overnight stopovers). Today the product has no transit-visa inference at all. The failure mode is the harshest in travel: **denied boarding at the origin gate** (the doc's "Phase 2/3 failure" — traveler loses the whole trip before it starts).

## 2. Current-state evidence (Tier 1, 2026-09-09)

| Capability | Status | Evidence |
|---|---|---|
| Layover/stopover extraction from notes | **Absent** | `src/intake/extractors.py` has only a preference regex (`direct flights / non-stop / no layover`, line 2017); no structured layover fact exists |
| Routing/segment data model | **Absent** | No `flight_segments` fact; `traveler_plan` only detects "has flights booked" (extractors.py:2301-2305) |
| Transit mentions in code | Unrelated | Hits are analytics vocabulary (`src/analytics/*`), lifecycle/booking task labels — none are visa transit logic |
| Visa pair registry | 7 hardcoded pairs | `spine_api/services/visa_radar.py` `VISA_RULES_REGISTRY` (now flagged `registry_match`, VA-03) |
| Transit-visa rules data | **Absent** | Transit rules (e.g. China TWOV, UK DATV, air-side vs landside) are materially more complex than direct-entry rules and are not represented anywhere |

## 3. Why this is genuinely hard (the design crux)

Transit rules are a **third dimension** beyond (passport × destination): they depend on

1. **Layover duration** (China TWOV allows 24h/144h city-specific; UK DATV vs direct air-side transit differ),
2. **Terminal/air-side vs landside** (changing terminals at London Heathrow can require a DATV even when air-side transit would not),
3. **Routing shape** (same-country connections, overnight stopovers, self-transfer bookings which always require entry),
4. **Final destination** (many transit exemptions apply only when onward ticket is confirmed).

A hardcoded registry like `VISA_RULES_REGISTRY` does not scale to this — the combinatorics are (passport × transit country × duration band × terminal policy × destination). This is the strongest argument that **VE-02 is blocked on VD-02 (live data source)**: a Sherpa/Timatic-class provider models transit rules natively (Timatic powers airline denied-boarding prevention today).

## 4. Options

| Option | Description | Cost | Verdict |
|---|---|---|---|
| A. Do nothing until a data source lands (VD-02) | Transit inference deferred; radar stays destination-only | 0 | **Recommended default** — pre-launch filter (better + money) says this is not on the marketplace-pilot critical path |
| B. Heuristic transit advisory | Detect "1-stop"/"layover in X" phrasing in notes → emit a *warning-tier* advisory ("confirm transit visa for X") with no legal determination | Small (1 extractor rule + 1 warning path) | Viable quick win once routing text extraction exists; abstain-documented like AT-11 |
| C. Full transit rules engine | Model duration bands + terminal policies in-house | Large, high stale-data risk | Reject — recreates a data vendor's core competency |

## 5. Prerequisites (dependency chain)

1. **Routing extraction**: a `transit_stops` / layover fact in the packet (needs flight-segment extraction — currently absent).
2. **Data source decision (VD-02)**: Timatic/Sherpa-class provider with transit support.
3. **Abstain doctrine**: when layover country is unknown or routing is unconfirmed, warn ("routing unknown — transit visa obligations not assessed") rather than guess — same posture as AT-11 and VA-01.

## 6. Recommendation

Register as **DECIDE-gated on VD-02**. When the visa lane becomes strategic (post marketplace pilot), take Option B as the v1 (warning-tier heuristic) and let the data provider supply Option C's depth. Do not build a hardcoded transit-rules registry.

**Falsifier**: if a provider API turns out to lack transit-rule coverage (check during VE-01 research follow-up), Option B becomes the ceiling and the product copy must never promise transit-visa protection.
