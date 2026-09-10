# E-10 Feedback→Memory Loop — Implementation Handoff

**Date:** 2026-09-06
**Mandate:** Pranay: "do all whatever is the best long term 1st principles and doctrines aligned solution" on F-36's ingestion/dispatch build (E-10).
**Design source:** `Docs/exploration/E10_SURVEY_MEMORY_FEEDBACK_LOOP_2026-09-02.md` (v2, deep-pass verified).
**Decisions ratified by this build:** shadow-mode writes (durable, influence-limited until F-13 evidence), supplier namespace separation, defaults-before-ranking influence sequencing, per-class decay as the repetition mechanism.

---

## 1. Executive summary

The feedback loop is now closed end-to-end: a post-trip response enters through a canonically-authenticated endpoint, persists on the trip, and flows through an event-class bridge into the durable memory store — where every write passes the eligibility gate, is prompt-injection sanitized *at write time*, carries provenance, and supersedes conflicts. The supplier scorecard computes from real responses (empty = honest empty; the fabricated demo rows are gone). F-13's first slot point is closed: retrieval now trust-weights the entire confidence-derived contribution by source type, so a traveler-stated fact outranks a system-inferred one at equal similarity and recency. 36 loop tests green; full suite confirming.

**Verdict:** Code ✅ · Feature ✅ (operator-transcribed ingestion; traveler self-service + real dispatch remain explicitly unbuilt, honestly labeled) · Influence deliberately **shadow** until F-13 slot 2 + a release cycle of trust-weighted evidence.

## 2. Technical changes

| Layer | File | Change |
|---|---|---|
| Ingestion | `spine_api/routers/feedback.py` | NEW `POST /{trip_id}/response` (canonical `get_current_agency_id`; `FeedbackResponseRequest` validates NPS 0–10, ratings 1–5, free-text ≤4000; response persisted under `post_trip_feedback.response`; status → `RESPONSE_RECEIVED`; audit event). Trigger-survey + scorecard moved off raw-header agency trust (F-30 family). |
| Scorecard | `spine_api/routers/feedback.py` | Aggregates from stored responses across agency trips: per-supplier mean/count, reliability tier from the mean, agency NPS mean (None when no responses — honest empty). `data_source: "computed_from_responses"`. |
| Bridge | `src/memory/feedback_bridge.py` (NEW) | Event-class rules: traveler free-text → correction (`cust_*` entity, TRAVELER_DIRECT, conf 0.8, 365d); supplier ratings → outcomes (`supplier::*` entity, conf 0.75, 365d); NPS feeds scorecard only (agency-level, never a memory write); empty response → skip. Never writes around `ingest_memory`. |
| Store hygiene | `src/memory/store.py` | `ingest_memory` gains `half_life_days` per-write override (tier default when None) — the single mechanism enforcing "implicit signals need repetition"; write-time `MemorySanitizer` on raw_text + payload + gate summary, so persisted summaries and provenance hashes describe sanitized content (deep-pass catch: gate didn't sanitize persisted text). |
| F-13 slot 1 | `src/memory/retriever.py` | Trust weighting at the blend: `SOURCE_CONFIDENCE_WEIGHTS[source_type]` scales **both** the activation term (35%) and confidence term (20%). Deep discovery while testing: the decay engine uses provenance confidence as *base activation*, so confidence flows through 55% of the blend — weighting only the 20% slice left inferred memories outranking stated ones. The fix scales the whole confidence-derived contribution. |

## 3. Test evidence

`tests/test_feedback_memory_loop.py` (12 tests): response recorded + status advanced + bridge writes counted; 404 unknown trip; 422 out-of-range; scorecard aggregation from a real response (per-agency isolated); honest empty scorecard; store half-life override honored; write-time injection sanitization (`ignore previous instructions` → `[FILTERED_INJECTION]`); bridge traveler+supplier namespaces (`cust_traveler@example.com`, `supplier::jr pass desk`); empty-response skip; **trust-ordering proof** (traveler-direct 0.7 conf outranks system-inferred 0.9 conf at identical text). Plus: capability-batch end-to-end updated to the honest contract (records a response, then asserts real aggregation — the old `nps >= 80` expectation relied on the deleted demo rows).

## 4. Doctrine notes

- **Shadow over big-bang:** writes are durable but influence flows through the trust-weighted retriever only; the legacy hydrate (F-13 slot 2, `customer_memory.py:302`) still bypasses weighting — deliberately left for its own pass since it serves the *existing* hydrate endpoint, not the new loop.
- **One mechanism, one job:** per-class decay replaces any bespoke suppression system for implicit signals — the curve enforces "needs repetition."
- **Honesty-first:** demo scorecard rows deleted (not labeled); NPS never becomes a memory fact (it measures the agency); empty states are true empties.
- **Shared-tree:** `test_capability_routers_batch` and `test_register_wave_f30_f40` updated where they pinned the fabricated contract; snapshots regenerated after route addition.

## 5. Remaining (correctly scoped)

1. **F-13 slot 2:** trust-weight the legacy hydrate path (`customer_memory.py:302`) — same pattern as slot 1.
2. **Influence activation:** after a release cycle of trust-weighted retrieval evidence, wire memory into suitability ranking (currently the loop writes are shadow by construction).
3. **Traveler self-service survey** (public-token response path) + **real dispatch** — the URL remains an honest placeholder; both are connectivity-class work.
4. **Auto-trigger** (window-end derived per E-9) — the trigger remains manual.
5. Implicit-signal class (re-booking patterns) — future rails needed; only correction + outcome classes exist today.
