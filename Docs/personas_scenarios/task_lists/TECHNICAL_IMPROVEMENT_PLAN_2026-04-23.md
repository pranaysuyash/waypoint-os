# Technical Improvement Plan (Post Green-Status Review)

Date: 2026-04-23
Scope: P1-S0 and P2-S4 executed case studies

## Goal

Raise test quality from "passing" to "behaviorally and architecturally trustworthy".

## Plan

1. Eliminate malformed/placeholder tests
- Replace non-TSX placeholders with runnable RTL/vitest suites.
- Current target: `frontend/src/components/workspace/panels/__tests__/OverrideModal.test.tsx`.

2. Harden scenario seam contracts
- Keep payload contract tests (mode selector -> `/api/spine/run`) in required suite.
- Keep timeline contract checks in backend runbook suite.

3. Reduce mock-only false confidence
- Where journey tests are heavily mocked, add at least one stronger integration path per scenario family.
- Ensure assertions validate decision-relevant outputs, not only rendering presence.

4. Prevent regression drift in scenario docs
- For each case study, maintain technical + logical open-item lists with explicit status.
- Update status only with evidence (test command + artifact/path).

## Immediate work order

1. Close remaining open technical item in P1-S0 task list (OverrideModal placeholder replacement).
2. Re-run targeted suite for that item.
3. Mark technical list status with verification evidence.
4. Continue to logical/product decisions after technical list reaches no-open status.
