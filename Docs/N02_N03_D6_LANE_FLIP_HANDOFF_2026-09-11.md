# N-02 / N-03 — D6 Gate Lane Content Authoring & Flip Attempt — Handoff

**Date:** 2026-09-11
**Scope:** `Docs/exploration/MASTER_FINDINGS_TASKS_INVENTORY_2026-09-02.md` POST-WAVE REFRESH items N-02 (extraction fixtures `raw_input` authoring) and N-03 (pipeline fixtures deterministic producer).
**Constraint compliance:** `src/intake/extractors.py` untouched. No DB writes. No commits.

## 1. Executive Summary

- **N-02 — DONE (content authored; lane intentionally not flipped).** All 50 extraction golden fixtures now carry an authored, realistic `raw_input` document text layer (additive keys only, prior fields byte-equal — machine-verified against HEAD). Feasibility verdict: the graded fields (`full_name`, `passport_number`, `visa_type`, `visa_expiry`, `visa_number`, `insurance_provider`, `insurance_policy_number`, `date_of_birth`, `nationality`, `passport_expiry`) are derivable from TEXT, but **no deterministic producer exists in CI**: the note pipeline (`ExtractionPipeline`) emits zero document facts, the vision-provider path (`spine_api/services/extraction_service.py`) consumes image bytes only (not text) and defaults to `noop` (human-gated), and the deterministic `MRZParserEngine` (TD3 passport, production-wired at `POST /api/v1/documents/mrz/parse-td3`) covers passport-number/name/dates for TD3-format text only — no visa-TD2 or insurance parser exists anywhere. Wiring the note pipeline against document expectations would grade a category error as 50/50 false negatives (F1 0.0). The collector therefore gained the same **genuine-actual guard** the pipeline collector already ratifies (skip fixtures with zero non-None actuals), keeping the lane on the flagged calibration fallback — **the lane flips live automatically, no further changes, the moment a deterministic text-path document producer emits packet facts.** That is the N-02 progress state: runnable corpus + auto-flip contract.
- **N-03 — INVESTIGATED; flip blocked; gap documented.** The three trip agents DO exist as deterministic rule engines (`FrontDoorAgent`, `DocumentReadinessAgent`, `ConstraintFeasibilityAgent` in `src/agents/runtime.py`) — but the 7 pipeline fixtures' `expected_agents` were authored against imagined contracts, and the `decision` stage has no in-process producer at all. Details + path forward in §4.

**Lane states did not flip** — honestly:

| Lane | Before | After | Why |
|---|---|---|---|
| extraction | `live_grading: false`, mirror, tier 0, F1 1.0 | **unchanged** (note text updated) | Corpus runnable; no deterministic document producer; guard prevents fake 0.0 category error |
| pipeline | `live_grading: false`, mirror, tier 0, accuracy 1.0 | **unchanged** | No producer for any of the 3 fixture stages (see §4) |

No re-baselining to hide failures: there is no metric drift to hide — both lanes remain non-authoritative calibration mirrors, now with a more accurate `note` in the snapshot explaining that raw_input exists but no producer does.

## 2. N-02 — raw_input authoring (50 fixtures)

**File touched:** `data/fixtures/extraction/golden_dataset.json` (additive only).

Note: the task brief located these fixtures at `data/fixtures/audit/`; they actually live at `data/fixtures/extraction/golden_dataset.json` (`DEFAULT_GOLDEN_DATASET_PATH` in `src/evals/audit/snapshot.py`, manifest category `extraction`). `data/fixtures/audit/` holds only the 2 activity-gate fixtures. The authoring target follows the manifest category and the task intent (additive keys, non-destructive).

**Authoring design:** each `raw_input` is a simulated OCR/confirmation text layer of the document, with labeled fields carrying each expected value verbatim (uppercase names, DD/MM/YYYY dates, exact passport/visa/policy numbers, exact provider names). Damage cases (worn edge, water damage, torn corner, ink smudge, glare) are depicted so expected `null` fields correspond to genuinely unreadable/missing fields — a future text producer graded against these fixtures gets honest null semantics. A probe test now enforces "every non-null expected value appears verbatim in raw_input" (`tests/evals/test_independent_eval_producers.py`).

**Coverage:** 27 passport / 13 visa / 10 insurance — all 50.

## 3. N-02 — collector wiring (what existing code supports)

`src/evals/audit/snapshot.py` `_collect_live_extraction_results`:

- Added the genuine-actual guard (skip fixtures whose mapped actuals contain no non-None value), matching the ratified contract of `_collect_live_pipeline_results` ("an empty per-stage shell would grade as false negatives"). Docstring updated with the full contract history.
- `_run_extraction_baseline` fallback `note` updated: "fixtures carry authored raw_input, but the deterministic pipeline emits no document facts — document vision extraction has no deterministic producer."
- Considered and rejected: wiring `MRZParserEngine` TD3 into the collector for the 27 passport fixtures. Reasons: (a) visa TD2/insurance have no parser, so the lane could never fully flip; (b) MRZ output requires extensive eval-side value normalization (YYYY-MM-DD→DD/MM/YYYY, `IND`→`INDIAN` nationality table, surname/given reordering), which would grade the eval mapping, not a production producer; (c) raw_input as MRZ lines contradicts the authored realistic-document corpus. This belongs in a production text-extraction path (out of scope; `extractors.py` frozen this pass).

