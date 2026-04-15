# Session Writeup: Destination Ambiguity Investigation and Spine Hardening

**Date**: 2026-04-15
**Session Start Context**: User asked to verify prior findings about gaps between NB01/NB02/NB03 contract and implementation

---

## 1. Original Task

User asked: "Check if these findings are still correct" and provided a detailed list of prior findings about:

- `03_session_strategy_contract.md` being the canonical design doc
- `strategy.py` implementing that contract
- `decision.py` supporting the upstream structure
- 5 known gaps/contradictions (ambiguous destinations, last-minute soft blockers, budget stretch signal, multi-source authority, corporate/urgency blockers)
- 4 unresolved questions (runtime path correctness, NB02 branch metadata, open gaps status, modified local files)
- The immediate blocker being design ambiguity in contract vs implementation

The user then said: "and what we need to do" — asking for action, not just verification.

---

## 2. Initial Verification Phase

### What was verified against the codebase

1. **`03_session_strategy_contract.md`** is still canonical — confirmed. Defines all 5 decision states, question ordering, branch rules, traveler-safe boundary.

2. **`strategy.py`** still implements the contract — confirmed. Has `build_session_strategy`, `build_traveler_safe_bundle`, `build_internal_bundle`, question sorting, branch framing, tone scaling, leakage enforcement via `safety.py`.

3. **`decision.py`** still supports upstream — confirmed. DecisionResult has hard/soft_blockers, ambiguities, contradictions, urgency handling, MVB-by-stage structure.

4. **`NB03_V02_SPEC.md`** exists at `notebooks/NB03_V02_SPEC.md` — 299 lines covering full spec including operating-mode matrix, structural sanitization, question intent model, branch-quality rules, 16 test requirements.

5. **`safety.py`** implements structural sanitization — `sanitize_for_traveler()`, `SanitizedPacketView`, `check_no_leakage()`, `enforce_no_leakage()`, `FORBIDDEN_TRAVELER_CONCEPTS`, `INTERNAL_ONLY_FIELDS`.

### Updated gap status

| Gap | Original Status | Updated Status |
|-----|----------------|----------------|
| 1. Ambiguous destination ("Andaman or Sri Lanka") treated as valid | Open | **CONFIRMED BUG** — two distinct failure modes found |
| 2. Last-minute trips still get soft blockers | Open | **Partially resolved** — `decision.py:apply_urgency()` suppresses when urgency="high", but only if NB02's urgency signal is correct |
| 3. Budget stretch signal ("200000 can stretch") loses signal | Open | **Still open** — severity entry exists as advisory but signal not preserved in question generation |
| 4. Multi-source authority not surfaced | Open | **Still open** — sources listed but not paired with values (who said what) |
| 5. Corporate/urgency-specific blockers not in MVB | Open | **Still open** — MVB has no corporate-specific entries |
| `audience="both"` sets bundle.audience="traveler" | Question | **Confirmed minor bug** — misleading but not data-leaking |
| NB02 branch prompts lack trade-off summaries | Question | **Confirmed** — only label/description/approach, missing pros/cons/budget/timeline |

---

## 3. The Critical Discussion: Which Layer Owns the Fix?

### Original finding said

> "NB03 mitigation: If destination value contains 'or' or 'maybe', add a clarification question even if NB02 said PROCEED_TRAVELER_SAFE."

This implied the fix should go in NB03 (strategy.py) as an override.

### User pushback #1

> "But shouldn't we mitigate NB02 itself? So your override is better I think."

I proposed an NB02 override that would synthesize the ambiguity in `run_gap_and_decision()`. User agreed this was better than NB03.

### User pushback #2 (the key architectural correction)

> "Don't do as I say, do what's better architecture. Override was NB02, wasn't it?"

This forced me to think properly. The correct answer is **NB01 is the root cause layer**. Here's the reasoning:

