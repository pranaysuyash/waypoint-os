# E-10 Exploration — Closing the Survey→Memory Feedback Loop (v2, code-verified)

**Date:** 2026-09-02 (v2 rewritten 2026-09-04 after full code verification).
**Candidate:** E-10 (P2). v1 authored by primary agent under quota constraints; v2 verifies every v1 claim against code, corrects two material errors, and makes decay/confidence parameters concrete.
**Question:** How do explicit corrections, implicit signals, and outcomes flow into customer memory — with write rules per class — so the next trip's decisions are better without amplifying untrusted writes?

**Verification legend:** ✅ VERIFIED = read in code, line-cited. ✏️ CORRECTED = v1 claim was wrong or imprecise. ◻️ INFERRED = design proposal, not existing code.

---

## 1. Current state

### 1a. Write side — `spine_api/routers/feedback.py` (read in full, 141 lines) ✅

Exactly two endpoints, no survey-response ingestion:

| Endpoint | Behavior (verified) |
|---|---|
| `POST /api/v1/feedback/{trip_id}/trigger-survey` (L50) | 404s if trip not agency-scoped (L58-60). Generates `survey_id = f"srv_{trip_id[:8]}_{MMSS}"` (L63 — minute+second only, collision-prone across days). Persists `trip["post_trip_feedback"] = {survey_id, status:"DISPATCHED", delivery_channel, dispatched_at}` and saves (L66-73). Audit event `post_trip_feedback_triggered` (L75-83). |
| `GET /api/v1/feedback/supplier-scorecard` (L95) | ✏️ **CORRECTED:** returns **100% hardcoded demo data** (L100-133): 4 named suppliers, `total_feedback_submissions=156`, `average_agency_nps=89`. There is **no aggregation math, no persistence, no data source** — `SupplierRatingEntry`/`SupplierScorecardResponse` (L34-47) are response shapes only; `reliability_tier` (PREFERRED/ACCEPTABLE/UNDER_REVIEW) is never computed anywhere. The router does not touch `CONTRACTS_STORE` (`spine_api/routers/supplier.py:36`) — that store holds contracts and is consumed by `price_lock.py`/`yield_arbitrage.py`, unrelated to ratings. |

**Fabricated survey URL — CONFIRMED ✅:** L64 `survey_url = f"https://feedback.waypointos.com/s/{survey_id}"`. No dispatch backend exists; `delivery_channel` is recorded but nothing sends. Extra detail v1 missed: the fabricated URL is **returned in the response only — it is not persisted** to the trip record (only survey_id/status/channel/dispatched_at are). Honesty flag stands; same class as I-6.

**Additional findings:**

- ✏️ No response-ingestion endpoint: `post_trip_feedback.status` is only ever written as `"DISPATCHED"` — "SUBMITTED"/"COMPLETED" states do not exist. The loop's first missing link is confirmed upstream of memory.
- ✏️ **Auth inconsistency:** feedback.py uses raw `X-Agency-ID` header with `TEST_AGENCY_ID` fallback (L57), whereas `customer_memory.py` uses the canonical `get_current_agency_id` dependency. E10.2 must adopt the dependency pattern.

### 1b. Memory write contract — `src/memory/store.py` `ingest_memory` (L87-152) ✅

Signature confirmed: `(agency_id, entity_id, raw_text, source_type: MemorySourceType, payload, source_ref_id, actor_id, category_hint, explicit_confidence, is_safety_critical=False) → (Optional[BaseMemoryItem], str)`. Flow: gate → provenance (`ProvenanceEngine.create_provenance`, SHA-256 over `provenance_id:source_type:source_ref_id:actor_id:recorded_at:payload`) → `BaseMemoryItem` → supersession scan against same-entity items (`SupersessionEngine.detect_conflict/resolve/apply`) → append + atomic JSONL save. Rejections explicit: `return None, f"Rejected: {eval_res.rejection_reason}"` (L112-113).