**Manifest** (`src/evals/audit/manifest.yaml`): extraction comment updated to the new runnable-but-producerless state; pipeline comment extended with the N-03 vocabulary-mismatch evidence (§4).

**Tests** (`tests/evals/test_independent_eval_producers.py`): N-02 probe updated per its own doctrine ("adding an input artifact … must update the durable contract … rather than silently changing a mirror into authority"): asserts raw_input present + field-verbatim coverage + collector still empty. The mirror/non-authority probes are unchanged and still hold.

## 4. N-03 — pipeline lane verdict (blocked, gap documented)

Fixture contracts vs. reality:

1. **`expected_extraction` (document stage):** identical gap to N-02 — document-vision fields, no deterministic producer.
2. **`expected_agents` (agents stage):** producers exist and are deterministic (`src/agents/runtime.py`), but the fixture expectations don't match their real output contracts:
   - `front_door_agent.missing_fields` expects `["travel_dates", "hotel_preference"]` — the agent emits human-readable names (`"travel dates"`) and only ever checks destination/travel-dates/traveler-count/budget (never hotel); worse, fixture 1's own raw_note contains dates, party, and budget, so the real agent would emit `[]` — the expectation contradicts its own input.
   - `document_readiness_agent` expects `checklist_items` (list of strings); the real checklist emits `items` (list of structured dicts) + `must_confirm` + `critical_changes`.
   - `constraint_feasibility_agent` is closest (expected `feasibility_status`/`hard_blockers`/`soft_constraints` vs real `status`/`hard_blockers`/`soft_constraints`), but the key name and value vocabularies still differ.
3. **`expected_decision`:** expects `trip_status`/`stage`/`owner_action_required`/`escalation_needed` — the in-process `DecisionResult` emits `decision_state`/`hard_blockers`/`contradictions`; `spine_api/core/trip_status.py` mutations live in the serving persistence flow, and `readiness.py` `should_auto_advance_stage` is always False (stage transitions require explicit action). **No deterministic producer for this vocabulary anywhere.**

**Why not wire the agents live anyway:** flipping would grade the imagined-vocabulary mismatch (≈0 accuracy = a failing shadow lane), i.e., measure the fixtures, not the product. Re-authoring `data/fixtures/pipeline/pipeline_golden.json` expectations from real agent runs is outside this pass's allowed touch-scope (only `data/fixtures/audit/**` and additive extraction keys authorized).

**Path forward (follow-up task, requires pipeline_golden.json write authorization):** (1) record real agent outputs for the 7 raw_notes (synthesize trip payloads, run the three agents in-process); (2) re-author `expected_agents` to the real contracts; (3) either add a deterministic decision-stage producer for the trip_status/stage vocabulary or re-scope the decision stage out of the lane; (4) extend `_collect_live_pipeline_results` to compose the three agent stages per fixture (its docstring already anticipates exactly this).

## 5. Verification evidence (tails)

```
$ .venv/bin/python -m pytest tests/evals/ -q
........................................................................ [ 27%]
........................................................................ [ 54%]
........................................................................ [ 81%]
........................................................................ [100%]
266 passed in 30.27s
```

```
$ .venv/bin/python scripts/generate_d6_gate_snapshot.py
D6 gate snapshot written: data/evals/d6_audit_gate_snapshot.json
$ .venv/bin/python scripts/verify_d6_gate_snapshot.py
{
  "ok": true,
  "snapshot_path": "data/evals/d6_audit_gate_snapshot.json"
}
EXIT=0
```

```
$ git diff data/fixtures/extraction/golden_dataset.json  (additivity machine-check)
OK: 50/50 additive-only; all prior fields byte-equal; raw_input non-empty
$ ruff check src/evals/audit/snapshot.py tests/evals/test_independent_eval_producers.py
All checks passed!
```

Snapshot diff vs HEAD: extraction `note` text updated (now states raw_input exists but no document producer); `generated_at`/`checked_at` timestamps; no metric, status, threshold, or category changes.

## 6. Files touched

- `data/fixtures/extraction/golden_dataset.json` — +`raw_input` on 50 fixtures (additive)
- `src/evals/audit/snapshot.py` — genuine-actual guard + docstrings + fallback note
- `src/evals/audit/manifest.yaml` — extraction/pipeline comments (no threshold/status changes)
- `tests/evals/test_independent_eval_producers.py` — N-02 probe updated to new contract
- `data/evals/d6_audit_gate_snapshot.json` — regenerated
- `Docs/N02_N03_D6_LANE_FLIP_HANDOFF_2026-09-11.md` — this handoff

## 7. Open items

- N-02 closure requires a deterministic text-path document producer (or human-gated vision enablement, which stays outside deterministic CI). The lane auto-flips when one lands.
- N-03 follow-up task as scoped in §4 (needs `data/fixtures/pipeline/**` write authorization).
- `MRZParserEngine` TD3 remains a real, production-wired text producer for passport fields; wiring it into an intake/eval path (with proper value normalization at the producer, not the evaluator) is the cheapest genuine flip candidate for the passport subset.