- NB01 owns **truth capture and normalization** (per V02_GOVERNING_PRINCIPLES.md)
- NB01's `ExtractionPipeline` extracts "Andaman or Sri Lanka" as `["Andaman", "Sri Lanka"]` with `status="semi_open"` and creates an `unresolved_alternatives` Ambiguity object
- In the **normal path** (raw text through NB01), this works correctly — NB02 sees the ambiguity, classifies it as blocking, outputs ASK_FOLLOWUP
- The **bug** is when the Ambiguity object is absent (structured import, API call, edge case in extraction) — then NB02 treats `destination_candidates=["Andaman", "Sri Lanka"]` as "filled" and says PROCEED_TRAVELER_SAFE
- NB02 doesn't inspect the **value structure** — it only checks if the Ambiguity object exists
- NB03 shouldn't re-classify decisions — it's the presentation layer

**Decision**: Fix at NB01 (value-structural ambiguity synthesis) + NB02 (defense-in-depth), not NB03 (override). The contract was wrong about which layer owns this.

### User pushback #3

> "So based on everything, don't you think we should look at the post-freeze rules? Phase A / Phase B?"

This led to examining the architecture docs and recognizing that the regex-based extraction has a quality ceiling that affects the entire product flow.

---

## 4. Root Cause Investigation (Following Investigate Skill Methodology)

### Iron Law: No fixes without root cause investigation

Traced the full data flow for "Andaman or Sri Lanka" through NB01 → NB02 → NB03 with concrete Python execution:

**Normal path (works):**
```
NB01: dest_candidates=["Andaman", "Sri Lanka"], status=semi_open
      + Ambiguity(unresolved_alternatives, raw="Andaman or Sri Lanka")
NB02: ambiguity → blocking → ASK_FOLLOWUP ✓
NB03: "Where would you like to go?" (generic, but correct decision) ✓
```

**Broken path (Bug A):**
```
NB01: dest_candidates=["Andaman", "Sri Lanka"] (via structured import)
      NO Ambiguity objects
NB02: field "filled" (list exists with fact authority) → PROCEED_TRAVELER_SAFE ✗
NB03: Presents proposal as if destination is resolved, to a traveler who hasn't chosen ✗
```

**Broken path (Bug B):**
```
NB01: Same as normal path
NB02: ASK_FOLLOWUP (correct)
      follow_up_questions: "Where would you like to go? (Any specific destinations or are you open?)"
      suggested_values: []  ← should be ["Andaman", "Sri Lanka"]
NB03: Traveler sees generic "where?" instead of "Between Andaman and Sri Lanka?" ✗
```

**Fresh verification revealed additional bugs:**
```
"maybe Singapore" → dest_candidates=["Singapore"], status=definite ✗ (should be semi_open)
"thinking about Singapore" → dest_candidates=["Singapore"], status=definite ✗
"We want to go somewhere nice" → dest_candidates=["We"], status=definite ✗
value_vague on destination_candidates → severity=advisory ✗ (should be blocking)
```

---

## 5. All Bugs Found and Fixed

### Bug A: Multi-candidate destination reaches PROCEED_TRAVELER_SAFE

**Symptom**: `destination_candidates=["Andaman", "Sri Lanka"]` with no Ambiguity objects → NB02 says PROCEED_TRAVELER_SAFE

**Root cause**: NB02's blocker evaluation checks if a field has a fact with sufficient authority, but doesn't inspect the value structure. A multi-element list IS structurally unresolved. NB01's text-pattern ambiguity detection works for raw text but fails when packets come from other sources.

**Fix** (two layers, defense-in-depth):
1. **NB01** (`extractors.py:752-767`): After text-pattern ambiguity detection, check if `dest_candidates` has 2+ items. If no `unresolved_alternatives` ambiguity was already flagged, synthesize one from the value structure. Catches cases the regex missed.
2. **NB02** (`decision.py:939-940`): `_synthesize_destination_ambiguity()` runs before blocker evaluation. If `destination_candidates` has 2+ values but no blocking ambiguity, synthesizes one in-place. Catches packets that bypassed NB01 entirely (structured imports, API calls).

