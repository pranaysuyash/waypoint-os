# Independent evaluation producers — N-02 / N-03

**Date:** 2026-09-04\
**Scope:** audit the extraction and end-to-end pipeline fixture contracts,
their live collector paths, and the minimum implementation needed before
either lane can become product-quality evidence.\
**Owner:** evaluation/quality lane; product-contract decisions remain with the
project owner.\
**Evidence status:** Tier 1 static inspection plus Tier 2 deterministic local
probes. No provider, browser, hosted, production, or real-traveler claim.

## Executive decision

N-02 and N-03 remain open. No safe local implementation can honestly turn the
current mirror scores into independent quality evidence without first resolving
the input and stage contracts.

The correct near-term action is to keep both manifest categories `shadow`,
retain the expected-vs-expected path only as evaluator calibration, and build
the producer boundary in the sequence below. Fabricating document values from
the expected labels, mapping note facts onto document fields, or treating
client-supplied expected outputs as live actuals would violate the evidence
and epistemic-label doctrines.

## Current observed state

### N-02 — extraction fixtures

`data/fixtures/extraction/golden_dataset.json` contains **50** fixtures:

| Document type | Fixtures | Expected field slots |
|---|---:|---:|
| passport | 27 | 5 each |
| visa | 13 | 6 each |
| insurance | 10 | 3 each |
| **Total** | **50** | **220** |

The 50 rows contain no `raw_input` key. `src/evals/audit/rules/extraction.py`
loads only `fixture_id`, document type, description, difficulty, expected
fields, and tags; its `ExtractionFixture` model has no source-artifact field
(`extraction.py:40-67`). The expected field distribution is:

| Expected field | Slots |
|---|---:|
| `full_name` | 50 |
| `passport_number` | 40 |
| `nationality` | 40 |
| `date_of_birth` | 27 |
| `passport_expiry` | 27 |
| `visa_type` | 13 |
| `visa_number` | 13 |
| `visa_expiry` | 13 |
| `insurance_provider` | 10 |
| `insurance_policy_number` | 10 |

The live collector in `src/evals/audit/snapshot.py:214-265` is correctly
fail-closed for this state: it only invokes `ExtractionPipeline` for fixtures
with a `raw_input`. The probe returned **0 live results**. The fallback then
uses expected values as actuals with `actual_source=expected_fixture_mirror`,
`live_grading=false`, and `evidence_tier=0`; the manifest correctly keeps the
extraction category in `shadow`.

The production document path is materially different from the note path:
`spine_api/services/extraction_service.py:56-149` accepts document bytes,
MIME type, and document type through a `DocumentExtractor`/provider chain.
`NoopExtractor` is explicitly a dev/test mock with sentinel values, and the
vision providers require provider configuration. Existing vision tests mock
the provider client; they are contract tests, not an independent corpus
producer.

**Conclusion:** this is not a missing regex or a missing call to
`ExtractionPipeline`. It is a missing source-artifact contract and an absent
independent document producer.

### N-03 — end-to-end pipeline fixtures

`data/fixtures/pipeline/pipeline_golden.json` contains **7** fixtures, all with
a non-empty `raw_input.raw_note`. The notes can be run through the canonical
note `ExtractionPipeline`, but every fixture expects three additional stages:

1. `expected_extraction`: nested `passport`, `visa`, and `insurance` document
   fields (the same document-vision contract as N-02);
2. `expected_agents`: compact outputs from names such as
   `front_door_agent`, `document_readiness_agent`, and
   `constraint_feasibility_agent`;
3. `expected_decision`: `trip_status`, `stage`, `owner_action_required`, and
   `escalation_needed`.

The local probe ran all seven notes through `ExtractionPipeline` and observed
the following invariant:

```text
raw notes exercised:                 7/7
fixtures with document-field overlap: 0/7
collector-produced gradable fixtures: 0/7
```

The actual note facts are destination/date/party/budget/traveler-plan facts
(for example `destination_candidates`, `date_window`, `party_size`, and
`budget_max`); none of the expected document keys are emitted. This is why
`_collect_live_pipeline_results()` (`snapshot.py:268-325`) returns an empty
result instead of scoring note facts against document expectations.

