# travel_agency_process_issue_review_2026-05-12

Date: 2026-05-12 (Asia/Kolkata)
Scope: Recheck of intake/deconstruction pipeline assets after parallel-agent updates.
Reviewer: Codex agent

## Why this review was run
The project had concurrent parallel updates and mixed notebook/spec/code generations. The goal was to re-verify canonical runtime contracts, docs consistency, and regression safety before further implementation.

## Instruction + context stack loaded
1. `/Users/pranay/AGENTS.md`
2. `/Users/pranay/Projects/AGENTS.md`
3. `/Users/pranay/Projects/travel_agency_agent/AGENTS.md`
4. `/Users/pranay/Projects/travel_agency_agent/CLAUDE.md`
5. `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/AGENT_KICKOFF_PROMPT.txt`
6. `/Users/pranay/Projects/travel_agency_agent/Docs/context/agent-start/SESSION_CONTEXT.md`
7. Repo-local companion guidance inspected:
   - `/Users/pranay/Projects/travel_agency_agent/.qwen/settings.json`
   - `/Users/pranay/Projects/travel_agency_agent/.claude/handoffs/2026-05-08-203511-phase3-checkpoint-post-push.md`

## Status checks performed
- Virtual env sanity:
  - `source .venv/bin/activate`
  - `python -V` => `Python 3.13.3`
- Notebook inventory check (`notebooks/*.ipynb`) and quick metadata pass.
- Canonical code audit:
  - `/Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py`
  - `/Users/pranay/Projects/travel_agency_agent/src/intake/extractors.py`
  - `/Users/pranay/Projects/travel_agency_agent/src/intake/decision.py`
  - `/Users/pranay/Projects/travel_agency_agent/src/intake/validation.py`
- Spec and doc contract checks:
  - `/Users/pranay/Projects/travel_agency_agent/specs/canonical_packet.schema.json`
  - `/Users/pranay/Projects/travel_agency_agent/specs/source_envelope.schema.json`
  - `/Users/pranay/Projects/travel_agency_agent/specs/decision_policy.md`
  - `/Users/pranay/Projects/travel_agency_agent/notebooks/02_gap_and_decision_contract.md`

## Regression verification run
Executed targeted contract tests:

1) `pytest -q tests/test_nb01_v02.py tests/test_nb02_v02.py tests/test_decision_policy_conformance.py tests/test_contradiction_data_model.py`
- Result: **66 passed**

2) `pytest -q tests/test_nb03_v02.py tests/test_realworld_scenarios_v02.py tests/test_p1_backend_regressions.py`
- Result: **76 passed**

Total in this review: **142 tests passed**.

## Findings (priority ordered, after this pass)

### P0 — Contract-version drift between code and specs — resolved in this pass
- Code packet model is **v0.3** (`packet_models.py`, `schema_version = "0.3"`).
- `specs/canonical_packet.schema.json` now declares packet schema const as **v0.3** and validates `CanonicalPacket.to_dict()`.
- `specs/source_envelope.schema.json` now mirrors the runtime `SourceEnvelope` dataclass instead of the earlier v0.1 raw-intake shape.

Impact:
- Prior to this pass, new implementers could follow stale schemas and accidentally regress runtime behavior.
- Current state is aligned by direct schema validation against runtime objects.

### P1 — Stale NB02 contract note had legacy fields and legacy flow
- `notebooks/02_gap_and_decision_contract.md` contained legacy field names and rules (v0.1-era language).
- This is now risky because active runtime and tests are v0.2/v0.3 hybrid migration.

Action taken in this review:
- Added a **deprecation notice** at top of the file and explicit canonical pointers.
- Historical content preserved (no deletion).

### P1 — Documentation split-brain risk (v0.1/v0.2/v0.3 simultaneously) — reduced, not fully eliminated
- Current code comments and docs mix v0.2 and v0.3 references across notebooks/specs.
- Several notebook docs still claim v0.2 while packet runtime class is v0.3.

Impact:
- Review feedback can become contradictory depending on which file is read.
- Onboarding cost rises; architecture debates recur due to stale references.