**Files**: `src/intake/extractors.py`, `src/intake/decision.py`

### Bug B: Generic question instead of "Between X and Y?"

**Symptom**: "Andaman or Sri Lanka" → question is "Where would you like to go?" with empty suggested_values

**Root cause**: NB02's `generate_question()` (decision.py:912-926) uses static template strings. The `destination_candidates` template is a generic "Where would you like to go?" even when candidate values are available in the packet.

**Fix** (`decision.py:1064-1082, 1108-1122`): When generating follow-up questions for `destination_candidates` with unresolved alternatives, use candidate values from the packet to produce "Between X and Y, which are you leaning toward?" and populate `suggested_values`.

**Files**: `src/intake/decision.py`

### Bug C: "maybe Singapore" extracted as `definite` instead of `semi_open`

**Symptom**: `ExtractionPipeline.extract("maybe Singapore from Bangalore...")` → `dest_candidates=["Singapore"], status=definite, confidence=0.5`

**Root cause**: `_extract_destination_candidates()` (extractors.py) checks the single-destination regex BEFORE the "maybe" regex. "Singapore" matches the general regex, returns `(["Singapore"], "definite", "Singapore")`, and the "maybe" pattern on line 187-193 never executes.

**Fix** (`extractors.py:126-197`): Reordered extraction — "maybe" and "thinking about/perhaps/considering" patterns now checked BEFORE the general destination regex. "maybe Singapore" now returns `(["Singapore"], "semi_open", "maybe Singapore")`.

**Files**: `src/intake/extractors.py`

### Bug D: "We" extracted as a destination

**Symptom**: `_extract_destination_candidates("We want to go somewhere nice from Bangalore")` → `candidates=["We"], status=definite`

**Root cause**: `_DESTINATION_RE` matches "We" as a capitalized word. Either `is_known_destination("We")` returns True, or the check doesn't filter it.

**Fix** (`extractors.py:175-176`): Added `_DESTINATION_STOP_WORDS` set (`{"we", "i", "my", "our", "the", "this", "that", "it", "they", "he", "she", "us"}`). Filtered before `is_known_destination()`.

**Files**: `src/intake/extractors.py`

### Bug E: `value_vague` on destinations classified as `advisory` (should be `blocking`)

**Symptom**: Packet with `destination_candidates=["Singapore"]` + Ambiguity(value_vague, "maybe Singapore") + all blockers filled → PROCEED_TRAVELER_SAFE

**Root cause**: `AMBIGUITY_SEVERITY` table (decision.py:209-220) has no explicit entry for `("destination_candidates", "value_vague")`. Falls through to default "advisory". A hedged destination ("maybe Singapore") is functionally unconfirmed — should block progression.

**Fix** (`decision.py:211`): Added `("destination_candidates", "value_vague"): "blocking"` to `AMBIGUITY_SEVERITY`.

**Files**: `src/intake/decision.py`

---

## 6. Test Results

### Before fixes
- Bug A reproduction: `decision_state = PROCEED_TRAVELER_SAFE` ← wrong

### After fixes
All bugs verified fixed. Full test suite:

```
tests/test_nb01_v02.py — 25 passed (includes 7 new regression tests)
tests/test_nb02_v02.py — 23 passed (includes 4 new regression tests)
tests/test_nb03_v02.py — 38 passed
tests/test_e2e_freeze_pack.py — 35 passed
tests/test_decision_policy_conformance.py — 6 passed
Total: 127 passed, 0 failed, 22 skipped (spine API tests need server)
```

### New regression tests added