The agent names do exist in the production runtime, but their contracts are
different. For example, `FrontDoorAgent` declares a persisted
`front_door_assessment` plus priority, next action, acknowledgment, source,
and timestamps (`src/agents/runtime.py:635-734`). `DocumentReadinessAgent`
returns a checklist with static-rule tool evidence, freshness, and a legal
disclaimer (`runtime.py:971-1050`). `ConstraintFeasibilityAgent` persists a
structured assessment (`runtime.py:1582-1635`). These are not the fixture's
small dictionaries, and several outputs contain wall-clock timestamps or
provider/static-evidence metadata. Running them without a deterministic clock,
stable repository, and explicit output projection would not produce a
reproducible gate.

The decision engine's canonical result is also different: `DecisionResult`
owns `decision_state`, `hard_blockers`, and `contradictions`
(`src/intake/decision.py:234-268`), while the pipeline fixture expects a
separate `trip_status`/`stage` vocabulary. The adapter and mapping therefore
require a product-contract decision; they cannot be inferred safely from the
fixture names.

## Why the current scores are not authority

The extraction and pipeline baseline functions preserve an expected-as-actual
mirror for comparator calibration. Their source is explicit in
`src/evals/audit/snapshot.py:334-517`, and `src/evals/audit/gates.py` withholds
public authority when the source is a mirror. The current 1.0 scores prove
that comparison and serialization work; they prove neither extraction
accuracy nor end-to-end correctness.

This distinction is especially important here:

| Tempting shortcut | Why it is invalid | Correct replacement |
|---|---|---|
| Put expected passport strings in `raw_note` | Tests note parsing, not OCR/document layout | Attach independent image/PDF artifacts with hashes |
| Use `NoopExtractor` | Sentinel mock values are not document truth | Use a reviewed provider or a separately generated offline OCR fixture producer |
| Map `destination_candidates` to `passport` | Changes field meaning and creates false positives | Keep note extraction as a separate stage contract |
| Run agents and compare raw dicts | Timestamps/evidence/side effects make results unstable and schema-incompatible | Add a pure, deterministic stage projection over an immutable fixture repository |
| Treat fixture expectations as agent actuals | Reintroduces the mirror problem | Persist producer outputs with producer/version/provenance metadata |
| Promote on one aggregate score | A passing stage can hide an absent stage | Require per-stage coverage and threshold evidence |

## Decision and implementation sequence

### Phase 1 — freeze and make provenance machine-readable

1. Keep the extraction and pipeline manifest entries `shadow`.
2. Extend the fixture contract with explicit provenance metadata, without
   changing current fixtures until the owner chooses a migration:
   - `input_ref` (repo-relative, non-PII artifact path or external fixture
     identifier);
   - `input_sha256` and MIME/type metadata;
   - `gold_source` and adjudication/version metadata;
   - `producer_contract` and `producer_version`.
3. Make the snapshot report counts for `runnable`, `missing_input`,
   `producer_available`, and `stage_coverage` instead of only an empty/nonempty
   collector result. An unavailable producer must remain non-authoritative.
4. Add schema tests that fail closed when a fixture claims `live` provenance
   without the required input and producer metadata.

### Phase 2 — close N-02 with a real artifact-backed producer

1. Choose one document-artifact policy: synthetic sanitized PDF/images,
   de-identified real artifacts, or a provider-approved corpus. Do not mix
   policies under one score.
2. Generate or curate artifacts independently of the expected labels. Store
   only hashes and safe fixture references in Git; keep sensitive artifacts in
   the approved encrypted fixture store if required.
3. Build a test-only adapter around the existing `DocumentExtractor` contract:
   bytes + MIME + document type → fields + confidence + provider metadata.
   Normalize output into `ExtractionFixture` fields without writing to the
   application database.
4. Require deterministic provider configuration for local runs (fixed prompt,
   schema, routing, normalization, and model versions). If the provider is
   unavailable, emit an explicit unavailable result, never a mirror.
5. Add field-level and document-level checks for missing, wrong, hallucinated,
   and low-confidence values; preserve abstentions as data.
6. Add a fresh private holdout with the same artifact contract and no input
   leakage into `tests/`, following `data/fixtures/evals/holdout/README.md`.
