# Next Actions Review (Codebase + Docs)

**Date**: 2026-04-18  
**Reviewer**: Codex  
**Scope**: Repository structure, current implementation state, architecture/gap docs, test health  
**Method**: Document-first review + code presence checks + runtime test execution

---

## 1) Workflow + Skill Usage

Applied the requested workflow:
1. Analyze request and constraints
2. Review codebase and docs
3. Verify runtime health before recommendations
4. Document completed and pending actions

Skills used from preferred project-level ecosystem:
- `search-first` (context discovery and evidence gathering)
- `verification-before-completion` (test before final recommendations)

Note: `plan-writing` was checked under `/Users/pranay/Projects/skills/` but not present there in this repo context.

---

## 2) Test Verification (Completed)

### Commands run

1. `pytest -q`  
2. `uv run pytest -q`  
3. `PYTHONPATH=. uv run pytest -q`

### Result summary

- `pytest -q` and `uv run pytest -q` fail at collection with `ModuleNotFoundError: No module named 'src'`.
- With explicit import path:

```bash
PYTHONPATH=. uv run pytest -q
```

Result:
- **371 passed, 11 skipped, 0 failed**

### Immediate reliability note

The project's documented default command (`uv run pytest`) is currently not self-sufficient in this environment without `PYTHONPATH=.`, which is a release/process risk.

---

### Status Update (2026-04-24): All P0 Items Verified Complete

The following items, previously marked as pending in this document, have been **verified as implemented** through direct code inspection and test execution:

**P0-A. Test Invocation Contract**
- **Status**: ✅ Complete
- **Evidence**: `pyproject.toml` line 56 contains `pythonpath = ["src", "."]`. `uv run pytest -q` passes with 614+ tests from a clean shell.

**P0-B. Suitability Engine (Tier 1)**
- **Status**: ✅ Complete
- **Evidence**: `src/suitability/` contains: `models.py`, `scoring.py`, `confidence.py`, `catalog.py`, `integration.py`. Tests in `test_suitability.py` (23 tests) and `test_suitability_wave_12.py` (6 tests) all pass.

**P0-C. Suitability Engine (Tier 2)**
- **Status**: ✅ Complete
- **Evidence**: `src/suitability/context_rules.py` implements all sequence rules. Coverage verified by Tier 2 tests in `test_suitability.py`.

See `Docs/SUITABILITY_IMPLEMENTATION_SUMMARY_2026-04-18.md` and `Docs/D1_D4_STATUS_RECONCILIATION_2026-04-21.md` for authoritative implementation details.

---

## 3) Key Evidence Reviewed

Primary files:
- `Docs/MASTER_GAP_REGISTER_2026-04-16.md`
- `Docs/status/COVERAGE_CLOSURE_BUILD_QUEUE_2026-04-15.md`
- `Docs/status/PHASE_1_BUILD_QUEUE.md`
- `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md`
- `Docs/status/ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md`
- Docs/SUITABILITY_IMPLEMENTATION_SUMMARY_2026-04-18.md
- `src/` module inventory and `tests/` suite health

Observed structural state:
- Core intake/decision/llm modules exist and are heavily tested.
- **src/suitability/ implementation is fully complete**. See SUITABILITY_IMPLEMENTATION_SUMMARY_2026-04-18.md.
- Gap register marks discovery docs as complete, but many runtime closures remain planned.

---

## 4) Most Suitable Next Additions (Priority-Ordered)

These are ordered by dependency and production leverage, not by novelty.

### P1-D. Wire Tier 3 LLM contextual scorer via existing hybrid engine pattern

**Why**: Adds contextual depth only where deterministic tiers are ambiguous, consistent with existing cache→rule→LLM architecture.  
**Build targets**:
- `src/suitability/llm_contextual_scorer.py`
- integration points with `src/decision/hybrid_engine.py` and cache key hashing
- `tests/suitability/test_llm_contextual_cache_behavior.py`

**Acceptance**:
- LLM scorer trigger criteria are explicit and testable
- Cache key includes tour-context hash fields
- Deterministic fallback remains default path

---

### P1-E. Close coverage gap between planning docs and executable queue

**Why**: Multiple queue docs exist, but execution state is fragmented; this slows team throughput and handoff quality.  
**Build targets**:
- One canonical execution board doc under `Docs/status/` (single source)
- Cross-links from `Docs/INDEX.md`
- Explicit "Not started / In progress / Done / Blocked" rows per phase item

**Acceptance**:
- One canonical queue is authoritative
- No duplicate contradictory status across queue docs

---

### P1-F. Frontend/API contract tests for Spine integration boundary

**Why**: Backend core is test-healthy; frontend page/API boundary remains under-tested per prior audit notes.  
**Build targets**:
- `frontend` API contract tests (e.g., `/api/spine/run` request/response shape)
- minimal e2e smoke for dashboard → run flow

**Acceptance**:
- Contract mismatch breaks tests early
- At least one end-to-end happy path is continuously testable

---

## 5) Suggested Execution Sequence (Practical)

1. P1-D (Tier 3 LLM contextual scorer)
2. P1-E (queue consolidation and documentation alignment)
3. P1-F (frontend/API contract tests)

This sequence minimizes blast radius while converting the highest-value documented architecture into running code.

---

## 6) Copy-Paste Prompts for Next Build Sessions

Use these as direct implementation prompts for focused runs.

### Prompt 1 — LLM contextual scorer

> Implement P1-D Tier 3 LLM contextual scorer using the existing cache→rule→LLM pattern in `src/decision/hybrid_engine.py`. Ensure cache key includes tour context hash and deterministic tiers remain primary gate.

### Prompt 2 — Queue consolidation

> Implement P1-E. Align all `Docs/status/` queue docs. Mark P0-A, P0-B, P0-C as Done. Ensure `BUILD_QUEUE_CONSOLIDATED.md` is the single source of truth.

### Prompt 3 — Frontend API contract tests

> Implement P1-F. Add minimal e2e tests for `/api/spine/run` happy path.

---

## 7) Completed vs Pending (This Review Run)

### Completed
- Reviewed core docs and architecture decisions
- Verified current runtime test status
- ~~Identified concrete, dependency-ordered additions~~ (superseded by P0 completion)
- ~~Produced implementation prompts for next build runs~~ (superseded by P0 completion)

### Pending (Next Build Work)
- P1-D: Tier 3 LLM contextual scorer (D4 addendum deferred work)
- P1-E: Queue consolidation (ensure canonical status docs are the only source of truth)
- P1-F: Frontend/API contract tests

---

## 8) Git/Release Note

No commit or push performed in this review run.  
If/when a commit is requested in a future run, stage with:

```bash
git add -A
```

and proceed only with explicit user approval.