**`tests/test_nb01_v02.py::TestHedgingExtractionOrder`** (5 tests):
- `test_maybe_pattern_produces_semi_open`
- `test_thinking_about_pattern_produces_semi_open`
- `test_perhaps_pattern_produces_semi_open`
- `test_definite_destination_still_definite`
- `test_or_pattern_still_sem_open`

**`tests/test_nb01_v02.py::TestStopWordFilter`** (2 tests):
- `test_we_pronoun_filtered`
- `test_real_destination_after_pronoun`

**`tests/test_nb02_v02.py::TestDestinationAmbiguitySynthesis`** (4 tests):
- `test_multi_candidate_destination_never_proceeds_traveler_safe`
- `test_single_candidate_destination_no_synthesis`
- `test_existing_ambiguity_no_duplicate_synthesis`
- `test_candidate_aware_question_for_destination`

---

## 7. Documentation Created

| Document | Purpose |
|----------|---------|
| `Docs/travel_agency_process_issue_review_2026-04-15.md` | Gap 1 bug analysis (multi-candidate destination) — root cause, fix, tests |
| `Docs/destination_hedging_issue_review_2026-04-15.md` | Hedging extraction bugs — 3 bugs found, fixes, tests |

---

## 8. What Was NOT Fixed (Still Open from Original Findings)

| Gap | Status | Why Not Fixed |
|-----|--------|---------------|
| Budget stretch signal ("200000 can stretch") loses signal in question generation | Open | Different problem class — NB01 detects the ambiguity but NB02/NB03 don't preserve the stretch signal in question framing. Needs separate investigation. |
| Multi-source authority not surfaced (who said what) | Open | Contradictions carry `sources` as a flat list. Contract wants per-value source attribution. Architectural change to contradiction data model. |
| Corporate/urgency-specific blockers not in MVB | Open | Requires product decision on which fields to add per stage. |
| `audience="both"` sets bundle.audience="traveler" | Open | Minor — not data-leaking, just misleading. |
| NB02 branch prompts lack trade-off summaries | Open | `_build_branch_prompts` in strategy.py is minimal. Contract requires pros/cons/budget/timeline per branch. |
| "I want to maybe visit Singapore" → `definite` | Partially mitigated | The "maybe" regex only matches `\bmaybe\s+(\w+)` (word directly after "maybe"). Mid-sentence "maybe" is caught by Normalizer.detect_ambiguities → value_vague → now blocking. So it doesn't reach PROCEED_TRAVELER_SAFE, but the extraction status is still "definite" instead of "semi_open". |

---

## 9. Decision Points (For External Review)

### Decision 1: Which layer owns destination ambiguity detection?

**Options considered:**
- A) NB03 override — re-classify PROCEED_TRAVELER_SAFE → ASK_FOLLOWUP when destination has "or"/"maybe"
- B) NB02 synthesis — inspect packet value structure in `run_gap_and_decision()` and create ambiguity if missing
- C) NB01 value-structural synthesis — extract ambiguity from value structure, not just text patterns
- D) NB01 + NB02 defense-in-depth — both layers guarantee the invariant

**Chosen: D**

**Reasoning:**
- NB01 owns truth capture — it should guarantee that extracted values carry appropriate ambiguity signals
- NB02 owns judgment — it should validate NB01's output (trust but verify)
- NB03 owns presentation — it should NOT re-classify decisions; that breaks layer separation
- The contract (03_session_strategy_contract.md) says NB03 mitigates this, but the contract is wrong about which layer owns the concern

**Question for review**: Should the contract be updated to reflect that NB01/NB02 own this mitigation, not NB03? Or should NB03 also have a final safety check?

### Decision 2: Severity of `value_vague` on destination_candidates

**Options considered:**
- A) `blocking` — "maybe Singapore" must be confirmed before proceeding
- B) `advisory` — "maybe Singapore" is a hint, not a blocker; the destination is named
- C) Conditional severity — blocking at shortlist/proposal/booking, advisory at discovery

**Chosen: A (blocking)**

