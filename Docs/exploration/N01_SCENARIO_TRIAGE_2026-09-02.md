# N-01 Scenario Triage — 13 Drifting Scenarios in the D6 Live Scenario Lane

**Date:** 2026-09-03 (analysis of snapshot `data/evals/d6_audit_gate_snapshot.json`, generated 2026-09-02T12:55Z)
**Persona:** PER-PDEV-0425 LLM Evaluation Specialist — slice analysis, inspect disagreements rather than averages
**Method:** Read-only in-process probes (`.venv/bin/python`, no DB writes, dev server untouched). Every scenario was re-run live through `load_scenario_fixtures()` + `run_gap_and_decision()` from `src/evals/audit/rules/scenarios.py`, with per-scenario extraction of hard/soft blockers, contradiction classifications + priorities, confidence, and follow-up questions. Proposed fixes were validated with in-memory counterfactual probes (deep-copied packets, no code or fixture changes).

**Reproduced snapshot exactly:** composite 0.5667 (17/30), decision_state_accuracy 0.60, hard_blocker_accuracy 0.8696, contradiction_accuracy 1.0, 13 failing IDs identical to the drift.

**Failing IDs:**
`basic_complete_discovery`, `basic_minimal_safe`, `contradiction_count_ask`, `contradiction_origin_ask`, `authority_manual_override`, `authority_owner_vs_imported`, `authority_explicit_user_high`, `stage_proposal_to_booking`, `stage_booking_complete`, `edge_empty_strings`, `hybrid_multi_source`, `hybrid_normalized`, `hybrid_cross_layer`

---

## 1. Triage Table

