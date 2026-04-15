# Pre-Build Corrections: Operator Workbench / Agency Flow Simulator

**Date:** 2026-04-15
**Status:** Approved for execution
**Scope:** Apply these corrections first, then execute tickets WB-001 → WB-002 → WB-003 → (stop for review)

---

## Scope Guardrails

- Do NOT redesign the plan.
- Do NOT widen scope.
- Do NOT add auth, DB, API, or infra.
- Do NOT duplicate spine logic in the UI.
- Do NOT rename packages.
- Keep the existing component spec and ticket map.

---

## Correction 1: Move Orchestration Out of the Streamlit App

**Problem:** The spec says the UI should call "one local orchestration helper function in app." This couples the spine to the UI and makes future callers (CLI, API, batch eval) impossible without duplication.

**Fix:** Create a shared spine entrypoint under `src/intake/orchestration.py`.

### File: `src/intake/orchestration.py`

- Function: `run_spine_once(...)`
- Must call ONLY the frozen shared modules:
  - `ExtractionPipeline` (from `src/intake/extractors.py`)
  - `validate_packet` (from `src/intake/validation.py`)
  - `run_gap_and_decision` (from `src/intake/decision.py`)
  - `build_session_strategy_and_bundle` (from `src/intake/strategy.py`)
  - `sanitize_for_traveler` (from `src/intake/safety.py`)
  - `check_no_leakage` / `enforce_no_leakage` (from `src/intake/safety.py`)
  - `build_internal_bundle` (from `src/intake/strategy.py`)
  - `build_traveler_safe_bundle` (from `src/intake/strategy.py`)

### Required Output Shape

`run_spine_once(...)` must return a single `SpineResult` dataclass with these fields:

| Field              | Type                     | Source                                   |
| ------------------ | ------------------------ | ---------------------------------------- |
| `packet`           | `CanonicalPacket`        | ExtractionPipeline output                |
| `validation`       | `PacketValidationReport` | `validate_packet(packet)`                |
| `decision`         | `DecisionResult`         | `run_gap_and_decision(packet)`           |
| `strategy`         | `SessionStrategy`        | `build_session_strategy_and_bundle(...)` |
| `internal_bundle`  | `PromptBundle`           | `build_internal_bundle(...)`             |
| `traveler_bundle`  | `PromptBundle`           | `build_traveler_safe_bundle(...)`        |
| `sanitized_view`   | `SanitizedPacketView`    | `sanitize_for_traveler(packet)`          |
| `leakage_result`   | `dict`                   | `{ "leaks": [...], "is_safe": bool }`    |
| `assertion_result` | `Optional[dict]`         | Only set when fixture compare is enabled |
| `run_timestamp`    | `str`                    | ISO timestamp of the run                 |

### Streamlit App Contract

The Streamlit app must:

1. Import `run_spine_once` from `src.intake.orchestration`
2. Call it only when `Run Spine` is clicked or a fixture is loaded/run
3. Store the result in `st.session_state`
4. Display the stored result — NOT recompute it

---

## Correction 2: Formalize Fixture Shape

**Problem:** Scenario fixtures are described informally. Compare mode and fixture loading will drift without a strict schema.

**Fix:** Define one stable fixture schema for `data/fixtures/scenarios/*.json`.

### Fixture Schema (JSON)

Every fixture file must conform to this shape:

```json
{
  "scenario_id": "string — unique stable ID, e.g. SC-001",
  "title": "string — human-readable name",
  "mode": "normal_intake | audit | emergency | follow_up | cancellation | post_trip | coordinator_group | owner_review",
  "stage": "discovery | shortlist | proposal | booking",
  "inputs": {
    "raw_note": "string — freeform agency/traveler text",
    "owner_note": "string | null — owner-specific instructions",
    "structured_json": "object | null — structured import data",
    "itinerary_text": "string | null — existing itinerary text"
  },
  "expected": {
    "allowed_decision_states": ["string — one or more acceptable states"],
    "required_packet_fields": [
      "string — fact field names that must be present"
    ],
    "forbidden_traveler_terms": [
      "string — terms that must NOT appear in traveler bundle"
    ],
    "leakage_expected": "boolean — should leakage be detected? (for negative tests)",
    "assertions": [
      {
        "type": "field_present | field_absent | field_equals | decision_state_in | no_leakage | leakage_detected",
        "field": "string (optional)",
        "value": "any (optional)",
        "message": "string — failure explanation"
      }
    ]
  }
}
```

### App Contract for Fixtures