**✏️ Half-life handling is narrower than v1 implied:** L135 sets `half_life_days = None if is_safety_critical else (730.0 if tier == SEMANTIC else None)`. `ingest_memory` constructs **`BaseMemoryItem` directly**, so the subclass `__post_init__` defaults (EPISODIC 365d, WORKING 0.05d in `models.py:158/172`) **never apply through this API**. Consequence: anything ingested via `ingest_memory` either decays at 730d half-life (semantic, non-safety) or not at all. There is **no caller-settable `half_life_days` parameter** — ◻️ the E10.3 bridge needs this parameter added (or a post-construction override) to implement per-event-class decay.

### 1c. Gate acceptance criteria — `src/memory/eligibility_gate.py` `evaluate` (L64-119) ✅

Exact acceptance rules, in order:

1. Reject `len(cleaned) < 4` (L75-81).
2. Reject conversational chatter via 4 anchored regexes (L27-32, L84-91) — greeting/bye/help/joke only; real survey free-text passes.
3. Confidence: `SOURCE_CONFIDENCE_WEIGHTS[source_type]` (default 0.6 if missing); if `explicit_confidence` given → **`0.5 * explicit + 0.5 * source_weight`** (L97); else source weight alone.
4. Reject if `confidence < 0.75` (`DEFAULT_WRITE_CONFIDENCE_THRESHOLD`, L24; check L102-108, strict `<`).
5. Classify tier/category (`_classify_tier_and_category`, L121-151): hint map — `policy|rule|procedure|guideline`→PROCEDURAL; `preference|autonomy|settings`→PREFERENCE; `disruption|incident|interaction|trip_milestone`→EPISODIC; any other hint→SEMANTIC with hint as category. No hint → keyword heuristics (procedural terms; safety-dietary→`dietary_safety`; seating; loyalty; else `general_affinity`).
6. `sanitized_summary = cleaned[:250]` (L118). ✏️ **CORRECTED:** the gate itself does **not** run `MemorySanitizer` — sanitization happens at **read time only** (`retriever.py:84`). "Sanitizer in-path" is true for retrieval, not for persisted text.

**No source-type allowlist** — all `MemorySourceType` values are admissible; the threshold is the only filter. **No special safety-critical path in the gate** — `is_safety_critical` only affects half-life in the store (infinite), never acceptance.

**`MemorySourceType` enum (models.py:34-41) — exact values + weights ✅:**

| Value | Weight | Gate outcome (no explicit conf / with explicit) |
|---|---|---|
| `TRAVELER_DIRECT` | 1.0 | Passes alone. With explicit e: passes iff e ≥ 0.50 (e=0.5 → exactly 0.75, strict `<` lets it through). |
| `VERIFIED_DOCUMENT` | 0.95 | Passes alone. |
| `AGENT_MANUAL` | 0.90 | Passes alone. |
| `GDS_IMPORT` | 0.90 | Passes alone. |
| `SYSTEM_INFERRED` | 0.75 | Passes alone (0.75). With explicit e: passes iff e ≥ 0.75. |
| `THIRD_PARTY_WEB` | 0.60 | Fails alone; passes iff e ≥ 0.90. |

**◻️ Which source_type a survey outcome should use:** `TRAVELER_DIRECT` — the traveler authored the response, so it sits at the top of the hierarchy and needs only `explicit_confidence ≥ 0.5` to clear the gate (bridge will send 0.7–0.9 based on §2). Averaged/scorecard-derived supplier facts are agent-derived observations → `AGENT_MANUAL` (0.90, passes alone). **Do not add a new enum value** — the 6-value hierarchy plus explicit confidence already expresses this, and a new value would silently default to 0.6 anywhere `SOURCE_CONFIDENCE_WEIGHTS` is consulted before being mapped.

### 1d. Read side — retriever + decay (verified with concrete numbers)