| # | Scenario | Input summary | Expected | Actual | Root cause (file:line) | Classification | Fix est. |
|---|----------|--------------|----------|--------|------------------------|----------------|----------|
| 1 | `contradiction_count_ask` | party_size slot holds conflicting `[3,5]` + authored party contradiction | ASK_FOLLOWUP | PROCEED_INTERNAL_DRAFT | High-priority contradictions never escalate: `src/intake/decision.py:2034-2040` collects only `priority=="critical"`; `party_conflict` is `high` (`decision.py:372`) so its `CONTRADICTION_ACTIONS` decision `ASK_FOLLOWUP` (`decision.py:363-376`) is dead intent | **DEFECT-decision** | **M** (`src/intake/decision.py`) |
| 2 | `contradiction_origin_ask` | origin_city slot holds conflicting `["Bangalore","Mumbai"]` + authored origin contradiction | ASK_FOLLOWUP | PROCEED_INTERNAL_DRAFT | Same as #1 (`origin_conflict`, `high`, `decision.py:373`) | **DEFECT-decision** | M (same fix) |
| 3 | `authority_owner_vs_imported` | origin fact (imported_structured, "Mumbai") vs owner-note contradiction | ASK_FOLLOWUP | PROCEED_INTERNAL_DRAFT | Same as #1. (Authority resolution itself is correct — imported_structured is fact-level, `packet_models.py:69-71`) | **DEFECT-decision** | M (same fix) |
| 4 | `basic_complete_discovery` | All 4 hard + budget_min/trip_purpose/soft_preferences filled; no `budget_raw_text` | PROCEED_TRAVELER_SAFE, 0 HB | PROCEED_INTERNAL_DRAFT | MVB soft-blocker list requires BOTH `budget_raw_text` AND `budget_min` (`decision.py:274-275`) — double-counts one budget dimension; missing raw echo alone demotes to draft (`decision.py:2119-2137`) | **DEFECT-decision** | **S/M** (`src/intake/decision.py`) |
| 5 | `basic_minimal_safe` | All 7 fields at conf 0.60; no `budget_raw_text` ("low confidence edge" per docstring) | PROCEED_TRAVELER_SAFE, 0 HB | PROCEED_INTERNAL_DRAFT | Same budget double-count as #4. Secondary: the confidence floor (`overall_confidence < 0.6` → draft, `decision.py:2158-2163`) is **unreachable dead code** — the first branch (`decision.py:2119-2120`) catches no-soft-blocker packets before it, so A6's low-confidence intent (conf 0.496) is never enforced | **DEFECT-decision** (+ latent dead-gate finding) | S/M (same fix) |
| 6 | `authority_explicit_user_high` | All 7 fields explicit_user ≥0.90; no `budget_raw_text` | PROCEED_TRAVELER_SAFE, 0 HB | PROCEED_INTERNAL_DRAFT | Same budget double-count as #4 (sole soft blocker: `budget_raw_text`) | **DEFECT-decision** | S/M (same fix) |
| 7 | `edge_empty_strings` | destination/date/party slots are `""` at conf 0.1, authority explicit_user | ASK_FOLLOWUP, 3 HB | PROCEED_INTERNAL_DRAFT, 0 HB | `field_fills_blocker` (`decision.py:486-509`) guards only `slot.value is None` (`:499`) — empty/blank strings and list-valued slots fill hard blockers. TEST_PHILOSOPHY.md:153 mandates "Empty strings → Don't treat as valid" | **DEFECT-decision** (value validation) | **S** (`src/intake/decision.py`, `field_fills_blocker`) |
| 8 | `authority_manual_override` | 5 manual_override fields; **no** budget_raw_text / trip_purpose / soft_preferences | PROCEED_TRAVELER_SAFE, 0 HB | PROCEED_INTERNAL_DRAFT | Fixture omits 3 soft-context fields its own expectation requires; engine policy "missing soft blockers → draft" (`decision.py:2121-2137`) is coherent | **FIXTURE-ERROR** | S (`data/fixtures/test_scenarios.py:398-412`) |
| 9 | `hybrid_normalized` | origin normalized blr→Bangalore (imported_structured); **no** budget/trip_purpose/soft_preferences slots | PROCEED_TRAVELER_SAFE, 0 HB | PROCEED_INTERNAL_DRAFT | Same as #8 — 4 soft blockers unfilled. Note the FM2 intent IS honored: normalized/imported value fills the hard blocker (no origin re-ask) | **FIXTURE-ERROR** | S (`data/fixtures/test_scenarios.py:705-726`) |
| 10 | `hybrid_cross_layer` | facts dest=Singapore vs derived dest=Thailand; no soft-context fields | PROCEED_TRAVELER_SAFE, 0 HB | PROCEED_INTERNAL_DRAFT | Same as #8. Cross-layer behavior itself is BY-DESIGN (facts layer wins; `resolve_field` `decision.py:453-483` checks facts first; matches TEST_PHILOSOPHY.md:118 and passing sibling E4) — no contradiction is authored, none should surface | **FIXTURE-ERROR** | S (`data/fixtures/test_scenarios.py:729-745`) |
| 11 | `stage_proposal_to_booking` | booking stage; missing traveler details + payment | ASK_FOLLOWUP, **2** HB | ASK_FOLLOWUP, **3** HB | Booking MVB gained `visa_status` (`decision.py:314`, v0.2 commit 2627920 on 2026-04-14) after the corpus was authored (initial commit 473d5de, 2026-04-09); corpus expectation of 2 (`test_scenarios.py:884`) predates it. Actual blockers are exactly `passport_status, visa_status, payment_method` — correct for current MVB | **FIXTURE-ERROR** (stale expectation) | S (`data/fixtures/test_scenarios.py:884`: 2→3) |
| 12 | `stage_booking_complete` | booking stage "complete"; has passport_status + payment_method, **no `visa_status`** | PROCEED_TRAVELER_SAFE, 0 HB | ASK_FOLLOWUP, 1 HB (`visa_status`) | Fixture content incomplete vs current 8-field booking MVB (`decision.py:306-318`) — the fixture never satisfied the expectation it asserts | **FIXTURE-ERROR** | S (`data/fixtures/test_scenarios.py:555-580`: add visa_status slot) |
| 13 | `hybrid_multi_source` | dest fact with 2-source evidence; authored contradiction values `["SG","Singapore"]` | PROCEED_INTERNAL_DRAFT | ASK_FOLLOWUP | Authored contradiction classifies `destination_conflict` → priority **critical** (`decision.py:365`) → forced ASK (`decision.py:2053-2067`). Expectation is internally inconsistent: sibling B3 `contradiction_destination_ask` expects ASK for the identical contradiction type and **passes**. The engine cannot satisfy both | **FIXTURE-ERROR** | S (`data/fixtures/test_scenarios.py:895`: state → ASK_FOLLOWUP) |

