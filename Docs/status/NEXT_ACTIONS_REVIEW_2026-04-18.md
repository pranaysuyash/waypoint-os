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

The project’s documented default command (`uv run pytest`) is currently not self-sufficient in this environment without `PYTHONPATH=.`, which is a release/process risk.

---

## 3) Key Evidence Reviewed

Primary files:
- `Docs/MASTER_GAP_REGISTER_2026-04-16.md`
- `Docs/status/COVERAGE_CLOSURE_BUILD_QUEUE_2026-04-15.md`
- `Docs/status/PHASE_1_BUILD_QUEUE.md`
- `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md`
- `Docs/status/ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md`
- `src/` module inventory and `tests/` suite health

Observed structural state:
- Core intake/decision/llm modules exist and are heavily tested.
- No `src/suitability/` implementation exists yet despite mature architecture + handoff docs.
- Gap register marks discovery docs as complete, but many runtime closures remain planned.

---

## 4) Most Suitable Next Additions (Priority-Ordered)

These are ordered by dependency and production leverage, not by novelty.

### P0-A. Stabilize test invocation contract

**Why now**: Current default test command fails without env patching; this undermines CI/dev reliability and can hide regressions.  
**Build targets**:
- `pyproject.toml` (`[tool.pytest.ini_options]`) to include a deterministic pythonpath strategy
- Optional `tools/test_runner.py` or `Makefile`/script wrapper for canonical test invocation
- `README.md` + docs command alignment

**Acceptance**:
- `uv run pytest -q` passes from clean shell without manual `PYTHONPATH` export.
- Docs and CI command match exactly.

---

### P0-B. Implement Suitability Foundation (Tier 1 deterministic scorer)

**Why now**: Architecture for D4/D6 is finalized (latest addendum), but runtime module is missing; this is the highest-value implementation/doc gap.  
**Build targets**:
- `src/suitability/models.py`
- `src/suitability/scoring.py`
- `src/suitability/confidence.py`
- `src/suitability/__init__.py`
- `tests/suitability/test_scoring_tier1.py`

**Scope**:
- ActivityDefinition + SuitabilityContext + ActivitySuitability contracts
- Tag-predicate rules for hard exclusion / discourage / recommend
- Confidence output and missing-signal diagnostics

**Acceptance**:
- Tier 1 per-activity fixtures pass
- Hard exclusions are deterministic and test-visible
- Outputs include score, confidence, reasons

---

### P0-C. Implement Tour-Context Deterministic Layer (Tier 2 coherence)

**Why now**: The addendum explicitly elevates day/trip coherence as the guardrail against “works in isolation, breaks in tour sequence.”  
**Build targets**:
- `src/suitability/context_rules.py`
- `tests/suitability/test_scoring_tier2_sequence.py`
- Fixtures for day/trip sequence patterns

**Scope**:
- Add context fields (`day_activities`, `trip_activities`, climate/season signals)
- Sequence checks: cumulative intensity, rest-day gaps, duration overload, climate amplification

**Acceptance**:
- Sequence-specific risks appear in `generated_risks`
- Same activity can score differently depending on day/trip context (by design)

---

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
- Explicit “Not started / In progress / Done / Blocked” rows per phase item

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

1. P0-A (test command stabilization)
2. P0-B (suitability contracts + Tier 1)
3. P0-C (Tier 2 sequence coherence)
4. P1-D (Tier 3 LLM contextual scorer)
5. P1-E (queue consolidation)
6. P1-F (frontend/API contract tests)

This sequence minimizes blast radius while converting the highest-value documented architecture into running code.

---

## 6) Copy-Paste Prompts for Next Build Sessions

Use these as direct implementation prompts for focused runs.

### Prompt 1 — Test contract hardening

> Implement P0-A from `Docs/status/NEXT_ACTIONS_REVIEW_2026-04-18.md`: make `uv run pytest -q` pass without manual `PYTHONPATH`. Update `pyproject.toml`, docs, and add a regression check. Run tests and document exact before/after commands and outputs.

### Prompt 2 — Suitability Tier 1

> Implement P0-B (Tier 1 deterministic suitability engine) exactly aligned to `Docs/ARCHITECTURE_DECISION_D4_SUBDECISIONS_ADDENDUM_2026-04-18.md` and `Docs/status/ACTIVITY_SUITABILITY_IMPLEMENTATION_HANDOFF_2026-04-16.md`. Create `src/suitability/*` contracts and tests. Keep changes additive and deterministic-first.

### Prompt 3 — Suitability Tier 2

> Implement P0-C tour-context deterministic sequence rules. Add `day_activities` and `trip_activities` context handling, cumulative intensity checks, and generated risk outputs. Add sequence fixtures and tests that prove context-sensitive scoring.

### Prompt 4 — LLM contextual scorer

> Implement P1-D Tier 3 LLM contextual scorer using the existing cache→rule→LLM pattern in `src/decision/hybrid_engine.py`. Ensure cache key includes tour context hash and deterministic tiers remain primary gate.

---

## 7) Completed vs Pending (This Review Run)

### Completed
- Reviewed core docs and architecture decisions
- Verified current runtime test status
- Identified concrete, dependency-ordered additions
- Produced implementation prompts for next build runs

### Pending (Next Build Work)
- Actual implementation of P0-A through P1-F
- Queue consolidation and progress tracking updates during implementation

---

## 8) Git/Release Note

No commit or push performed in this review run.  
If/when a commit is requested in a future run, stage with:

```bash
git add -A
```

and proceed only with explicit user approval.
