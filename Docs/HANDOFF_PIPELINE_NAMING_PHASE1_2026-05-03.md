# Handoff — Pipeline Naming Refactor Phase 1 Complete

**Date**: 2026-05-03
**Status**: Phase 1 complete — ready for review/merge
**Branch**: master (commit `7a0d487`)

---

## Phase 1 scope

Introduce semantic pipeline stage/gate identifiers while preserving legacy
`NB01`-`NB06` compatibility.

Done:
- Central semantic contract (`PipelineStage`, `GateIdentifier` enums)
- Legacy-to-semantic mapping (`resolve_stage`, `resolve_gate`)
- API payload shape evolution (`stage`, `gate`, `legacy_gate`)
- Frontend label mapping (`validationLabelFor()`)
- Raw NB code leakage removal in UI
- Backward-compat regression tests
- Canonical allowed-vs-forbidden rule doc

Not done (and intentionally deferred):
- Class name renames (`NB01CompletionGate`)
- Test filename renames (`test_nb01_v02.py`)
- OTel span renames (`nb01_gate`)
- Persisted draft JSON migration
- Frontend generated-type regeneration (not needed)

---

## Files changed

| # | File | Type | Lines | What changed |
|---|------|------|-------|--------------|
| 1 | `src/intake/constants.py` | Edit | +80 | Added `PipelineStage`, `GateIdentifier`, legacy maps, resolve helpers |
| 2 | `src/intake/gates.py` | Edit | +14 | Added `stage`, `gate_key`, `legacy_code` class attrs |
| 3 | `src/intake/orchestration.py` | Edit | +27 | Validation events emit `stage`+`gate` semantic + `legacy_gate` |
| 4 | `frontend/src/types/spine.ts` | Edit | +46 | `ValidationReport` gains `stage`/`legacy_gate`; `validationLabelFor()` |
| 5 | `frontend/src/app/(agency)/workbench/page.tsx` | Edit | +2 | Alert banner uses `validationLabelFor(report)` - no raw gate leak |
| 6 | `frontend/src/app/(agency)/workbench/PacketTab.tsx` | Edit | +2 | Same fix in PacketTab validation alert |
| 7 | `tests/test_pipeline_semantic_contract.py` | New | +126 | 21 tests for contract parity, legacy compat, label resolution |
| 8 | `tests/test_call_capture_phase2.py` | Edit | +32 | Test isolation fix (TRIPS_DIR cleanup - see separate doc) |
| 9 | `Docs/PIPELINE_NAMING_REFACTOR_2026-05-03.md` | New | ~170 | Migration guide |
| 10 | `Docs/PIPELINE_NAMING_ALLOWED_VS_FORBIDDEN.md` | New | ~120 | Code review rule doc |
| 11 | `Docs/TEST_ISOLATION_FIX_PHASE2_2026-05-03.md` | New | ~80 | Isolates test fix from naming work |
| 12 | `Docs/UX_TERMINOLOGY_AUDIT_2026-04-15.md` | Edit | +1 | Cross-reference to refactor doc |

**Total**: 12 files (4 backend, 2 frontend, 5 docs, 1 test edit, 1 new test file)

---

## Compatibility behavior

### Read (backward compat)
- `resolve_stage("NB01")` -> `PipelineStage.INTAKE_EXTRACTION`
- `resolve_gate("NB01")` -> `GateIdentifier.INTAKE_COMPLETION`
- `resolve_gate("intake_completion")` -> `GateIdentifier.INTAKE_COMPLETION`
- `validationLabelFor({ gate: "NB01" })` -> `"Trip Details"`
- Old draft JSON with `"gate": "NB01"` still renders correctly

### Write (new canonical)
- Validation events emit: `{"stage": "intake_extraction", "gate": "intake_completion", "legacy_gate": "NB01"}`
- `legacy_gate` is temporary compat - will be removed in future phase

---

## Tests run

```
Full backend suite:     1402 passed, 9 skipped, 0 regressions
Semantic contract:      21/21 passed
NB-related pipeline:    228/228 passed
TypeScript:             0 errors
Ruff (changed files):   All checks passed
```

---

## Allowed vs forbidden NB usage

See `Docs/PIPELINE_NAMING_ALLOWED_VS_FORBIDDEN.md` for the full rule set.

Summary:
- **Allowed**: Legacy maps, historical docs, OTel spans, old test names, persisted JSON
- **Forbidden**: Rendered UI text, new API payloads without semantic fields, new test names, product docs

---

## Known legacy NB locations intentionally preserved

| File | Legacy content | Reason |
|------|---------------|--------|
| `src/intake/gates.py` | `NB01CompletionGate`, `NB02JudgmentGate` | Internal compiler-stage identity |
| `tests/test_nb01_v02.py` | `NB01` in filename | Spec traceability |
| `Docs/V02_GOVERNING_PRINCIPLES.md` | `NB01`-`NB06` table | Historical specification |
| `data/drafts/` | `"gate": "NB01"` in old JSON | Persisted data, read-only |
| OTel spans | `nb01_gate`, `nb02_gate` | Observability continuity |
| `spine_api/draft_store_test.py` | Test fixture with `"gate": "NB01"` | Historical fixture |

---

## Next recommended phase

### Phase 2: Actionable Validation UX

The raw code leak is fixed. The next product-facing problem is copy clarity.

Current alert:
```text
Trip Details Need Attention
```

Next target:
```text
Trip Details Need Attention
  Missing: origin city, budget, dates
  Why: These are required before quoting
  Action: Open the Trip Details tab
```

Suggested work:
1. Enrich `ValidationReport` with structured missing-field metadata
2. Add `validationMissingFields()` helper in frontend
3. Render actionable guidance in alert banners
4. Update `validationLabelFor()` to include severity-based action text
5. Design and implement `ValidationActionPanel` component

Do **not** begin Phase 2 until Phase 1 is merged.

---

## Merge recommendation

**Recommended**: Merge now.

This PR is additive, backward-compatible, and scoped. It does not:
- Touch any CI/CD config
- Add new dependencies
- Change database schemas
- Require frontend API regeneration

Risk assessment: **Low**. Changes are behind the existing `Dict[str, Any]` API contract.

---

## Contact / questions

- See `Docs/PIPELINE_NAMING_REFACTOR_2026-05-03.md` for full mapping tables and API payload examples
- See `Docs/PIPELINE_NAMING_ALLOWED_VS_FORBIDDEN.md` for code review enforcement rules
- See `tests/test_pipeline_semantic_contract.py` for contract parity CI tests
