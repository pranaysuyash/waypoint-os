# Holdout Fixtures — Policy

**Status:** active policy (2026-09-02) · **Established by:** honest-eval core
implementation (E-03), per `Docs/exploration/EVAL_ARCHITECTURE_AND_RED_TEAM_AUDIT_2026-08-31.md`
§2.3 (holdout leak CONFIRMED) and §4 Phase 2.

## What this directory is for

Fixtures placed under `data/fixtures/evals/holdout/` **grade the gate but are
never tuned against**. They are the held-out grading set: their inputs must
not be readable by the people/processes tuning the extractors, or the gate
measures memorization instead of generalization.

## Rules

1. **Holdout fixtures MUST NOT be copied into dev-visible tests.** No
   verbatim input string, no near-verbatim phrasing, no asserting on the
   exact note text of a holdout fixture from anywhere under `tests/`.
   Dev tests verify the same *behavior* through *different phrasings*
   (paraphrase, not copy). The audit found the reverse situation
   (all 15 colloquial gate fixtures leaked verbatim into
   `tests/test_extraction_fixes.py`); de-leaked 2026-09-02.
2. **Additions follow the failure-becomes-fixture rule.** When a real
   production failure (mis-extraction, warning miss, wrong scope) is found,
   first add a paraphrased dev test pinning the behavior, then add a fresh,
   never-before-used phrasing of the same failure class here so the gate —
   not the dev suite — is the place the *exact* real-world string first
   grades.
3. **Holdout results are graded with live collectors only** and reported in
   the D6 gate snapshot with `status="shadow"` (reported, hash-tracked,
   non-blocking), per the audit §4 Phase 2 doctrine. Promote a holdout lane
   to `gating` only after its fixtures pass honestly at the manifest
   threshold.
4. **Promotion out of holdout is a PR with rationale** ("pattern class now
   covered by extractor tests; keep a variant in holdout"), and only ever
   moves copies — the holdout keeps at least one variant of every seeded
   failure class.

## Allowlist — graded fixtures that intentionally exist in dev tests

| Fixture | Dev location | Reason |
| --- | --- | --- |
| `extraction/colloquial_golden.json::colloq_full_note_001` (the Tool-Taster demo note) | `tests/test_extraction_fixes.py::DEMO02_FULL_NOTE` + `TestDemoNoteEndToEnd` | Gate fixture mirror; not a holdout. Kept verbatim as the end-to-end regression anchor for the shipped demo P0. Annotated in the test file. |
| `extraction/colloquial_golden.json::colloq_party_member_ref_001`, `colloq_dates_flex_001` (derived slices quoting the demo note's sentences) | shared sentences reach dev tests only via the `DEMO02_FULL_NOTE` mirror above | Slice fixtures share the full note's text; the full-note allowlist row covers their verbatim presence. No separate dev mirror exists. |

Everything else from the graded corpora (`extraction/golden_dataset.json`,
`extraction/colloquial_golden.json`, `budget/golden_dataset.json`,
`pipeline/pipeline_golden.json`) must appear in `tests/` only as
**paraphrase**, never verbatim. The dev-test file carries the same policy
statement at its DEMO-02 section header.

## Current holdout contents

Empty at policy creation. Seed it by splitting fresh colloquial phrasings
per field family (destination verb-object, party group sizes, season/late-
month dates, per-person budget) that have never appeared in any test,
comment, or extractor source string.
