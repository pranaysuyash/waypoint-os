# EX-DEMO-03 — Packet Coverage & Confidence/Authority Audit (Tool-Taster Demo Note)

*Date: 2026-08-31*
*Covers: DEMO-10 (full packet coverage unknown) and DEMO-11 (confidence/authority labeling oddity) from `Docs/exploration/DEMO_FOLLOWUP_TASK_BRIEFS_2026-08-31.md`.*
*Method: read-only, in-process empirical run on the exact demo note. Zero persistence (no trips, no leads, no DB rows, no store calls — see Method).*
*Checklist applied: IMPLEMENTATION_AGENT_REVIEW_HANDOFF_CHECKLIST.md*

---

## 1. Executive Summary

1. The packet captured **16 facts + 3 derived signals** — far more than the 5 fields the demo UI showed. Beyond the visible fields, it DID capture: `meal_preferences="vegetarian"` @0.8, `trip_priorities=["vegetarian food"]` @0.8, and `hard_constraints=["cable cars please", "idea of the name"]` @0.8 (the fear constraint, but polluted by a false positive from "no idea of the name").
2. **Hard misses** (nothing captured): Japan + tokyo/kyoto/osaka, dates ("next spring, maybe late march"), trip duration (10-12 days), purpose (cherry blossoms), activity wish (cooking class), date flexibility ("dates flexible plus or minus a week"), accommodation hint (unnamed ryokan), "pretty active" fitness level, "not sure if that includes flights".
3. **Silently WRONG captures** (worse than missing): `party_size=1` @0.9 explicit_user (real: 4); `budget_scope="total"` @0.7 explicit_user (real: per-person — "3.5k USD **each**"); `destination_status="open"` triggered by "somewhere" in the unrelated activity clause "cooking class somewhere".
4. **Confidence/authority verdict: MISLABELED, systemic.** Every freeform extractor stamps `authority=explicit_user` + epistemic `FACT` regardless of whether the value was literally asserted or pattern-inferred/defaulted. `destination_status "open" @80% explicit_user` is doubly wrong: the value is spurious AND its own evidence excerpt says "Derived from destination text" while claiming explicit_user authority.
5. **Classification:** destination/date/party/budget-scope/date-flex misses are **extractor gaps on existing fields** (fields + enums exist; colloquial phrasings don't match). Accommodation wish, structured fear/fitness constraints, trip duration, and date-flex window magnitude are **schema gaps** (no field exists).
6. Highest business value: party=4 + per-person budget scope (a 4x quote-amount error), destinations (blocks NB01 → everything downstream), then suitability-aware fear constraints.

---

## 2. Full Packet Schema (cited)

Canonical model: `src/intake/packet_models.py` (self-declared "single source of truth", line 4).

### 2.1 CanonicalPacket v0.3 — `packet_models.py:417-466`
| Layer | Type | Lines |
|---|---|---|
| `facts` / `derived_signals` / `hypotheses` | `Dict[str, Slot]` — open-world; there is NO closed enumeration of fact keys in the model. Coverage is defined by extractor write-sites. | 441-443 |
| `lifecycle` | `LifecycleInfo` (lead status, engagement, payment stage — 30+ fields) | 253-296, 444 |
| `raw_note`, `feedback`, `stage`, `operating_mode`, `decision_state`, `schema_version`, `packet_id` | metadata | 429-446 |
| `suitability_flags` | `List[SuitabilityFlag]` (flag_type, severity, confidence, affected_travelers) | 29-37, 449 |
| `ambiguities` | `List[Ambiguity]` | 452 |
| `unknowns` | `List[UnknownField]` (reason: not_present_in_source \| not_extracted_yet \| extraction_failed \| intentionally_unknown) | 184-190, 453 |
| `contradictions` (lifecycle: detected→open→resolved) | 599-694, 454 |
| `assumptions` | `List[AssumptionRecord]` (slot_name, assumed_value, rationale, criticality) | 99-119, 463 |
| `metadata`, `events`/`event_cursor` (auto-audited mutations via `_EventTrackingDict`) | 342-392, 459-466 |

### 2.2 Slot — `packet_models.py:150-181`
`value, confidence, authority_level, extraction_mode, evidence_refs[EvidenceRef], derived_from, updated_at, notes, maturity (stub|heuristic|verified), epistemic_status (FACT|INFERRED|ASSUMED|UNKNOWN)`.

### 2.3 Authority + epistemic semantics
- `AuthorityLevel`: 7 ranked levels — `manual_override > explicit_user > imported_structured > explicit_owner > derived_signal > soft_hypothesis > unknown` (`packet_models.py:44-67`). `set_fact` REJECTS non-fact authority (`packet_models.py:503-507`); inferred values must go through `set_derived_signal` (549-556) / `set_hypothesis` (558-568).
- `EpistemicStatus`: FACT (explicitly stated) / INFERRED (extracted by NLP or derived >0.85) / ASSUMED (system default or heuristic) / UNKNOWN (`packet_models.py:91-96`). Mapping authority→epistemic at `extractors.py:1829-1842`.

### 2.4 Fact keys the extraction pipeline can write (the de-facto schema)
Source: `rg 'set_fact\(' src/intake/extractors.py` + intent/passport/plan dicts.

- **Destination**: `destination_candidates`, `destination_status` (`extractors.py:1868-1935`)
- **Dates**: `date_window`, `date_start`, `date_end`, `date_confidence` (1937-1955); `date_flexibility` (1979-1984, enum firm/flexible/moderate — `extractors.py:1085-1104`)
- **Budget**: `budget_raw_text`, `budget_min`, `budget_max`, `budget_currency` (1957-1977); `budget_flexibility` (1986-1995); `budget_scope` enum per_person/per_night/daily/total (1119-1129, 1997-2006); `budget_soft_ceiling` (2031-2036)
- **Party**: `party_size`, `party_composition`, `child_ages` (2038-2054; extractor 1238-1357)
- **Origin**: `origin_city` (2056-2139, 4 strategies)
- **Constraints**: `mobility_constraints`, `medical_constraints` (2141-2154)
- **Trip intent** (`_extract_trip_intent`, 1364-1504): `trip_purpose`, `activity_interests`, `trip_style`, `hotel_preferences`, `meal_preferences`, `hard_constraints`, `soft_preferences`, `trip_priorities`
- **Owner/agency**: `owner_constraints`, `agency_notes`, `customer_id` (1511-1552); `sub_groups` (1559-1581); `coordinator_id` (2247-2252)
- **Logistics signals**: `rooming_list_count/requested/requirements`, `procurement_share_needed/notes` (2170-2222)
- **Documents** (stage-gated): `passport_status`, `visa_status`, `visa_concerns_present` (1654-1736)
- **Traveler plan**: `traveler_plan`, `existing_itinerary` (1743-1768); `past_trips` (2283-2290)
- **Derived-only fields** (never facts, `validation.py:27-43`): `domestic_or_international`, `urgency`, `sourcing_path`, `is_repeat_customer`, `internal_data_present`, `budget_feasibility`, etc.
- **Gates**: `INTAKE_MINIMUM = [destination_candidates, date_window]` (`validation.py:46-49`); `QUOTE_READY` = 6 fields incl. `origin_city, party_size, budget_raw_text, trip_purpose` (`validation.py:52-59`).

**Notable absences (schema):** no accommodation-wish/preference field beyond star-rating `hotel_preferences`; no trip-duration field; no structured fear/phobia or fitness-level field (only free-text `hard_constraints`); no country-vs-city destination structure (flat list); no date-flex window magnitude; no flights-included budget dimension.

---

## 3. Method (exactly what was run)

Read-only, in-process, mirroring the production path:

1. Envelope construction identical to `spine_api/server.py:1520-1526` (the workbench pastes into `raw_note`): `SourceEnvelope.from_freeform(NOTE, "agency_notes", "agent")`.
2. Packet build identical to Phase 1 of `run_spine_once` (`src/intake/orchestration.py:247-263`): `ExtractionPipeline().extract([envelope], stage="discovery")` — **called directly**, NOT via `run_spine_once`.
3. `validate_packet(packet, stage="discovery")` (pure, `src/intake/validation.py`).
4. Edge-case probes of `_extract_destination_candidates`, `_extract_date_flexibility`, `_extract_budget`, `_extract_budget_scope`, `_extract_party`, `Normalizer.detect_ambiguities` on the note.

**Safety:** `run_spine_once` was deliberately NOT invoked because it emits audit events via `TripEventLogger.log_stage_transition` (`orchestration.py:84-128`) — a persistence side effect. `ExtractionPipeline.extract()` and `validate_packet()` are pure in-memory functions (verified by reading their bodies: no store, no file I/O, no logger writes). `TRIPSTORE_BACKEND=sql` untouched; no trips/leads created. The scratch runner script was deleted after the run; only this doc was created.

**Contract validation:** the run reproduces the demo's visible UI state exactly (Destinations `-`, Destination Status open @0.80, budget_raw_text @0.80, min/max 3500 @0.90, Party 1) — confirming the in-process path is the same contract the UI rendered.

---

## 4. Coverage Matrix (complete output of the run + required dimensions)

### 4.1 What the packet actually contains (full capture)

| # | Field (layer) | Value | Conf | Authority | Epistemic | Verdict |
|---|---|---|---|---|---|---|
| 1 | `destination_candidates` | `[]` | 0.50 | explicit_user | FACT | **MISS** — "japan", "tokyo + kyoto + osaka" never captured |
| 2 | `destination_status` | `"open"` | 0.80 | explicit_user | FACT | **MISLABELED + spurious** — trigger is "somewhere" in "cooking class somewhere" (§5) |
| 3 | `budget_raw_text` | `"budget around 3.5k usd"` | 0.80 | explicit_user | FACT | HIT |
| 4 | `budget_min` | `3500` | 0.90 | explicit_user | FACT | HIT |
| 5 | `budget_max` | `3500` | 0.90 | explicit_user | FACT | HIT (point budget; "around" collapsed to min==max — defensible but lossy) |
| 6 | `budget_currency` | `"USD"` | 0.90 | explicit_user | FACT | HIT |
| 7 | `budget_flexibility` | `"soft"` | 0.85 | explicit_user | FACT | **MISLABELED** — system default (unmarked budget ⇒ soft, `extractors.py:1988-1995`), not user-stated |
| 8 | `budget_scope` | `"total"` | 0.70 | explicit_user | FACT | **WRONG** — "3.5k USD **each**" = per-person; default flipped it to trip-total (§4.2 row 7) |
| 9 | `party_size` | `1` | 0.90 | explicit_user | FACT | **WRONG** — "me and 3 friends" = 4 (§4.2 row 1) |
| 10 | `party_composition` | `{"adults": 1}` | 0.85 | explicit_user | FACT | **WRONG** — same cause |
| 11 | `origin_city` | `"SF"` | 0.90 | explicit_user | FACT | HIT ("from SF.", `extractors.py:2092-2120`; not normalized to San Francisco, but geography resolved origin_country=US) |
| 12 | `meal_preferences` | `"vegetarian"` | 0.80 | explicit_user | FACT | **HIT** (beyond what UI showed) |
| 13 | `hard_constraints` | `["cable cars please", "idea of the name"]` | 0.80 | explicit_user | FACT | **PARTIAL** — fear constraint captured, but false positive "idea of the name" from "no idea of the name" (`extractors.py:1436-1442` `no\s+(...)` pattern) |
| 14 | `soft_preferences` | `["to do japan next spring"]` | 0.80 | explicit_user | FACT | **False positive** — from "want to do japan next spring" (`extractors.py:1445-1455`); ironically the destination survives only here, as prose |
| 15 | `trip_priorities` | `["vegetarian food"]` | 0.80 | explicit_user | FACT | HIT-ish |
| 16 | `traveler_plan` | `"nothing_booked"` | 0.85 | explicit_user | FACT | Default, harmless |
| d1 | `derived: domestic_or_international` | `"unknown"` | 0.30 | derived_signal | INFERRED | Correct semantics (can't classify with empty destinations) |
| d2 | `derived: internal_data_present` | `true` | 1.00 | derived_signal | INFERRED | OK (ambiguity present) |
| d3 | `derived: sourcing_path` | `"open_market"` | 0.70 | derived_signal | INFERRED | OK |
| a1 | `ambiguities[0]` | `destination_candidates / value_vague` @0.8, raw_value = first 80 chars of note | — | — | — | Weak signal; raw_value is an arbitrary prefix because `_extract_relevant_span(text, "")` matches at index 0 when `dest_raw=None` (`extractors.py:373-384`, 1912) |
| u1 | `unknowns` | `date_window` (not_present_in_source), `trip_purpose` (not_present_in_source) | — | — | — | Matches the demo's "Blocked: Travel Dates, Trip Purpose" |
| — | `suitability_flags` | 0 flags | — | — | — | Fear constraint invisible to suitability (§4.2 row 3) |

Also recorded in-run: `operating_mode="normal_intake"`, 22 packet events, 1 contradiction: none, hypotheses: none.

### 4.2 Required dimensions (mission list)

| Dimension | In schema? | Captured? | What happened | Verdict |
|---|---|---|---|---|
| Party = 4 ("me and 3 friends") | Yes (`party_size`, `party_composition`) | No — captured as 1 @0.9 | `_extract_party` (`extractors.py:1248-1257`) credits "me" → adults:1; **no pattern for "N friends"**; `_PEOPLE_RE`/`_ADULTS_RE` need "N people/adults" phrasing | **Extractor gap, silently wrong** |
| Dietary (vegetarian) | Yes (`meal_preferences`, `trip_priorities`) | **Yes** @0.8 ×2 | `(?:vegetarian|vegan|jain|halal|kosher...)` (`extractors.py:1430-1432`, 1475) | **HIT** (but invisible in demo UI) |
| Fear constraint (terrified of heights → no cable cars) | Partial (free-text `hard_constraints`; no structured fear field) | Partially — `hard_constraints=["cable cars please", "idea of the name"]` | `no\s+([^.,]+)` over-matches; "terrified of heights" itself dropped; `suitability_flags=0` (nothing structured to feed `assess_activity_suitability`, `orchestration.py:411-436`) | **Extractor gap (noise) + schema gap (structured fear/phobia)** |
| Activity wish (cooking class) | Yes (`activity_interests`) | No | `activity_interests` patterns cover only sightseeing/beach-time/business-offsite (`extractors.py:1399-1410`); "wanna do a cooking class" matches nothing ("wanna" also invisible to soft_preferences `(?:want|prefer|like...)`) | **Extractor gap** |
| Accommodation hint (unnamed ryokan from TikTok) | **No** — no accommodation-wish field; `hotel_preferences` only matches "3/4/5-star resort/hotel" | No | No ryokan/lodging/inspiration-source concept anywhere in `src/intake/` (rg confirmed) | **Schema gap** |
| Flexible date window (±1 week) | Partial (`date_flexibility` enum firm/flexible/moderate — no window magnitude) | No | Probe: `_extract_date_flexibility("dates flexible plus or minus a week")` → `None`. Phrase list (`extractors.py:1093-1099`) has "flexible dates"/"dates are flexible" but **not bare "dates flexible"**; "+/-"/"plus minus" listed but note says "plus or minus" | **Extractor gap (phrase) + schema gap (window size)** |
| Per-person vs total budget ("3.5k USD each") | Yes (`budget_scope`) | **Worse than missing — mis-scoped to `"total"` @0.7** | `_extract_budget_scope` (`extractors.py:1119-1129`) recognizes only "per person"/"per head"/"per night"/"a day"/total-markers; "each"/"a head"/"pp" unrecognized → falls to default `unknown → total` (`extractors.py:1997-2006`) | **Extractor gap, silently wrong** |
| Flights-included ambiguity ("not sure if that includes flights") | Ambiguity type `budget_unclear_scope` exists (`packet_models.py:214`) but no budget field models flight inclusion | No | `budget_unclear_scope` never fired: budget ambiguity detection only runs on stretch-gated text (`extractors.py:2022-2028`) and Normalizer didn't flag it either | **Extractor gap for the signal; minor schema extension for a tri-state `budget_includes_flights`** |
| Destinations ("do japan"; "tokyo + kyoto + osaka") | Yes (`destination_candidates`) | No | "do japan": "do" not in `_TRAVEL_VERB_DEST_RE` verb list (`extractors.py:119-124`); "thinking tokyo" fails `_HEDGING_RE` which requires "thinking about" (`extractors.py:223-226`); lowercase "tokyo/kyoto/osaka" unreachable by capitalized `_DESTINATION_RE` (`extractors.py:109-111`) and not after any travel verb; note has no country+city structure (flat list only) | **Extractor gap (+ DEMO-12 modeling question)** |
| Dates ("next spring", "maybe late march") | Yes (`date_window`/`date_start`/`date_end`) | No | "maybe late march": `_MAYBE_RE` grabs "late" (not a destination; no date equivalent); `_SINGLE_MONTH_NO_YEAR_RE` needs "(in\|during\|for) March" (`extractors.py:170-174`); `_FUZZY_MONTH_RE` needs "around/sometime in/during" (`extractors.py:182-185`); "next spring" has no pattern at all | **Extractor gap** |
| Trip duration ("10-12 days") | **No duration field** (would have to become date_start/end, impossible without a month anchor) | No | — | **Schema gap** |
| Purpose (cherry blossoms / sightseeing spring trip) | Yes (`trip_purpose`) | No | Purpose patterns (`extractors.py:1370-1382`) don't include cherry-blossom/spring-travel; "cultural" needs the word | **Extractor gap** |
| Fitness level ("pretty active") | **No field** | No | — | **Schema gap** (feeds suitability) |
| Origin ("flying from SF") | Yes | **Yes** @0.9 | — | **HIT** |
| Channel metadata | Yes (`SourceEnvelope` source_system/actor_type, `packet_models.py:303-335`) | Yes (agency_notes/agent) | — | HIT |

---

## 5. Confidence/Authority Audit (DEMO-11)

**Where labels are assigned:** every freeform extraction funnels through `ExtractionPipeline._make_slot` (`extractors.py:1844-1861`), which maps authority→epistemic via `_epistemic_for_authority` (`extractors.py:1829-1842`): `explicit_user ⇒ FACT`. All ~25 freeform extraction call-sites in `_extract_from_freeform` (`extractors.py:1863-2290`) pass `AuthorityLevel.EXPLICIT_USER` unconditionally — whether the value is a literal user assertion (`"budget around 3.5k usd"`), a pattern inference (`party_size=1` from "me"), or a **system default** (`budget_flexibility="soft"`, `budget_scope="total"`).

**The specific oddity:** `destination_status="open" @0.80 authority=explicit_user, epistemic=FACT`, evidence excerpt = **"Derived from destination text"** (`extractors.py:1895-1898`).

Root cause chain, verified by probe:
1. `_extract_destination_candidates` finds no candidates ("do japan"/lowercase city list defeat every pattern) and hits the terminal fallback `extractors.py:721`: `return [], "open" if ("somewhere" in text_lower or "any" in text_lower) else "undecided", None`. The note contains "somewhere" — in **"we also wanna do a cooking class somewhere"**, an activity clause. Probe 1-3 confirmed: candidates `([], 'open', None)`; "somewhere" present; "any" absent.
2. The pipeline then writes `destination_status="open"` with confidence 0.8 and `explicit_user` (`extractors.py:1878-1898`), with the canned excerpt "Derived from destination text".

**Verdict: MISLABELED — on two independent axes.**
- **Authority-axis:** the value is *derived by pattern*, not stated by the user. By the codebase's own semantics (`packet_models.py:44-67`, `91-96`), derived-by-NLP should be `derived_signal`/`INFERRED`. Labeling a derivation `explicit_user/FACT` inverts the authority ladder. The slot's own excerpt admits it ("Derived from destination text").
- **Truth-axis:** the value is spurious. No user statement about destination openness exists; "open" was triggered by an unrelated word. When no candidates are found, the honest packet state is `unknowns` + the (already-present) `value_vague` ambiguity — not a confident FACT.

Same defect class, same run:
- `budget_flexibility="soft"` @0.85 explicit_user — golden-convention default (`extractors.py:1988-1995`), should be `ASSUMED`.
- `budget_scope="total"` @0.7 explicit_user — default-derived AND wrong, should be `ASSUMED` (and fixed).
- `party_size=1` @0.9 explicit_user — pattern-inferred from "me" with the "3 friends" half of the sentence ignored; at minimum `INFERRED`, ideally with a validation warning (Pattern 5: clamp/warn, never silently wrong).

**Not wrong:** the per-field transparency UX (confidence + authority per field) is exactly the right design — the label *vocabulary* is what's broken. Also correctly labeled: all three `derived_signals` used `derived_signal/INFERRED` — proving the machinery exists and is simply not used on the facts path.

**Recommendation (minimal, non-breaking):** `Slot` already supports an explicit `epistemic_status` override (`packet_models.py:163-164`, `extractors.py:1846`), and `set_fact` only gates on *authority*, not epistemic status (`packet_models.py:503-507`). So: keep fact-tier authority for routing/MVB compatibility, but pass `epistemic_status=ASSUMED` for default-filled values and `INFERRED` for pattern-inferred ones, and render epistemic status in the Trip Details table next to authority. Reserve `explicit_user/FACT` for values whose evidence excerpt is a verbatim user span (enforceable: excerpt must equal the matched source span, never a canned string like "Derived from destination text").

---

## 6. Schema-Gap vs Extractor-Gap Classification

**Extractor gaps (field exists; phrasing/logic doesn't):**
1. Destinations: "do japan" verb-object; lowercase "tokyo + kyoto + osaka"; "thinking X" hedge (no "about").
2. Party: "me and N friends" / "the N of us" group phrasings.
3. Dates: "next spring", "late march" (bare month without in/during/for), relative-season windows.
4. `date_flexibility`: "dates flexible" (bare inverted form); "plus or minus" spelled out.
5. `budget_scope`: "each", "a head", "pp" → per_person. (Highest-severity extractor gap: silently wrong today.)
6. `hard_constraints` noise: `no\s+(...)` captures "idea of the name" from "no idea".
7. `activity_interests`: only 3 signal patterns; "cooking class" (and "wanna") uncovered.
8. `budget_unclear_scope` ambiguity never fires for "not sure if that includes flights".

**Schema gaps (no field anywhere in the packet shape):**
1. Accommodation wish/preference incl. inspiration source ("ryokan seen on TikTok") — high commercial value for hotel sourcing.
2. Trip duration ("10-12 days") — a primary pricing driver.
3. Structured fear/phobia & fitness level ("terrified of heights", "pretty active") — needed so `assess_activity_suitability` can act (today: 0 flags).
4. Date-flexibility window magnitude ("±1 week") — current enum is only firm/flexible/moderate.
5. Budget flight-inclusion tri-state (included / not included / unknown).
6. Country-vs-city destination structure (DEMO-12): flat `destination_candidates` cannot represent {country: Japan, cities: [Tokyo, Kyoto, Osaka]}.

---

## 7. Recommendations (prioritized by quote-context business value)

1. **P0 — Silent-wrong fixes (correctness before coverage):** (a) party under-detection emits a validation warning when composition cites "me/friends" but count stays 1 (aligns with IMP-02/Pattern 5); (b) `budget_scope` recognizes "each/a head/pp" → `per_person`; (c) stop writing `destination_status="open"` from the generic "somewhere/any" fallback when the "somewhere" is not in a destination clause — emit unknown + ambiguity instead. A quote built on party=1/total=3.5k when the truth is 4 pax × per-person is a 4x commercial error.
2. **P1 — Colloquial extraction pass** (feeds IMP-02 + IMP-07 fixture manifest): destinations ("do/hit X", lowercase city triads, "thinking X"), party ("me and N friends", "N of us"), dates ("next spring", "late march"), `date_flexibility` ("dates flexible", "plus or minus"). All are extractor-side; fields already exist. Fixtures from this note go into the F-18/D6 eval set, not ad-hoc patterns.
3. **P1 — Authority/epistemic relabel** (DEMO-11): per §5 — `epistemic_status=INFERRED/ASSUMED` on pattern-inferred/defaulted fact slots + UI render; forbid canned evidence excerpts on `explicit_user` slots. Low cost, high trust payoff ("honest gauges" is the demo's praised differentiator — make the labels honest too).
4. **P2 — Surface captured-but-hidden fields:** `meal_preferences`, `hard_constraints`, `trip_priorities` were in the packet but absent from the demo's Trip Details table. The "wow moment" was already computed; the UI just didn't show it. (UI surfacing, no extraction change.)
5. **P2 — Schema additions:** `accommodation_wish` (text + inspiration source + known/unknown flag), `duration_days` (min/max), structured `traveler_constraints` entry point for fear/phobia → suitability wiring, `date_flex_window_days`, `budget_includes_flights` tri-state. Each is additive to `facts` (open-world dict) + a JSON-schema/spec mirror update (`specs/canonical_packet.schema.json`).
6. **P3 — Dedup noise:** `hard_constraints` regex should require the negation to bind to a service/activity noun, not "no idea/no problem/no rush".

---

## 8. Effort Estimate

| Item | Size | Notes |
|---|---|---|
| Silent-wrong fixes (party warning, budget scope, destination_status guard) | 1-2 dev-days | Extractor + validation warning + tests |
| Authority/epistemic relabel + UI render | 1-2 dev-days | `_make_slot` call-site audit (~25 sites); Slot already supports override |
| Colloquial extractor pass + fixtures + eval wiring | 3-5 dev-days | Overlaps IMP-02/IMP-07 scope |
| UI surfacing of hidden captured fields | 1 dev-day | Trip Details renderer subset |
| Schema additions (5 fields) + spec mirror + extractors + tests | 3-5 dev-days | Additive; open-world facts dict keeps migration trivial |
| **Total** | **~9-15 dev-days** | Sequenced 1→6; items 1-4 unblock the demo loop on their own |

---

## 9. Open Questions for Pranay

1. **Authority semantics:** Should `explicit_user` be reserved for verbatim-stated values, with pattern-inferred values moved to `derived_signals` (out of `facts`) or kept in facts with `epistemic_status=INFERRED`? Moving them out of facts changes MVB gating that counts `field in packet.facts` (`validation.py:113-122`) — a contract decision, not just cosmetics.
2. **`destination_status` lifecycle:** keep as a derived enum with a fixed trigger, or drop the slot entirely when no candidates exist (unknown + ambiguity only)?
3. **Country+city modeling (DEMO-12):** structured `{country, cities[]}` vs flat list + a separate `destination_countries` slot?
4. **Silent-wrong policy:** should mis-scoped budget / under-counted party *block* quoting (error) or warn? (Pattern 5 currently argues warn-and-preserve.)
5. **Trip Details UI subset:** is the 6-field table intentional, or should all non-empty facts render (which would have shown vegetarian + no-cable-cars in the demo)?

---

*Evidence artifacts: complete in-process packet dump reproduced in §4.1; probes documented in §5. No product code, tests, fixtures, or data were modified. No git writes.*