- Load fixtures from `data/fixtures/scenarios/*.json` using this exact shape
- Validate fixture shape on load (reject malformed fixtures with clear error)
- Compare mode must evaluate against this shape only — no ad-hoc assertions

---

## Correction 3: Make Sanitized View First-Class on the Safety Screen

**Problem:** The spec compares "raw packet vs sanitized traveler bundle" — which mixes a data structure (raw packet) with an output artifact (traveler bundle). The sanitized view must be its own first-class object.

**Fix:** The Safety screen must show these three artifacts separately:

1. **Raw Packet** — the full `CanonicalPacket` with all internal data
2. **Sanitized Traveler-Safe View** — the `SanitizedPacketView` (intermediate transformation)
3. **Final Traveler-Safe Bundle** — the `PromptBundle` (final output to traveler)

### Screen Layout

```
┌─────────────────────────────────────────────┐
│ SAFETY / LEAKAGE SCREEN                     │
├─────────────┬───────────────┬───────────────┤
│ RAW PACKET  │ SANITIZED VIEW│ TRAVELER      │
│             │               │ BUNDLE        │
│ All facts,  │ Filtered facts│ user_message  │
│ hypotheses, │ + safe derived│ + system_ctx  │
│ contradicts │ signals only  │ + follow_ups  │
├─────────────┴───────────────┴───────────────┤
│ LEAKAGE CHECK: ✅ SAFE  |  ❌ LEAKAGE DETECTED │
│ Reasons: (if any)                           │
└─────────────────────────────────────────────┘
```

The boundary transformation must be visible: raw → sanitized → final.

---

## Correction 4: Harden Strict-mode Behavior

**Problem:** "Strict mode failure visibly flagged" is too weak. A red banner alone does not prevent the user from seeing leaked content.

**Fix:** In strict mode, if leakage is detected:

1. **Traveler-safe preview must be suppressed** or clearly marked INVALID with a red border and "STRICT MODE: OUTPUT BLOCKED" label
2. **Leakage reasons must be shown prominently** in a dedicated panel above the suppressed preview
3. **Compare/assertion panel must mark the run as FAILED** — not just warned
4. The `sanitized_view` must still be shown (for debugging) but the `traveler_bundle` must be blocked

### Strict Mode Checklist (Acceptance Criterion)

- [ ] Leakage detected → red banner with count of leaks
- [ ] Leakage reasons listed explicitly (term + field + excerpt)
- [ ] Traveler bundle preview is suppressed OR marked INVALID
- [ ] If suppressed: show "Traveler output blocked — leakage detected" placeholder
- [ ] If marked invalid: red border + "STRICT MODE: OUTPUT BLOCKED" label
- [ ] Assertion panel marks run as FAILED (not just warned)
- [ ] Raw packet and sanitized view remain visible for debugging

---

## Correction 5: Make "System Understanding Summary" Derived

**Problem:** The Flow Simulation's "System understanding summary" could drift into UI-owned inference logic, quietly growing its own spine.

**Fix:** The summary shown in Flow Simulation must be assembled ONLY from:

- `packet` (facts + derived_signals)
- `validation` (errors + warnings)
- `decision` (decision_state + confidence + risk_flags + ambiguities)
- `strategy` (session_goal + priority_sequence + suggested_opening)

### Rules

- No separate UI inference logic
- If a summary helper is needed, put it under `src/intake/` as a presentation helper
- The summary must be a deterministic function of the spine outputs
- No additional data sources, no LLM calls, no ad-hoc heuristics

---

## Correction 6: Prevent Rerun Drift

**Problem:** Switching tabs or mode views could silently rerun the spine, causing inconsistent outputs and poor UX.

**Fix:** Add one explicit acceptance criterion:

### Acceptance Criterion: No Rerun on Tab Switch

- Switching tabs must NOT rerun the spine
- Switching mode views (Strict/Lenient) must NOT rerun the spine
- The spine reruns ONLY when:
  - `Run Spine` button is clicked, OR
  - The user explicitly loads/runs a fixture again
- `st.session_state` must hold the last successful outputs
- Clear display of "Last run: <timestamp>" on each screen

---

## Correction 7: Documentation Rule

- The component spec and acceptance checklist are primary docs
- Any implementation note or review note must reference them, not replace them
- Do not delete historical documentation — preserve and archive

---

## Execution Order

After applying these corrections, execute in this order:

1. **WB-001:** Create `src/intake/orchestration.py` with `run_spine_once()` ✅ DONE
2. **WB-002:** Define formal fixture schema + create sample fixtures ✅ DONE
3. **WB-003:** Create thin Streamlit app shell with tab structure and session state
4. _(stop for review after WB-003)_