**Split: 7 DEFECT-decision across 3 distinct root causes (flipping 7 scenarios) · 6 FIXTURE-ERROR (6 scenarios) · 0 BY-DESIGN standalone · 0 DEFECT-extraction** (no extraction-path code is implicated — this lane grades hand-built packets through the decision engine only; the one extraction-adjacent note is that production budget extraction always fills `budget_raw_text` + `budget_min` together, `src/intake/extractors.py:2276-2295`, which is why the double-count defect only surfaces on structured/CRM-imported packets — a real production path).

---

## 2. Per-Scenario Analysis

### 2.1 Contradiction escalation dead intent — B4, B5, C2 (DEFECT-decision, fix M)

**Probe evidence (all three):**

```text
contradiction_count_ask    state: expected=ASK_FOLLOWUP   actual=PROCEED_INTERNAL_DRAFT
  contradictions: [('party_size', 'party_conflict', 'high')]   hard_blockers=[]   conf=0.665
contradiction_origin_ask   state: expected=ASK_FOLLOWUP   actual=PROCEED_INTERNAL_DRAFT
  contradictions: [('origin_city', 'origin_conflict', 'high')] hard_blockers=[]   conf=0.665
authority_owner_vs_imported state: expected=ASK_FOLLOWUP  actual=PROCEED_INTERNAL_DRAFT
  contradictions: [('origin_city', 'origin_conflict', 'high')] hard_blockers=[]   conf=0.689
```

**Mechanism.** The action table explicitly declares `party_conflict` and `origin_conflict` → `{"decision": "ASK_FOLLOWUP", "priority": "high"}` (`src/intake/decision.py:372-373`), and TEST_PHILOSOPHY.md:99-101 pins the intent ("B4 count mismatch affects pricing; B5 origin conflict affects flights → ASK"). But Phase 7 of `run_gap_and_decision` (`decision.py:2034-2040`) collects only `action["priority"] == "critical"` contradictions into `critical_contradictions`, and the Phase 9 state machine (`decision.py:2051-2067`) escalates solely from that list (plus the special-cased `budget_conflict → BRANCH_OPTIONS` at `decision.py:2107-2114`). The `decision` field for every non-critical, non-budget contradiction type is never consulted anywhere — the scenario falls to the else-branch, where the only soft blockers are the unfilled enrichment fields, producing `PROCEED_INTERNAL_DRAFT` and follow-up questions about budget/purpose instead of the actual conflict. The contradiction *survives* in the result (contradiction axis passes lane-wide, 1.0) but drives nothing — a silent contradiction.

**Real-world impact (Tool-Taster demo pattern).** This is the worst family to demo: a traveler writes "family of 3" in WhatsApp and "5 of us" on a call; the system quietly drafts a quote for the wrong party size — wrong pricing, the exact FM3 failure the corpus exists to prevent. Highest-stakes defect in the lane.

**Fix path.** In `run_gap_and_decision`, honor `CONTRADICTION_ACTIONS[...]["decision"]` for high-priority types: when any contradiction's action decision is `ASK_FOLLOWUP` (and no STOP-level conflict already routed), emit a targeted follow-up question for that field and route `ASK_FOLLOWUP` before the soft-blocker branch. Add regression tests asserting B4/B5/C2-shaped packets → ASK with a party/origin question. Verified pinning risk: no existing test asserts party/origin conflicts stay non-escalating (searched `tests/` for `party_conflict|origin_conflict`; only critical date/document escalation is pinned in `tests/test_decision_policy_conformance.py:67-82`).

