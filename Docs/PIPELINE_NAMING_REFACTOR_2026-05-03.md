# Pipeline Naming Refactor — NB Codes to Semantic Identifiers

**Date**: 2026-05-03
**Status**: Implemented (Phase 1 — semantic contract layer + UI prep)

---

## Why

NB01-NB06 are pipeline stage identifiers masquerading as product names. They leak into
API payloads and UI banners, creating confusion for travel agency operators who don't
know (or care) what "NB01" means.

The fix is **not** a blind rename. It's a **three-layer naming model** that demotes NB
codes to internal legacy identifiers while promoting semantic names into the product contract.

## Three-Layer Naming Model

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: Internal Stage Code (kept)                     │
│ NB01, NB02, NB03, NB04, NB05, NB06                     │
│ → Class names, test filenames, OTel spans, doc headings │
├─────────────────────────────────────────────────────────┤
│ Layer 2: Semantic Contract Key (new)                    │
│ intake_extraction, decision_judgment, session_strategy  │
│ → API payloads, log messages, FE type lookups           │
├─────────────────────────────────────────────────────────┤
│ Layer 3: User-Facing Label (FE-only)                    │
│ "Trip Details", "Ready to Quote?", "Build Proposal"     │
│ → Rendered in UI banners, tabs, status badges           │
└─────────────────────────────────────────────────────────┘
```

## Canonical Mapping

| Legacy     | Semantic Stage             | Semantic Gate         | User Label            |
|------------|----------------------------|-----------------------|-----------------------|
| NB01       | `intake_extraction`        | `intake_completion`   | Trip Details          |
| NB02       | `decision_judgment`        | `decision_readiness`  | Ready to Quote        |
| NB03       | `session_strategy`         | (none yet)            | Strategy              |
| NB04       | `traveler_proposal`        | (none yet)            | Build Proposal        |
| NB05       | `golden_path_evaluation`   | (none yet)            | Final Review          |
| NB06       | `shadow_replay`            | (none yet)            | Production QA         |

## What Changed

### Backend

| File | Change |
|------|--------|
| `src/intake/constants.py` | Added `PipelineStage` enum, `GateIdentifier` enum, `_LEGACY_NB_TO_STAGE`/`_LEGACY_NB_TO_GATE` maps, `resolve_stage()`/`resolve_gate()` helpers |
| `src/intake/gates.py` | Added `stage`, `gate_key`, `legacy_code` class attributes to `NB01CompletionGate` and `NB02JudgmentGate` |
| `src/intake/orchestration.py` | Validation event payloads now emit `stage` + `gate` (semantic) + `legacy_gate` (NB01 compat). Audit reason strings use semantic names. Gate rationale keys changed from `"NB01_ESCALATE"` → `"intake_completion"` |

### Frontend

| File | Change |
|------|--------|
| `frontend/src/types/spine.ts` | Added `stage`, `legacy_gate` fields to `ValidationReport`. Added `validationLabelFor()` function mapping semantic/legacy gate keys → user labels |
| `frontend/src/app/(agency)/workbench/page.tsx` | Alert banner now uses `validationLabelFor()` instead of rendering raw `gate` string. No more "NB01" monospace leak |
| `frontend/src/app/(agency)/workbench/PacketTab.tsx` | Same fix — validation alert uses `validationLabelFor()` |

### API Payload Shape (before → after)

```jsonc
// BEFORE
{"status": "ESCALATED", "gate": "NB01", "reasons": ["..."]}

// AFTER
{
  "status": "ESCALATED",
  "stage": "intake_extraction",
  "gate": "intake_completion",
  "legacy_gate": "NB01",
  "reasons": ["..."]
}
```

## What Was Preserved (Intentionally Not Changed)

| What | Why |
|------|-----|
| Class names: `NB01CompletionGate`, `NB02JudgmentGate` | Internal compiler-pass identifiers — meaningful for debugging |
| Test filenames: `test_nb01_v02.py`, `test_nb02_v02.py` | Traceability to specs (`NB01_V02_SPEC.md`, etc.) |
| OTel span names: `nb01_gate`, `nb02_gate` | Observability continuity — spans are queried by name |
| Module docstrings: `NB01 v0.2`, `NB02 v0.2` | Historical / spec alignment |
| `data/drafts/draft_a6cd62ba5757.json` | Persisted historical data — reads work via legacy map |

## Compatibility Strategy

- **Read**: Accept both old (`"NB01"`) and new (`"intake_completion"`) values via `resolve_gate()` and `validationLabelFor()` LEGACY_LABELS map
- **Write**: Always emit the new semantic values in `stage` and `gate` fields
- **Display**: Never render raw gate values — use `validationLabelFor()` exclusively
- **`legacy_gate` field**: Temporary compat, slated for removal after all persisted drafts are migrated

## Future Cleanup (Phase 2 — when ready)

1. Remove `legacy_gate` from validation event payloads
2. Remove `LEGACY_LABELS` from `validationLabelFor()`
3. Rename `PipelineStage.SESSION_STRATEGY` → more descriptive (TBD)
4. Add semantic gate identifiers for NB03-NB06 when those layers are implemented
5. Rename gate classes (`NB01CompletionGate` → `IntakeCompletionGate`) after NB04-NB06 land

## Test Results

```
1346 passed, 44 skipped, 0 regressions
TypeScript: 0 errors
Ruff (changed files): All checks passed
```

## References

- `Docs/UX_TERMINOLOGY_AUDIT_2026-04-15.md` — Original UX audit flagging NB leakage as P0
- `Docs/V02_GOVERNING_PRINCIPLES.md` — Pipeline layer ownership definitions
- `src/intake/constants.py` — Canonical `PipelineStage` / `GateIdentifier` enums
- `frontend/src/types/spine.ts:310-346` — `validationLabelFor()` implementation