**Reasoning**: A hedged destination is functionally unconfirmed. If the system proceeds as if Singapore is locked in, it will produce options for Singapore that the traveler may reject entirely. The cost of an extra confirmation question is low; the cost of wrong-destination proposals is high (wasted sourcing, client confusion, trust erosion).

**Question for review**: Should there be a severity override at discovery stage where "maybe Singapore" could be advisory (they're just exploring)? Or is blocking always the right call?

### Decision 3: Extraction ordering — hedging patterns first or destination regex first?

**Options considered:**
- A) Keep current order (destination regex first, hedging patterns as fallback)
- B) Reorder (hedging patterns first, then destination regex)

**Chosen: B**

**Reasoning**: The "maybe" context is meaning-changing. "Singapore" and "maybe Singapore" are different extraction results. The regex that matches "Singapore" in "maybe Singapore" loses the hedging signal. Reordering preserves context in both the extraction status and the raw_match.

**Trade-off**: If we add more hedging patterns later, the list grows before the general regex. The general regex is the "catch-all" — it should always be last.

**Question for review**: What other hedging patterns exist in real traveler input? "Sort of X", "X probably", "X I guess", "not sure but X"? Should we expand the hedging detection?

### Decision 4: Stop words as a hardcoded set vs geography filter improvement

**Options considered:**
- A) Hardcoded `_DESTINATION_STOP_WORDS` set in extractors.py
- B) Fix `is_known_destination()` to return False for "We", "I", etc.
- C) Both

**Chosen: A (with implied C)**

**Reasoning**: `is_known_destination()` uses `geography.py` which checks against a curated destination list. "We" should never be in a geography database. The fact that it matched suggests either: (a) the geography list is too permissive, or (b) the capitalized-word regex matches before the geography check can filter. The stop-word list is a necessary input validation regardless. We should also check `is_known_destination("We")` to see why it passes.

**Question for review**: Should we audit `is_known_destination()` for other false positives? What's the actual check?

---

## 10. Implications for Post-Freeze Phases

### How the fixes connect to the product roadmap

The `FROZEN_SPINE_STATUS.md` post-freeze rules say:

- **Phase A (Now)**: UI/workbench on deterministic baseline. Only patch for real surfaced bugs.
- **Phase B (Later)**: Hybrid extraction track (regex baseline + NER/LLM merge)

The `PM_EXECUTION_BLUEPRINT_2026-04-14.md` Priority Backlog says:

- **P0(1)**: Parser-first (deterministic constraints) ← we just hardened this
- **P0(2)**: NER/IE second (semantic fill + disambiguation) ← Phase B
- **P0(5)**: Fallback strategy: deterministic parser > NER suggestion > regex fallback

### What the bugs exposed

The regex baseline has a quality ceiling. We patched 5 bugs, but the fundamental limitation remains:

| Input | Regex Result | What It Should Do |
|-------|-------------|-------------------|
| "Andaman or Sri Lanka" | ✅ Fixed — semi_open with blocking ambiguity | ✓ |
| "maybe Singapore" | ✅ Fixed — semi_open + value_vague blocking | ✓ |
| "looking for a warm beach destination in March with good seafood" | ❌ `candidates=[], status=open` | Should extract intent: beach, warm, March, seafood |
| "trip for my parents' 25th anniversary, they love temples" | ❌ `trip_purpose` may miss "anniversary" | Should extract: elderly, anniversary, temples |
| "budget around 2L, can stretch to 2.5L for something really good" | ⚠️ `budget_min=200000, budget_flexibility=flexible` | Stretch amount (2.5L) lost; Gap 3 still open |

The regex layer can harden patterns. It cannot do semantic understanding. That's Phase B.

### Recommended sequencing

The `NEXTJS_IMPLEMENTATION_TRACK_2026-04-15.md` defines FE-003 through FE-017 for Phase A. The spine API route (FE-003) wires the intake pipeline to the Next.js backend. The workbench (FE-011) needs the spine API.