`src/memory/retriever.py` ✅: `retrieve(query, memories, top_k=10, min_score=0.20)`; per item: skip tombstoned/superseded (L59); skip activation ≤ 0.01 (L63); similarity = set token overlap `|q∩t|/|q|` over `summary + " " + category` (L34-43, L66); **L70: `combined_score = round(0.45*sim + 0.35*activation + 0.20*conf, 4)`** — this exact line is the F-13 slot; token budget 800 (~4 chars/token, L19/L31/L87).

`src/memory/decay_engine.py` ✅: `activation = confidence * 2^(−elapsed_days/half_life_days)` clamped [0,1] (L53-56); `half_life_days` None/≤0 → constant activation = confidence (L40-41); `is_active(threshold=0.25)` exists but has **no production caller** (verified — only the retriever calls `calculate_activation_strength`).

**Concrete decay table (replaces v1's "slow/faster"):**

| Class | half_life_days | Conf at write | Activation day 0 / 365d / 730d | Effect on combined score |
|---|---|---|---|---|
| Explicit survey correction (SEMANTIC, non-safety) | 730 (store default, L135) | ~0.95 (TRAVELER_DIRECT, e=0.9) | 0.95 / 0.67 / 0.48 | `0.35*activation` term halves in 2 yrs; `0.20*conf` constant |
| Outcome/supplier signal (EPISODIC or SEMANTIC) | ◻️ 365 proposed (needs param, see 1b) | ~0.83 (AGENT_MANUAL, e=0.75) | 0.83 / 0.59 / 0.41 | — |
| Implicit behavioral (◻️ SEMANTIC, low conf) | ◻️ **90 proposed** | ≥0.75 floor (SYSTEM_INFERRED, e≥0.75) | 0.75 / 0.19 / 0.047 | At 90d: 0.45·sim + 0.067 + 0.15 — survives only if sim ≥ ~0.35 vs min_score 0.20; i.e., repetition (re-ingest refreshes `created_at`, resetting decay) is what keeps it alive. That is the "needs repetition to persist" rule, mechanically enforced by the decay curve. |
| Safety-critical (allergy etc.) | None (infinite) | — | constant | Never fades; supersession is the only update path |
| Never-write class | — | — | — | Gate-rejected; never stored, never decays |

### 1e. Where retrieved memory actually reaches decisions — ✏️ CORRECTED (v1 overstated)

`rg memory src/suitability/` returns **zero hits**. Verified actual flow:

- Suitability reads preferences from the **intake packet**, not the memory store: `src/suitability/integration.py:69-80` (`_extract_pace_preference_from_packet`), `L221-231`/`L318-329` (`packet.facts["budget_preference"]/["pace_preference"]` → `SuitabilityContext`), consumed by the Tier-3 LLM scorer payload at `src/suitability/llm_scorer.py:~300` (`"context": {... "pace_preference" ...}`). Packet facts originate from the intake extraction pipeline (`src/intake/extractors.py:2915` maps vocabulary), surfaced via `trip["extracted.facts.<key>.value"]` fallbacks (`spine_api/contract.py:1199-1215`).
- The only code that moves customer memory into decisions is **`hydrate_trip_with_customer_memory`** (`spine_api/routers/customer_memory.py:302-388`): profile fields → `trip["extracted"]["dietary"/"seating_preference"/"room_preference"]` → later read into trip/contract fields.
- ✏️ **Critical:** that hydrate path reads the **legacy process-local dict `CUSTOMER_MEMORY_STORE`** (`customer_memory.py:43`, `_find_customer_profile` L144-169) — **not** the durable `MemoryStore`. The durable store's hybrid retriever is reachable **only** via REST (`GET /api/v1/customers/memory/query`, L436-470, the sole `query_memories` caller). No in-process decision pipeline queries memory today.

**F-13 exact register wording** (`Docs/review/FINDINGS_REGISTER_2026-08-31.md:90`): *"`src/memory/` writes sanitized but not trust-weighted; cross-trip prefs inject into suitability scoring" (open, P1).*

**Exact F-13 slot points (named):**

1. **Primary:** `HybridMemoryRetriever.retrieve`, `src/memory/retriever.py:70` — re-weight `0.45/0.35/0.20` or add a trust multiplier on `conf` keyed by `source_type`. This is correct once decisions read memory in-process.
2. **Current actual injection (today's blast radius):** `hydrate_trip_with_customer_memory`, `customer_memory.py:347-366` — hydrate writes have no provenance/decay/trust at all because they bypass the durable store. E10.x should migrate hydrate onto `MemoryStore` reads so F-13 has one lever, not two.

**NEW-06** (register L232) confirmed: `api-client.ts` has zero customer-memory functions; it also has **no feedback trigger/scorecard calls** (only a `feedback?` UI type, `api-client.ts:375`) — FE is uninvolved in the entire loop today. Orthogonal to E-10.

---

## 2. Loop design — event classes × write rules (deepened)

| Event class | Example | Path into `ingest_memory` | source_type | explicit_confidence | Tier / category_hint | half_life_days | Gate outcome | Eligibility expectation |
|---|---|---|---|---|---|---|---|---|
| **Explicit correction** (post-trip survey free-text/ratings) | "The 'boutique hotel' was a demolition site"; room/seating ratings | E10.2 response endpoint → E10.3 bridge | `TRAVELER_DIRECT` ✏️ (v1 said "survey-outcome" type — none exists) | 0.9 for attributed ratings; 0.7 for free-text | SEMANTIC; hint `traveler_preference` (or EPISODIC + `trip_milestone` for trip-scoped incidents) | 730 default | Passes (0.95 / 0.85 blend) | Should pass; gate chatter/length rules apply to free text |
| **Outcome signal** (supplier-level) | Scorecard-derived reliability; "delivered late, refunded" | E10.4 scorecard→memory bridge | `AGENT_MANUAL` | 0.75 (per observation) | SEMANTIC, supplier entity_id namespace; hint e.g. `supplier_reliability` | 365 ◻️ | Passes (0.825) | Aggregate per supplier, not per trip; confidence grows with `total_reviews_count` (◻️ proposal, see Decisions #4) |
| **Implicit signal** | Re-books same destination; upgrades room class; ignores advised category | future behavioral rails (none exist ✅) | `SYSTEM_INFERRED` | 0.75 exactly (floor) | SEMANTIC; keyword or hint category | **90** ◻️ (needs new param) | Passes at floor | Persist only after N corroboration: the 90d curve makes single observations fade in ~90d; re-observation resets `created_at` |
| **Never-write** | One-off planning complaint; pricing grumbles; survey NPS number alone ("7") | — | — | — | — | — | Rejected (chatter regex, <4 chars, or sub-threshold blend) | Excluded at event-class level in the bridge; noise amplification guard |

**Key architectural rule (v1, confirmed sound):** every loop write goes through `ingest_memory` — never a side-channel write. Gate = admission; F-13 = influence at retrieval (`retriever.py:70`). ◻️ Amendment from §1e: the bridge must ALSO be the trigger to migrate `hydrate_trip_with_customer_memory` from `CUSTOMER_MEMORY_STORE` to `MemoryStore` reads, otherwise loop writes influence nothing (hydrate ignores the durable store) while F-13 weights a retriever no decision path calls.

---

## 3. Dependency order (binding)

1. **F-13 lands first or with this loop** — but with a precise scope update: F-13's lever is `retriever.py:70` AND the hydrate migration (§1e). Writing survey outcomes with high confidence before influence is trust-weighted would amplify whatever the survey says.
2. **Survey-response ingestion endpoint** (E10.2) must exist first — today the response has no path in at all (verified).
3. **Scorecard honesty** is now worse than v1 recorded: it is not "router-local aggregation", it is hardcoded demo data. Fabricated-URL fix (E10.1) and hardcoded-scorecard fix (E10.0 new) join the I-6 honesty family.
4. NEW-06 (FE wiring) orthogonal and separate.

---

## 4. Privacy / GDPR notes

- All loop writes ride `gdpr_engine` + retention via the memory subsystem (verified: `forget_entity_gdpr` → `GDPRMemoryEngine.erase_entity_memories` → tombstones + certificate, `store.py:187-201`). Survey text may contain third-party PII; sanitizer runs at retrieval (`retriever.py:84`), not at write — persisted summaries retain first 250 chars raw (gate L118) ✏️. E10.2/3 should pre-sanitize or accept this and note it.
- Ingestion endpoint should set `is_safety_critical=False` (survey corrections are not allergies) and explicit category hints to keep gate behavior predictable. ◻️ Exception: a survey response confirming a dietary allergy SHOULD set `is_safety_critical=True` (infinite half-life, matching the `/remember` precedent at `customer_memory.py:255-264`).
- DSAR/erasure: memory-side erasure covers loop writes automatically; the trip-embedded `survey_id` stub remains after entity erasure — retention-policy note stands.

---

## 5. Sized next tasks (updated)

1. **E10.0 (S, new):** Scorecard honesty — `get_supplier_scorecard` currently returns invented data presented as agency analytics. Either label demo/badge it, or source it from real survey responses once E10.2 exists. Group with I-6 honesty family.
2. **E10.1 (S):** Survey trigger stops emitting fabricated URL (badge or omit); also fix `survey_id` collision window (use trip_id + full timestamp/uuid).
3. **E10.2 (M):** Survey-response ingestion endpoint: `POST /feedback/{trip_id}/response` accepting ratings + free text; canonical auth dependency; persists to `trip["post_trip_feedback"]` (status SUBMITTED) + audit. Validates shape; rejects re-submission.
4. **E10.3 (M):** `FeedbackMemoryBridge` — maps response/scorecard events → `ingest_memory` per the §2 table. First store change: add optional `half_life_days` parameter to `ingest_memory` (store.py:135) so per-class decay is expressible.
5. **E10.4 (S):** Supplier-scorecard → supplier-scoped memory writes (outcome class), traveler and supplier `entity_id` namespaces kept distinct (e.g. `cust_*` vs `supp_*`).
6. **E10.5 (L, gated on F-13):** Trust-weighting at `retriever.py:70` by `source_type`/confidence + migrate `hydrate_trip_with_customer_memory` to read `MemoryStore` (kills the legacy-dict bypass).
7. **E10.6 (S):** Tests: gate-rejection paths for never-write class; supersession when a later trip contradicts an earlier preference; decay-curve assertions (90d implicit fading, 730d correction persistence). Extend `tests/test_agent_memory_architecture.py`; no feedback tests exist today (verified).

## Decision needed

1. Ratify the deepened event-class table — especially concrete confidences (0.9/0.7 survey; 0.75 supplier; 0.75-floor implicit) and half-lives (730/365/90).
2. Sequence: build E10.2/3 in shadow (write-but-don't-influence until F-13) vs hold the loop behind F-13. Recommend shadow — writes are inert until retrieval is trust-weighted, and §1e shows they're inert *now* anyway (hydrate ignores the durable store).
3. Supplier-scorecard memory: separate supplier entity namespace (recommended: `supp_*` entity_id, no schema change) vs agency-level aggregate only?
4. ◻️ Should supplier-outcome confidence scale with sample size (e.g. `min(0.9, 0.6 + 0.05*reviews)`), or stay flat 0.75 per observation with aggregation left to retrieval weighting? Flat-first is simpler and avoids gate-threshold coupling; scaling is more honest. Recommend flat 0.75 + E10.5 weighting.
