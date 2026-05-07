# ChatGPT Secondary Review Brief — server.py Refactor

Date: 2026-05-07
Repo: travel_agency_agent
Branch: master
Latest pushed commit: 804d778
Primary file: spine_api/server.py
Reference plan: Docs/status/SERVER_PY_REFACTOR_REVIEW_2026-05-07.md

## Goal
Get an independent architecture/risk review of the server.py refactor plan under strict no-regression constraints.

## Current state
- server.py is ~5k LOC and includes 100+ route decorators.
- It mixes app/bootstrap wiring, startup schema/invariant checks, route handlers, and orchestration logic.
- Recently added behavior that must be preserved:
  - PUBLIC_CHECKER_AGENCY_ID env resolution
  - SQL-mode fail-fast startup invariant validation
  - Product B event instrumentation and KPI endpoints

## Non-negotiables
1) No behavior regressions.
2) Keep endpoint contracts stable.
3) Preserve startup fail-fast invariant behavior.
4) Preserve auth/rate-limit/audit side effects.
5) Use phased extraction (no rewrite).

## Request to ChatGPT
Review Docs/status/SERVER_PY_REFACTOR_REVIEW_2026-05-07.md and provide:

A. Plan validation
- Is the phased plan sound?
- Which phase boundaries are high risk and why?
- What hidden coupling risks do you expect?

B. Design improvements
- Better module boundaries if needed.
- Extraction candidates that should move earlier/later.
- Anti-patterns in proposed layering.

C. Regression controls
- Exact test gates per phase.
- Route parity and startup invariant checks.
- Smoke checks before/after each phase.

D. Execution sequencing
- Smallest safe first PR.
- PR slicing for phases 1–5.
- Blast radius estimate per phase.

## Required output format
1. Verdict (Accept / Accept with modifications / Reject)
2. Top 5 risks (ranked)
3. Improved phase plan (if different)
4. Per-phase verification checklist
5. First PR scope (files + acceptance criteria)
6. “Do not do” list

## Explicitly avoid
- Rewrite-from-scratch advice
- Broad framework migration
- API contract changes in first PR

## Useful references
- spine_api/server.py
- tests/test_public_checker_agency_config.py
- tests/test_product_b_events.py
- Docs/status/PRODUCTB_SMOKE_RUN_2026-05-07.md
- Docs/status/PUBLIC_CHECKER_AGENCY_CONFIG_HARDENING_2026-05-07.md
- Docs/status/SERVER_PY_REFACTOR_REVIEW_2026-05-07.md