**Proposed parallel tracks:**

| Track | What | When | Blocks |
|-------|------|------|--------|
| Track 1: FE-003 | Spine API route (`POST /api/spine/run`) | Now | Nothing — regex baseline just hardened |
| Track 2: FE-011 | Workbench UI | After FE-003 | Needs API route |
| Track 3: Phase B | NER extraction layer | In parallel with FE-011 | Needs regex baseline as fallback (done ✓) |
| Track 4: P1.5 | Evaluation gate | After Phase B baseline | Needs both tracks to compare |

The workbench becomes the evaluation harness — every NER enhancement compared against the regex baseline in real time.

### Important architectural invariant

From the PM Blueprint: **"deterministic parser > NER suggestion > regex fallback (never reverse for critical fields)"**

This means:
- Regex results are the hardened floor (what we just fixed)
- NER results are additions/suggestions that can override with higher confidence but cannot REMOVE a regex result
- Critical fields (destination, budget, dates, party) always prefer the more authoritative source
- The merge strategy must preserve provenance

---

## 11. Files Changed in This Session

| File | Lines Changed | Change Type |
|------|--------------|-------------|
| `src/intake/extractors.py` | ~75 lines rewritten in `_extract_destination_candidates`; ~15 lines added for value-structural synthesis | Fix (hedging order + stop words + ambiguity synthesis) |
| `src/intake/decision.py` | ~60 lines added across 3 locations (`_synthesize_destination_ambiguity`, candidate-aware questions in hard-blocker and ambiguity paths, severity table entry) | Fix (ambiguity synthesis + question framing + severity) |
| `tests/test_nb01_v02.py` | ~90 lines added (7 tests in 2 classes) | Regression tests |
| `tests/test_nb02_v02.py` | ~70 lines added (4 tests in 1 class) | Regression tests |
| `Docs/travel_agency_process_issue_review_2026-04-15.md` | New file, ~180 lines | Issue documentation |
| `Docs/destination_hedging_issue_review_2026-04-15.md` | New file, ~160 lines | Issue documentation |

---

## 12. Open Questions for External Review

1. **Should the NB03 contract be updated?** The contract says NB03 mitigates destination ambiguity via an override. We proved the mitigation belongs in NB01/NB02. Should we update `03_session_strategy_contract.md` to reflect this, or keep the contract as-is and add an addendum?

2. **Should `value_vague` on destinations always be blocking?** At discovery stage, "maybe Singapore" might be advisory (exploratory). At shortlist/proposal/booking, it must be blocking. Should we add conditional severity?

3. **What other hedging patterns exist in real traveler input?** We added "maybe", "thinking about", "perhaps", "considering", "looking at". What else? "Sort of X", "X probably", "X I guess", "not sure but X", "might go to X"?

4. **Should we audit `is_known_destination()` for false positives?** "We" got through. What other non-destinations pass?

5. **When should Phase B (NER extraction) start relative to Phase A (UI/workbench)?** Options: (a) after Phase A complete, (b) in parallel with FE-011, (c) immediately after FE-003.

6. **How should NER output merge with regex output?** The PM blueprint says "deterministic parser > NER suggestion > regex fallback." But what does "merge" look like concretely? Same CanonicalPacket with different authority levels? A separate extraction result that gets reconciled?

7. **Budget stretch signal (Gap 3)**: "200000 can stretch" → NB01 detects `budget_stretch_present` as advisory ambiguity, but the stretch amount ("2.5L") is not captured as a separate field. Should `budget_max` be inferred from stretch text? Or should question generation say "We see 2L with flexibility — what's the absolute upper limit?"

8. **Multi-source authority (Gap 4)**: Contradictions carry flat `sources: ["env1", "env2"]`. Contract wants `[{value: "3L", source: "email"}, {value: "4L", source: "whatsapp"}]`. Is this a data model change or an enrichment layer?