7. Promote only after live collector evidence meets the manifest threshold on
   dev and private holdout, with independent review of artifact/label lineage.

### Phase 3 — close N-03 with stage-owned deterministic producers

1. Ratify whether N-03 is one true end-to-end pipeline or a composition of
   independently evaluated stages. Recommended: compose stages but retain
   per-stage provenance and coverage.
2. Define canonical schemas for:
   - document extraction (reuse N-02 output, not note facts);
   - agent outputs (stable fields only; timestamps/evidence in sidecar
     metadata);
   - decision output (map to the canonical `DecisionResult` vocabulary, then
     explicitly derive any UI `trip_status`/stage projection).
3. Create an immutable in-memory fixture repository and deterministic clock for
   agent runs. Agent writes must be captured as proposed updates, not mutate
   real application state or depend on ambient database/provider state.
4. Add a pure adapter from each runtime output to the fixture's canonical
   stage schema. Reject unknown agents, missing required stages, and partial
   stage coverage unless the fixture explicitly declares an intentional
   absence.
5. Require the seven fixtures to produce actuals for every expected stage;
   partial extraction-only output must remain non-authoritative.
6. Add retry, missing-stage, malformed-output, and side-effect isolation tests,
   then seed independent private pipeline holdouts.
7. Promote only when stage-level and overall thresholds pass with producer
   metadata, no mirror source, and a falsifying mutation that breaks the gate.

## Falsifiers and acceptance criteria

The work is not complete if any of these remain true:

- an extraction fixture has expected fields but no independently retrievable
  input artifact;
- a pipeline fixture's actuals are copied from expected values or are produced
  by the same code that authored the labels;
- a note fact is compared with a document field because their names happen to
  overlap;
- a runtime agent's timestamp or mutable store affects the score;
- one pipeline stage is absent but the aggregate still reports a passing
  result;
- the snapshot reports `live_grading=true` without producer/version/input
  provenance;
- a provider or holdout failure silently falls back to expected-as-actual;
- promotion is based only on the seven public fixtures without a private
  holdout and mutation-sensitive gate.

## Verification receipt

Commands run on 2026-09-04 from the repository root:

```text
PYTHONPATH=. .venv/bin/python <read-only fixture/producers probe>
→ extraction: 50 fixtures, 0 raw_input; passport 27, visa 13, insurance 10
→ pipeline: 7 fixtures, 7 raw notes; document-field overlap 0/7
→ _collect_live_extraction_results(...): 0 results
→ _collect_live_pipeline_results(...): 0 results

PYTHONPATH=. .venv/bin/python -m pytest -q \
  tests/evals/test_extraction_rule.py \
  tests/evals/test_pipeline.py \
  tests/evals/test_d6_gate_snapshot.py \
  tests/evals/test_public_authority.py
→ 130 passed in 5.69s

PYTHONPATH=. .venv/bin/pytest -q tests/evals/test_independent_eval_producers.py
→ 3 passed in 4.11s
```

The read-only corpus probe and the executable contract tests are Tier 2 for
the observed local collector behavior (S1: current assertions pass). They do
not close N-02/N-03: they make the missing producer and the non-authoritative
mirror state regression-sensitive. The appropriate status remains
**open / shadow**.

## Ownership and follow-up

| Task | Owner decision needed | Implementation owner | Next proof |
|---|---|---|---|
| N-02 artifact contract | artifact policy, privacy boundary, provider scope | extraction/eval | artifact-backed collector with hashes and field-level report |
| N-02 holdout | holdout custodian and access policy | evaluation/quality | private live run with no dev leakage |
| N-03 canonical stage schema | product mapping for agent and decision fields | architecture + eval | schema/projection tests and deterministic repository run |
| N-03 producer composition | true E2E versus per-stage promotion | product/architecture | all seven fixtures actualize all declared stages |
| Promotion | threshold and falsifying mutation policy | release/eval | manifest change only after independent evidence |

Until these decisions and proofs exist, the current implementation is aligned
with first principles: it preserves the useful comparator, labels its
limitations, keeps unsupported authority fail-closed, and avoids inventing
document or agent truth.
