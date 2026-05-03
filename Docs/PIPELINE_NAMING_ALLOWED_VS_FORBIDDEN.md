# NB Code Usage Rules — Allowed vs Forbidden

**Date**: 2026-05-03
**Status**: Canonical rule (follow or flag in code review)
**Scope**: Pipeline stage identifiers (NB01–NB06)

---

## Why these rules exist

NB codes (`NB01`–`NB06`) are historical pipeline stage identifiers from the early notebook-based design. They serve as debug/traceability anchors but leak into user-facing surfaces when used as product language. The rules below draw the line.

---

## ALLOWED — where NB codes may appear

| Context | Example | Rationale |
|---|---|---|
| Python class names | `NB01CompletionGate`, `NB02JudgmentGate` | Internal compiler-pass identity; easy to grep |
| Test filenames | `test_nb01_v02.py`, `test_nb02_v02.py` | Traceability to spec documents (`NB01_V02_SPEC.md`) |
| OTel span names | `nb01_gate`, `nb02_gate` | Observability continuity; spans are queried by name |
| Module docstrings | `intake — NB01 v0.2` | Historical versioning |
| Legacy spec filenames | `NB01_V02_SPEC.md`, `NB02_V02_SPEC.md` | Spec history preserved |
| Legacy mapping tables | `_LEGACY_NB_TO_STAGE`, `_LEGACY_NB_TO_GATE` | Runtime compatibility |
| Backward-compat parsing | `resolve_stage("NB01")` | Accept old payloads |
| Old draft JSON on disk | `"gate": "NB01"` in `data/drafts/` | Persisted data; read via compat layer |
| Internal debug logs | `logger.debug("NB01 gate returned ESCALATE")` | Dev-only, never in user logs |

---

## FORBIDDEN — where NB codes must NOT appear

| Context | Bad Example | Good Replacement |
|---|---|---|
| Rendered UI text | `<span>NB01</span>` in alert banner | `validationLabelFor(report)` → "Trip Details Need Attention" |
| API payload primary fields | `{"gate": "NB01"}` without semantic fields | `{"stage": "intake_extraction", "gate": "intake_completion", "legacy_gate": "NB01"}` |
| Frontend type definitions (new) | `gate?: string` as sole field | `gate?: string` with `stage?: string; legacy_gate?: string` |
| Product docs / help text | "When NB01 fails..." | "When intake extraction fails..." |
| New test names | `test_nb01_something_new` | `test_intake_completion_something_new` |
| User-facing error messages | `"NB01 gate escalation"` | `"Trip details need attention"` |
| Telemetry/analytics labels sent to dashboards | `event_name: "nb01_gate"` | `event_name: "intake_completion_gate"` |
| URL paths / route names | `/api/nb01/validate` | `/api/intake/validate` |

---

## Enforcement

### Automated checks (CI)

```bash
# Block raw NB codes in frontend source
rg "\bNB0[1-6]\b" frontend/src --glob "*.{ts,tsx}" -N
# Should return: only legacy map entries in spine.ts

# Block unmapped gate rendering in frontend
rg "result_validation\.gate" frontend/src --glob "*.{ts,tsx}" -N
# Should return: only inside validationLabelFor() calls

# Block raw NB in backend orchestration payloads
rg '"gate": "NB0[1-6]"' src/intake --include "*.py" -N
# Should return: 0 matches (should use semantic constants)
```

### Code review checklist

When reviewing PRs that touch pipeline stages or gates:

- [ ] No `NB0` in user-facing strings
- [ ] `legacy_gate` is only used as a read-only compat field
- [ ] `gate` field in new code uses semantic value (`intake_completion`, etc.)
- [ ] Frontend always calls `validationLabelFor()` or equivalent
- [ ] New tests don't use `NB0` in test names unless specifically testing legacy compat

---

## Violation reporting

If you see an NB code in a forbidden context, open an issue or fix in the same PR:

1. Map the legacy code to the semantic identifier
2. Update the display code to use `validationLabelFor()`
3. Update the API payload to include `stage` + `gate` fields
4. Keep `legacy_gate` for backward compat only

---

## References

- `Docs/PIPELINE_NAMING_REFACTOR_2026-05-03.md` — Full migration guide
- `Docs/UX_TERMINOLOGY_AUDIT_2026-04-15.md` — Original P0 issue
- `src/intake/constants.py` — Canonical `PipelineStage` / `GateIdentifier` enums
- `frontend/src/types/spine.ts` — `validationLabelFor()` and compat maps