**Secondary finding (same probe):** the conflicting slot values are lists (`[3,5]`, `["Bangalore","Mumbai"]`) at fact authority, and `field_fills_blocker` counts them as filling the hard blocker (only `value is None` is rejected, `decision.py:499`). A multi-valued slot is intrinsically unresolved; folding a non-scalar/blank guard into the same `field_fills_blocker` fix (see 2.2/#7) makes the blocker state honest even before escalation routes to ASK.

### 2.2 Budget OR-group double-count — A2, A6, C4 (DEFECT-decision, fix S/M)

**Probe evidence:**

```text
basic_complete_discovery    soft_blockers=['budget_raw_text']            conf=0.699 → PROCEED_INTERNAL_DRAFT
basic_minimal_safe          soft_blockers=['budget_raw_text']            conf=0.496 → PROCEED_INTERNAL_DRAFT
authority_explicit_user_high soft_blockers=['budget_raw_text']           conf=0.751 → PROCEED_INTERNAL_DRAFT
```

**Mechanism.** Discovery MVB soft blockers are `budget_raw_text, budget_min, trip_purpose, soft_preferences` (`decision.py:273-278`). `budget_raw_text` (raw utterance echo) and `budget_min` (normalized slot) are the same underlying dimension; the MVB requires both. Any packet with a canonical budget but no raw echo is demoted to `PROCEED_INTERNAL_DRAFT` (`decision.py:2119-2137`). Production extraction always fills both together (`src/intake/extractors.py:2276-2295`), so the defect is invisible on chatty intake but fires on every structured/CRM-imported budget — precisely the hybrid lane's subject matter.

**Counterfactual validation (in-memory, no code change):** adding a `budget_raw_text` slot to each of the three packets flips all three to `PROCEED_TRAVELER_SAFE, 0 HB`. The single OR-group change is the highest-leverage code fix in the lane (3 scenarios).

**Fix path.** Treat budget as satisfied when either canonical form is present (skip `budget_raw_text` from blocker evaluation when `budget_min` is filled, or introduce an OR-group in the MVB loop). Fix lands in `src/intake/decision.py` Phase 3 / MVB evaluation.

**Latent finding (A6 only).** `basic_minimal_safe` is documented as the "low confidence edge" (overall conf 0.496 in probe), but the confidence floor at `decision.py:2158-2163` (`overall_confidence < 0.6 → PROCEED_INTERNAL_DRAFT`) is **unreachable**: the first branch (`decision.py:2119-2120`) captures every no-soft-blocker/no-ambiguity packet before it. The dead gate means low-confidence fully-populated packets are traveler-safe today. Fixing the OR-group makes A6 pass as authored; the dead gate should be raised as a separate decision-layer hardening item (move the confidence check ahead of the first branch or delete the dead branch) — not required to flip the lane, but flag it now so the "minimal safe" scenario's stated intent is actually enforced.

### 2.3 Empty/blank value validation — E2 (DEFECT-decision, fix S)

**Probe evidence:**

```text
edge_empty_strings  state: expected=ASK_FOLLOWUP actual=PROCEED_INTERNAL_DRAFT
  hard_blockers: expected=3 actual=[]   conf=0.268
```

**Mechanism.** `field_fills_blocker` (`decision.py:486-509`) rejects only `None` values (`:499`). Empty strings (`""` at conf 0.1, explicit_user authority) fill all three destination/date/party hard blockers, so the engine proceeds to draft at 0.268 confidence instead of asking. TEST_PHILOSOPHY.md:153 is explicit: "E2 Empty strings — Don't treat as valid." This is FM1 (false positive) leaking through a validation gap.

**Counterfactual validation:** blanking `""` → `None` in-memory yields exactly `ASK_FOLLOWUP` with 3 hard blockers — the corpus expectation.

**Fix path.** Add a value-validity guard in `field_fills_blocker`: reject blank/whitespace-only strings and non-scalar unresolved lists (covers the 2.1 secondary finding). One site, `src/intake/decision.py:486-509`; alternative companion site is `src/intake/normalizer.py` (normalize `""` → absent at packet construction), but the decision-layer guard is the defense that holds regardless of producer.

### 2.4 Stage/booking MVB drift — D3, D4 (FIXTURE-ERROR, fix S each)

**Probe evidence:**

```text
stage_proposal_to_booking  state OK; hard_blockers: expected=2 actual=['passport_status','visa_status','payment_method']
stage_booking_complete     state: expected=PROCEED_TRAVELER_SAFE actual=ASK_FOLLOWUP
  hard_blockers: expected=0 actual=['visa_status']
```

**Mechanism.** The booking MVB has 8 hard blockers including `visa_status` (`decision.py:306-318`), added in the v0.2 intake foundation (commit `2627920`, 2026-04-14). The corpus predates it (initial commit `473d5de`, 2026-04-09; TEST_PHILOSOPHY dated 2026-04-09 says "D3 needs traveler_details, payment" — two fields). D3's expectation of 2 is stale by one field (the legacy alias `traveler_details → passport_status`, `decision.py:334`, never covered visa). D4's fixture content itself omits `visa_status`, so it never satisfied its own "complete" expectation under the current MVB.

**Fix path.** Corpus-only: `test_scenarios.py:884` expected `hard_blockers` 2 → 3; add a `visa_status` slot to `stage_booking_complete` (`test_scenarios.py:555-580`). Counterfactual validated: D4 with `visa_status` → `PROCEED_TRAVELER_SAFE, 0 HB`. Engine behavior is correct for the current MVB — do not "fix" the engine here.

### 2.5 Traveler-safe expectations on soft-incomplete fixtures — C1, F2, F3 (FIXTURE-ERROR, fix S each)

**Probe evidence:**

```text
authority_manual_override soft_blockers=['budget_raw_text','trip_purpose','soft_preferences'] conf=0.840
hybrid_normalized         soft_blockers=['budget_raw_text','budget_min','trip_purpose','soft_preferences'] conf=0.706
hybrid_cross_layer        soft_blockers=['budget_raw_text','budget_min','trip_purpose','soft_preferences'] conf=0.734
```

**Mechanism.** Each fixture omits the soft-context fields its `PROCEED_TRAVELER_SAFE` expectation requires; the engine's rule "missing soft blockers → PROCEED_INTERNAL_DRAFT" (`decision.py:2119-2137`) is coherent and documented. Note the *stated* failure-mode intents of F2 and F3 are already honored: `hybrid_normalized`'s imported/normalized origin fills the hard blocker (FM2, `packet_models.py:69-71` — `imported_structured` is fact-level), and `hybrid_cross_layer`'s facts-layer precedence matches FM4 (`resolve_field`, `decision.py:453-483`, facts first; sibling E4 passes with the same semantics). F3 surfaces no cross-layer contradiction **by design** — none is authored, and TEST_PHILOSOPHY.md:118 defines F3 as "fact > derived", not "flag the conflict".

**Fix path.** Corpus-only, minimal-diff preserving each scenario's isolation intent: add the missing soft slots (`budget_raw_text`, `budget_min` where absent, `trip_purpose`, `soft_preferences`) to C1 (`test_scenarios.py:398-412`), F2 (`:705-726`), F3 (`:729-745`). Counterfactual validated: all three flip to `PROCEED_TRAVELER_SAFE, 0 HB`. Alternative (change expectations to `PROCEED_INTERNAL_DRAFT`) is rejected — it would blur "fully known → traveler-safe" semantics and weaken the corpus's false-negative coverage.

### 2.6 Inconsistent destination-conflict expectation — F1 (FIXTURE-ERROR, fix S)

**Probe evidence:**

```text
hybrid_multi_source  state: expected=PROCEED_INTERNAL_DRAFT actual=ASK_FOLLOWUP
  contradictions: [('destination_candidates','destination_conflict','critical')]  follow_up: ['destination_candidates']
```

**Mechanism.** The packet hand-authors a `destination_candidates` contradiction, which classifies `destination_conflict` → priority `critical` (`decision.py:365`) → forced `ASK_FOLLOWUP` (`decision.py:2053-2067`). This is not negotiable engine-side without breaking B3 (`contradiction_destination_ask`), which expects ASK for the identical contradiction type and **passes**. The two fixtures assert contradictory semantics for the same event; the engine currently satisfies B3 and fails F1. F1's stated intent ("DETECT — same field, different sources", TEST_PHILOSOPHY.md:101) is about detection, and detection succeeds (the contradiction survives; that axis passes).

**Fix path.** Corpus-only: change F1 expected state to `ASK_FOLLOWUP` (`test_scenarios.py:895`). Optional future enhancement (separate item, not this lane): alias-aware contradiction resolution ("SG" ≡ "Singapore" → downgrade to non-conflict) — but as authored, the fixture *creates* the conflict it then expects the engine to ignore.

---

## 3. Recommended Fix Order (highest real-world impact first)

| Order | Fix | Scenarios flipped | File | Est. | Why this order |
|---|---|---|---|---|---|
| 1 | **High-priority contradiction escalation** (honor `CONTRADICTION_ACTIONS` decisions for `party_conflict`/`origin_conflict`) | B4, B5, C2 (3) | `src/intake/decision.py` (~2034-2114) | M | Silent party/origin conflicts produce wrong-count/wrong-origin quotes shown to customers — the exact demo-killer (Tool-Taster colloquial pattern: "family of 3" vs "5 of us" across messages). Highest stake per fix. |
| 2 | **Budget OR-group** (budget satisfied by `budget_min` OR `budget_raw_text`) | A2, A6, C4 (3) | `src/intake/decision.py` (~273-278, Phase 3) | S/M | Unblocks every structured/CRM-imported budget from spurious draft demotion; equal scenario yield to #1, slightly lower blast radius. Also file the dead confidence gate (`decision.py:2158-2163`) as a follow-up hardening item surfaced by A6. |
| 3 | **Blank/non-scalar value guard** in `field_fills_blocker` | E2 (1) | `src/intake/decision.py:486-509` | S | Cheap defensive fix; closes the FM1 false-positive leak and the list-fills-blocker hole used by B4/B5 packets. |
| 4 | **Corpus batch** (single file, `data/fixtures/test_scenarios.py`): D3 expectation 2→3; D4 add `visa_status`; C1/F2/F3 add missing soft slots; F1 expectation → ASK_FOLLOWUP | D3, D4, C1, F2, F3, F1 (6) | `data/fixtures/test_scenarios.py` | S (batch) | Pure fixture corrections; no code risk; makes the lane internally consistent and gatable. Do after the code fixes so the corpus isn't churned twice. |

After 1-4: re-run the lane, expect composite ≥ 0.93 minimum (27/30 guaranteed by counterfactuals; the confidence-gate follow-up could affect A6 semantics if applied simultaneously — sequence it after the lane re-baseline). Then flip the scenario lane to gating (`blocks_ci` / raise `expected_baseline_accuracy` from the aspirational 1.0 to a verified baseline).

**Regression safety:** no existing test pins the non-escalating behavior of party/origin conflicts, budget double-counting, or blank-string blocker fills (searched `tests/`); the pinned critical date/document escalation (`tests/test_decision_policy_conformance.py:67-82`) is untouched by all three code fixes.

---

## 4. Fixture-Error List — Corpus Corrections to Propose

All in `data/fixtures/test_scenarios.py` (+ expectations at `:856-899`):

1. **`stage_proposal_to_booking`** (`:884`): `hard_blockers` 2 → 3 (booking MVB includes `visa_status` since v0.2, `decision.py:314`).
2. **`stage_booking_complete`** (`:555-580`): add `visa_status` slot (explicit_user, ≥0.9) so the fixture satisfies its own "booking complete" expectation.
3. **`authority_manual_override`** (`:398-412`): add `budget_raw_text`, `trip_purpose`, `soft_preferences` slots to match its `PROCEED_TRAVELER_SAFE` expectation.
4. **`hybrid_normalized`** (`:705-726`): add `budget_raw_text`, `budget_min`, `trip_purpose`, `soft_preferences` slots.
5. **`hybrid_cross_layer`** (`:729-745`): same soft-context completion.
6. **`hybrid_multi_source`** (`:895`): expected `decision_state` `PROCEED_INTERNAL_DRAFT` → `ASK_FOLLOWUP` (inconsistent with sibling B3 and the `destination_conflict` critical action).

Minor, optional hygiene (non-blocking): the corpus hardcodes `sys.path.insert(0, '/Users/pranay/Projects/travel_agency_agent')` (`test_scenarios.py:23`) — machine-specific path; the `scenarios.py` importlib loader already contains this, but the hardcode breaks portability outside this checkout.

## 5. New Extraction Test Fixtures vs Decision-Layer Work

- **Decision-layer work (code):** items 1-3 in the fix order — contradiction escalation, budget OR-group, blank/non-scalar value guard. Each ships with unit tests (B4/B5/C2 shapes → ASK with conflict-targeted question; `budget_min`-only packet → no budget soft blocker; `""`/list-valued slot → does not fill blocker).
- **New extraction test fixtures:** none required for these 13 — the lane grades hand-built packets through the decision engine, so no extractor/pattern is implicated. The corpus itself, once corrected, becomes the regression fixture set (that is the lane's purpose). Separately, the N-02 item (50 extraction fixtures lacking `raw_input`) remains the extraction-fixture workstream and is unaffected by this triage.
- **Not defects / no action:** F3's missing cross-layer contradiction (by-design, facts win), D3/D4 engine blocker counts (correct for current MVB), C2's authority resolution (imported > owner verified correct, `packet_models.py:69-84`).

---

*Probe commands were read-only in-process (`load_scenario_fixtures` + `run_gap_and_decision` + deep-copied counterfactual packets); no DB writes, no server contact, no code or fixture modifications.*