Action taken in this review:
- Added `/Users/pranay/Projects/travel_agency_agent/specs/runtime_contract_version_matrix_2026-05-12.md`.

### P2 — Non-canonical prompt registry path — not present on final recheck
- Earlier review state referenced `prompts/registry l`.
- Final recheck with `find prompts -maxdepth 2` reports `prompts` does not currently exist in this working tree.

Impact:
- No current prompt-registry path action was taken because the artifact is absent in current ground truth.

Recommendation:
- If prompt assets are reintroduced, create only canonical `prompts/registry/` and document it in `specs/runtime_contract_version_matrix_2026-05-12.md` or a prompt-specific contract doc.

## External-review intake assessment
External reviewer feedback was valuable and is now mostly satisfied by runtime code:
- Authority precedence: fixed in runtime model.
- Hypothesis leakage: guarded by strict setter methods.
- Derived signals path: present.
- Hybrid conflict policy: named resolver exists.
- Event-log readiness: explicit and enforced.

Residual concern from first principles:
- Spec/code/doc alignment is now a larger risk than runtime correctness.

## No-regression statement
Based on the targeted tests above and the post-fix rerun below, there is no evidence in this review of runtime regression in NB01/NB02/NB03 and decision policy conformance paths.

## Post-fix verification

Schema validation:
- `specs/canonical_packet.schema.json` passes `Draft202012Validator.check_schema`.
- `specs/source_envelope.schema.json` passes `Draft202012Validator.check_schema`.
- A live `SourceEnvelope.from_freeform(...)` object validates against `specs/source_envelope.schema.json`.
- A live `CanonicalPacket(...).to_dict()` object validates against `specs/canonical_packet.schema.json`.

Targeted regression suite:
- Command: `pytest -q tests/test_nb01_v02.py tests/test_nb02_v02.py tests/test_decision_policy_conformance.py tests/test_contradiction_data_model.py tests/test_nb03_v02.py tests/test_realworld_scenarios_v02.py tests/test_p1_backend_regressions.py`
- Result: **142 passed**

## Immediate next actions (recommended)
1. Continue reducing v0.2/v0.3 wording drift in notebook markdown and older docs.
2. Add schema validation to CI or the relevant local verification script so runtime packet/schema drift is caught automatically.
3. If prompt assets are reintroduced, use only `prompts/registry/` as the canonical path and document it.

## Change log for this review
- Updated: `/Users/pranay/Projects/travel_agency_agent/notebooks/02_gap_and_decision_contract.md`
  - Added top deprecation notice and canonical-source pointers.
- Updated: `/Users/pranay/Projects/travel_agency_agent/specs/canonical_packet.schema.json`
  - Aligned schema const and serialized fields with runtime `CanonicalPacket` v0.3.
- Updated: `/Users/pranay/Projects/travel_agency_agent/specs/source_envelope.schema.json`
  - Aligned schema with runtime `SourceEnvelope` dataclass.
- Updated: `/Users/pranay/Projects/travel_agency_agent/specs/INDEX.md`
  - Added runtime contract version matrix pointer.
- Added: `/Users/pranay/Projects/travel_agency_agent/specs/runtime_contract_version_matrix_2026-05-12.md`
  - Records source-of-truth versions and migration notes.
- Added: `/Users/pranay/Projects/travel_agency_agent/Docs/travel_agency_process_issue_review_2026-05-12.md`

## Evidence artifacts touched/read
- `/Users/pranay/Projects/travel_agency_agent/src/intake/packet_models.py`
- `/Users/pranay/Projects/travel_agency_agent/src/intake/decision.py`
- `/Users/pranay/Projects/travel_agency_agent/src/intake/validation.py`
- `/Users/pranay/Projects/travel_agency_agent/specs/canonical_packet.schema.json`
- `/Users/pranay/Projects/travel_agency_agent/specs/source_envelope.schema.json`
- `/Users/pranay/Projects/travel_agency_agent/notebooks/01_intake_and_normalization.ipynb`
- `/Users/pranay/Projects/travel_agency_agent/notebooks/02_gap_and_decision.ipynb`
- `/Users/pranay/Projects/travel_agency_agent/notebooks/02_gap_and_decision_contract.md`
