# Stub / Placeholder / TODO Detection Audit

**Date**: 2026-05-03
**Tool**: `comprehensive-audit/scripts/stub_detect.py` v2 (enhanced)
**Scope**: `travel_agency_agent` — source-only scan (`--nosource` flag)
**Status**: Complete

## Quick Numbers

210 findings across 77 files. 26 HIGH, 180 MEDIUM, 4 LOW.
After manual review: 2 real blocking gaps. 3 real low-severity TODOs.
Everything else is false positives or legitimate patterns.

---

## Real Findings

### HIGH — Blocking Gaps

1. `src/intake/extractors.py:1792`
   `sourcing_path` derived signal has `maturity="stub"`.
   Note: "Stub signal — no real supplier data available yet."
   The signal is wired into the pipeline but has no backend data source.

2. `tests/test_usage_guard.py:655`
   `def reset(self): pass` — empty method. Unimplemented test fixture.

### MEDIUM — Real TODOs / Debt

3. `frontend/instrumentation.ts:5` — `// TODO: re-enable telemetry`
4. `frontend/src/app/api/trips/route.ts:79` — `// TODO: Call spine pipeline`
5. `src/decision/health.py:181` — `# TODO: Add actual LLM ping/health check`
6. `spine_api/services/membership_service.py:53` — "placeholder password" on invite
7. `src/intake/orchestration.py:93` — `# Placeholder for actual packet delta`

### Product Decisions (Not Code Gaps)

8. `frontend/src/lib/nav-modules.ts` — 8 nav modules at `enabled: false`:
   Quotes, Bookings, Documents, Payments, Suppliers, Audit, Knowledge Base.
   Intentional roadmap placeholders with "Soon" badges. Not missing code.

---

## False Positive Analysis

### 23 HIGH "stub" hits — all noise

The word "stub" appears inside the maturity tag system itself:
- Type definitions: `Literal["stub", "heuristic", "verified"]`
- Validation logic: `if slot.maturity == "stub"`
- Test assertions: `assert signal["maturity"] == "stub"`
These are infrastructure that manages stubs, not stubs themselves.

### 105 MEDIUM "placeholder" hits — mostly noise

~90 are React `placeholder={...}` props on inputs/textareas.
Standard HTML patterns, not code gaps.

### 31 MEDIUM API "empty return" hits — all noise

`return []` and `return {}` are legitimate "no results" fallbacks
in production functions with real logic above them.

### 21 MEDIUM "TBD" hits — all noise

Field defaults in frontend adapters and test fixtures for
"data not yet available" display states.

---

## Tool Improvements Needed

- Filter "stub" inside type annotations and validation logic
- Skip React placeholder={...} props (only flag in comment context)
- Context-check `return []` — only flag when it's the sole return in a handler

---

## Source

Script: `/Users/pranay/.hermes/skills/software-development/comprehensive-audit/scripts/stub_detect.py`
Skill: `/Users/pranay/.hermes/skills/software-development/comprehensive-audit/SKILL.md`
