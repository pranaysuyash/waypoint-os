# First Principles Gap Assessment (2026-04-14)

## Purpose
This document translates first-principles thinking into an execution checkpoint:
- what exists in code now,
- what must exist for MVP correctness,
- what should be built next in strict dependency order.

## Baseline Reviewed
- `Docs/FIRST_PRINCIPLES_FOUNDATION_2026-04-14.md`
- `src/intake/packet_models.py`
- `src/intake/normalizer.py`
- `src/intake/validation.py`
- `src/intake/extractors.py`
- `src/intake/decision.py`
- `specs/decision_policy.md`

## What We Have (Current State)

### 1) Deterministic Intake Core Exists
- Canonical packet modeling is implemented (`packet_models.py`).
- Source extraction and normalization pipeline exists (`extractors.py`, `normalizer.py`).
- Contradiction and ambiguity handling exists (`validation.py`).

### 2) Decision Gate Exists
- Decision outcomes exist (`ASK_FOLLOWUP`, `PROCEED_INTERNAL_DRAFT`, `PROCEED_TRAVELER_SAFE`, `BRANCH_OPTIONS`, `STOP_NEEDS_REVIEW`) in `decision.py`.
- Basic feasibility checks are present, including budget feasibility heuristics.

### 3) Test Baseline Is Good for Core Modules
- `pytest -q tests` currently passes (core test suite health).
- Full-repo `pytest -q` still blocked by known notebook test loader issue (tracked separately in `Docs/issue_review.md`).

## What We Should Have (MVP Correctness)

### A) Stage 0 Contract Lock (Must Be Explicit)
- A single authoritative contract for canonical packet fields/invariants.
- Clear source authority precedence policy and deterministic merge rules.
- Policy docs and code version alignment.

### B) Stage 1 Deterministic Compiler Hardening
- Deterministic transformations should be covered by property-like tests for stable output.
- Contradiction classes should map one-to-one with user-facing follow-up intents.

### C) Stage 2 Realism Engine (Currently Partial)
- Budget realism should include:
  - route/seasonality sensitivity,
  - transfer and fatigue constraints,
  - party profile effects (elderly/toddler/medical constraints),
  - destination-level floor/ceiling bands.
- Current feasibility logic appears heuristic and not yet rich enough for robust agency-grade drafts.

### D) Stage 3 Optioning and Ranking
- Multi-option generation (conservative/balanced/premium, etc.).
- Deterministic scoring trace: why option A outranks option B.
- Explicit downgrade/upgrade suggestions when constraints conflict.

## Gap Summary

## P0 (Immediate)
1. Lock and publish one canonical contract source of truth (schema + code + policy alignment).
2. Expand deterministic tests around intake normalization and ambiguity/contradiction transitions.
3. Fix policy drift/mismatch where docs indicate different decision policy versioning from runtime behavior.

## P1 (Next)
1. Upgrade feasibility from static heuristic table to structured realism model inputs.
2. Implement deterministic option generator with ranking trace and acceptance thresholds.
3. Add scenario regression packs (family, budget-tight, mixed constraints, contradiction-heavy).

## P2 (After P0/P1)
1. Plug ranking outputs into planner orchestration (without breaking deterministic gate).
2. Add monitoring for decision-state frequencies and follow-up friction.
3. Calibrate scoring weights using offline eval loops.

## What Next (Execution Order)
1. **Contract/Policy Alignment Pass (P0)**
2. **Deterministic Test Hardening (P0)**
3. **Feasibility Realism Upgrade (P1)**
4. **Option + Ranking Engine (P1)**
5. **Orchestration Integration + Metrics (P2)**

## Acceptance Criteria for Next Checkpoint
- Contract and policy docs/code are version-aligned.
- Core deterministic tests pass and cover ambiguity/contradiction transitions.
- Feasibility decision includes at least one route/seasonality and one party-profile realism factor.
- Optioning returns >= 2 valid alternatives with scoring rationale.
